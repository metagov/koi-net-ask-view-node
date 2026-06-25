from dataclasses import dataclass
from logging import Logger
from rid_lib.types import SlackMessage
from slack_bolt import App
from koi_net.components import Cache, KobjQueue

from .config import AskViewNodeConfig
from .models import ThreadLinkModel
from .rid_types import ThreadLink


@dataclass
class SlackHandlers:
    log: Logger
    slack_app: App
    kobj_queue: KobjQueue
    cache: Cache
    config: AskViewNodeConfig
    
    def __post_init__(self):
        self.register_handlers()
    
    def register_handlers(self):
        self.slack_app.event("message")(self.handle_msg_event)
        
    def handle_msg_event(self, event: dict):
        team_id = event["team"]
        channel_id = event["channel"]
        ts = event["ts"]
        user_id = event["user"]
        thread_ts = event.get("thread_ts")
        
        text = event["text"]
        
        if thread_ts:
            thread_rid = SlackMessage(team_id, channel_id, thread_ts)
            
            for thread_link_rid in self.cache.list_rids(rid_types=(ThreadLink,)):
                bundle = self.cache.read(thread_link_rid)
                if not bundle:
                    continue
                
                thread_link = bundle.validate_contents(ThreadLinkModel)
                if thread_link.message == thread_rid:
                    self.slack_app.client.chat_postEphemeral(
                        channel=channel_id,
                        thread_ts=thread_ts,
                        user=user_id,
                        text="You've responded to a thread archive. To parcticipate in the conversation, click the 'Jump to thread' button below the 'Prompt' and post your response there!"
                    )