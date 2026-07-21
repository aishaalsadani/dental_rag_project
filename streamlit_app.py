"""
streamlit_app.py
Chains the full pipeline (documents -> preprocessing -> chunking -> retrieval ->
context building -> prompting) and serves grounded, source-cited answers.

The API key is read from Streamlit secrets when deployed (exact rubric pattern);
it is never stored in code.
"""

from importlib import import_module

import streamlit as st

rag = import_module("07_prompting")

# --- Read the key from Streamlit secrets when deployed (exact rubric pattern) ---
try:
    if not rag.OPENROUTER_API_KEY:
        rag.OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
    rag.OPENROUTER_MODEL = st.secrets.get("OPENROUTER_MODEL", rag.OPENROUTER_MODEL)
except Exception:
    pass

st.set_page_config(page_title="Dental Patient-Education Assistant", page_icon="🦷")
st.title("🦷 Dental Patient-Education Assistant")
st.caption(
    "Answers are grounded ONLY in retrieved patient-education handouts, prefer CURRENT "
    "sources over OUTDATED ones, and cite their sources."
)

with st.sidebar:
    st.subheader("Example questions")
    st.write(
        "- How should I take care of my new crown or bridge?\n"
        "- How do I know if my gum disease treatment is actually working?\n"
        "- Can I drink coffee while my aligner trays are in?\n"
        "- Is it okay to sleep with my new dentures in?"
    )

question = st.text_area("Your question", height=90)

if st.button("Answer") and question.strip():
    if not rag.OPENROUTER_API_KEY:
        st.warning(
            "OPENROUTER_API_KEY is not configured — showing a grounded extractive fallback. "
            "Add your key in Streamlit → Manage app → Secrets for full LLM answers."
        )
    with st.spinner("Retrieving context and generating a grounded answer..."):
        answer, sources = rag.answer_question(question)

    st.subheader("Answer")
    st.write(answer)

    with st.expander(f"Sources used ({len(sources)})", expanded=True):
        if not sources:
            st.write("No sufficiently relevant CURRENT source was found.")
        for number, e in enumerate(sources, start=1):
            status = "CURRENT" if e["is_current"] else "OUTDATED"
            st.markdown(
                f"**[{number}] {e['title']}** — {status}, updated {e['effective_date']}"
            )
            st.write(e["text"])
