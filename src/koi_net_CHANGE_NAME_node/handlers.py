import structlog
from koi_net.processor.handler import (
    KnowledgeHandler, 
    HandlerType, 
    HandlerContext,
    KnowledgeObject
)

log = structlog.stdlib.get_logger()


@KnowledgeHandler.create(
    handler_type=HandlerType.RID,
    rid_types=[])
def my_handler(ctx: HandlerContext, kobj: KnowledgeObject):
    log.info(f"Handling {ctx.identity.rid}")
