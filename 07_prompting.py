"""
07_prompting.py
Grounded LLM generation via OpenRouter — STRICT mode.

Behavior:
  - The model answers ONLY from the retrieved context (the uploaded files).
  - If the answer is not in the context, it says so and STOPS. No general
    knowledge, no guessing, no hallucination.
  - If retrieval returns nothing, we do NOT call the LLM at all — we return a
    fixed "not found" message.
  - Inline citations [1], [2] are kept; the "SOURCES USED" footer is stripped.
"""

import os
import re
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
DEBUG = os.getenv("DEBUG_PROMPTING", "0") == "1"

# Fixed message shown (in the question's language) when the answer is not in the files.
NOT_FOUND_EN = ("ANSWER: I couldn't find this information in the provided documents. "
                "Please contact the clinic for help with this question.")
NOT_FOUND_AR = ("الإجابة: المعلومة دي مش موجودة في الملفات المتاحة عندي. "
                "من فضلك تواصل مع العيادة عشان يساعدوك في السؤال ده.")

# ---------------------------------------------------------------------------
# Prompts (STRICT — grounded only)
# ---------------------------------------------------------------------------
WEAK_PROMPT = """Answer the question using ONLY the context. If the answer is not in the context, say you don't know.
Context: {context}
Question: {question}"""

BETTER_PROMPT = """You are a dental patient-education assistant. Answer the patient's question using
ONLY information that is explicitly stated in the context below. Cite the source number(s) for each
claim, like [1]. If the context does not contain the answer, reply exactly: "NOT_IN_CONTEXT".

Context:
{context}

Question: {question}

Answer:"""

STRICT_PROMPT = """You are DentAI, a dental patient-education assistant.

CORE RULE — GROUNDING (most important):
- Answer using ONLY information that is explicitly stated in the context package below.
- You may NOT use outside knowledge, assumptions, or general dental knowledge.
- Every factual claim MUST be supported by a citation to a source number, like [1] or [2].
- If the context does NOT contain enough information to answer the question, DO NOT guess and DO NOT
  fill gaps from general knowledge. Instead reply with EXACTLY this token and nothing else:
  NOT_IN_CONTEXT
- If only part of the question is covered by the context, answer that part from the context and, for
  the rest, say clearly that the documents don't cover it — do NOT invent an answer.

Safety rules:
- Do not prescribe medication doses or diagnose specific conditions.
- For emergencies (severe swelling, trauma, uncontrolled bleeding), tell the patient to seek urgent care.
- Keep answers under 180 words, plain patient-friendly language.

Source freshness:
- Sources are labeled CURRENT or OUTDATED. Prefer CURRENT. If two CURRENT sources conflict, prefer the
  most recent and mention the conflict briefly.

Language rule (VERY IMPORTANT):
- Detect the language AND dialect of the patient's question and reply in the SAME language/dialect.
- If the question uses Egyptian colloquial Arabic (words like "ازاي", "عايز", "بتاع", "مش", "ايه", "ليه", "فين"),
  reply ENTIRELY in natural Egyptian Arabic (العامية المصرية) — friendly and warm. Do NOT use فصحى in that case.
- If the question is in Modern Standard Arabic, reply in فصحى.
- If in English, reply in English.
- Start with the label naturally:
    * English  -> "ANSWER:"
    * فصحى     -> "الإجابة:"
    * مصري     -> "الإجابة:"

Output format:
ANSWER: <your answer, grounded ONLY in the context, with inline citations like [1], [2]>
(do NOT add a separate "SOURCES USED" line at the end; the inline citations are enough.)

Context package:
{context}

Patient question: {question}
Reply now:"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_prompt(question, context_text, style="strict"):
    template = {"weak": WEAK_PROMPT, "better": BETTER_PROMPT, "strict": STRICT_PROMPT}[style]
    return template.format(context=context_text, question=question)


_ARABIC_RE = re.compile(r"[؀-ۿ]")


def is_arabic(text):
    return bool(_ARABIC_RE.search(text or ""))


def _not_found_message(question):
    return NOT_FOUND_AR if is_arabic(question) else NOT_FOUND_EN


# Detects the model's own "I don't know / not in context" signal.
_NOT_IN_CONTEXT_RE = re.compile(r"NOT[_\s]?IN[_\s]?CONTEXT", re.IGNORECASE)


def _is_not_in_context(text):
    return bool(text) and bool(_NOT_IN_CONTEXT_RE.search(text))


# Regex to strip the entire "SOURCES USED: ..." footer line (Arabic or English)
_SOURCES_FOOTER_RE = re.compile(
    r"^\s*(?:\*\*)?"
    r"(?:SOURCES\s*USED"
    r"|المصادر\s*المستخدمة"
    r"|المصادر\s*اللي\s*اتستخدمت"
    r"|المصادر)"
    r"(?:\*\*)?"
    r"\s*[:：]\s*"
    r".+?$",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)


def _clean_answer(text):
    """Remove any trailing 'SOURCES USED: ...' line, keep inline citations."""
    if not text:
        return text
    cleaned = _SOURCES_FOOTER_RE.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _extractive_fallback(evidence, question=""):
    """Used only when no API key is configured but we DO have evidence."""
    if not evidence:
        return _not_found_message(question)
    if is_arabic(question):
        lines = ["الإجابة: [مفيش OPENROUTER_API_KEY -- ده رد مبني على المصادر مباشرة]"]
        for i, e in enumerate(evidence, start=1):
            snippet = " ".join(e["text"].split()[:40])
            lines.append(f"- {snippet} [{i}]")
        return "\n".join(lines)
    lines = ["ANSWER: Based on the retrieved sources:"]
    for i, e in enumerate(evidence, start=1):
        snippet = " ".join(e["text"].split()[:40])
        lines.append(f"- {snippet} [{i}]")
    return "[SIMULATED ANSWER -- no OPENROUTER_API_KEY set]\n" + "\n".join(lines)


def ask_openrouter(prompt):
    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,          # deterministic, minimizes improvisation
        max_tokens=500,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def answer_question(question, style="strict"):
    evidence = build_context(question)

    if DEBUG:
        print(f"[DEBUG] API key present: {bool(OPENROUTER_API_KEY)}")
        print(f"[DEBUG] Evidence chunks: {len(evidence) if evidence else 0}")

    # Case 1: retrieval returned nothing -> do NOT call the LLM. Refuse.
    if not evidence:
        return _not_found_message(question), []

    # Case 2: no API key -> local extractive fallback (still grounded in evidence)
    if not OPENROUTER_API_KEY:
        return _clean_answer(_extractive_fallback(evidence, question)), evidence

    # Case 3: API key + evidence -> grounded generation
    context_text = format_context_package(evidence)
    prompt = build_prompt(question, context_text, style=style)
    try:
        ans = ask_openrouter(prompt)
    except Exception as exc:
        return f"[LLM call failed: {exc}]", evidence

    # If the model said the answer isn't in the context, return the clean refusal.
    if _is_not_in_context(ans):
        return _not_found_message(question), []

    return _clean_answer(ans), evidence


if __name__ == "__main__":
    test_qs = [
        "Is teeth whitening safe?",                       # should be answered from files
        "ازاي اعرف ان علاج اللثة بتاعي بيشتغل فعلا؟",       # from files
        "What is the capital of France?",                 # NOT dental -> should refuse
    ]
    for q in test_qs:
        ans, srcs = answer_question(q)
        print(f"\nQ: {q}\n{ans}\n{'-'*60}")
