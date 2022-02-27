import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import urllib
import json
import os

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"


class Config:
    def __init__(
        self,
        task,
        input_text,
        input_seed,
        language,
        snippet_source,
        no_seed,
        algorithm,
        result_path,
        cpu,
    ):
        self.task = task
        self.input_text = input_text
        self.input_seed = input_seed
        self.language = language
        self.snippet_source = snippet_source
        self.no_seed = no_seed
        self.algorithm = algorithm
        self.result_path = result_path
        self.cpu = cpu

        self.times = 10
        self.max_num = -1
        self.threshold = 0.7
        self.decay = 0.8
        self.batch_size = 128

        self.zh_list = "data/zh_list"
        self.en_list = "data/en_list"

        self.mgdbcol = ""
        self.db = "snippet.db"
        self.cookie_paths = ["cookie/{}".format(file) for file in os.listdir("cookie/")]
        self.proxy = {
            "http": "http://localhost:8001",
            "https": "http://localhost:8001",
        }  # should change to your own proxy
        self.text_path = "tmp/text.txt"
        self.candidate_path = "tmp/candidate.txt"
        self.cached_vecs_path = "data/cached_vecs.pkl"


def sleep(t):
    time.sleep(t + random.random() * t * 0.5)


def clean(text):
    text = re.sub(r"\n|\r", "", text).strip()
    return text


class Crawler:
    def __init__(self, config):
        self.config = config
        self.sess = requests.Session()
        if self.config.snippet_source == "google":
            self.sess.proxies.update(self.config.proxy)
        self.tot_crawl = 0
        self._init()

    def _init(self):
        conn = sqlite3.connect(self.config.db)
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS baidu (concept TEXT PRIMARY KEY NOT NULL, snippet TEXT NOT NULL)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS google (concept TEXT PRIMARY KEY NOT NULL, snippet TEXT NOT NULL)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS bing (concept TEXT PRIMARY KEY NOT NULL, snippet TEXT NOT NULL)"
        )
        conn.commit()
        conn.close()
        for cookie_path in self.config.cookie_paths:
            with open(cookie_path, "r", encoding="utf-8") as f:
                cookie = json.load(f)
                for i in range(len(cookie)):
                    self.sess.cookies.set(cookie[i]["name"], cookie[i]["value"])

    def update_cookie(self, cookie):
        for c in cookie.split("; "):
            c = c.split("=", 1)
            if len(c) == 2:
                self.sess.cookies.set(c[0], c[1])

    def crawl_snippet_google(self, concept):
        res = []
        url = "https://www.google.com/search?gws_rd=cr&q={}".format(concept)
        headers = {"user-agent": USER_AGENT, "referer": "https://www.google.com/"}
        page = self.sess.get(url, headers=headers)
        if "Set-Cookie" in page.headers:
            self.update_cookie(page.headers["Set-Cookie"])
        soup = BeautifulSoup(page.text, "html.parser")
        block = soup.find("div", class_="ifM9O")
        if block is not None:
            title, snippet = "", ""
            t = block.find("div", class_="r")
            s = block.find("div", class_="LGOjhe")
            if t and t.find("a") and t.find("h3") and s:
                title = clean(t.find("a").find("h3").text)
                snippet = clean(s.text)
                res.append("{} {}".format(title, snippet))
        for block in soup.find_all("div", class_="g"):
            title, snippet = "", ""
            t = block.find("div", class_="r")
            s = block.find("span", class_="st")
            if t and t.find("a") and t.find("h3") and s:
                title = clean(t.find("a").find("h3").text)
                snippet = clean(s.text)
                res.append("{} {}".format(title, snippet))
        return res

    def crawl_snippet_baidu(self, concept):
        res = []
        url = "http://www.baidu.com/s?wd={}".format(concept)
        headers = {"user-agent": USER_AGENT, "referer": url}
        page = self.sess.get(url, headers=headers)
        soup = BeautifulSoup(page.text, "html.parser")
        block = soup.find("div", class_="result-op c-container xpath-log")
        if block is not None:
            title, snippet = "", ""
            t = block.find("h3", class_="t")
            s = block.find("div", class_="c-span18 c-span-last")
            if t and t.find("a") and s and s.find("p"):
                title = clean(t.find("a").text)
                snippet = clean(s.find("p").text)
                res.append("{} {}".format(title, snippet))
        for block in soup.find_all(
            "div", class_="result c-container" + (" " if os.name == "nt" else "")
        ):
            title, snippet = "", ""
            t = block.find("h3", class_="t")
            s = block.find("div", class_="c-abstract")
            if t and t.find("a") and s:
                title = clean(t.find("a").text)
                snippet = clean(s.text)
                res.append("{} {}".format(title, snippet))
        return res

    def crawl_snippet_bing(self, concept):
        res = []
        url = "https://cn.bing.com/search?q={}".format(concept)
        headers = {"user-agent": USER_AGENT, "referer": url}
        page = self.sess.get(url, headers=headers)
        soup = BeautifulSoup(page.text, "html.parser")
        if "cookie" in page.headers:
            self.update_cookie(page.headers["cookie"])
        block = soup.find("div", class_="b_subModule")
        if block is not None:
            title, snippet = "", ""
            t = block.find("h2", class_="b_entityTitle")
            s = block.find("div", class_="b_lBottom")
            if t and s:
                title = clean(t.text)
                snippet = clean(t.text)
                res.append("{} {}".format(title, snippet))
        for block in soup.find_all("li", class_="b_algo"):
            title, snippet = "", ""
            t = block.find("h2")
            if t and t.find("a"):
                title = clean(t.find("a").text)
            s = block.find("div", class_="b_caption")
            if s and s.find("p"):
                snippet = clean(s.find("p").text)
            s = block.find("div", class_="tab-content")
            if s and s.find("div"):
                snippet = s.find("div").text
            if title and snippet:
                res.append("{} {}".format(title, snippet))
        return res

    def crawl_snippet(self, concept):
        self.tot_crawl += 1
        if self.tot_crawl % 100 == 0:
            print("sleep 60s~90s after crawl 100 times")
            sleep(60)
        concept = urllib.parse.quote_plus(concept)
        sleep(2)
        if self.config.snippet_source == "baidu":
            res = self.crawl_snippet_baidu(concept)
        if self.config.snippet_source == "google":
            res = self.crawl_snippet_google(concept)
        if self.config.snippet_source == "bing":
            res = self.crawl_snippet_bing(concept)
        return "\n".join(res)

    def get_snippet(self, concept):
        conn = sqlite3.connect(self.config.db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM {} WHERE concept=?".format(self.config.snippet_source),
            (concept,),
        )
        res = cursor.fetchall()
        print(res)
        if not res:
            snippet = self.crawl_snippet(concept)
            print(
                "get snippet {} from source {}".format(
                    concept, self.config.snippet_source
                )
            )
            cursor.execute(
                "INSERT INTO {} (concept, snippet) VALUES (?,?)".format(
                    self.config.snippet_source
                ),
                (
                    concept,
                    snippet,
                ),
            )
            conn.commit()
        else:
            snippet = res[0][1]
        conn.close()
        return snippet


if __name__ == "__main__":
    config = None
    crawler = Crawler(config)
