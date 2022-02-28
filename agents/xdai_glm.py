### Baseline implementation without knowledge injected using GLM as the PLM
### version = "glm_baseline"

from agents import AgentBase
from module.use_plm import getGeneratedText
from utils.processor import filter_glm
from database.models import UtterranceMode,TalkerType
from utils import get_logger

logger = get_logger("XDAI")


class ChatAgentGLMBaseline(AgentBase):
    botname = "BOT"
    version = "glm_baseline"
    activate_kw = version
    concat_turns = 6
    background = [
        ("你好", "你好, 很开心见到你"),
        ("最近怎么样", "还是老样子"),
    ]
    model = "glm"

    def __init__(self, sess_mgr=None, talkername="USER"):
        logger.info(f"init class: {self.version}, talker's name:{talkername}")
        super().__init__(sess_mgr=sess_mgr)
        self.username = talkername

    async def make_reply(self, mode="normal",**kwargs):
        if mode in [UtterranceMode.normal, UtterranceMode.activate]:
            num = self.concat_turns
            prompt = self.get_concat_history(num)
            #logger.info(f"[selected prompt]:\n{prompt}")
            raw_generated_contents = await getGeneratedText(prompt, limit=30, batchsize=1, model=self.model)
            for text in raw_generated_contents:
                reply = filter_glm(text, split="|", prefix=f"({self.botname}:|{self.username}:)")
            #logger.info(f"reply:{reply}")
            return [reply]

        elif mode == UtterranceMode.close:
            return self.byemsg

    def get_concat_history(self, num=None):
        """
        :param num: int
        :return: str
        """
        username = self.username
        history_selected = self.history[-num:]
        res = [
            "{botname}:" + i["text"]
            if i["talker"] == TalkerType.bot
            else "{username}:" + i["text"]
            for i in history_selected
        ]

        context = "|".join(
            ["{username}:" + i[0] + "|{botname}:" + i[1] for i in self.background]
        )
        res = [context] + res
        res.append("{botname}:")
        concat_text = "|".join(res)
        concat_text = concat_text.format(botname=self.botname, username=username)
        return concat_text



if __name__ == "__main__":
    pass
