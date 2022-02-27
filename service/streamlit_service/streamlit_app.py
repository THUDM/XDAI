import streamlit as st
import sys
from pathlib import Path
BASE_DIR = Path.resolve(Path(__file__)).parent.parent.parent
sys.path.append(str(BASE_DIR))
print(BASE_DIR)
from module.internal_api import get_response
import asyncio


def local_css(css_path=str(Path.resolve(Path(__file__)).parent)+"/style.css"):
    with open(css_path) as f:
        st.markdown(f"{f.read()}", unsafe_allow_html=True)


def add_response():
    if st.session_state.input_area:
        st.session_state.dialogue.append(("user", st.session_state.input_area))
        st.session_state.input_area = ""


def get_answer(version=""):
    if st.session_state.dialogue:
        if st.session_state.dialogue[-1][0] == "bot":
            return
        else:
            history = [{"talker":talker,"text":text} for talker,text in st.session_state.dialogue]
            res = asyncio.run(get_response(history=history,version=version,botname="机器人",username="USER"))
            if res:
                append_bot_reply(res)
            else:
                append_bot_reply("FAILED")


def append_bot_reply(reply):
    st.session_state.dialogue.append(("bot", reply))


def print_dialogue(placeholder_output, wrapper):
    out = st.session_state.dialogue
    if not out:
        placeholder_output.info("Conversation to be shown here ")
    else:
        list_str = [wrapper[k].format(v) for k, v in out]
        outall = "".join(list_str)
        # with container:
        placeholder_output.markdown(outall, unsafe_allow_html=True)



def init_session():
    st.session_state.dialogue = []
    st.session_state.current_topic = ""


def show():
    local_css()
    # st.session_state.
    
    wrapper = {}
    wrapper[
        "user"
    ] = '<div class="triangle"><li class="textRight"><span>{}</span><img class="header-img" src="https://s3.bmp.ovh/imgs/2022/02/accef6bf2d15cc70.png"/></li></div>' 
    wrapper[
        "bot"
    ] = '<div class="triangle"><li class="textLeft"><img class="header-img" src=https://s3.bmp.ovh/imgs/2022/02/ab2893e3378db7a7.png /><span>{}</span></li></div>'
    if "dialogue" not in st.session_state:
        init_session()

    st.title("Bot")
    version = st.text_input("version",value="")
    if len(st.session_state.dialogue) > 0:
        send_button = st.button("Clear all", key="clear", on_click=init_session)

    container = st.container()
    with container:
        placeholder_output = st.empty()
        placeholder_waiting = st.empty()

    col1, col2 = st.columns([2, 8])
    with col2:
        input_text = st.text_input(
            "Your message：", value="", key="input_area", on_change=add_response
        )
    print_dialogue(placeholder_output, wrapper)
    with placeholder_waiting.container():
        with st.spinner("对方正在输入"):
            get_answer(version=version)
    print_dialogue(placeholder_output, wrapper)
    # st.stop()


if __name__ == "__main__":
    show()
