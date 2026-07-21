"""
07_prompting.py
Three prompt styles (Task 5) + grounded LLM generation (Lab 9) via OpenRouter.

  - WEAK   : dumps context + question, no rules (free to hallucinate).
  - BETTER : adds grounding rules + a citation requirement, free-form prose.
  - STRICT : full anatomy - role, task, evidence boundary, operational rules
             (cite sources, refuse if unsupported, resolve conflicts by recency),
             and a two-part ANSWER / SOURCES USED output format. This is the prompt
             the deployed assistant ships, so every answer both USES the retrieved
             context and CITES its sources.

The API key is NEVER hardcoded: it is read from the environment (local .env) or, when
deployed, injected by streamlit_app.py from Streamlit secrets into OPENROUTER_API_KEY /
OPENROUTER_MODEL below. If no key is present the module returns a clearly-labeled
extractive fallback so the pipeline still runs end-to-end.
"""

import os
from importlib import import_module

from dotenv import load_dotenv
from openai import OpenAI

retrieve = import_module("06_retrieve_context")
build_context = retrieve.build_context
format_context_package = retrieve.format_context_package

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

WEAK_PROMPT = """Answer the question using the context.
Context: {context}
Question: {question}"""

BETTER_PROMPT = """You are a dental patient-education assistant. Use the context below to answer
the patient's question. Only use information that is actually stated in the context, and mention
which source number(s) support each claim, like [1].

Context:
{context}

Question: {question}

Answer:"""

STRICT_PROMPT = """You are a dental patient-education assistant.

Task: Answer the patient's question using ONLY the evidence in the context package below.

Rules:
- If the answer is not fully supported by the context, say you don't have enough information and recommend they call the clinic.
- Every source in the context package is already labeled CURRENT or OUTDATED. Never base your answer on an OUTDATED source; if only an OUTDATED source is present, say so explicitly.
- If two CURRENT sources conflict, prefer the most recently updated one and note the conflict.
- Do not give medical advice beyond what is written in the sources.
- Keep the answer under 150 words, in plain, patient-friendly language.

Context package:
{context}

Patient question: {question}

Respond in exactly this two-part format:
ANSWER: <your grounded answer, with inline citations like [1]>
SOURCES USED: <comma-separated list of the source numbers you actually relied on>"""


def build_prompt(question, context_text, style="strict"):
    template = {"weak": WEAK_PROMPT, "better": BETTER_PROMPT, "strict": STRICT_PROMPT}[style]
    return template.format(context=context_text, question=question)


def _extractive_fallback(evidence):
    """Grounded, citation-preserving answer used only when no API key is configured."""
    if not evidence:
        return ("ANSWER: I don't have enough information in the current sources to answer "
                "that. Please call the clinic.\nSOURCES USED: none")
    lines = ["ANSWER: Based on the retrieved CURRENT sources:"]
    used = []
    for i, e in enumerate(evidence, start=1):
        snippet = " ".join(e["text"].split()[:40])
        lines.append(f"- {snippet} [{i}]")
        used.append(str(i))
    lines.append("SOURCES USED: " + ", ".join(used))
    return ("[SIMULATED ANSWER -- no OPENROUTER_API_KEY set]\n" + "\n".join(lines))


def ask_openrouter(prompt):
    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=400,
    )
    return response.choices[0].message.content


def answer_question(question, style="strict"):
    evidence = build_context(question)
    context_text = format_context_package(evidence)
    prompt = build_prompt(question, context_text, style=style)

    if not OPENROUTER_API_KEY:
        return _extractive_fallback(evidence), evidence

    try:
        return ask_openrouter(prompt), evidence
    except Exception as exc:
        return f"[LLM call failed: {exc}]", evidence


if __name__ == "__main__":
    for q in [
        "How should I take care of my new crown or bridge?",
        "How do I know if my gum disease treatment is actually working?",
    ]:
        ans, sources = answer_question(q)
        print(f"Q: {q}\n{ans}\n{'-' * 80}")
