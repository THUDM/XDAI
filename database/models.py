#!/usr/bin/python
# -*-coding:utf-8-*-

from typing import Dict, Optional, List, Any, Union
from enum import Enum
from pydantic import BaseModel


class PlatformType(str, Enum):
    api = "api"  # default api
    term = "term"  # terminal
    wechat = "wechat"  # wechaty


class UtterranceMode(str, Enum):
    close = "close"
    activate = "activate"
    normal = "normal"


class OptType(str, Enum):
    close = "close"
    create = "create"
    update = "update"
    query = "query"
    delete = "delete"
    create_if_not_exists = "force_create"
    create_multi_sessions = "multi_create"


class SessionType(str, Enum):
    active = "active"
    normal = "normal"


class TalkerType(str, Enum):
    bot = "bot"
    user = "user"

# =====
class SingleUserInfo(BaseModel):
    platform: Optional[PlatformType] = PlatformType.wechat
    platform_id: str = "exampleuserid"
    username: Optional[str] = "username"


# =============================================
### Hua API
class History(BaseModel):
    # history: Optional[Union[List[Tuple[str]], str]]
    history: Optional[List] = []
    botname: Optional[str] = "BOT"
    username: Optional[str] = "user_id123"
    version: str = "base"


class Query(BaseModel):
    query: Optional[Any] = "你好呀"
    brand: Optional[History] = {}
    platform: PlatformType = PlatformType.api


class ResBody(BaseModel):
    code: int = 0
    msg: str = "ok"
    debug: Optional[Any] = {}
    data: Optional[Any] = {}
    # brand:Optional[Any]


# =======================================================


class GetSessInfo(BaseModel):
    operation: OptType = (
        OptType.create_if_not_exists
    )  # 如果不存在activesession 新建一个session并把window的这个字段更新
    # OptType.query 单纯查询当前活跃session,如果没有,则返回无
    version: Optional[str] = ""  # if assigned typical version
    userinput: Optional[str] = ""  # version may be defined by userinput text
    setup_type: List[Optional[SessionType]] = [
        SessionType.normal
    ]  # 新建立的session的模式, 有可能既是test 又是temp, 所以用list
    window_info: Optional[SingleUserInfo] = SingleUserInfo()
    session_id: Optional[str] = ""  # 如果只是想查询该id的session_doc


class APIBrand(BaseModel):
    platform: Optional[str] = ""
    platform_id: Optional[str] = ""
    version: Optional[str] = ""
    is_test: bool = False
    is_temp_session: bool = False
    window_id: Optional[str] = ""
    room_topic: Optional[str] = ""
    username: Optional[str] = ""
    userinput: str = ""
    session_id: str = ""


class MsgModel(BaseModel):
    session_id: str = ""
    window_id: str = ""
    talker: TalkerType = TalkerType.user
    talkername: str = ""
    text: str = ""
    created_t: float = 0
    created_time: str = ""
    is_bot: bool = True
    mode: str = ""
    session_doc: Optional[Dict] = None
    details: Optional[Dict] = {}


class GenReply(BaseModel):
    session_id: str = ""
    mode: str = ""


class SentSim(BaseModel):
    target: str = ""
    candidates: List[str] = []
