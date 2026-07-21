"""
evaluation.py  (Lab 8 Final Assignment - Tasks 2, 3 and 6)

Not required by the deployment rubric, but preserved so the academic tasks stay runnable
outside the notebook:

  - Task 2: 14 queries + ground truth (7 paraphrase traps).
  - Task 3: retrieval metrics (Precision@K / Recall@K / Hit-Rate@K / MRR) for
            TF-IDF / BM25 / Semantic / Hybrid, plus an alpha sweep over {0.3, 0.5, 0.7}.
  - Task 6: automatic error analysis - for every query the Hybrid retriever misses at
            top-3, classify the likely failing layer and suggest a fix.

Run:  python evaluation.py
"""

from importlib import import_module

import numpy as np

vectors = import_module("04_vector_representation")
tfidf_search = vectors.tfidf_search
bm25_search = vectors.bm25_search
semantic_search = vectors.semantic_search
hybrid_search = vectors.hybrid_search
chunks = vectors.chunks

_DOC_BY_CHUNK = {c["chunk_id"]: c["document_id"] for c in chunks}

# --- Task 2: queries + ground truth -----------------------------------------
GROUND_TRUTH = {
    "How do I control bleeding after having a tooth pulled?": ["D17", "D4"],
    "How do I use my irrigation syringe to keep the surgical site clean?": ["D7", "D11", "D17"],
    "Why can't I open my mouth all the way after my surgery?": ["D7", "D11"],
    "How should I take care of my new crown or bridge?": ["D9"],
    "How many hours a day should I wear my clear aligner trays?": ["D14"],
    "Can I drink coffee while my aligner trays are in?": ["D14"],
    "What's a good way to check if I'm missing spots when I brush my teeth?": ["D8"],
    "How long should I wear my take-home whitening gel tray each day?": ["D6", "D19"],
    "When can I start rinsing with salt water after my root canal?": ["D5"],
    "How do I know if my gum disease treatment is actually working?": ["D12"],
    "Is it okay to sleep with my new dentures in?": ["D16"],
    "What should I do if my night guard doesn't fit right anymore?": ["D15"],
    "What foods should I avoid right after deep cleaning (scaling and root planing)?": ["D12"],
    "How long do I need to avoid smoking after a bone graft?": ["D7"],
}

IS_PARAPHRASE = {
    "How do I control bleeding after having a tooth pulled?": True,
    "How do I use my irrigation syringe to keep the surgical site clean?": False,
    "Why can't I open my mouth all the way after my surgery?": True,
    "How should I take care of my new crown or bridge?": False,
    "How many hours a day should I wear my clear aligner trays?": False,
    "Can I drink coffee while my aligner trays are in?": True,
    "What's a good way to check if I'm missing spots when I brush my teeth?": True,
    "How long should I wear my take-home whitening gel tray each day?": False,
    "When can I start rinsing with salt water after my root canal?": False,
    "How do I know if my gum disease treatment is actually working?": True,
    "Is it okay to sleep with my new dentures in?": True,
    "What should I do if my night guard doesn't fit right anymore?": True,
    "What foods should I avoid right after deep cleaning (scaling and root planing)?": False,
    "How long do I need to avoid smoking after a bone graft?": False,
}

K = 3

# --- Task 3: metrics ---------------------------------------------------------
def precision_at_k(retrieved, relevant, k=K):
    top = retrieved[:k]
    return sum(d in relevant for d in top) / k


def recall_at_k(retrieved, relevant, k=K):
    top = retrieved[:k]
    return sum(d in relevant for d in top) / len(relevant) if relevant else 0.0


def hit_rate_at_k(retrieved, relevant, k=K):
    return 1.0 if any(d in relevant for d in retrieved[:k]) else 0.0


def mrr_at_k(retrieved, relevant, k=K):
    for rank, d in enumerate(retrieved[:k], start=1):
        if d in relevant:
            return 1.0 / rank
    return 0.0


def _retrieved_doc_ids(search_fn, query, pool_k=K * 4, **kwargs):
    results = search_fn(query, top_k=pool_k, **kwargs) if kwargs else search_fn(query, top_k=pool_k)
    seen, doc_ids = set(), []
    for cid, _ in results:
        d = _DOC_BY_CHUNK[cid]
        if d not in seen:
            seen.add(d)
            doc_ids.append(d)
    return doc_ids


def evaluate_retriever(search_fn, name, **kwargs):
    metrics = {"precision": [], "recall": [], "hit_rate": [], "mrr": []}
    per_query = {}
    for query, relevant in GROUND_TRUTH.items():
        doc_ids = _retrieved_doc_ids(search_fn, query, pool_k=K * 4, **kwargs)
        metrics["precision"].append(precision_at_k(doc_ids, relevant))
        metrics["recall"].append(recall_at_k(doc_ids, relevant))
        metrics["hit_rate"].append(hit_rate_at_k(doc_ids, relevant))
        metrics["mrr"].append(mrr_at_k(doc_ids, relevant))
        per_query[query] = doc_ids
    summary = {k: float(np.mean(v)) for k, v in metrics.items()}
    summary["retriever"] = name
    return summary, per_query


# --- Task 6: error analysis --------------------------------------------------
def diagnose_failure(query, relevant, per_query_by_retriever):
    hybrid_docs = per_query_by_retriever["hybrid"][query]
    tfidf_docs = per_query_by_retriever["tfidf"][query]
    semantic_docs = per_query_by_retriever["semantic"][query]

    if hit_rate_at_k(hybrid_docs, relevant) == 1.0:
        return None  # not a failure for the retriever we ship (hybrid)

    found_anywhere = any(d in tfidf_docs[:K * 4] or d in semantic_docs[:K * 4] for d in relevant)
    if not found_anywhere:
        layer = "retrieval (vocabulary/embedding gap: no retriever's pool contained the correct doc)"
        fix = "Add missing vocabulary/synonyms to search_text (title/doc_type), or enrich metadata."
    elif any(d in tfidf_docs[:K] for d in relevant) and not any(d in hybrid_docs[:K] for d in relevant):
        layer = "retrieval (alpha: TF-IDF had it top-3 but the hybrid blend pushed it out)"
        fix = "Lower alpha (lean lexical) for this query type; re-check the alpha sweep."
    elif any(d in semantic_docs[:K] for d in relevant) and not any(d in hybrid_docs[:K] for d in relevant):
        layer = "retrieval (alpha: Semantic had it top-3 but the hybrid blend pushed it out)"
        fix = "Raise alpha (lean semantic) for this query type."
    else:
        layer = "retrieval (ranking: in a larger pool but not top-3 by any single retriever)"
        fix = "Increase pool_size/top_k before re-ranking, or add a metadata boost for exact doc_type."

    return {
        "query": query,
        "correct_document(s)": relevant,
        "hybrid_returned_instead": hybrid_docs[:K],
        "tfidf_returned": tfidf_docs[:K],
        "semantic_returned": semantic_docs[:K],
        "likely_failing_layer": layer,
        "suggested_fix": fix,
    }


def run_full_evaluation():
    print("SEMANTIC_MODE:", vectors.SEMANTIC_MODE)
    print(f"Queries: {len(GROUND_TRUTH)} | paraphrase traps: {sum(IS_PARAPHRASE.values())}\n")

    summaries, per_query = [], {}
    for key, fn, label in [
        ("tfidf", tfidf_search, "TF-IDF"),
        ("bm25", bm25_search, "BM25"),
        ("semantic", semantic_search, "Semantic"),
        ("hybrid", hybrid_search, "Hybrid (alpha=0.6)"),
    ]:
        s, pq = evaluate_retriever(fn, label)
        summaries.append(s)
        per_query[key] = pq

    print("=== Retrieval metrics @K=3 ===")
    for s in summaries:
        print(f"  {s['retriever']:20s} P={s['precision']:.3f} R={s['recall']:.3f} "
              f"Hit={s['hit_rate']:.3f} MRR={s['mrr']:.3f}")

    print("\n=== Alpha sweep (Task 3: >=3 values) ===")
    best, best_avg = None, -1.0
    for alpha in [0.3, 0.5, 0.7]:
        s, _ = evaluate_retriever(hybrid_search, f"Hybrid(alpha={alpha})", alpha=alpha)
        avg = np.mean([s["precision"], s["recall"], s["hit_rate"], s["mrr"]])
        print(f"  alpha={alpha}: P={s['precision']:.3f} R={s['recall']:.3f} "
              f"Hit={s['hit_rate']:.3f} MRR={s['mrr']:.3f} | avg={avg:.3f}")
        if avg > best_avg:
            best, best_avg = alpha, avg
    print(f"  -> best alpha on this dataset: {best}")

    print("\n=== Error analysis (Task 6) ===")
    failures = []
    for query, relevant in GROUND_TRUTH.items():
        diag = diagnose_failure(query, relevant, per_query)
        if diag:
            failures.append(diag)
    print(f"Queries where Hybrid@3 missed ground truth: {len(failures)}")
    for d in failures:
        print(f"\n  Q: {d['query']}")
        print(f"     correct={d['correct_document(s)']} hybrid_returned={d['hybrid_returned_instead']}")
        print(f"     layer: {d['likely_failing_layer']}")
        print(f"     fix  : {d['suggested_fix']}")
    return summaries, per_query, failures


if __name__ == "__main__":
    run_full_evaluation()
