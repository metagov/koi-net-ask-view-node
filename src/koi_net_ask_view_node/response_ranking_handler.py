from dataclasses import dataclass
import re

from koi_net.components import Cache, Effector, KobjQueue
from koi_net.components.interfaces import KnowledgeHandler, HandlerType
from koi_net.protocol import KnowledgeObject
from rid_lib.ext import Bundle
from rid_lib.types import SlackMessage
from slack_bolt import App

from .config import AskViewNodeConfig
from .models import (
    AskCoreResponseModel,
    AskCoreThreadModel,
    RankedResponsesModel,
    ThreadLinkModel,
    TopicGroupModel
)
from .rid_types import (
    AskCoreResponse,
    AskCoreThread,
    AskRankedResponses,
    AskTopicGroup,
    ThreadLink
)


@dataclass
class ResponseRankingHandler(KnowledgeHandler):
    cache: Cache
    slack_app: App
    effector: Effector
    kobj_queue: KobjQueue
    config: AskViewNodeConfig
    
    handler_type = HandlerType.Network
    rid_types = (AskRankedResponses, AskTopicGroup)
    
    def format_text(self, text: str):
        text = text.replace("<!everyone>", "@ everyone")
        text = text.replace("@everyone", "@ everyone")
        text = text.replace("<!channel>", "@ channel")
        text = text.replace("@channel", "@ channel")
        text = text.replace("<!here>", "@ here")
        text = text.replace("<@here>", "@ here")
        text = re.sub(r"<!subteam\^(\w+)>", "@ subteam", text)
        text = "\n".join([
            "&gt;" + line if line.startswith(("> ", "&gt; ")) else "&gt; " + line
            for line in text.splitlines()  
        ])
        return text
    
    def render_blocks(self, ranked_responses: RankedResponsesModel) -> list[dict]:
        thread_rid = ranked_responses.thread
        thread_bundle = self.effector.deref(thread_rid, use_network=True)
        if not thread_bundle:
            self.log.warning("Failed to find thread bundle")
            return
        
        thread = thread_bundle.validate_contents(AskCoreThreadModel)
        
        asker_ref = self.effector.deref(thread.asker).contents.get("real_name", f"<@{thread.asker.user_id}>")
        timestamp = thread_rid.ts.split(".")[0]
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Prompt:*\n" + self.format_text(thread.prompt)
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Asked in <#{thread_rid.channel_id}> by *{asker_ref}* on _<!date^{timestamp}^{{date}} at {{time}}|(time unknown)>_ — <{thread.permalink}|Jump to thread>"
                    }
                ]
            }
        ]
        
        topic_group_names = []
        self.log.debug("Searching topic groups...")
        for topic_group_rid in self.cache.list_rids(rid_types=[AskTopicGroup]):
            self.log.debug(topic_group_rid)
            
            topic_group_bundle = self.cache.read(topic_group_rid)
            if not topic_group_bundle: continue
            
            topic_group = topic_group_bundle.validate_contents(TopicGroupModel)
            
            self.log.debug(f"{topic_group.name} -> {topic_group.threads}")
            
            if thread_rid in topic_group.threads:
                self.log.info(f"Thread found in {topic_group.handle}")
                topic_group_names.append(topic_group.name)
                
        topic_group_str = " + ".join(topic_group_names)
        if len(topic_group_str) > 0:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Tagged topic groups — {topic_group_str}"
                    }
                ]
            })
        
        message_map: dict[SlackMessage, list] = {}
        message_map.setdefault(ranked_responses.community_voted.response, []).append("Community Voted :+1:")
        message_map.setdefault(ranked_responses.staff_pick.response, []).append("Staff Pick :sports_medal:")
        message_map.setdefault(ranked_responses.accepted_answer.response, []).append("Accepted Answer :white_check_mark:")
        
        first_response = True
        for message, rankings in message_map.items():
            if message is None:
                continue
            
            response_bundle = self.effector.deref(message, use_network=True)
            if not response_bundle:
                self.log.warning("Failed to find response bundle")
            
            response = response_bundle.validate_contents(AskCoreResponseModel)
            ranking_str = " + ".join(sorted(rankings))
            
            author_ref = self.effector.deref(response.author).contents.get("real_name", f"<@{response.author.user_id}>")
            
            prefix = ""
            if first_response:
                prefix = "*Responses:*\n"
                first_response = False
            
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": prefix + self.format_text(response.content)
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Answered by *{author_ref}* — {ranking_str}"
                        }
                    ]
                }
            ])
            
        blocks.append({"type": "divider"})
        
        return blocks
        
    
    def handle(self, kobj: KnowledgeObject):
        if type(kobj.rid) is AskRankedResponses:
            self.log.info("processing ranked responses")
            ranked_responses = kobj.bundle.validate_contents(RankedResponsesModel)
            self.process_ranked_responses(ranked_responses)
            
        elif type(kobj.rid) is AskTopicGroup:
            self.log.info("processing topic group")
            topic_group = kobj.bundle.validate_contents(TopicGroupModel)
            for thread_rid in topic_group.threads:
                ranked_response_rid = AskRankedResponses(
                    team_id=thread_rid.team_id,
                    channel_id=thread_rid.channel_id,
                    ts=thread_rid.ts
                )
                
                ranked_responses_bundle = self.cache.read(ranked_response_rid)
                if not ranked_responses_bundle:
                    continue
                
                ranked_responses = ranked_responses_bundle.validate_contents(RankedResponsesModel)
                self.process_ranked_responses(ranked_responses)
                
    def process_ranked_responses(self, ranked_responses: RankedResponsesModel):
        thread_link_rid = ThreadLink(
            team_id=ranked_responses.thread.team_id,
            channel_id=ranked_responses.thread.channel_id,
            ts=ranked_responses.thread.ts
        )
        
        blocks = self.render_blocks(ranked_responses)
        
        if not blocks:
            self.log.warning("Block rendering failed")
            return
        
        bundle = self.cache.read(thread_link_rid)
        if bundle:
            self.log.info("Updated existing view message")
            thread_link = bundle.validate_contents(ThreadLinkModel)
            self.slack_app.client.chat_update(
                channel=thread_link.message.channel_id,
                ts=thread_link.message.ts,
                blocks=blocks
            )
            
        else:
            self.log.info("Creating new view message")
            msg = self.slack_app.client.chat_postMessage(
                channel=self.config.ask_view.slack_channel_id,
                blocks=blocks,
                text="",
                unfurl_links=False
            )
            
            thread_link = ThreadLinkModel(
                thread=ranked_responses.thread,
                message=SlackMessage(
                    team_id=ranked_responses.thread.team_id,
                    channel_id=msg["channel"],
                    ts=msg["ts"]
                )
            )
            
            self.kobj_queue.push(bundle=Bundle.generate(
                rid=thread_link_rid,
                contents=thread_link.model_dump()
            ))
