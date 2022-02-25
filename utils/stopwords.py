import os

file_dir = os.path.dirname(os.path.abspath(__file__))


def stopwordslist():
    filepath = os.path.join(file_dir, "data", "stopwords_ch.txt")
    stopwords = [line.strip() for line in open(filepath, encoding="UTF-8").readlines()]
    return stopwords


if __name__ == "__main__":
    print("我" in stopwordslist())
