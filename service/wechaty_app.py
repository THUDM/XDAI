import asyncio
import os, sys
import time
from typing import List, Optional, Union
from wechaty import (
    MessageType,
    Wechaty,
    Message,
)
from wechaty_puppet import (
    EventHeartbeatPayload,
)

api_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(api_dir)
BASE_DIR = module_dir  
sys.path.append(BASE_DIR)
from config import CONFIG
from utils import get_logger
from module.session_managers import SessionManager
from module.internal_api import get_valid_session,save_msg_with_session_id, get_reply_api

logger = get_logger('Wechaty')

class MyBot(Wechaty):

    def __init__(self):
        super().__init__()


    def __check_talker_valid(self, msg=None, talkername=None):
        ### do not reply myself
        if msg and msg.is_self():
            return False
        return True

    def __check_msgtype_valid(self, msgtype=None):
        if msgtype in [
                        MessageType.MESSAGE_TYPE_UNSPECIFIED,
                        MessageType.MESSAGE_TYPE_CHAT_HISTORY,
                        MessageType.MESSAGE_TYPE_RECALLED,
                        ]:
            return False
        return True

    def __check_content_valid(self, content=None):
        ### web, emoji type
        if content == "[Send an emoji, view it on mobile]":
            return False
        return True

    async def _gatekeeper(self,
                          msg=None,
                          talker=None,
                          ):
        """
        return agent,temp_reply
        """
        temp_reply = ""
        agent = None
        none_reply = (None, temp_reply)

        platform = "wechat"
        content = msg.text()
        msgtype = msg.message_type()
        talkername = talker.name
        talker_weixin = talker.weixin()
        user_id = talkername  #

        # print(talker.weixin(), talkername)

        ## ===== check none reply ======
        if not (self.__check_talker_valid(msg=msg, talkername=talkername)
                and self.__check_msgtype_valid(msgtype=msgtype)
                and self.__check_content_valid(content=content)):
            return none_reply

        platform_id = f"{user_id}"
        if not platform_id:
            platform_id = talker_weixin
        if not platform_id:
            platform_id = "unknown_user"

        assert platform_id

        if msgtype == MessageType.MESSAGE_TYPE_TEXT:
            session_id = get_valid_session(
                              platform=platform,
                              username=talkername,
                              platform_id=platform_id,
                              userinput=content,
                              )

        return session_id, temp_reply

    async def on_heartbeat(self, payload: EventHeartbeatPayload) -> None:
        """
        listen heartbeat event for puppet
        this is friendly for code typing
        """
        gap_minutes = CONFIG.session_cooling_time
        num = 0
        num = SessionManager.close_inactive_sessions(gap_minutes=gap_minutes)
        logger.info(f"close inactive sessions:{num}")
    

    async def on_message(self, msg: Message):
        #return 

        talker = msg.talker()
        await talker.ready()
        talkername = talker.name

        ### check
        session_id, temp_reply = await self._gatekeeper(msg, talker)

        if temp_reply:
            if isinstance(temp_reply, str):
                temp_reply = [temp_reply]
            if isinstance(temp_reply, list):
                for tmp in temp_reply:
                    tmp = [(tmp, "temp")]
                    await self._send_reply(talker=talker,
                                           session_id=session_id,
                                           reply_tuples=tmp,
                                           interval=0.5)

        if not session_id:
            print(f"No available session for {talkername}")
            return

        content = msg.text()
        content = content.replace("&amp;#x20;", " ")
        content = content.replace("  ", " ")

        if content in CONFIG.CHAT_WORD:
            content = "你好啊"

        print(content, session_id)
        utt_doc = save_msg_with_session_id(session_id=session_id,
                                 talker = "user",
                                 talkername=talkername,
                                 text=content,
                                 mode="normal"
                                 )
        if utt_doc:
            mode = utt_doc.get("mode")
        else:
            mode = "error"

        replies = await get_reply_api(session_id=session_id, mode=mode)
        print(replies)
        await self._send_reply(
            talker=talker,
            session_id = session_id,
            reply_tuples=replies,
            interval=1)

    # new
    async def _send_reply(self,
                          talker=None,
                          session_id=None,
                          reply_tuples=None,  # [(,),(,)]
                          interval=2):
        """
        send msgs to window(talker)
        & save msg to session
        if success:  mode="normal"
        else: mode = "error"
        """
        #talker = msg
        if not reply_tuples:
            return
        assert isinstance(reply_tuples, list)
        for body in reply_tuples:
            rep  = body.get("reply")
            mode = body.get("mode")
            success = True
            #await talker.say(rep)
            #await msg.say(rep)

            try:
                await talker.say(rep)
            except Exception as e:
                print(e)
                success = False

            mode = mode if success else "error"
            if not session_id:
                pass
            else:
                save_msg_with_session_id(session_id=session_id, talker = "bot", talkername="", text = rep, mode = mode)

            time.sleep(interval)


async def main():
    global bot
    if 'WECHATY_PUPPET_SERVICE_TOKEN' not in os.environ:
        try:
            os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = CONFIG.wechaty_token
        except:
            print('''
            Error: WECHATY_PUPPET_SERVICE_TOKEN is not found in the environment variables
            You need a TOKEN to run the Python Wechaty. Please goto our README for details
            https://github.com/wechaty/python-wechaty-getting-started/#wechaty_puppet_service_token
            ''')

    bot = MyBot()
    await bot.start()

    print('[Python Wechaty] Bot started.')



if __name__ == "__main__":
    asyncio.run(main())
