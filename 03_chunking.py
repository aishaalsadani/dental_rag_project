"""
03_chunking.py
Fixed overlapping word-window chunking (Lab 8 / Lab 9 "Single-Path Chunking"):
38-word chunks with 10-word overlap (step = 28). Each chunk keeps its parent
document's full metadata (including is_current, needed for context filtering) and
a `search_text` field that prepends title + doc_type to give the lexical/semantic
retrievers extra context clues.
"""

from importlib import import_module

DOCUMENTS = import_module("01_documents").DOCUMENTS
preprocess_text = import_module("02_preprocessing").preprocess_text

CHUNK_SIZE = 38
OVERLAP = 10


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    words = text.split()
    step = chunk_size - overlap
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + chunk_size]))
        if i + chunk_size >= len(words):
            break
        i += step
    return chunks


def build_chunks():
    rows = []
    for doc in DOCUMENTS:
        for idx, ch in enumerate(chunk_text(doc["text"])):
            rows.append(
                {
                    "chunk_id": f"{doc['document_id']}_{idx}",
                    "document_id": doc["document_id"],
                    "title": doc["title"],
                    "doc_type": doc["doc_type"],
                    "effective_date": doc["effective_date"],
                    "is_current": doc["is_current"],
                    "chunk_index": idx,
                    "text": ch,
                    "search_text": preprocess_text(
                        f"{doc['title']} | {doc['doc_type']} | {ch}"
                    ),
                }
            )
    return rows


# Built once and reused by the retrieval / store / retrieval-context modules.
CHUNKS = build_chunks()


if __name__ == "__main__":
    from collections import Counter

    print(f"Total chunks: {len(CHUNKS)} from "
          f"{len({c['document_id'] for c in CHUNKS})} documents")
    per_doc = Counter(c["document_id"] for c in CHUNKS)
    print("Chunks per document:", dict(per_doc))
