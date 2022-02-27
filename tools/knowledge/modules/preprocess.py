import re
import nltk
import jieba
import jieba.posseg as pseg
import json
from .crawler import Crawler
from pyhanlp import *


def is_noun(config, flag):
    if config.language == "en":
        flag = re.sub("JJ[RS]?", "JJ", flag)
        flag = re.sub("NN[SP(PS)]?", "NN", flag)
        if (
            re.match(r"^((@(JJ|NN))+|(@(JJ|NN))*(@(NN|IN))?(@(JJ|NN))*)@NN$", flag)
            is not None
        ):
            return True
        else:
            return False
    if config.language == "zh":
        pattern = re.compile(r"^(@(([av]?n[rstz]?)|l|a|v))*(@(([av]?n[rstz]?)|l))$")
        if re.match(pattern, flag) is not None:
            return True
        else:
            return False


def is_sp_noun_hanlp(config, flag):
    if config.language == "en":
        flag = re.sub("JJ[RS]?", "JJ", flag)
        flag = re.sub("NN[SP(PS)]?", "NN", flag)
        if (
            re.match(r"^((@(JJ|NN))+|(@(JJ|NN))*(@(NN|IN))?(@(JJ|NN))*)@NN$", flag)
            is not None
        ):
            return True
        else:
            return False
    if config.language == "zh":
        pattern = re.compile(r"^@(n[^inxz]+)|(g.*)$")
        if re.match(pattern, flag) is not None:
            return True
        else:
            return False


def get_candidates(config):
    if config.task == "expand":
        crawler = Crawler(config)
        text = []
        with open(config.input_seed, "r", encoding="utf-8") as f:
            for seed in f.read().split("\n"):
                if seed:
                    text.append(crawler.get_snippet(seed))
        text = "\n".join(text)
    else:
        with open(config.input_text, "r", encoding="utf-8") as f:
            text = f.read()
    text = re.sub("\xa3|\xae|\x0d", "", text).lower()
    if config.language == "en":
        with open(config.en_list, "r", encoding="utf-8") as f:
            vocabs = set(f.read().split("\n"))
    if config.language == "zh":
        with open(config.zh_list, "r", encoding="utf-8") as f:
            vocabs = set(f.read().split("\n"))
    res = set()
    for line in text.split("\n"):
        if config.language == "en":
            tmp = nltk.word_tokenize(line)
            seg = nltk.pos_tag(tmp)
        if config.language == "zh":
            tmp = pseg.cut(line)
            seg = [(t.word, t.flag) for t in tmp]
        n = len(seg)
        for i in range(n):
            phrase, flag = seg[i][0], "@" + seg[i][1]
            for j in range(i + 1, min(n + 1, i + 7)):
                if phrase not in res and phrase in vocabs and is_noun(config, flag):
                    res.add(phrase)
                if j < n:
                    if config.language == "en":
                        phrase += " " + seg[j][0]
                    if config.language == "zh":
                        phrase += seg[j][0]
                    flag += "@" + seg[j][1]
    print("candidate concepts number: {}".format(len(res)))
    with open(config.text_path, "w", encoding="utf-8") as f:
        f.write(text)
    with open(config.candidate_path, "w", encoding="utf-8") as f:
        f.write("\n".join(list(res)))
    print("preprocess done.")


def get_candidates_list_from_texts(config):
    if config.language == "en":
        with open(config.en_list, "r", encoding="utf-8") as f:
            vocabs = set(f.read().split("\n"))
    if config.language == "zh":
        with open(config.zh_list, "r", encoding="utf-8") as f:
            vocabs = set(f.read().split("\n"))
    res = set()
    for line in config.input_text:
        if config.language == "en":
            tmp = nltk.word_tokenize(line)
            seg = nltk.pos_tag(tmp)
        if config.language == "zh":
            # tmp = pseg.cut(line)
            # seg = [(t.word, t.flag) for t in tmp]
            tmp = HanLP.segment(line)
            seg = [(t.word, str(t.nature)) for t in tmp]
        print(seg)
        n = len(seg)
        for i in range(n):
            phrase, flag = seg[i][0], "@" + seg[i][1]
            for j in range(i + 1, min(n + 1, i + 7)):
                if (
                    phrase not in res
                    and phrase in vocabs
                    and is_sp_noun_hanlp(config, flag)
                ):
                    if (flag == "@nr" and len(phrase) >= 2) or (
                        flag != "@nr" and len(phrase) >= 3
                    ):
                        res.add(phrase)
                if j < n:
                    if config.language == "en":
                        phrase += " " + seg[j][0]
                    if config.language == "zh":
                        phrase += seg[j][0]
                    flag += "@" + seg[j][1]
    print("candidate concepts number: {}".format(len(res)))

    return res
