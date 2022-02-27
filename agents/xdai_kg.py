### GLM + open knowledge injected (Using Xlore & xlink)
### For better performance, you can add more components like preprocess and check-result-and-regenerate.
### version = "xdai_glm_kg"

from agents import AgentBase
from module.use_plm import getGeneratedText
from utils.processor import filter_glm
from utils import get_logger
from database.models import UtterranceMode
from module.internal_api import get_similarity_scores_query
from module.xloreapi import Xlore
import math

logger = get_logger("XDAI")

class ChatAgent_OPEN(AgentBase):
    botname = "B"
    username = "A"
    close_kw = ["bye"]
    byemsg = ["和你聊天很愉快，再见~"]
    version = "xdai_glm_kg"
    activate_kw = version
    concat_turns = 6
    background = [
        ("你好", "你好, 很开心见到你"),
        ("最近怎么样", "还是老样子"),
    ]
    model = "glm"

    def __init__(self, sess_mgr=None, talkername="A"):
        logger.info(f"init class: {self.version}, talker's name:{talkername}")
        super().__init__(sess_mgr=sess_mgr)
        self.username = talkername

    async def make_reply(self,  mode="normal",**kwargs):
        if mode in [UtterranceMode.normal, UtterranceMode.activate]:
            num = self.concat_turns
            prompt = self.get_concat_history(num)
            logger.info(f"[selected prompt]:\n{prompt}")
            raw_generated_contents = await getGeneratedText(prompt, limit=30, batchsize=1,model=self.model)
            for text in raw_generated_contents:
                reply = filter_glm(text, split="|", prefix=f"({self.botname}:|{self.username}:)")
            logger.info(f"reply:{reply}")
            return [reply]

        elif mode == UtterranceMode.close:
            return self.byemsg

    def get_concat_history(self, num=None):
        history_utts = self.get_chatlog_utterances(num=num)
        imported_qapairs = self.get_external_retrieved_qapairs()
        query = self.history[-1]
        all_candidates = history_utts + imported_qapairs
        if all_candidates:
            sim_res = self.score_prompt_sim(target=query.get("text"), prompt_list=all_candidates)
            candidates_ranking = [
                (c.get("text"), c.get("weight", 0.5) * sim * max(30, len(c.get("text")))/ 30)
                for c, sim in zip(all_candidates, sim_res)
            ]
            sorted_prompts = sorted(candidates_ranking, key=lambda x: x[-1])
            #print(sorted_prompts)
            sorted_prompts = [i[0] for i in sorted_prompts][-12:]
        else:
            sorted_prompts = []

        sorted_prompts.append("{username}"+":{}".format(query.get("text")))
        sorted_prompts.append("{botname}:")
        concat_text = "|".join(sorted_prompts)
        concat_text = concat_text.format(botname=self.botname, username=self.username)
        return concat_text

    def score_prompt_sim(self, target="", prompt_list=[]):
        ### prompt_list = [(q,a)]
        if not target:
            target = self.history[-1].get("text")
        target = target.replace("{botname}:", "").replace("{username}:", "")
        text_list = []
        for item in prompt_list:
            if isinstance(item, dict):
                q = item.get("q", "")
                a = item.get("a", "")
                text = q + a
            elif isinstance(item, str):
                text = item
            elif isinstance(item,tuple):
                try:
                    q = item[0]
                    a = item[1]
                    text = q + a
                except:
                    text = ""
            text = text.replace("{botname}:","").replace("{username}:","")
            text_list.append(text)

        res = get_similarity_scores_query(target=target, candidates=text_list)
        return res

    def get_chatlog_utterances(self,num):
        history_selected = self.history[-num:-1][::-1]
        def process_utt(utt, order=0):
            text = utt.get("text")
            talker = "{botname}" if utt.get("talker") == "bot" else "{username}"
            w = 1 + math.exp(-0.2 * order)
            res = {"text": f"{talker}:{text}", "weight": w}
            return res

        history_utts = [
            process_utt(doc, order=i) for i, doc in enumerate(history_selected)
        ]
        return history_utts

    def __get_conversational_cold_start(self):
        qapairs = [{"q": i[0], "a": i[1]} for i in self.background]
        return qapairs

    def __get_xlore_knowledge(self):
        if len(self.history) >= 3:
            utts = [self.history[-1], self.history[-3]]
        else:
            utts = self.history[::-1]

        if len(self.history) >= 1:
            questions = [doc.get("text", "") for doc in utts]
        else:
            return None
        logger.info("question:{}".format(questions))
        qapairs = []
        for i, text in enumerate(questions):
            cur_qapairs = Xlore.qa(text=text,trim=100)
            qapairs.extend(cur_qapairs)

            if cur_qapairs:
                break
        qapairs =  qapairs[:3]
        logger.info("exlore result:{}".format(qapairs))
        return qapairs

    def get_external_retrieved_qapairs(self):
        ###
        SourceDict = {
            "coldstart": (self.__get_conversational_cold_start, 0.1),
            "xlore":(self.__get_xlore_knowledge, 0.5)
        }
        all_pairs = []

        def merged(item, weight):
            q = item.get("q")
            a = item.get("a")
            text = "|".join(["{username}:" + q, "{botname}:" + a])
            return {"q": q, "text": text, "weight": weight}

        for k, v in SourceDict.items():
            func, w = v[0], v[1]
            qapirs = func()
            qapirs = [merged(item, w) for item in qapirs]
            all_pairs.extend(qapirs)
            print(k, v, qapirs)

        return all_pairs

if __name__ == "__main__":
    pass
