#!/usr/bin/python
# -*-coding:utf-8-*-

from typing import Optional, Any, List
from pydantic import BaseModel
from utils import get_time, hashidx,set_now_time


class UtteranceItem(BaseModel):
    ### to be set
    _id: str = ""  # {session_id}_{created_t}
    #
    session_id: str = ""  # to be set
    window_id: str = ""  # to be set
    created_t: float = 0
    created_time: str = ""  # "yyyy-mm-dd HH:MM:SS"
    is_bot: bool = None  # default:user
    hash_id: str = ""  # to be set

    ### init
    text: str = ""
    talker: str = ""  # bot/ single:user, room:user_{usrid1}，user_{usrid2},...

    ### else
    mode: Optional[str] = ""
    details: Optional[dict] = {}

    def set_id(self, id=None):
        if id is None:
            if self.session_id.startswith("sess_") and len(self.session_id) >= 6:
                sess_id = self.session_id[5:]
            else:
                sess_id = "temp_sess_id"
            id = f"utt_{sess_id}_{self.created_t}"
        object.__setattr__(self, "_id", id)
        self.hash_id = f"utt_{hashidx(id)}"  # new

    def set_attr(self, id=None):
        if not self.created_t:
            set_now_time(self, is_end=False)
        if self.created_t and not self.created_time:
            self.created_time, _ = get_time(self.created_t)
        if self.created_time and not self.created_t:
            pass
        self.set_id(id=id)

        self.is_bot = self.talker == "bot"
        if self.talker == "":
            self.talker = "bot" if self.is_bot is True else "user"

    @classmethod
    def mgdict(cls, dic):
        u = cls(**dic)
        u.set_id()
        return u

    @classmethod
    def parse(
        cls,
        session_id,
        window_id,
        content,
        talker="bot",
        is_bot=True,
        created_t=0,
        created_time="",
        mode="normal",
        details={},
    ):
        if not content:
            return None
        item = cls(
            session_id=session_id,
            window_id=window_id,
            text=content,
            talker=talker,
            is_bot=is_bot,
            created_t=created_t,
            created_time=created_time,
            mode=mode,
            details=details,
        )
        item.set_attr()
        # item_dict = item.dict()
        return item  # item_dict

    @classmethod
    def parse_apibrand(cls, brand):
        if not brand:
            return None
        item = cls(
            session_id=brand.session_id,
            window_id=brand.window_id,
            text=brand.text,
            talker=brand.talker,
            mode=brand.mode,
            details=brand.details,
            created_t=brand.created_t,
        )
        item.set_attr()
        return item

    @classmethod
    def parse_simple(cls, talker="bot",text=""):
        item = cls(
            text=text,
            talker=talker,
            mode="normal",
        )
        item.set_attr()
        return item


class SessionItem(BaseModel):
    _id: Optional[str] = ""  # = session_id
    session_id: str = ""  # {window_id}_{created_time}
    hash_id: str = ""
    window_id: str = ""  # refer to window col
    version: str = ""  # important for load agent type
    username: str = ""
    created_t: float = 0
    created_time: str = ""  # "yyyy-mm-dd HH:MM:SS"
    userinfo: Optional[Any] = {}
    ### at initial:
    active: bool = True
    latest_t: float = 0
    latest_time: Optional[str] = ""
    platform: Optional[str] = "term"

    ### update within a dialogue
    talker_ids: Optional[list] = []  # when new person appear, append
    # latest_t & latest_time

    ### update after close
    ## :active: True -> False
    ## :closed_time & closed_t: 0 -> nowtime
    num_total_turns: Optional[int] = 0  # count all utt in this session
    closed_t: float = 0
    closed_time: Optional[str] = ""

    ### to_be_added
    score: Optional[dict] = {}

    def set_id(self, id=None):
        if id is None:
            if self.window_id.startswith("win_") and len(self.window_id) >= 5:
                win_id = self.window_id[4:]
            else:
                win_id = "tempwinid"
            id = f"sess_{win_id}_{self.created_time}"
        object.__setattr__(self, "session_id", id)
        object.__setattr__(self, "_id", id)
        self.hash_id = f"sess_{hashidx(id)}"

    def set_attr(self, id=None):
        if not self.created_t:
            set_now_time(self, is_end=False)
        self.set_id(id=id)

    @classmethod
    def mgdict(cls, dic):
        u = cls(**dic)
        u.set_id()
        return u

    @classmethod
    def parse(
        cls,
        window_id="",
        version="xiaodai_0.1",
        is_test=False,
        room_topic="",
        created_t=0,
        created_time="",  # todo: add other information
        platform="wechat",
        is_temp_session=False,
        username="",
    ):
        item = cls(
            window_id=window_id,
            version=version,
            is_test=is_test,
            room_topic=room_topic,
            created_t=created_t,
            created_time=created_time,
            platform=platform,
            is_temp_session=is_temp_session,
            username=username,
        )
        item.set_attr()
        return item

    @classmethod
    def parse_apibrand(cls, brand):
        item = cls(
            window_id=brand.window_id,
            version=brand.version,
            is_test=brand.is_test,
            is_temp_session=brand.is_temp_session,
            room_topic=brand.room_topic,
            platform=brand.platform,
            username=brand.username,
        )
        item.set_attr()
        return item


class WindowItem(BaseModel):
    _id: Optional[str] = ""  #  = window_id
    window_id: str = "term_TEMP"  # {platform}_{platform_id}
    platform: str = "term"  # "term"/ "web"/"wechat"
    platform_id: str = "TEMP"  # user_id/room_id
    created_t: float = 0
    created_time: str = ""  # "yyyy-mm-dd HH:MM:SS"
    hash_id: str = ""

    ### to be updated
    first_session_id: str = ""  # session_id
    latest_session_id: str = ""  # session_id
    first_session_time: str = ""  # session_id
    latest_session_time: str = ""  # session_id

    active_session_id: Optional[str] = None  # current active session
    num_sessions: Optional[int] = 0
    num_sessions_test: Optional[int] = 0
    num_member: int = 2  # bot and human

    ### to be determined
    score: Optional[dict] = {}

    @staticmethod
    def get_id(
        platform="term",
        platform_id="human",  # weixin_id
    ):
        _id = f"win_{platform}_{platform_id}"
        return _id

    def set_id(self, id=None):
        if id is None:
            id = self.get_id(platform=self.platform, platform_id=self.platform_id)
        object.__setattr__(self, "_id", id)
        object.__setattr__(self, "window_id", id)
        self.hash_id = f"win_{hashidx(id)}"

    def set_attr(self):
        if not self.created_t:
            set_now_time(self, is_end=False)
        self.set_id()

    @classmethod
    def parse(
        cls,
        platform="term",
        platform_id="human",  # weixin_id
        room_topic="",
        created_t=0,
        created_time="",
    ):
        item = cls(
            platform=platform,
            platform_id=platform_id,
            room_topic=room_topic,
            created_t=created_t,
            created_time=created_time,
        )
        item.set_attr()
        return item

    @classmethod
    def parse_apibrand(cls, brand):
        item = cls.parse(
            platform=brand.platform,
            platform_id=brand.platform_id,
            room_topic=brand.room_topic,
        )
        item.set_attr()
        return item


if __name__ == "__main__":
    pass
