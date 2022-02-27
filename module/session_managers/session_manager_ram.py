from .session_manager_base import SessionManagerBase
from config import CONFIG
from utils import get_time
from database import WindowItem, UtteranceItem
from database.models import GetSessInfo
from utils import get_logger
logger = get_logger("ChatBotAPI")

class SessionManagerRam(SessionManagerBase):
    MEM_method = CONFIG.MEM_method
    registered_window = {}
    registered_session = {}

    def __init__(self, session_doc={}, window_doc={}):
        super().__init__(session_doc=session_doc, window_doc=window_doc)
        self.history = []

    @classmethod
    def append_msg_with_ssid(cls, utt:UtteranceItem=None, session_id="", details={}):
        sess = cls.get_one_session_ins(query={"session_id":session_id})
        sess.add_utterance(utt)

    def add_utterance(self,utt:UtteranceItem=None):
        utt_doc = utt.dict()
        self.history.append(utt_doc)

    # do close
    def close_self(self):
        session_id = self.session_id
        #del self.registered_window[window_id]
        del self.registered_session[session_id]
        return

    def get_history(self, num=6, time_sort=-1):
        if time_sort ==-1:
            history = self.history[-(num + 1):][::-1]
        else:
            history = self.history[-(num + 1):]
        return history

    @classmethod
    def get_agent_by_brand(
            cls,
            item:GetSessInfo=None
    ):

        brand = cls.get_parsed_sess_item(item)
        operation = item.operation
        if brand.version == "INVALID VERSION":
            data = {"parsed_info": brand, "session_doc": {}, "window_doc": {}}
        else:
            data = cls.get_session_api(brand=brand, operation=operation)
        session_doc = data.get("session_doc")
        window_doc = data.get("window_doc")
        session_id = session_doc.get("session_id")
        if not session_doc:  # not valid user or activative code
            return None

        if session_id not in cls.registered_session:
            session_ins = cls(session_doc=session_doc, window_doc=window_doc)
            agent_ins = cls.load_agent_with_session(session_ins=session_ins)
            cls.registered_session[session_id] = agent_ins
        else:
            agent_ins = cls.registered_session.get(session_id)

        return agent_ins

    @classmethod
    def get_one_session(cls, query={},timesort=1):
        agent_ins = cls.registered_session.get(query.get("session_id"))
        if agent_ins:
            session_doc = agent_ins.sess.info
        else:
            session_doc = {}
        return session_doc

    @classmethod
    def get_one_session_ins(cls, query={}, timesort=1):
        agent_ins = cls.registered_session.get(query.get("session_id"))
        if agent_ins:
            session = agent_ins.sess
        else:
            session = None
        return session

    @classmethod
    def get_one_window(cls, query):
        window_doc = cls.registered_window.get(query.get("window_id"),{})
        return window_doc

    @classmethod
    def _update_window(cls,window_id=None,addition_dict={}):
        window_doc = cls.get_one_window({"window_id":window_id})
        window_doc.update(addition_dict)


    @classmethod
    def add_new_window(cls, window_item:WindowItem):
        cls.registered_window[window_item.window_id] = window_item.dict()

    @classmethod
    def add_new_session(cls,session_item=None,window_doc={}):
        session_doc = session_item.dict()
        session_ins = cls(session_doc=session_doc, window_doc=window_doc)
        agent_ins = cls.load_agent_with_session(session_ins=session_ins)
        cls.registered_session[session_ins.session_id]=agent_ins

    @classmethod
    def close_inactive_sessions(cls, gap_minutes=30):
        # return num
        t, stamp = get_time()
        num = 0
        for session_id, agent in cls.registered_session.items():
            t_last = agent.history[-1].get("created_t")
            if stamp - t_last > gap_minutes * 60:
                agent.sess.close_self()
                num += 1
        return num

    @classmethod
    def close_session(cls, session_id, update_window=True):
        query = {"session_id": session_id}
        logger.info(f"close session:{session_id}")
        # should be set closed at once
        agent = cls.registered_session.get(session_id)
        if agent:
            agent.sess.close_self()
            ### update window info
            if update_window:
                window_id = agent.sess.window_id
                if window_id:
                    cls._update_window(window_id,{"active_session_id":""})
            return "Success"
        else:
            return "Failed"

