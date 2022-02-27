import numpy as np
import os
import torch
import pickle
import tqdm
import math
import json
from pytorch_pretrained_bert import BertModel, BertTokenizer


def calc_pow(x, y):
    if x > 0:
        return math.pow(x, y)
    else:
        return -math.pow(-x, y)


class Algorithm:
    def __init__(self, config):
        self.config = config
        self._init_new()

    def _init(self):
        with open(self.config.candidate_path, "r", encoding="utf-8") as f:
            self.candidates = f.read().split("\n")
        with open(self.config.text_path, "r", encoding="utf-8") as f:
            self.text = f.read().split("\n")
        if os.path.exists(self.config.cached_vecs_path):
            with open(self.config.cached_vecs_path, "rb") as f:
                self.cached_vecs = pickle.load(f)
        else:
            self.cached_vecs = {}
        print(
            "Load data done, candidate number: {}, text line number: {}, cached vocab vectors: {}".format(
                len(self.candidates), len(self.text), len(self.cached_vecs)
            )
        )
        if self.config.language == "zh":
            self.bert = BertModel.from_pretrained("bert-base-chinese")
            self.tokenizer = BertTokenizer.from_pretrained("bert-base-chinese")
        if self.config.language == "en":
            self.bert = BertModel.from_pretrained("bert-base-uncased")
            self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.bert.eval()
        for p in self.bert.parameters():
            p.requires_grad = False
        if not self.config.cpu:
            self.bert.cuda()
        print("Load bert done.")

    def _init_new(self):
        self.candidates = self.config.candidates
        self.text = self.config.input_text
        if os.path.exists(self.config.cached_vecs_path):
            with open(self.config.cached_vecs_path, "rb") as f:
                self.cached_vecs = pickle.load(f)
        else:
            self.cached_vecs = {}
        print(
            "Load data done, candidate number: {}, text line number: {}, cached vocab vectors: {}".format(
                len(self.candidates), len(self.text), len(self.cached_vecs)
            )
        )
        if self.config.language == "zh":
            self.bert = BertModel.from_pretrained("bert-base-chinese")
            self.tokenizer = BertTokenizer.from_pretrained("bert-base-chinese")
        if self.config.language == "en":
            self.bert = BertModel.from_pretrained("bert-base-uncased")
            self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.bert.eval()
        for p in self.bert.parameters():
            p.requires_grad = False
        if not self.config.cpu:
            self.bert.cuda()
        print("Load bert done.")

    def _get_vector(self, batch):
        input = []
        for concept in batch:
            c = self.tokenizer.tokenize(concept)
            c = [101] + self.tokenizer.convert_tokens_to_ids(c) + [102]
            input.append(c)
        max_len = max([len(c) for c in input])
        input = [
            torch.tensor(c + [0] * (max_len - len(c)), dtype=torch.long) for c in input
        ]
        input = torch.stack(input)
        if not self.config.cpu:
            input = input.cuda()
        with torch.no_grad():
            h, _ = self.bert(
                input, attention_mask=(input > 0), output_all_encoded_layers=False
            )
            h = h.detach()
        for i, concept in enumerate(batch):
            r = torch.sum(input[i] > 0)
            if r > 2:
                vec = torch.mean(h[i][1 : r - 1], 0).cpu().numpy()
                self.cached_vecs[concept] = vec / np.sqrt(np.sum(vec * vec))
            else:
                self.cached_vecs[concept] = None

    def get_vector(self):
        print("Get concept vectors.")
        batch = []
        print(self.candidates)
        for concept in self.candidates:
            if concept in self.cached_vecs:
                continue
            batch.append(concept)
            if len(batch) >= self.config.batch_size:
                self._get_vector(batch)
                batch = []
        if batch:
            self._get_vector(batch)
        self.concepts = []
        self.vecs = []
        # print(self.cached_vecs.keys())
        for c in self.candidates:
            if c in self.cached_vecs and self.cached_vecs[c] is not None:
                self.concepts.append(c)
                self.vecs.append(self.cached_vecs[c])

        self.vecs = np.stack(self.vecs)
        print(
            "Load vec done, concepts number: {}, vecs shape: {}".format(
                len(self.concepts), self.vecs.shape
            )
        )
        with open(self.config.cached_vecs_path, "wb") as f:
            pickle.dump(self.cached_vecs, f)

    def cal_vector_distance(self):
        print("Start calculate vector distance.")
        max_num = self.config.max_num
        n = self.vecs.shape[0]
        m = n if max_num == -1 else min(n, max_num)
        weights = np.dot(self.vecs, self.vecs.T)
        sorted_indexes = np.argsort(-weights)[:, :m]
        self.edges = []
        for i in tqdm.tqdm(range(n)):
            weight, sorted_index = weights[i], sorted_indexes[i]
            edge = []
            for j in range(m):
                w = weight[sorted_index[j]]
                target = sorted_index[j]
                if w > self.config.threshold:
                    edge.append([w, target])
                else:
                    break
            self.edges.append(edge)

    def init_score_list(self):
        n = len(self.concepts)
        if self.config.no_seed:
            score_list = np.ones(n)
        else:
            if not self.config.input_seed:
                with open(self.config.input_seed, "r", encoding="utf-8") as f:
                    seed_set = set([seed.strip() for seed in f.read().split("\n")])
            score_list = np.zeros(n)
            for i, c in enumerate(self.concepts):
                if c in seed_set:
                    score_list[i] = 1
        print("Seed number in candidate concepts:", np.sum(score_list))
        return score_list

    def graph_propagation(self):
        print("Graph propagation:")
        self.cal_vector_distance()
        score_list = self.init_score_list()
        final_score_list = score_list
        for i in tqdm.tqdm(range(self.config.times)):
            new_score_list = np.zeros(score_list.shape)
            for source, score in enumerate(score_list):
                if score != 0.0:
                    for (w, target) in self.edges[source]:
                        s = score * w
                        if self.config.language == "zh":
                            s *= math.log(len(self.concepts[target]) + 1)
                        new_score_list[target] += s
            new_score_list /= np.max(new_score_list)
            score_list = new_score_list
            final_score_list += score_list * calc_pow(self.config.decay, i + 1)
        return final_score_list

    def average_distance(self):
        print("average distance:")
        seed_set = set()
        n = len(self.concepts)
        if self.config.no_seed:
            seed_vecs = [vec for vec in self.vecs]
        else:
            with open(self.config.input_seed, "r", encoding="utf-8") as f:
                seed_set = set([seed.strip() for seed in f.read().split("\n")])
            seed_vecs = []
            for i, c in enumerate(self.concepts):
                if c in seed_set:
                    seed_vecs.append(self.vecs[i])
        seed_vecs = np.stack(seed_vecs)
        print("Seed number in candidate concepts:", seed_vecs.shape[0])
        score_list = np.mean(np.dot(self.vecs, seed_vecs.T), axis=1)
        return score_list

    def tf_idf(self):
        print("tf idf:")
        n = len(self.concepts)
        score_list = np.zeros(n)
        for i in tqdm.tqdm(range(n)):
            c = self.concepts[i]
            tf = max([len(t.split(c)) - 1 for t in self.text])
            idf = sum([c in t for t in self.text])
            score_list[i] = tf / math.log(1 + idf)
            if self.config.language == "zh":
                score_list[i] *= math.log(len(c) + 1)
        return score_list

    def pagerank(self):
        score_list = self.init_score_list()
        n = len(self.concepts)
        mat = np.zeros((n, n))
        for t in tqdm.tqdm(self.text):
            g = [i for i in range(n) if self.concepts[i] in t]
            for p1 in g:
                for p2 in g:
                    mat[p1, p2] += 1.0
        for i in range(n):
            mat[i] /= np.sum(mat[i])
        for i in tqdm.tqdm(range(self.config.times)):
            score_list = np.matmul(score_list, mat)
        return score_list

    def get_result(self):
        self.get_vector()
        if self.config.algorithm == "graph_propagation":
            score_list = self.graph_propagation()
        if self.config.algorithm == "average_distance":
            score_list = self.average_distance()
        if self.config.algorithm == "tf_idf":
            score_list = self.tf_idf()
        if self.config.algorithm == "pagerank":
            score_list = self.pagerank()
        sorted_list = np.argsort(-score_list)
        with open(self.config.result_path, "w", encoding="utf-8") as f:
            for index in sorted_list:
                obj = {"name": self.concepts[index], "score": float(score_list[index])}
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        print("Get result finished.")

    def get_result_list(self):
        self.get_vector()
        if self.config.algorithm == "graph_propagation":
            score_list = self.graph_propagation()
        if self.config.algorithm == "average_distance":
            score_list = self.average_distance()
        if self.config.algorithm == "tf_idf":
            score_list = self.tf_idf()
        if self.config.algorithm == "pagerank":
            score_list = self.pagerank()
        sorted_list = np.argsort(-score_list)

        res_list = [
            {"concept": self.concepts[index], "score": float(score_list[index])}
            for index in sorted_list
        ]

        print("Get result finished.")
        return res_list
