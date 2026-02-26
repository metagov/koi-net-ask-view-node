from koi_net.core import FullNode
from .config import MyNodeConfig
from .handlers import my_handler


class MyNode(FullNode):
    config_schema = MyNodeConfig
    knowledge_handlers = FullNode.knowledge_handlers + [
        my_handler
    ]