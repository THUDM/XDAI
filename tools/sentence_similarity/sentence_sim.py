from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

modelname = "uer/sbert-base-chinese-nli"
model = SentenceTransformer(modelname)


def get_similarity_scores(target="", candidates=[]):
    texts = [target] + candidates
    sentence_embeddings = model.encode(texts)
    res = cosine_similarity([sentence_embeddings[0]], sentence_embeddings[1:])
    return res[0].tolist()


_ = get_similarity_scores(
    target="", candidates=["你", "我"]
)  # first time called, take a bit longer


if __name__ == "__main__":
    target = "....."
    candidates = [".....", "..", "."]
    res = get_similarity_scores(target=target, candidates=candidates)