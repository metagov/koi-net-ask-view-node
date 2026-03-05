from koi_net.core import FullNode
from slack_bolt import App

from .deref_handlers import SlackUserDereferencer

from .response_ranking_handler import ResponseRankingHandler

from .socket_mode import SlackSocketMode
from .config import AskViewNodeConfig


class AskViewNode(FullNode):
    config_schema = AskViewNodeConfig
    
    slack_app: App = lambda config: App(
        token=config.env.ask_view_slack_bot_token,
        signing_secret=config.env.ask_view_slack_signing_secret)
    
    socket_mode = SlackSocketMode
    response_ranking_handler = ResponseRankingHandler
    slack_user_dereferencer = SlackUserDereferencer