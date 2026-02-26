from dataclasses import dataclass

from koi_net.components import Cache, Effector, KobjQueue
from koi_net.components.interfaces import KnowledgeHandler, HandlerType
from koi_net.protocol import KnowledgeObject
from rid_lib.ext import Bundle
from rid_lib.types import SlackMessage
from slack_bolt import App

from .config import AskViewNodeConfig

from .models import AskCoreResponseModel, AskCoreThreadModel, RankedResponsesModel, ThreadLinkModel, TopicGroupModel

from .rid_types import AskCoreResponse, AskCoreThread, AskRankedResponses, AskTopicGroup, ThreadLink


@dataclass
class ResponseRankingHandler(KnowledgeHandler):
    cache: Cache
    slack_app: App
    effector: Effector
    kobj_queue: KobjQueue
    config: AskViewNodeConfig
    
    handler_type = HandlerType.Network
    rid_types = (AskRankedResponses,)
    
    def response_block(self, response_rid: AskCoreResponse | None, intro: str) -> list[dict]:
        if not response_rid:
            return []
        
        response_bundle = self.effector.deref(response_rid, use_network=True)
        if not response_bundle:
            self.log.warning("Failed to find response bundle")
            return []
        
        response = response_bundle.validate_contents(AskCoreResponseModel)
        
        return [
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": intro
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": response.content
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Answered by <@{response.author.user_id}>"
                    }
                ]
            }
        ]
        
    def topic_group_blocks(self, thread: AskCoreThread):
        for topic_group_rid in self.cache.list_rids([AskTopicGroup]):
            topic_group_bundle = self.cache.read(topic_group_rid)
            if not topic_group_bundle: continue
            
            topic_group = topic_group_bundle.validate_contents(TopicGroupModel)
            
            if thread in topic_group.threads:
                self.log.info(f"Thread found in {topic_group.handle}")
        
    
    def render_blocks(self, ranked_responses: RankedResponsesModel) -> list[dict]:
        thread_bundle = self.effector.deref(ranked_responses.thread, use_network=True)
        if not thread_bundle:
            self.log.warning("Failed to find thread bundle")
            return
        
        thread = thread_bundle.validate_contents(AskCoreThreadModel)
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": thread.prompt
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Asked by <@{thread.asker.user_id}>"
                    }
                ]
            }
        ]
        
        # if (
        #     ranked_responses.community_voted.response or
        #     ranked_responses.staff_pick.response or
        #     ranked_responses.accepted_answer
        # ):
        #     blocks.append({"type": "divider"})
            
        # if ranked_responses.community_voted.response:
        #     blocks.append(
                
        #     )
        
        blocks.extend([
            *self.response_block(ranked_responses.community_voted.response, "Community Voted - 👍"),
            *self.response_block(ranked_responses.staff_pick.response, "Staff Pick - 🏅"),
            *self.response_block(ranked_responses.accepted_answer.response, "Accepted Answer - ✅")
        ])
        
        # blocks.extend(self.topic_group_blocks(ranked_responses.thread))
        
        return blocks
        
    
    def handle(self, kobj: KnowledgeObject):
        ranked_responses = kobj.bundle.validate_contents(RankedResponsesModel)
        
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
                text=""
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
