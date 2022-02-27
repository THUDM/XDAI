import sys
from pathlib import Path

BASE_DIR = Path.resolve(Path(__file__)).parent.parent
sys.path.append(str(BASE_DIR))
print(BASE_DIR)
from module.session_managers.session_manager_ram import SessionManagerRam
from database.data_types import UtteranceItem
from database.models import TalkerType,GetSessInfo
import asyncio

import argparse

def test_session(
    platform_id="user",
    version="base",
):
    # 本地终端运行方法, 用内存存储历史记录, utts不会存入mongodb
    item = GetSessInfo()
    item.version = version
    item.window_info.platform = "term"
    item.window_info.platform_id = platform_id
    agent = SessionManagerRam.get_agent_by_brand(item)
    if not agent:
        print("No available agent class, please check the version")
    while True:
        content = input("User：")
        if content == "bye":
            agent.sess.history = []
            print("----本轮会话结束 End of the session-----")
            continue

        utt = UtteranceItem.parse_simple(talker=TalkerType.user, text=content)
        agent.sess.add_utterance(utt)
        agent.import_history()
        replies = asyncio.run(agent.make_reply())

        for rep in replies:
            print("Bot：", rep)
            utt = UtteranceItem.parse_simple(talker=TalkerType.bot, text=rep)
            agent.sess.add_utterance(utt)


def set_args():
    parser = argparse.ArgumentParser(description="Interactive terminal interface for XDAI.",
                                     fromfile_prefix_chars="@",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-v","--version", dest="version")
    parser.add_argument("-u", "--username",dest="username")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = set_args()
    test_session(platform_id=args.username,version=args.version)

