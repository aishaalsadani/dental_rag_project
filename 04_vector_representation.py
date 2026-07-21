"""
04_vector_representation.py
Four retrievers over the chunk corpus (Lab 6 / Lab 7 / Task 3):

  - TF-IDF   : lexical baseline with bigrams (exact word/phrase overlap).
  - BM25     : stronger lexical model (term saturation + length normalization).
  - Semantic : SentenceTransformer("all-MiniLM-L6-v2") dense vectors, so
               "gum disease" can match a chunk that only says "periodontal disease".
  - Hybrid   : hybrid = alpha * semantic + (1 - alpha) * lexical, both min-max
               normalized to [0, 1].

Semantic embeddings try the real model first (works on Streamlit Cloud / Colab,
which have internet). If the model cannot be downloaded, the module falls back to a
TF-IDF + LSA (TruncatedSVD) pseudo-embedding so the pipeline still runs end-to-end.
`SEMANTIC_MODE` reports which path is active ("sentence-transformers" vs "lsa_fallback").
"""

from importlib import import_module

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi

preprocess_text = import_module("02_preprocessing").preprocess_text
CHUNKS = import_module("03_chunking").CHUNKS

# Kept as module-level so downstream modules can index chunks by position.
chunks = CHUNKS
corpus = [c["search_text"] for c in CHUNKS]

MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_ALPHA = 0.6

# --- TF-IDF ---
tfidf_vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
tfidf_matrix = tfidf_vec.fit_transform(corpus)


def tfidf_search(query, top_k=8):
    q_vec = tfidf_vec.transform([preprocess_text(query)])
    scores = cosine_similarity(q_vec, tfidf_matrix).flatten()
    order = np.argsort(-scores)[:top_k]
    return [(chunks[i]["chunk_id"], float(scores[i])) for i in order]


# --- BM25 (bonus retriever) ---
tokenized_corpus = [c.lower().split() for c in corpus]
bm25 = BM25Okapi(tokenized_corpus)


def bm25_search(query, top_k=8):
    scores = bm25.get_scores(preprocess_text(query).lower().split())
    order = np.argsort(-scores)[:top_k]
    return [(chunks[i]["chunk_id"], float(scores[i])) for i in order]


# --- Semantic embeddings (real model, with offline LSA fallback) ---
SEMANTIC_MODE = None
st_model = None
svd_model = None
try:
    from sentence_transformers import SentenceTransformer

    st_model = SentenceTransformer(MODEL_NAME)
    embeddings = st_model.encode(corpus, show_progress_bar=False)
    SEMANTIC_MODE = "sentence-transformers"
except Exception:
    from sklearn.decomposition import TruncatedSVD

    svd_model = TruncatedSVD(n_components=64, random_state=42)
    embeddings = svd_model.fit_transform(tfidf_matrix)
    SEMANTIC_MODE = "lsa_fallback"


def _embed_query(query):
    if SEMANTIC_MODE == "sentence-transformers":
        return st_model.encode([query])
    return svd_model.transform(tfidf_vec.transform([preprocess_text(query)]))


def semantic_search(query, top_k=8):
    q_emb = _embed_query(query)
    scores = cosine_similarity(q_emb, embeddings).flatten()
    order = np.argsort(-scores)[:top_k]
    return [(chunks[i]["chunk_id"], float(scores[i])) for i in order]


# --- Hybrid (lexical + semantic) ---
def normalize(scores):
    scores = np.asarray(scores, dtype=float)
    if scores.max() - scores.min() < 1e-9:
        return np.zeros_like(scores)
    return (scores - scores.min()) / (scores.max() - scores.min())


def hybrid_search(query, top_k=8, alpha=DEFAULT_ALPHA):
    q_tfidf = tfidf_vec.transform([preprocess_text(query)])
    lexical_scores = cosine_similarity(q_tfidf, tfidf_matrix).flatten()

    if SEMANTIC_MODE == "sentence-transformers":
        q_emb = st_model.encode([query])
    else:
        q_emb = svd_model.transform(q_tfidf)
    semantic_scores = cosine_similarity(q_emb, embeddings).flatten()

    hybrid_scores = alpha * normalize(semantic_scores) + (1 - alpha) * normalize(lexical_scores)
    order = np.argsort(-hybrid_scores)[:top_k]
    return [(chunks[i]["chunk_id"], float(hybrid_scores[i])) for i in order]


if __name__ == "__main__":
    print("SEMANTIC_MODE:", SEMANTIC_MODE, "| chunks:", len(chunks))
    q = "How do I know if my gum disease treatment is actually working?"
    for name, fn in [("TF-IDF", tfidf_search), ("BM25", bm25_search),
                     ("Semantic", semantic_search), ("Hybrid", hybrid_search)]:
        print(f"\n{name}:")
        for cid, score in fn(q, top_k=5):
            row = next(c for c in chunks if c["chunk_id"] == cid)
            flag = "CURRENT" if row["is_current"] else "OUTDATED"
            print(f"  {cid:8s} (doc={row['document_id']:4s} {flag:8s}) score={score:.3f}")
