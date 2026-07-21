# Dental Patient-Education RAG Assistant

A retrieval-augmented-generation assistant over **19 real dental patient-education
handouts**, refactored from the course notebook into the required Python-file structure.

```text
documents -> preprocessing -> chunking -> vector representation -> vector store
          -> context retrieval -> prompting -> Streamlit UI
```

## File structure

| File | Role |
|---|---|
| `01_documents.py` | The 19-document knowledge base + metadata (2 outdated/current pairs). |
| `02_preprocessing.py` | Lab 5 `minimal_clean` profile (lowercase / URLs / whitespace). |
| `03_chunking.py` | 38-word chunks, 10-word overlap; builds `search_text`. |
| `04_vector_representation.py` | TF-IDF, BM25, semantic (`all-MiniLM-L6-v2`), hybrid search. |
| `05_create_chroma_store.py` | Persists embeddings + metadata to a local Chroma store. |
| `06_retrieve_context.py` | Conflict resolution, dedup, 150-word budget, CURRENT/OUTDATED labels. |
| `07_prompting.py` | Weak/better/strict prompts + grounded OpenRouter call with citations. |
| `streamlit_app.py` | UI that chains the pipeline and shows the cited answer. |
| `evaluation.py` | (Extra) Lab 8 Tasks 2/3/6: queries, metrics, alpha sweep, error analysis. |
| `requirements.txt` | Dependencies. |

## Run locally

```powershell
python -m pip install -r requirements.txt

# secrets for local runs (never commit the real file)
Copy-Item .env.example .env          # then edit .env with your real key
# or:  Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml

python 05_create_chroma_store.py     # build the vector store
streamlit run streamlit_app.py
```

Run the academic evaluation separately: `python evaluation.py`.

## Deploy to Streamlit Cloud

1. Push to GitHub (`.gitignore` keeps `.env` and `secrets.toml` out).
2. Create the app pointing at `streamlit_app.py`.
3. **Manage app -> Secrets**, paste in TOML:

   ```toml
   OPENROUTER_API_KEY = "your_openrouter_key_here"
   OPENROUTER_MODEL = "openai/gpt-4o-mini"
   ```

The app reads the key from Streamlit secrets at runtime; no key is stored in code.
Every answer is grounded ONLY in retrieved context, prefers CURRENT over OUTDATED
sources, and cites its sources by number.
