import asyncio
import os
import sys
import json
import re
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from config import CONFIG
from module.use_plm import api_async, req_api

headers = {
    "Content-Type": "application/json;charset=utf8",
}

def get_valid_session(
    platform="wechat",
    username="",
    platform_id="",
    userinput="",
):
    setup_type = ["normal"]
    window_info = {}
    window_info["platform"] = platform
    window_info["platform_id"] = platform_id
    window_info["username"] = username

    query = dict(
        operation="force_create",
        version="",
        userinput=userinput,
        setup_type=setup_type,
        window_info=window_info,
        session_id="",
    )
    url = CONFIG.get_session_id_api

    data = req_api(url=url, payload=query, method="POST", headers=headers)
    # print(data)
    session_doc = data.get("data", {}).get("session_doc", False)
    if session_doc:
        session_id = session_doc.get("session_id")
        return session_id
    else:
        return None


def save_msg_with_session_id(
    session_id="", talker="", talkername="", text="", mode="normal"
):
    url = CONFIG.save_msg_api
    payload = {
        "session_id": session_id,
        "talker": talker,
        "talkername": talkername,
        "text": text,
        "mode": mode,
    }
    try:
        data = req_api(url=url, payload=payload, method="POST", headers=headers)
        utterance_doc = data.get("data", {}).get("utterance_doc", False)
        save_result = data.get("data", {}).get("save_result", False)
        print(data)
        if save_result:
            return utterance_doc
        else:
            return False
    except Exception as e:
        print(str(e))
        return False


async def get_reply_api(session_id="", mode=""):
    url = CONFIG.gen_reply_api
    payload = {"session_id": session_id, "mode": mode}
    try:
        data = await api_async(url=url, payload=payload, headers=headers)
        reply_tuples = data.get("data", {}).get("reply_tuples", False)
        return reply_tuples
    except Exception as e:
        print(str(e))
        return False


def get_similarity_scores_query(target="", candidates=[]):
    url = CONFIG.sentsim_api
    payload = {"target": target, "candidates": candidates}
    try:
        data = req_api(url=url, payload=payload, method="GET", headers=headers)
        res = data.get("data", {}).get("res")
        print(data)
        return res
    except Exception as e:
        print(str(e))
        return False

async def get_response(history=[], 
                 query="",
                 botname="BOT",
                 username="USER",
                 version=""):
    url = CONFIG.query_plain_api
    print(url)
    payload = {
        "query":query,
        "platform":"api",
        "brand":{
            "botname":botname,
            "username":username,
            "version": version,
            "history":history,
        }
    }

    try:
        data = req_api(url=url, payload=payload, method="POST", headers=headers)
        res = data.get("data", {}).get("reply")
        return res
    except Exception as e:
        print(str(e))
        return False



async def get_faq_pairs_api(query, topic="general", topk=3):
    url = CONFIG.faq_api
    payload = {"app_id": topic, "query": query, "topK": topk}
    res= req_api(url=url, payload=payload, method="POST", headers=headers)
    questions = res.get("questions", [])
    answer_docs = res.get("answers", [])
    scores = res.get("scores", [])
    qapairs = []
    for q, doc, score in zip(questions, answer_docs, scores):
        if doc is None:
            continue
        answer = doc.get("answer")
        answer = answer.strip("；;")
        answers = [answer]
        qapairs.extend([{"q": q, "a": a, "score": score} for a in answers])
    return qapairs

if __name__ == "__main__":
    #res = get_similarity_scores_query(
    #    target="我们的爱", candidates=["过了永不再回来", "直到现在我还默默地等待"]
    #)
    pass