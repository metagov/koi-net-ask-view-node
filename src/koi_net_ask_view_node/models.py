from pydantic import BaseModel, Field
from rid_lib.types import SlackMessage, SlackUser, SlackUserGroup

from .rid_types import AskCoreThread, AskCoreResponse, AskCoreThread


class AskCoreThreadModel(BaseModel):
    asker: SlackUser
    prompt: str
    original_msg: SlackMessage
    permalink: str

class AskCoreResponseModel(BaseModel):
    author: SlackUser
    content: str
    original_msg: SlackMessage
    permalink: str
    thread: AskCoreThread
    
    reactions: dict[str, list[SlackUser]] = Field(default_factory=dict)

class RankingModel(BaseModel):
    response: AskCoreResponse | None = None
    ranking: int = 0

class RankedResponsesModel(BaseModel):
    thread: AskCoreThread
    community_voted: RankingModel = RankingModel() # 👍 :+1
    staff_pick: RankingModel = RankingModel() # 🏅 :sports_medal
    accepted_answer: RankingModel = RankingModel() # ✅ :white_check_mark

class TopicGroupModel(BaseModel):
    usergroup: SlackUserGroup
    handle: str
    name: str
    emoji: str | None = None
    users: list[SlackUser] = []
    threads: list[AskCoreThread] = []
    
class ThreadLinkModel(BaseModel):
    thread: AskCoreThread
    message: SlackMessage

