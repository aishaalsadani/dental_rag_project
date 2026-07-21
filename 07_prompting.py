"""
07_prompting.py
Three prompt styles + grounded LLM generation via OpenRouter.

Cleaned version:
  - Removes any trailing "SOURCES USED: general knowledge" (or Arabic
    equivalents) from the final answer.
  - NO_CONTEXT_PROMPT no longer asks the model for a SOURCES line at all.
  - Smart fallback: if API key exists but no retrieval evidence, still
    answer using general dental knowledge.
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


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

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

STRICT_PROMPT = """You are DentAI, a friendly and knowledgeable dental patient-education assistant.

Your job: help the patient with a clear, useful answer to their dental question.

How to use the context:
- Prefer information from the context package below when it is relevant, and cite it with [1], [2], etc.
- If the context is only partially relevant, USE the relevant parts AND supplement with well-established general dental knowledge — but clearly separate cited claims from general guidance.
- If the context is empty or totally unrelated, still give a helpful answer based on general dental knowledge, and add a short note like: "This is general guidance — for your specific case, please contact the clinic."
- NEVER refuse to answer just because the context is thin. Only refuse if the question is dangerous, non-dental, or clearly requires an in-person exam.

Safety rules:
- Do not prescribe medication doses or diagnose specific conditions.
- For emergencies (severe swelling, trauma, uncontrolled bleeding), tell the patient to seek urgent care.
- Keep answers under 180 words, plain patient-friendly language.

Source freshness:
- Sources are labeled CURRENT or OUTDATED. Prefer CURRENT. If two CURRENT sources conflict, prefer the most recent and mention the conflict briefly.

Language rule (VERY IMPORTANT):
- Detect the language AND dialect of the patient's question and reply in the SAME language/dialect.
- If the question uses Egyptian colloquial Arabic (words like "ازاي", "عايز", "بتاع", "مش", "ايه", "ليه", "فين"), reply ENTIRELY in natural Egyptian Arabic (العامية المصرية) — friendly, warm, like a real Egyptian dental assistant. Do NOT use Modern Standard Arabic (فصحى) in that case.
- If the question is in Modern Standard Arabic, reply in فصحى.
- If in English, reply in English.
- Translate the output labels naturally:
    * English  -> "ANSWER:" and "SOURCES USED:"
    * فصحى     -> "الإجابة:" and "المصادر المستخدمة:"
    * مصري     -> "الإجابة:" and "المصادر اللي اتستخدمت:"
- Citations always stay as [1], [2] etc.
- If you did NOT actually use any of the numbered sources, DO NOT output the
  "SOURCES USED" line at all. Only output that line when you actually cited [n].

Context package:
{context}

Patient question: {question}

Reply in this format (omit the SOURCES line entirely if you didn't cite anything):
ANSWER: <your helpful answer, with [n] citations where context was used>
SOURCES USED: <comma-separated source numbers you actually cited>"""


# Prompt used when retrieval returns nothing but we still have an API key.
# NOTE: this prompt intentionally does NOT ask for a SOURCES USED line.
NO_CONTEXT_PROMPT = """You are DentAI, a friendly dental patient-education assistant.

The internal knowledge base did NOT return any relevant sources for this question,
but you should still help the patient with a clear answer based on well-established
general dental knowledge.

Rules:
- Give a helpful, practical answer (under 180 words).
- Add a brief note that this is general guidance and for their specific case they
  should contact the clinic.
- Do not prescribe medication doses or diagnose specific conditions.
- For emergencies (severe swelling, trauma, uncontrolled bleeding), tell them to seek urgent care.
- DO NOT include any "SOURCES USED", "المصادر المستخدمة", or "المصادر اللي اتستخدمت" line.
- DO NOT add citations like [1], [2]. Just give the answer directly.

Language rule:
- Detect the language/dialect of the question and reply in the same one.
- Egyptian colloquial Arabic ("ازاي","عايز","بتاع","مش","ايه") -> reply in العامية المصرية.
- Modern Standard Arabic -> reply in فصحى.
- English -> reply in English.
- Start with the label naturally:
    English -> "ANSWER:"
    فصحى    -> "الإجابة:"
    مصري    -> "الإجابة:"

Patient question: {question}

Reply in this format ONLY (no sources line):
ANSWER: <your helpful general-knowledge answer>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_prompt(question, context_text, style="strict"):
    template = {"weak": WEAK_PROMPT, "better": BETTER_PROMPT, "strict": STRICT_PROMPT}[style]
    return template.format(context=context_text, question=question)


_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

def is_arabic(text):
    return bool(_ARABIC_RE.search(text or ""))


# Matches lines like:
#   SOURCES USED: general knowledge
#   SOURCES USED: none
#   SOURCES USED:
#   المصادر المستخدمة: لا يوجد
#   المصادر اللي اتستخدمت: معرفة عامة
#   المصادر اللي اتستخدمت:
_EMPTY_SOURCES_RE = re.compile(
    r"^[\-\*\s>]*"
    r"(?:\*\*)?"
    r"(SOURCES\s*USED|المصادر\s*المستخدمة|المصادر\s*اللي\s*اتستخدمت|المصادر)"
    r"(?:\*\*)?"
    r"\s*[:\-–]\s*"
    r"(general\s*knowledge|none|n/?a|لا\s*يوجد|معرفة\s*عامة|—|-|\.|)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _clean_answer(text):
    """
    Remove any empty / 'general knowledge' SOURCES line from the answer.
    Also trims trailing whitespace and stray blank lines.
    """
    if not text:
        return text

    cleaned = _EMPTY_SOURCES_RE.sub("", text)

    # collapse 3+ blank lines to just one
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.rstrip()


def _egyptian_no_context_fallback(question):
    """Used only when NO api key AND NO evidence."""
    if is_arabic(question):
        return ("الإجابة: للأسف مفيش مفتاح API متظبط، فمقدرش أجاوبك دلوقتي. "
                "من فضلك ظبطي OPENROUTER_API_KEY في ملف .env أو في Streamlit Secrets.")
    return ("ANSWER: I can't answer right now because no OPENROUTER_API_KEY is configured. "
            "Please set it in your .env file or Streamlit Secrets.")


def _extractive_fallback(evidence, question=""):
    """Used only when no API key is configured but we DO have evidence."""
    if not evidence:
        return _egyptian_no_context_fallback(question)

    if is_arabic(question):
        lines = ["الإجابة: [مفيش OPENROUTER_API_KEY متظبط -- ده رد مبني على المصادر مباشرة]"]
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
        temperature=0.2,
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
        print(f"[DEBUG] Model: {OPENROUTER_MODEL}")

    # Case 1: no API key -> local fallback
    if not OPENROUTER_API_KEY:
        ans = _extractive_fallback(evidence, question)
        return _clean_answer(ans), evidence

    # Case 2: API key but no evidence -> general-knowledge prompt
    if not evidence:
        if DEBUG:
            print("[DEBUG] No evidence found, using NO_CONTEXT_PROMPT")
        prompt = NO_CONTEXT_PROMPT.format(question=question)
        try:
            ans = ask_openrouter(prompt)
            return _clean_answer(ans), []
        except Exception as exc:
            return f"[LLM call failed: {exc}]", []

    # Case 3: API key + evidence -> normal grounded generation
    context_text = format_context_package(evidence)
    prompt = build_prompt(question, context_text, style=style)
    try:
        ans = ask_openrouter(prompt)
        return _clean_answer(ans), evidence
    except Exception as exc:
        return f"[LLM call failed: {exc}]", evidence


if __name__ == "__main__":
    test_qs = [
        "How should I take care of my new crown or bridge?",
        "ازاي اعرف ان علاج اللثة بتاعي بيشتغل فعلا؟",
        "بسنانى بتوجعنى قوى بالليل ايه اعمل؟",
    ]
    for q in test_qs:
        ans, srcs = answer_question(q)
        print(f"\nQ: {q}\n{ans}\nSources: {len(srcs)}\n{'-'*80}")
