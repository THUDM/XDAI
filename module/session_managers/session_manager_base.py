from agents import (
    DEFAULT_CHATBOT,
    IN_USE_AGENTS_DICT,
)
from database import Mongodb, MgOpt, WindowItem, SessionItem, UtteranceItem
from database.models import  (OptType,
                            UtterranceMode,
                            PlatformType,
                            APIBrand,
                            GetSessInfo,
                            TalkerType,
                            MsgModel)
from config import CONFIG
from utils import get_logger
mgdb = Mongodb()
DBopt = MgOpt(mgdb)

logger = get_logger("ChatBotAPI")

class SessionManagerBase:
    IN_USE_SINGLE_AGENTS_DICT = IN_USE_AGENTS_DICT
    DEFAULT_CHATBOT = DEFAULT_CHATBOT

    def __init__(self, session_doc={}, window_doc={}):
        self.plm_url = CONFIG.default_plm_api
        self.info = session_doc
        self.window = window_doc
        self.platform = self.info.get("platform", "")
        self.version = session_doc.get("version")
        self.session_id = session_doc.get("session_id")
        self.window_id = session_doc.get("window_id")

    @classmethod
    def get_one_window(cls, *args, **kwargs):
        pass

    @classmethod
    def get_one_session(cls, query={}, timesort=1):
        pass

    @classmethod
    def _update_window(cls,*args,**kwargs):
        pass

    @classmethod
    def append_msg_with_ssid(cls, utt:UtteranceItem=None, session_id="", details={}):
        sess = cls.get_one_session_ins(query={"session_id":session_id})
        sess.add_utterance(utt)


    def close_self(self):
        pass

    def get_history(self, num=6, time_sort=-1):
        """
        :param num: history num
        :param time_sort: in chronological order or reversed
        :return: history docs
        """
        docs = []
        raise NotImplementedError

    @classmethod
    def __check_activate_version(
        cls,
        userinput="",
        **kwargs,
    ):
        """
        check if userinput activates an agent
        if true: return the agent's version
        else： return ""
        """
        agent = cls.IN_USE_SINGLE_AGENTS_DICT.get(userinput,None)
        if agent:
            return agent.version
        else:  # chat
            if not cls.DEFAULT_CHATBOT:
                return ""
            else:
                return cls.DEFAULT_CHATBOT.version
        return ""


    @classmethod
    def __get_version_by_platform(cls, brand):
        version = ""
        platform = brand.platform
        print(
            platform,
            version,
            brand.userinput,
            brand.platform_id,
        )

        if platform == PlatformType.wechat:
            # === wechat manager
            version = cls.__check_activate_version(
                userinput=brand.userinput,
                platform_id=brand.platform_id,
                platform=brand.platform,
            )
            logger.info(f"version is {version}")
        elif platform == PlatformType.term:
            # === self defined
            pass
        else:
            version = cls.DEFAULT_CHATBOT.version
        return version

    # create an agent ins
    @classmethod
    def load_agent_with_session(cls, version="", session_ins=None):
        try:
            if version == "" and session_ins:
                version = session_ins.version
        except:
            return None

        agent_cls = cls.IN_USE_SINGLE_AGENTS_DICT.get(version)
        if agent_cls:
            return agent_cls(session_ins)
        return None

    def close_inactive_sessions(cls, gap_minutes=30):
        pass

    @classmethod
    def get_parsed_sess_item(cls, item: GetSessInfo):
        ### parse info
        operation = item.operation
        if operation == OptType.close:
            brand = APIBrand()
            brand.session_id = item.session_id
            print(brand.session_id)
            return brand
        version = item.version
        userinput = item.userinput
        window_info = item.window_info
        session_id = item.session_id

        ### parse windo info
        platform = window_info.platform or "tempPlatform"
        platform_id = window_info.platform_id or "TempUser"

        username = window_info.username

        window_id = WindowItem.get_id(platform=platform, platform_id=platform_id)

        brand = APIBrand()
        brand.userinput = userinput
        brand.platform = platform
        brand.platform_id = platform_id
        brand.window_id = window_id
        brand.username = username
        brand.session_id = session_id

        # === set version

        if version == "":
            version = cls.__get_version_by_platform(brand)
        elif version == "stable":
            # === default
            version = cls.DEFAULT_CHATBOT.version
        else:
            if version not in cls.IN_USE_SINGLE_AGENTS_DICT:
                version = "INVALID VERSION"
        brand.version = version
        if not brand.version:
            pass

        return brand

    @classmethod
    def get_agent_by_session_id(cls, session_id="", **kw):
        """
        :param session_id:
        :param kw:
        :return: agent_instance
        """
        session_doc = cls.get_one_session({"session_id": session_id})
        logger.info(session_doc)
        if not session_doc:
            return None

        window_id = session_doc.get("window_id", "")
        window_doc = {}
        if window_id:
            window_doc = cls.get_one_window(query={"window_id": window_id})

        if not window_doc:
            window_doc = {}

        session_ins = cls(session_doc=session_doc, window_doc=window_doc)
        agent_ins = cls.load_agent_with_session(session_ins=session_ins)
        return agent_ins

    @classmethod
    def get_parsed_msg_item(cls, item: MsgModel):
        session_id = item.session_id
        session_doc = cls.get_one_session({"session_id": session_id})
        if not session_doc:
            item.session_doc = {}
            item.window_id = ""
        else:
            item.session_doc = session_doc
            item.window_id = session_doc.get("window_id", "")

        if item.talker == TalkerType.user and item.talkername:
            item.talker = f"{TalkerType.user}_{item.talkername}"
        item.is_bot = item.talker == TalkerType.bot
        version = session_doc.get("version")

        # deal with mode
        agent = cls.get_agent_by_session_id(session_id=session_id)
        if not agent:
            return None
        if not item.mode or item.mode == UtterranceMode.normal:
            if agent.is_close_word(item.text):
                mode = UtterranceMode.close
            elif agent.is_activate_word(item.text):
                mode = UtterranceMode.activate
            else:
                mode = UtterranceMode.normal
            item.mode = mode

        details = {}
        details["need_reply"] = True

        item.details = details
        content = item.text
        content = content.replace("\u2005", " ")
        if content == "":
            content = " "
        item.text = content
        return item

    @classmethod
    def get_session_api(cls, brand:APIBrand=None, operation=""):
        window_doc = cls.get_one_window(
            query={"window_id": brand.window_id}
        )
        if not window_doc:
            window_item = WindowItem.parse_apibrand(brand)
            window_doc = window_item.dict()
            res = cls.add_new_window(window_item)
            window_opt = OptType.create  # 新建一个window
        else:
            window_opt = OptType.query  # 无操作

        if brand.is_temp_session:
            active_session_id = ""
        else:
            active_session_id = window_doc.get("active_session_id")

        if operation == OptType.create_multi_sessions:
            active_session_id = ""

        session_opt = OptType.query  # 无操作
        if not active_session_id and not brand.version:
            session_id = ""
        elif not active_session_id:
            ### create new session
            if operation not in [
                OptType.create_if_not_exists,
                OptType.create_multi_sessions,
            ]:
                session_id = ""
            else:
                session_item = SessionItem.parse_apibrand(brand)
                cls.add_new_session(session_item,window_doc=window_doc)
                cls._update_window(window_id=brand.window_id)
                session_id = session_item.session_id
                session_opt = OptType.create
        elif active_session_id:
            session_id = active_session_id

        session_doc = cls.get_one_session({"session_id": session_id})
        window_doc = cls.get_one_window({"window_id": window_doc.get("window_id", "")})
        if not session_doc:
            session_doc = {}

        brand_new = brand.dict()
        brand_new.update(
            {
                "operation": operation,
                "window_opt": window_opt,
                "session_opt": session_opt,
            }
        )
        data = {
            "parsed_info": brand_new,
            "session_doc": session_doc,
            "window_doc": window_doc,
        }
        return data

    @classmethod
    def close_session(cls, session_id, update_window=True):
        pass