import argparse
import os
import sys
from database.mongo import Mongodb
from config import CONFIG
import tools.knowledge.modules.preprocess as preprocess
from tools.knowledge.modules.algorithm import Algorithm
from tools.knowledge.modules.crawler import Crawler
import re
from pydantic import BaseModel
from typing import Dict, Optional, List, Any, Union

test_dir = os.path.dirname(os.path.abspath(__file__))


class Snippet(BaseModel):
    type: str = "snippet"
    topic: str = ""
    title: str = ""  # crawled title
    content: str = ""  # crawled content
    seed: str = ""
    question: Optional[str]  # processed q
    answer: Optional[str]  # processed a
    source: Optional[str]  # baidu zhihu
    url: Optional[str]


class Concept(BaseModel):
    concept: str = ""
    topic: str = ""
    score: Optional[float]
    algorithm: Optional[str]


class ConfigParser:
    def __init__(self, entries: dict = {}):
        for k, v in entries.items():
            if isinstance(v, dict):
                self.__dict__[k] = Config(v)
            else:
                self.__dict__[k] = v


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

        self.zh_list = os.path.join(test_dir, "data/zh_list")
        self.en_list = os.path.join(test_dir, "data/en_list")
        self.db = "snippet.db"
        self.cookie_paths = [
            os.path.join(test_dir, "cookie", file)
            for file in os.listdir(os.path.join(test_dir, "cookie"))
        ]
        self.proxy = {
            "http": "http://localhost:8001",
            "https": "http://localhost:8001",
        }  # should change to your own proxy
        self.cached_vecs_path = os.path.join(test_dir, "data/cached_vecs.pkl")


class KGPipeline:
    def __init__(self, topic="mytopic"):
        self.topic = topic
        self.concepts_colname = "knowledge_concepts"
        DB = Mongodb()
        self.concepts_col = DB.db[self.concepts_colname]
        self.faq_col = DB.db[CONFIG.faq_col]

    def crawl_text_with_seed(self, config):
        crawler = Crawler(config)
        snipptes_list = []
        for seed in config.input_seed:
            if seed:
                snippets = crawler.get_snippet_rightnow(seed)
                for body in snippets:
                    url = body.get("url")
                    if not url:
                        continue
                    body["seed"] = seed
                    snippet = Snippet(topic=self.topic, **body)
                    snipptes_list.append(snippet)
        return snipptes_list

    def extract_related_concept(self):
        pass

    @staticmethod
    def __clean_content(text):
        return re.sub(
            "\xa3|\xae|\x0d|\xa0|…| \.\.\.|See more on baike\.baidu\.com", "", text
        ).lower()

    @staticmethod
    def __process_title(title):
        source = ""
        if "_百度百科" in title:
            source = "百度百科"
            prompt = title.split("_百度百科")[0]
        elif " - 知乎" in title:
            source = "知乎"
            prompt = title.split(" - 知乎")[0]
        else:
            prompt = title
        return source, prompt

    def save_snippet2db(self, snippet):
        # check duplicate
        # topic: raw_snippet
        query = {
            "topic": snippet.topic,
            "question": snippet.question,
            "url": snippet.url,
        }
        set_doc = snippet.dict()
        doc = self.faq_col.update_one(query, {"$set": set_doc}, upsert=True)

    def save_concept2db(self, concept):
        query = {
            "topic": concept.topic,
            "concept": concept.concept,
        }
        set_doc = concept.dict()
        doc = self.concepts_col.update_one(query, {"$set": set_doc}, upsert=True)

    def __get_concepts_from_db(self):
        query = {"topic": self.topic}
        res = self.concepts_col.find(query, {"concept": 1})
        res = [i["concept"] for i in res]
        return res

    def __get_snippets_from_db(self):
        query = {"topic": self.topic}
        res = self.faq_col.find(query, {"question": 1, "answer": 1})
        res = ["{} {}".format(r.get("question", ""), r.get("answer", "")) for r in res]
        return res

    def __snippet2faq(self, snippet):
        snippet.answer = self.__clean_content(snippet.content)
        snippet.source, snippet.question = self.__process_title(snippet.title)
        return snippet

    def __ConceptWrapper(self, concept):
        concept = Concept(**concept)
        concept.topic = self.topic
        concept.algorithm = self.config.algorithm
        return concept

    def run_search(self, text=""):
        conf = {
            "task": "expand",
            "input_text": [""],
            "input_seed": [],
            "language": "zh",
            "snippet_source": "bing_new",
            "no_seed": True,
            "algorithm": [
                "graph_propagation",
                "average_distance",
                "tf_idf",
                "pagerank",
            ][0],
            "result_path": "tmp/result.txt",
            "cpu": True,
        }
        args = ConfigParser(conf)
        config = Config(
            args.task,
            args.input_text,
            args.input_seed,
            args.language,
            args.snippet_source,
            args.no_seed,
            args.algorithm,
            args.result_path,
            args.cpu,
        )
        crawler = Crawler(config)
        snippets = crawler.get_snippet_rightnow(text)
        return snippets

    def run_expand(
        self,
    ):
        input_seed = self.__get_concepts_from_db()
        conf = {
            "task": "expand",
            "input_text": [""],
            "input_seed": input_seed[:],
            "language": "zh",
            "snippet_source": "bing_new",
            "no_seed": True,
            "algorithm": [
                "graph_propagation",
                "average_distance",
                "tf_idf",
                "pagerank",
            ][0],
            "result_path": "tmp/result.txt",
            "cpu": True,
        }
        args = ConfigParser(conf)
        config = Config(
            args.task,
            args.input_text,
            args.input_seed,
            args.language,
            args.snippet_source,
            args.no_seed,
            args.algorithm,
            args.result_path,
            args.cpu,
        )

        snippets_list = self.crawl_text_with_seed(config)
        for s in snippets_list[:]:
            print(s)
            r = self.__snippet2faq(s)
            print(r.dict())
            self.save_snippet2db(r)

    def run_extract(self):
        input_seed = []
        input_seed = self.__get_concepts_from_db()
        if len(input_seed) >= 20:
            return

        input_text = self.__get_snippets_from_db()
        print(input_seed, input_text)
        if not input_text:
            return
        conf = {
            "task": "extract",
            "input_text": input_text,
            "input_seed": input_seed,
            "language": "zh",
            "snippet_source": "bing_new",
            "no_seed": True,
            "algorithm": [
                "graph_propagation",
                "average_distance",
                "tf_idf",
                "pagerank",
            ][2],
            "result_path": "tmp/result.txt",
            "cpu": True,
        }
        args = ConfigParser(conf)
        config = Config(
            args.task,
            args.input_text,
            args.input_seed,
            args.language,
            args.snippet_source,
            args.no_seed,
            args.algorithm,
            args.result_path,
            args.cpu,
        )
        self.config = config
        config.candidates = preprocess.get_candidates_list_from_texts(config)
        algorithm = Algorithm(config)
        res_list = algorithm.get_result_list()
        max_idx = max(50, int(len(res_list) * 0.8))
        res_list = res_list[:max_idx]
        res_list = [i for i in res_list if i["concept"] not in input_seed]
        prob_list = [i["score"] for i in res_list]
        sample_list = sample_prob(p=prob_list, size=5)
        for idx in sample_list:
            c = res_list[idx]
            concept = self.__ConceptWrapper(c)
            print(concept.dict())
            self.save_concept2db(concept)

        # Extract

    def init_seed_concepts(self,concepts=[]):
        for concept in concepts:
            self.save_concept2db(concept)

def sample_prob(p=[], size=1):
    import numpy as np

    np.random.seed(0)
    index = np.arange(len(p))
    pp = np.array(p)
    pp = pp / np.sum(pp)
    idx = np.random.choice(index, size=size, replace=False, p=pp)
    return idx



if __name__ == "__main__":
    pass
