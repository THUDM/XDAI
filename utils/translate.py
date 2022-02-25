
import json
import requests
import re

def translator_youdao(word):

    # API
    url = "https://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule"
    Form_data = {
        "i": word,
        "from": "AUTO",
        "to": "AUTO",
        "smartresult": "dict",
        "client": "fanyideskweb",
        "salt": "16430343357744",
        #"sign": "78181ebbdcb38de9b4a3f4cd1d38816b",
        "sign":"c35540eb508fbcdd61b83d6229d8f555",
        "doctype": "json",
        "version": "2.1",
        "keyfrom": "fanyi.web",
        "action": "FY_BY_CLICKBUTTION",
        #"action": "FY_BY_REALTIME",
        "typoResult": "false",
    }
    response = requests.post(url, data=Form_data)
    if response.status_code == 200:
        result = json.loads(response.text)
        translation = result['translateResult'][0][0]['tgt']
        return translation
    else:
        print("Youdao Failed")
        return None

if __name__ == '__main__':
    text = "羽毛球是一项隔着球网，使用长柄网状球拍击打用羽毛和软木制作而成的一种小型球类的室内运动项目。"
    print(text)
    answer = translator_youdao(text)
    print(answer)
    text = "Badminton is a across the net, using a long-handled mesh racket struck with feathers and cork is made and be become a small ball of indoor sports."
    answer2 = translator_youdao(answer)
    print(answer2)
