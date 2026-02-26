from rid_lib.types import SlackMessage, SlackUserGroup


class AskCoreThread(SlackMessage):
    namespace = "ask-core.thread"
    
class AskCoreResponse(SlackMessage):
    namespace = "ask-core.response"
    
class AskTopicGroup(SlackUserGroup):
    namespace = "ask-tg.topic-group"

class AskRankedResponses(SlackMessage):
    namespace = "ask.ranked_responses"
    
class ThreadLink(SlackMessage):
    namespace = "ask.thread-link"
