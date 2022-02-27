#!/usr/bin/python
# -*-coding:utf-8-*-

import os
import sys
from pymongo import MongoClient

#BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#sys.path.append(BASE_DIR)

from utils import get_logger
from config import CONFIG
from enum import Enum

logger = get_logger("ChatBotAPI")

class ColType(str, Enum):
    utterance = "utterance"
    session = "session"
    window = "window"

class Mongodb:
    # uri = uri
    uri_chatbot = CONFIG.mongo_chatbot_uri
    dbname = CONFIG.dbname
    # dbname = "chatbot"

    def __init__(self, dbname="chatbot"):
        self.dbname = dbname or self.dbname
        self.client = MongoClient(self.uri_chatbot)
        self.db = self.client[self.dbname]
        self.__set_collections()

    def __set_collections(self):
        self.COLs = {
            ColType.utterance: self.db["chat_utterance"],
            ColType.session: self.db["chat_session"],
            ColType.window: self.db["chat_window"],
        }

    @classmethod
    def check_connection(cls, **kw):
        try:
            mg = cls().COLs[ColType.utterance].find_one({})
            return mg
        except:
            return False


class MgOpt:
    def __init__(self, DB):
        self.DB = DB

    def find_one(self,query,col="",sort=[]):
        if isinstance(sort,dict):
            sort_list = [(k, v) for k, v in sort.items()]
        elif isinstance(sort,list):
            sort_list = sort
        return self.DB.COLs.get(col).find_one(query,sort=sort_list)

    def find(self,query,col="",sort=[],limit=0):
        if isinstance(sort, dict):
            sort_list = [(k, v) for k, v in sort.items()]
        elif isinstance(sort, list):
            sort_list = sort
        return self.DB.COLs.get(col).find(query,sort=sort_list,limit=limit)

    def update_one(self,query,set_dict={},col="",upsert=False):
        self.DB.COLs.get(col).update(query,{"$set":set_dict},upsert=upsert)

    def insert_one(self, obj, col="utt"):
        col = self.DB.COLs.get(col, None)
        if not col:
            return "error: invalid type"
        _id = obj._id
        if col.find_one({"_id": _id}):
            print(obj)
            return f"error: {col}_doc already exists"
        col.insert_one(obj.dict())
        return "Success"

    def count_docs(self,query,col=""):
        docs = self.DB.COLs.get(col).count_documents(query)
        return docs


if __name__ == "__main__":
    pass
