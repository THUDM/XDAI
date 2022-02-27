
import json
import requests

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
    text = "Natural language generation is fun!"
    print(text)
    answer = translator_youdao(text)
    print(answer)
