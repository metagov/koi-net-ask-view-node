from dataclasses import dataclass

from koi_net.components.interfaces import DerefHandler
from rid_lib.ext import Bundle
from rid_lib.types import SlackUser
from slack_bolt import App


@dataclass
class SlackUserDereferencer(DerefHandler):
    slack_app: App
    
    rid_types=(SlackUser,)
    
    def handle(self, rid: SlackUser):
        profile_resp = self.slack_app.client.users_profile_get(user=rid.user_id)
        profile = profile_resp["profile"]
        
        user_resp = self.slack_app.client.users_info(user=rid.user_id)
        user = user_resp["user"]
        
        user["profile"] = profile
        
        return Bundle.generate(rid, user)