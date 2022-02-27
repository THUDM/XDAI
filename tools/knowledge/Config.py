import os


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
        self.db = "snippet.db"
        self.cookie_paths = ["cookie/{}".format(file) for file in os.listdir("cookie/")]
        self.proxy = {
            "http": "http://localhost:8001",
            "https": "http://localhost:8001",
        }  # should change to your own proxy
        self.text_path = "tmp/text.txt"
        self.candidate_path = "tmp/candidate.txt"
        self.cached_vecs_path = "data/cached_vecs.pkl"
