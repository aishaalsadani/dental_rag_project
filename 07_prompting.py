مفيش مشكلة! هعمللك تعديل بسيط في الـ `_clean_answer` عشان **تشيل أي سطر "SOURCES USED" أو "المصادر..."** سواء كان فيه أرقام أو "general knowledge" أو أي حاجه تانيه.

**استبدلي الفايل كامل بده:**

```python
"""
07_prompting.py
Three prompt styles + grounded LLM generation via OpenRouter.

FINAL FIX:
  - Removes the ENTIRE "SOURCES USED" line (or Arabic equivalents)
    from every answer, regardless of content.
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
# Prompts (unchanged from previous version)
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

Task: Answer the patient's question using ONLY the evidence in the context package below.

Rules:
- If the answer is not fully supported by the context, say you don't have enough information and recommend they call the clinic.
- Every source in the context package is already labeled CURRENT or OUTDATED. Never base your answer on an OUTDATED source; if only an OUTDATED source is present, say so explicitly.
- If two CURRENT sources conflict, prefer the most recently updated one and note the conflict.
- Do not give medical advice beyond what is written in the sources.
- Keep the answer under 150 words, in plain, patient-friendly language.

Language rule:
- Detect the language AND dialect of the patient's question, and reply in that same language/dialect.
- If the question is written in Arabic using Egyptian colloquial expressions/spelling (Egyptian Arabic, "Masri" — e.g. "ازاي", "عايز", "بتاع", "مش", "ايه"), reply entirely in natural Egyptian colloquial Arabic (العامية المصرية), the way a friendly Egyptian dental assistant would talk to a patient. Do not switch to Modern Standard Arabic (فصحى) in that case.
- If the question is in Modern Standard Arabic, reply in Modern Standard Arabic.
- If the question is in English, reply in English.
- Keep the two-part output format below in every language, but translate the labels "ANSWER" and "SOURCES USED" naturally into the reply language (e.g. Egyptian Arabic: "الإجابة" and "المصادر اللي اتستخدمت").
- Citations like [1], [2] stay in the same numeric format regardless of language.

Context package:
{context}

Patient question: {question}

Respond in exactly this two-part format (translate the labels into the reply language as instructed above):
ANSWER: <your grounded answer, with inline citations like [1]>
SOURCES USED: <comma-separated list of the source numbers you actually relied on>"""

NO_CONTEXT_PROMPT = """You are DentAI, a friendly dental patient-education assistant.

The internal knowledge base did NOT return any relevant sources for this question,
but you should still help the patient with a clear answer based on well-established
general dental knowledge.

Rules:
- Give a helpful, practical answer (under 180 words).
- Add a brief note that this is general guidance and for their specific case they
  should contact the clinic.
- Do not prescribe medication doses or diagnose specific conditions.
- For emergencies (severe swelling, trauma, uncontrolled bleeding), tell the patient to seek urgent care.

Language rule:
- Detect the language AND dialect of the patient's question, and reply in that same language/dialect.
- If the question is written in Arabic using Egyptian colloquial expressions/spelling (Egyptian Arabic, "Masri" — e.g. "ازاي", "عايز", "بتاع", "مش", "ايه"), reply entirely in natural Egyptian colloquial Arabic (العامية المصرية).
- If the question is in Modern Standard Arabic, reply in Modern Standard Arabic.
- If the question is in English, reply in English.

Patient question: {question}

Respond in this format:
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

# This regex will remove ANY line containing SOURCES USED or مصادر
_SOURCES_LINE_RE = re.compile(
    r"^[\s\*\-\>]*"
    r"(?:SOURCES\s*USED|المصادر\s*(?:المستخدمة|اللي\s*اتستخدمت|))"
    r"\s*[:\-–]\s*.*$",
    re.IGNORECASE | re.MULTILINE
)

def _clean_answer(text):
    """Remove ANY 'SOURCES USED' line (or Arabic equivalents) from the answer."""
    if not text:
        return text
    # Remove all SOURCES lines
    cleaned = _SOURCES_LINE_RE.sub("", text)
    # Clean up extra blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()

def _egyptian_no_context_fallback(question):
    if is_arabic(question):
        return "الإجابة: للأسف مفيش مفتاح API متظبط، فمقدرش أجاوبك دلوقتي. من فضلك ظبطي OPENROUTER_API_KEY في ملف .env أو في Streamlit Secrets."
    return "ANSWER: I can't answer right now because no OPENROUTER_API_KEY is configured. Please set it in your .env file or Streamlit Secrets."

def _extractive_fallback(evidence, question=""):
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

    if not OPENROUTER_API_KEY:
        ans = _extractive_fallback(evidence, question)
        return _clean_answer(ans), evidence

    if not evidence:
        prompt = NO_CONTEXT_PROMPT.format(question=question)
        try:
            ans = ask_openrouter(prompt)
            return _clean_answer(ans), []
        except Exception as exc:
            return f"[LLM call failed: {exc}]", []

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
        "Is teeth whitening safe?",
    ]
    for q in test_qs:
        ans, srcs = answer_question(q)
        print(f"Q: {q}\n{ans}\n{'-'*80}")
```

---

### **اللي اتغير بالظبط:**
1. **`_SOURCES_LINE_RE`** - regex جديدة **بتشيل أي سطر** فيه:
   - `SOURCES USED: ...`
   - `المصادر المستخدمة: ...`
   - `المصادر اللي اتستخدمت: ...`
   **بغض النظر عن المحتوى اللي بعد الكولون** (سواء أرقام أو "general knowledge" أو أي حاجه)

2. **`_clean_answer()`** - دلوقتي بتطبّق على **كل رد** قبل ما يترجّع للمستخدم

3. **الـ prompts** - مفيش تغيير فيها، بس الـ `_clean_answer` هتشيل السطر بعدين

---

### **نتيجة متوقعة دلوقتي:**
```
ANSWER: Teeth whitening is generally safe when done correctly, especially with professional products like take-home trays. It's important to follow the instructions carefully...
```
**مفيش** `SOURCES USED: [1], [2], [3]` خالص 🎯

جربي الكود الجديد وقلّي لو لسه في مشكلة 🚀
