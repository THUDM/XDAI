### Agent Base

import copy
from database.models import UtterranceMode


class AgentBase(object):
    activate_kw = None
    byemsg = ["bye"]
    close_kw = "bye"
    username = "USER"
    botname = "BOT"
    version = "base"
    concat_turns = 1

    def __init__(self, sess_mgr=None):
        self.sess = sess_mgr
        self._history = []
        
    def import_history(self):
        docs = self.sess.get_history(num= max(30,self.concat_turns * 2), time_sort=1)
        self._history = copy.deepcopy(docs)

    @property
    def history(self):
        if not self._history:
            self.import_history()
        return self._history

    @classmethod
    def is_close_word(cls, text):
        if cls.close_kw is None:
            return False
        if isinstance(cls.close_kw, str) and text == cls.close_kw:
            return True
        if isinstance(cls.close_kw, list) and text in cls.close_kw:
            return True
        return False


    def make_reply(self, style="mono", mode=UtterranceMode.normal,**kwargs):
        """
        suppose all previous utterances have been stored
        """
        if mode == UtterranceMode.normal:
            if style == "mono":
                return ["嗯嗯"]
            elif style == "multi":
                return ["嗯嗯", "再见"]
        elif mode == "close":
            return self.byemsg


if __name__ == "__main__":
    pass
