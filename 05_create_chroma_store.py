"""
05_create_chroma_store.py
Persist the chunk embeddings + metadata into a local Chroma vector store.

The store path is resolved RELATIVE to this file (never a hardcoded absolute path),
so it works both locally and on Streamlit Cloud. Run this once to (re)build the store:

    python 05_create_chroma_store.py
"""

from importlib import import_module
from pathlib import Path

import chromadb
from chromadb.config import Settings

vectors = import_module("04_vector_representation")

DB_PATH = Path(__file__).resolve().parent / "chroma_db"
COLLECTION_NAME = "dental_patient_education"


def create_vector_store():
    client = chromadb.PersistentClient(
        path=str(DB_PATH),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(COLLECTION_NAME)

    collection.upsert(
        ids=[c["chunk_id"] for c in vectors.chunks],
        documents=[c["text"] for c in vectors.chunks],
        metadatas=[
            {
                "document_id": c["document_id"],
                "title": c["title"],
                "doc_type": c["doc_type"],
                "effective_date": c["effective_date"],
                "is_current": str(c["is_current"]),
            }
            for c in vectors.chunks
        ],
        embeddings=[list(map(float, e)) for e in vectors.embeddings],
    )
    return collection


if __name__ == "__main__":
    col = create_vector_store()
    print(f"Chroma store created at {DB_PATH} "
          f"(collection='{COLLECTION_NAME}', mode={vectors.SEMANTIC_MODE}).")
