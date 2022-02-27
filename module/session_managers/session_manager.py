
from .session_manager_base import SessionManagerBase
from database import Mongodb, MgOpt, WindowItem, SessionItem, UtteranceItem, ColType
from config import CONFIG
from database.models import  (
                              UtterranceMode)
from utils import get_time, get_logger


logger = get_logger("ChatBotAPI")

class SessionManager(SessionManagerBase):
    MEM_method = CONFIG.MEM_method
    if MEM_method=="mongo":
        db = Mongodb()
    DBopt = MgOpt(db)

    def __init__(self, session_doc={}, window_doc={}):
        super().__init__(session_doc=session_doc, window_doc=window_doc)


    @classmethod
    def append_msg_with_ssid(cls, utt:UtteranceItem=None, session_id="", details={}):
        res = cls.DBopt.insert_one(obj=utt, col=ColType.utterance)
        if res == "Success":
            cls._update_session(
                session_id, last_utt=utt.dict(), addition_dict={}, closed=False
            )
            return True
        else:
            return False

    # to test
    def get_history(self, num=6, time_sort=-1):
        filters = {"mode": UtterranceMode.normal}
        _, nowstamp = get_time()
        query = {}
        time_thresh = 0
        if time_thresh > 0:
            query = {"created_t": {"$gt": nowstamp - time_thresh}}
        query.update(filters)
        cursor = self.DBopt.find(
            query={"session_id": self.session_id, **query},
            col=ColType.utterance,
            sort={"created_t": time_sort},
        )
        docs = list(cursor)
        return docs

    @classmethod
    def get_one_session(cls, query={},timesort=1):
        doc = cls.DBopt.find_one(query,col=ColType.session,sort={"created_t":timesort})
        logger.info("doc:{}".format(doc))
        return doc

    @classmethod
    def get_one_window(cls, query={}, timesort=1):
        doc = cls.DBopt.find_one(query,col=ColType.window,sort={"created_t":timesort})
        return doc

    @classmethod
    def __get_one_utterance(cls, query={},timesort=1):
        doc = cls.DBopt.find_one(query,col=ColType.utterance,sort={"created_t":timesort})
        return doc

    @classmethod
    def add_new_window(cls,window_item:WindowItem):
        res = cls.DBopt.insert_one(window_item, col=ColType.window)


    @classmethod
    def add_new_session(cls,session_item:SessionItem=None,**kwargs):
        res = cls.DBopt.insert_one(session_item, col=ColType.session)


    @classmethod
    def close_session(cls, session_id, update_window=True):
        query={"session_id": session_id}
        doc = cls.get_one_session({"session_id": session_id})
        logger.info(f"close session:{session_id}")
        # should be set closed at once
        cls.DBopt.update_one(query, set_dict={"active": False}, col=ColType.session)
        if doc.get("active") == False:
            msg = "error:is already closed"
        else:
            ### update session info
            msg = "success"
        cls._update_session(session_id, closed=True)

        ### update window info
        if update_window:
            window_id = doc.get("window_id")
            if window_id:
                cls._update_window(window_id=window_id)
        return msg

    @classmethod
    def close_inactive_sessions(
        cls, gap_minutes=0, is_active=True, do_close=True
    ):
        min_interval= 60 * gap_minutes,
        nowtime, nowstamp = get_time()
        # query = {"latest_t":{"$lt":nowstamp-min_interval,"$ne":0}}
        query = {"latest_t": {"$lt": nowstamp - min_interval}}
        if is_active:
            query.update({"active": True})
        cursor = cls.DBopt.find(query,col=ColType.session)
        docs = list(cursor)
        num = len(docs)
        if do_close:
            for doc in docs:
                session_id = doc.get("_id")
                created_t = doc.get("created_t", 0)
                cursor_x = cls.DBopt.find(
                    query={"session_id":session_id},
                    sort={"created_t":-1},
                    col=ColType.utterance,
                    limit=1,
                )
                last_utt = list(cursor_x)
                if not last_utt and nowstamp - created_t < min_interval:
                    continue
                if last_utt:
                    last_utt = last_utt[0]
                else:
                    last_utt = {}
                utt_created_t = last_utt.get("created_t", 0)
                if nowstamp - utt_created_t < min_interval:
                    continue
                cls.close_session(doc.get("_id"), update_window=True)
        return num



    # todo:deal with talker_ids
    @classmethod
    def _update_session(cls, session_id=None, addition_dict={}, last_utt=None, closed=False):
        query = {"_id": session_id}

        if isinstance(addition_dict, dict) and addition_dict:
            cls.DBopt.update_one(query, set_dict=addition_dict,col=ColType.session)
        #sess_obj = self.get_one_session(query)

        ### update latest utterance
        if last_utt is None:
            last_utt = cls.__get_one_utterance(
                query={"session_id": session_id},timesort=-1
            )
            if not last_utt:
                return

        if not closed:
            # talker = last_utt.get("talker","")
            # talker_ids = sess_obj.get("talker_ids",["bot"])
            update_dict = dict(
                latest_t=last_utt.get("created_t"),
                latest_time=last_utt.get("created_time"),
                # talker_ids = list(set(talker_ids.append(talker)))
            )
        ### if need to close session, update statistical info
        elif closed:
            num_turns_total = cls.DBopt.count_docs(
                query={"session_id": session_id},
                col=ColType.utterance,
            )
            num_turns_bot = cls.DBopt.count_docs(
                query={"session_id": session_id,"is_bot": True},
                col=ColType.utterance,
            )
            # num_turns_user = num_turns_total - num_turns_bot
            update_dict = dict(
                active=False,  # make sure
                num_turns={
                    "total": num_turns_total,
                    "from_bot": num_turns_bot,
                    # "from_user":num_turns_user
                },
                num_total_turns=num_turns_total,
                closed_t=last_utt.get("created_t"),
                closed_time=last_utt.get("created_time"),
                latest_t=last_utt.get("created_t"),
                latest_time=last_utt.get("created_time"),
            )
        cls.DBopt.update_one(query, set_dict=update_dict, col=ColType.session)

    @classmethod
    def _update_window(
        cls,
        window_id=None,
        addition_dict={},
    ):
        ### by query the db
        # first_session: session_id
        # latest_session: session_id
        # active_session_id
        query = {"_id": window_id}
        if isinstance(addition_dict, dict) and addition_dict:
            cls.DBopt.update_one(query,set_dict=addition_dict,col=ColType.window)
        # print(query)
        first_session  = cls.get_one_session(
            query={"window_id": window_id},
            timesort= 1,
        )
        latest_session = cls.get_one_session(
            query={"window_id": window_id},
            timesort=-1,
        )

        if not first_session or not latest_session:
            first_session = {}
            latest_session = {}
        # print(first_session,latest_session)
        num_sessions_total = cls.DBopt.count_docs(
            query={"window_id":window_id},
            col=ColType.session
        )
        num_sessions_test = cls.DBopt.count_docs(
            query={"window_id":window_id,"is_test": True},
            col=ColType.session
        )
        if latest_session.get("active") is True:
            active_session_id = latest_session.get("session_id")
        else:
            active_session_id = ""

        update_dict = dict(
            first_session_id=first_session.get("session_id"),
            latest_session_id=latest_session.get("session_id"),
            first_session_time=first_session.get("created_time"),
            latest_session_time=latest_session.get("created_time"),
            active_session_id=active_session_id,
            num_sessions=num_sessions_total,
            num_sessions_test=num_sessions_test,
        )
        # print(update_dict)
        cls.DBopt.update_one(query, set_dict=update_dict, col=ColType.window)
        return update_dict

