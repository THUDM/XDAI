import socket
from urllib.parse import quote_plus
import requests
import configparser
import os

curPath = os.path.dirname(os.path.realpath(__file__))
cfgPath = os.path.join(curPath, "conf.ini")

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

class Config:
    cf = configparser.ConfigParser()
    cf.read(cfgPath)
    session_cooling_time = 30  # minutes

    def __init__(self, use_local=True, plm_ip="", check=False):
        self.local_ip = get_host_ip()
        self.set_plm_url()
        self.set_tools()
        self.set_authentication()
        self.set_external_api()
        self.set_database()
        self.set_chat_service()
        self.set_server()
        self.set_mongo()

    def set_database(self):
        section = "HISTORY_STORAGE"
        self.MEM_method = self.cf.get(section, "type")
        #self.mg_uri

    def set_external_api(self):
        section = "EXTERNAL_API"
        pass

    def set_chat_service(self):
        section = "CHAT_SERVICE"
        self.use_wechaty = self.cf.get(section,"wechaty").lower() == "true"
        if self.use_wechaty:
            self.set_wechaty_token()
            assert self.check_wechaty_token()

    def set_server(self):
        section = "SERVER"
        self.server_ip = self.cf.get(section, "server_ip")
        self.server_port = self.cf.get(section, "server_port")
        self.server_url = f"http://{self.server_ip}:{self.server_port}"
        self.query_plain_route = self.cf.get(section, "query_plain")
        self.get_session_id_route = self.cf.get(section, "get_session_id")
        self.save_msg_route = self.cf.get(section, "save_msg")
        self.gen_reply_route = self.cf.get(section, "gen_reply")
        self.query_plain_api = self.server_url + self.query_plain_route
        self.get_session_id_api = self.server_url + self.get_session_id_route
        self.save_msg_api = self.server_url + self.save_msg_route
        self.gen_reply_api = self.server_url + self.gen_reply_route



    def set_tools(self):
        section = "TOOL"
        self.tool_api_ip = self.cf.get(section, "tool_api_ip")

        self.faq_port = self.cf.get(section, "faq_port")
        self.faq_route = self.cf.get(section, "faq_route")
        self.faq_col = self.cf.get(section,"faq_col")
        self.qagen_port = self.cf.get(section, "qagen_port")
        self.qagen_route = self.cf.get(section, "qagen_route")
        self.sbert_model = self.cf.get(section,"sbert_model")
        self.sentsim_port = self.cf.get(section, "sentsim_port")
        self.sentsim_route = self.cf.get(section, "sentsim_route")
        self.sentsim_api = f"http://{self.tool_api_ip}:{self.sentsim_port}{self.sentsim_route}"
        self.faq_api = f"http://{self.tool_api_ip}:{self.faq_port}{self.faq_route}"
        self.qagen_api = f"http://{self.tool_api_ip}:{self.qagen_port}{self.qagen_route}"


    def set_authentication(self):
        section = "CHAT_AUTHENTICATION"
        self.CHAT_WORD = self.cf.get(section, "chat_words").split(";")
        self.CHAT_ALLOWED = self.cf.get(section, "chat_allowed").split(";")
        if "all" in self.CHAT_ALLOWED:
            self.CHAT_ALLOWED = "all"

    def set_plm_url(self):
        section = "PLM"
        self.plm_ip = self.cf.get(section, "ip_address") or self.local_ip
        glm_port = self.cf.get(section, "glm_port") or 8888
        glm_url = "http://{ip_address}:{glm_port}/glm".format(ip_address=self.plm_ip,glm_port=glm_port)
        self.glm_query_api = self.cf.get(section, "glm_api") or glm_url
        self.default_plm_api = self.glm_query_api

    def set_wechaty_token(self):
        section = "WECHATY"
        puppet = self.cf.get(section,"chosen_puppet")
        self.wechaty_token = self.cf.get(section,f"{puppet}_token")
        return self.wechaty_token

    def check_wechaty_token(self, token=None):
        """
        check if wechaty_token is valid
        """
        if token is None:
            token = self.wechaty_token
        check_api = f"https://api.chatie.io/v0/hosties/{token}"
        response = requests.request("GET", check_api)
        body = response.json()
        host = body.get("host")
        return host != "0.0.0.0"

    def set_mongo(self):
        user = self.cf.get("MONGO","user")
        password = self.cf.get("MONGO","password")
        host = self.cf.get("MONGO","host")
        port = self.cf.get("MONGO","port")
        self.dbname = self.cf.get("MONGO","dbname")
        dbname=self.dbname
        self.mongo_chatbot_uri = f"mongodb://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/?authSource={dbname}"
        return self.mongo_chatbot_uri


def test(conf=None):
    if conf is None:
        conf = Config()
    print("[mg_url]:\n", conf.mongo_chatbot_uri)
    print("[token]:\n", conf.chose_token, ":", conf.wechaty_token)
    print("[token is valid]:", conf.check_wechaty_token())
    print("[chat allowed]:\n", conf.CHAT_ALLOWED)


CONFIG = Config()

if __name__ == "__main__":
    pass