import requests
import json
import sys
sys.path.append('..')
from utils.translate import translator_youdao
from config import CONFIG


def get_t5_result(query,url = CONFIG.qagen_api, limit=60):
    payload = json.dumps({
        "query": query,
        "limit": limit
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.text)
    return json.loads(response.text)



class answer_QA:
    url = CONFIG.qagen_api

    @classmethod
    def QAgeneration(cls, method="template", doc={}, url = "", text='', segdict={}):

        # doc:dict,include name,summary,tag
        # text:user's input
        if not url:
            url = cls.url
        qapair = {}
        name = doc.get("name","")
        tag = doc.get("tag","")
        summary = doc.get("summary",text)
        if name not in text or tag == "hanzi":
            return False

        flag = segdict.get(name, "")
        if method == "t5":
            send = translator_youdao(summary)
            # in ENGLISH
            answer_dict = get_t5_result(send,url)
            if answer_dict.get("code")==0:
                qalist =  answer_dict.get("data")
                if qalist:
                    Q_en = qalist[0].get("question")
                    Q_ch = translator_youdao(Q_en)
                    answer = qalist[0].get("answer")
                    qapair = {"q": Q_ch, "a": text, "name": answer}

        if method == "template" or qapair is None:
            if flag == "np":
                question = "{}是谁？".format(name)
                answer = "{}".format(summary)
            else:
                question = "{}是什么？".format(name)
                answer = "{}".format(summary)
            qapair = {"q": question, "a": answer, "name": name}

        return qapair

if __name__ == '__main__':
    query = "清华大学，简称“清华”，是中华人民共和国教育部直属的全国重点大学，位列国家“双一流”A类、“985工程”、“211工程”，入选“2011计划”、“珠峰计划”、“强基计划”、“111计划”，为九校联盟、松联盟、中国大学校长联谊会、亚洲大学联盟、环太平洋大学联盟、中俄综合性大学联盟、清华—剑桥—MIT低碳大学联盟成员、中国高层次人才培养和科学技术研究的基地，被誉为“红色工程师的摇篮”。"
    print("中文问题：",query)
    print(answer_QA.QAgeneration(method="t5",text = query))


