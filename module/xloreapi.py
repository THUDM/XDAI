import requests
from utils.posseg import PosTagging
from module.qa_t5 import answer_QA
from utils.stopwords import stopwordslist

import re
stopw = stopwordslist()
class Xlore:
    xlink_url = "https://xlink.xlore.cn/xlinkapi/link"
    xlore_url = "http://api.xlore.cn/query"
    cut_method = "jieba"

    @classmethod
    def xlink(cls,text):
        print(text)
        query = {"text":text,"lang":"zh","domain":"zh"}
        headers ={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        url = cls.xlink_url
        data = requests.request("POST", url, data=query, headers=headers)
        data = data.json()
        mentions = data.get("mentions",[])

        res_names = set()
        res = []
        for m in mentions:
            label = m.get("label","")
            if label in res_names:
                continue
            else:
                res_names.add(label)
            instance_url = m.get("url","")
            abstract = m.get("abstract","")
            abstract = cls.filter_html(abstract)
            doc = cls.parse_instance(label=label, abstract=abstract, uri=instance_url)
            res.append(doc)
        return res

    @classmethod
    def parse_instance(cls,ins=None,label="",abstract="",uri=""):
        if ins:
            label = ins.get("Label", "")
            uri = ins.get("Uri", "")
            abstract = ins.get("Abstracts", "")
        elif label:
            pass
        return {"name": label, "uri": uri, "summary": abstract}


    @classmethod
    def xlore_search(cls,word="",uri="",instance=""):
        headers = {
            "Content-Type": "application/json",
        }
        url = cls.xlore_url
        query = dict(word=word,uri=uri,instance=instance)
        data = requests.request("GET", url, headers=headers, params=query)
        data = data.json()
        if uri:
            label = data.get("label",{}).get("label","")
            abstract = data.get("abstracts",{}).get("enwiki")
            abstract = cls.filter_html(abstract)
            return [{"name":label,"uri":uri,"summary":abstract}]
        elif instance or word:
            instances = data.get("Instances",[])
            res = []
            for ins in instances:
                doc = cls.parse_instance(ins=ins)
                if "zhi" in doc.get("uri",""):
                    continue
                else:
                    res.append(doc)
            return res

    @staticmethod
    def filter_html(text):
        pattern = re.compile(r"<.*?>|\[.*?\]|\(.*?\)|（.*?）")
        text = re.sub(pattern,"",text)
        text = re.sub(pattern, "", text)
        return text

    @classmethod
    def entity_link(cls,text):
        text_cut,seg_dict = PosTagging.segs(text, method=cls.cut_method, seg_only=True, segdict=True)
        text_cut = " ".join(text_cut)
        query_text = text_cut+";"+text # raise xlink accuracy
        docs = cls.xlink(query_text)
        res = []
        for doc in docs:
            name = doc.get("name")
            summary = doc.get("summary")
            flag = seg_dict.get(name, "")
            if name in stopw or (f"《{name}》" in summary and f"《{name}》" not in text):
                continue
            res.append(doc)
        return res

    @classmethod
    def qa(cls,text="",trim=30):
        docs = cls.entity_link(text)
        qapairs = []
        for doc in docs:
            qapair = answer_QA.QAgeneration(method="template",doc=doc,text=text)
            answer = qapair.get("a","")
            if len(answer)>trim:
                answer = answer[:trim-3]+"..."
            qapair["a"] = answer
            if qapair:
                qapairs.append(qapair)
        return qapairs

    @classmethod
    def qa_list(cls, texts=[]):
        qapairs = []
        for i, text in enumerate(texts):
            cur_qapairs = cls.qa(text=text)
            qapairs.extend(cur_qapairs)
            if cur_qapairs:
                break
        return qapairs, i

if __name__=="__main__":
    text = """北京冬奥会开始了，你在哪呢"""
    print(Xlore.entity_link(text))
    print(Xlore.qa(text))
    import time
    st = time.time()
    text = """你觉得羽生结弦怎么样"""
    print(Xlore.qa(text))
    print(time.time()-st)