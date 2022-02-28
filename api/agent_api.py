import os, sys
api_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(api_dir)
sys.path.append(BASE_DIR)

from utils import get_logger
from database.models import (
    ResBody,
    Query,
    OptType,
    GenReply,
    GetSessInfo,
    MsgModel,
    TalkerType,
    PlatformType,
)
from database.data_types import UtteranceItem
from database.mongo import Mongodb, MgOpt
from module import SessionManagerRam, SessionManager
from agents import DEFAULT_CHATBOT
from config import CONFIG
from .coreweb import app
logger = get_logger("ChatBotAPI")

mgdb = Mongodb()
DBopt = MgOpt(mgdb)

@app.post(CONFIG.query_plain_route, summary="Direct generation with context", response_model=ResBody)
async def query_plain(item: Query) -> ResBody:
    q = item.query
    brand = item.brand
    his = brand.history
    botname = brand.botname
    username = brand.username
    if botname == username:
        botname = "BOT"
        username = "USER"

    version = brand.version or DEFAULT_CHATBOT.version
    brand.version = version
    platform = item.platform or PlatformType.api
    logger.info(item.dict())

    if isinstance(his, list):
        pass
    # todo save to DB
    item = GetSessInfo()
    item.version=version
    item.window_info.platform = platform
    item.window_info.platform_id = username
    agent = SessionManagerRam.get_agent_by_brand(item)
    agent.botname = botname if botname else agent.botname
    agent.username = username if username else agent.username

    for uttdict in his:
        utt = UtteranceItem.parse_simple(**uttdict)
        agent.sess.add_utterance(utt)

    if q:
        utt = UtteranceItem.parse_simple(talker=TalkerType.user, text=q)
        agent.sess.add_utterance(utt)

    replies = await agent.make_reply()
    reply = replies[0] if replies else ""

    data = {"brand": brand, "reply": reply,"platform":platform}
    res = ResBody(data=data)
    logger.info(res.dict())
    return res

@app.post(CONFIG.get_session_id_route, summary="", response_model=ResBody)
async def get_session_id(item: GetSessInfo) -> ResBody:
    logger.info("get_sess_id:item.dict:{}".format(item.dict()))
    operation = item.operation
    if operation == OptType.close and item.session_id:
        msg = SessionManager.close_session(item.session_id, update_window=True)
        session_doc = SessionManager.get_one_session({"session_id": item.session_id})
        data = {"session_doc":session_doc}
    else:
        brand = SessionManager.get_parsed_sess_item(item)  # todo
        if brand.version == "INVALID VERSION":
            data = {"parsed_info": brand, "session_doc": {}, "window_doc": {}}
        else:
            data = SessionManager.get_session_api(brand=brand, operation=operation)

    res = ResBody(data=data)
    logger.info("get_sess_id:res.dict:{}".format(res.dict()))
    return res


@app.post(CONFIG.save_msg_route, summary="", response_model=ResBody)
async def save_msg(item: MsgModel) -> ResBody:
    logger.info("save msg:{}".format(item.dict()))
    brand = SessionManager.get_parsed_msg_item(item)
    utt = UtteranceItem.parse_apibrand(brand)

    if not utt:
        utt_doc = {}
        data = {"brand": brand, "utterance_doc": utt_doc, "save_result": False}
        res = ResBody(data=data)
        return res

    utt_doc = utt.dict()
    brand.created_t = utt.created_t
    brand.created_time = utt.created_time

    try:
        res = SessionManager.append_msg_with_ssid(utt=utt, session_id=brand.session_id)
        save_result = res
    except:
        save_result = False
    save_result = res
    data = {"brand": brand, "utterance_doc": utt_doc, "save_result": save_result}

    if brand.mode == "close":
        SessionManager.close_session(brand.session_id, update_window=True)
    res = ResBody(data=data)
    logger.info("save msg")
    logger.info(res.dict())
    return res


@app.post(CONFIG.gen_reply_route, summary="", response_model=ResBody)
async def gen_reply(item: GenReply) -> ResBody:
    logger.info("gen_reply:{}".format(item.dict()))

    session_id = item.session_id
    agent = SessionManager.get_agent_by_session_id(session_id)

    mode = item.mode
    if not mode:
        mode = "normal"
    print(mode)
    if not agent:
        replies = [""]
    else:
        agent.import_history()
        if agent.history:
            logger.info("history:{}".format(agent.history[-1]))
        replies = await agent.make_reply(mode=mode)

    print(replies)
    if not replies:
        replies = []
    results = [{"reply":r,"mode":mode} for r in replies]
    data = {"replies": replies, "reply_tuples": results}

    res = ResBody(data=data)
    logger.info("gen_reply result:{}".format(res.dict()))
    return res

if __name__ == '__main__':
    pass
