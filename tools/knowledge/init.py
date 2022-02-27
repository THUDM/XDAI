import nltk
import os

if not os.path.exists("tmp/"):
    os.mkdir("tmp/")
if not os.path.exists("data/"):
    os.system("wget http://lfs.aminer.cn/misc/moocdata/toolkit/data.zip")
    os.system("unzip data.zip")
nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")
