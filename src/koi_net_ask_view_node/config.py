from pydantic import BaseModel
from rid_lib.types import KoiNetNode
from koi_net.config import (
    FullNodeConfig, 
    KoiNetConfig, 
    FullNodeProfile,
    EnvConfig
)

from .rid_types import AskCoreThread, AskRankedResponses, AskTopicGroup


class SlackEnvConfig(EnvConfig):
    ask_view_slack_bot_token: str
    ask_view_slack_signing_secret: str
    ask_view_slack_app_token: str

class AskViewConfig(BaseModel):
    slack_channel_id: str | None = None

class AskViewNodeConfig(FullNodeConfig):
    koi_net: KoiNetConfig = KoiNetConfig(
        node_name="ask-view",   # human readable name for your node
        node_profile=FullNodeProfile(),
        rid_types_of_interest=[
            KoiNetNode,
            AskTopicGroup,
            AskRankedResponses,
            AskCoreThread
        ]
    )
    env: SlackEnvConfig = SlackEnvConfig()
    ask_view: AskViewConfig = AskViewConfig()
    