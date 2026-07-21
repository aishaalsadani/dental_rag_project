"""
06_retrieve_context.py
Turn raw hybrid-retriever candidates into a clean, safe context package (Task 4).

build_context() applies four steps, in order:
  1. Current/outdated conflict resolution - if candidates share the same doc_type but
     come from different documents (old vs new crown/bridge, old vs new scaling), keep
     only the chunk(s) from the document marked is_current=True (most recent wins).
  2. Outdated safety net - drop any remaining chunk whose document is is_current=False.
  3. Near-duplicate chunk removal - several current handouts repeat near-identical
     boilerplate (irrigation-syringe, bleeding, smoking paragraphs); chunks >=85%
     similar (difflib) to one already kept are dropped, highest score wins.
  4. 150-word budget - add chunks highest-score-first until the next one would exceed 150.

format_context_package() labels each surviving chunk [n] with its title, effective_date
and a CURRENT/OUTDATED tag, so the prompt can cite sources by number.
"""

from difflib import SequenceMatcher
from importlib import import_module

vectors = import_module("04_vector_representation")
hybrid_search = vectors.hybrid_search
chunks = vectors.chunks

_CHUNK_BY_ID = {c["chunk_id"]: c for c in chunks}


def is_near_duplicate(text_a, text_b, threshold=0.85):
    return SequenceMatcher(None, text_a, text_b).ratio() >= threshold


def build_context(query, pool_size=10, alpha=0.6, min_score=0.02, max_words=150):
    candidates = hybrid_search(query, top_k=pool_size, alpha=alpha)

    evidence = []
    for cid, score in candidates:
        if score < min_score:
            continue
        row = _CHUNK_BY_ID[cid]
        evidence.append(
            {
                "chunk_id": cid,
                "document_id": row["document_id"],
                "title": row["title"],
                "doc_type": row["doc_type"],
                "effective_date": row["effective_date"],
                "is_current": bool(row["is_current"]),
                "text": row["text"],
                "score": float(score),
            }
        )

    # Step 1: same doc_type across multiple documents -> keep the current / newest one
    by_type = {}
    for e in evidence:
        by_type.setdefault(e["doc_type"], []).append(e)
    filtered = []
    for _doc_type, items in by_type.items():
        docs_present = {i["document_id"] for i in items}
        if len(docs_present) > 1:
            current_items = [i for i in items if i["is_current"]]
            keep_pool = current_items if current_items else items
            keep_doc = max(keep_pool, key=lambda x: x["effective_date"])["document_id"]
            items = [i for i in items if i["document_id"] == keep_doc]
        filtered.extend(items)

    # Step 2: outdated safety net
    filtered = [e for e in filtered if e["is_current"]]

    # Step 3: near-duplicate chunk removal (highest score wins)
    filtered = sorted(filtered, key=lambda x: -x["score"])
    deduped = []
    for e in filtered:
        if any(is_near_duplicate(e["text"], kept["text"]) for kept in deduped):
            continue
        deduped.append(e)

    # Step 4: 150-word budget
    final, used_words = [], 0
    for e in deduped:
        n_words = len(e["text"].split())
        if used_words + n_words > max_words and final:
            break
        final.append(e)
        used_words += n_words

    return final


def format_context_package(evidence):
    lines = []
    for i, e in enumerate(evidence, start=1):
        status = "CURRENT" if e["is_current"] else "OUTDATED"
        lines.append(
            f"[{i}] Source: {e['title']} ({status}, updated {e['effective_date']})\n{e['text']}"
        )
    return "\n\n".join(lines)


if __name__ == "__main__":
    demo = "How should I take care of my new crown or bridge?"
    ctx = build_context(demo)
    print(f"QUERY: {demo}")
    print(format_context_package(ctx))
    print("\nword count:", sum(len(e["text"].split()) for e in ctx), "/ 150")
