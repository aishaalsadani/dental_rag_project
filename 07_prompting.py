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

{language_directive}

Context: {context}
Question: {question}"""

BETTER_PROMPT = """You are a dental patient-education assistant. Answer the patient's question using
ONLY information that is explicitly stated in the context below. Cite the source number(s) for each
claim, like [1]. If the context does not contain the answer, reply exactly: "NOT_IN_CONTEXT".

{language_directive}

Context:
{context}

Question: {question}

Answer:"""

STRICT_PROMPT = """You are DentAI, a dental patient-education assistant.

CORE RULE — RESPONSE LANGUAGE (most important, applies before anything else):
- Your reply language is determined ONLY by the language the PATIENT QUESTION is written in below.
- The CONTEXT PACKAGE may be written in a completely different language than the question. That is
  expected and IRRELEVANT to your reply language — never let the context's language leak into your
  reply, and never switch languages partway through.
- Never translate the question or the topic into another language unless the patient explicitly asks
  you to translate something.
- The exact rule (English question -> English reply, Arabic question -> Arabic reply, Egyptian
  colloquial question -> Egyptian colloquial reply, mixed-language question -> reply in whichever
  language is dominant in the question) is restated precisely, in code, in the LANGUAGE INSTRUCTION
  near the end of this prompt. Treat that instruction as binding.

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

Output format:
ANSWER: <your answer, grounded ONLY in the context, with inline citations like [1], [2]>
(do NOT add a separate "SOURCES USED" line at the end; the inline citations are enough.)

Context package (the sources below may be written in a different language than the patient's
question — that is normal and does NOT change what language you reply in):
{context}

Patient question: {question}

{language_directive}

Reply now:"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_ARABIC_RE = re.compile(r"[؀-ۿ]")
_LATIN_RE = re.compile(r"[A-Za-z]")

# A handful of high-signal Egyptian colloquial markers. Not exhaustive by
# design — this only needs to catch the common case so we can pick the right
# opening label / register; the model still writes the actual reply.
_EGYPTIAN_MARKERS = (
    "ازاي", "عايز", "عاوز", "بتاع", "بتاعت", "مش", "ايه", "إيه", "ليه",
    "فين", "كده", "كدا", "دلوقتي", "خالص", "علشان", "عشان", "هو ده",
    "مفيش", "حاجة", "اهو", "يلا", "بقى",
)


def is_arabic(text):
    """True if the text contains any Arabic-script characters at all.
    Used for lightweight UI decisions (e.g. RTL bubble alignment)."""
    return bool(_ARABIC_RE.search(text or ""))


def _dominant_script(text):
    """Decide which script dominates a piece of text, for mixed-language
    input. Returns 'ar' or 'en'. Arabic wins ties (e.g. a mostly-Arabic
    sentence with one English brand name should still get an Arabic reply)."""
    text = text or ""
    arabic_count = len(_ARABIC_RE.findall(text))
    latin_count = len(_LATIN_RE.findall(text))
    if arabic_count == 0:
        return "en"
    if latin_count == 0:
        return "ar"
    return "ar" if arabic_count >= latin_count else "en"


def _is_egyptian_colloquial(text):
    text = text or ""
    return any(marker in text for marker in _EGYPTIAN_MARKERS)


def _language_directive(question):
    """Build an explicit, non-negotiable instruction that pins the reply
    language in code (based on the actual question), instead of leaving
    language detection up to the model. This is deliberately placed right
    before "Reply now:" in the prompt template — the position closest to
    generation, which models weight most heavily — so it isn't overridden
    by the language of the (often Arabic) retrieved context sitting just
    above it.
    """
    script = _dominant_script(question)
    if script == "ar":
        if _is_egyptian_colloquial(question):
            return (
                "LANGUAGE INSTRUCTION (must follow exactly, overrides every other signal "
                "including the context's language): The patient wrote in Egyptian colloquial "
                "Arabic. Reply ENTIRELY in Egyptian colloquial Arabic (العامية المصرية) — warm "
                "and natural, not فصحى. Do NOT reply in English, even if the context above is "
                "in English, even if it would be easier to answer in English. Do not mix "
                "languages. Begin your reply with \"الإجابة:\"."
            )
        return (
            "LANGUAGE INSTRUCTION (must follow exactly, overrides every other signal including "
            "the context's language): The patient wrote in Modern Standard Arabic. Reply "
            "ENTIRELY in Modern Standard Arabic (الفصحى). Do NOT reply in English, even if the "
            "context above is in English, even if it would be easier to answer in English. Do "
            "not mix languages. Begin your reply with \"الإجابة:\"."
        )
    return (
        "LANGUAGE INSTRUCTION (must follow exactly, overrides every other signal including the "
        "context's language): The patient wrote in English. Reply ENTIRELY in English. Do NOT "
        "reply in Arabic, even if the context above is in Arabic, even if it would be easier to "
        "answer in Arabic. Do not mix languages. Begin your reply with \"ANSWER:\"."
    )


def build_prompt(question, context_text, style="strict"):
    template = {"weak": WEAK_PROMPT, "better": BETTER_PROMPT, "strict": STRICT_PROMPT}[style]
    return template.format(
        context=context_text,
        question=question,
        language_directive=_language_directive(question),
    )


def _not_found_message(question):
    return NOT_FOUND_AR if _dominant_script(question) == "ar" else NOT_FOUND_EN


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
    if _dominant_script(question) == "ar":
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
# Cross-language retrieval support
# ---------------------------------------------------------------------------
def _translate_query_to_english(text):
    """Best-effort INTERNAL translation of a query into English, used only to
    improve retrieval matching against an English-heavy knowledge base.

    This translation is never shown to the user, never stored in chat
    history, and never used for grounding or for the final answer text —
    it exists purely as a lookup key for build_context(). The original
    question (in its original language) is what gets answered.
    """
    if not OPENROUTER_API_KEY or not text:
        return text
    try:
        client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{
                "role": "user",
                "content": (
                    "Translate the following dental patient question into English. "
                    "Reply with ONLY the translated question and nothing else — no "
                    "quotes, no explanation, no preamble.\n\n"
                    f"Question: {text}"
                ),
            }],
            temperature=0.0,
            max_tokens=100,
        )
        translated = (resp.choices[0].message.content or "").strip()
        return translated or text
    except Exception:
        return text


def _retrieve_evidence(question):
    """Retrieve context, with a cross-language strategy for Arabic queries.

    The knowledge base is indexed primarily in English. A literal Arabic query
    can either match nothing OR — worse — match a few irrelevant chunks, which
    then makes the LLM answer NOT_IN_CONTEXT even though the answer is present
    in an English document. English questions already retrieve correctly.

    Strategy:
      - English question -> retrieve with the question exactly as written
        (unchanged behaviour, so nothing English can regress).
      - Arabic question  -> translate to English FIRST and use that as the
        PRIMARY retrieval key (this is what actually matches the English KB).
        Only if the translated retrieval finds nothing do we fall back to the
        raw Arabic query, so any natively-indexed Arabic content still works.

    The translation is used for RETRIEVAL ONLY. Grounding and the final answer
    still use the original question and the retrieved source text, and the
    reply language is pinned to the original question's language elsewhere.
    """
    # Non-Arabic: keep the exact original behaviour.
    if _dominant_script(question) != "ar":
        return build_context(question)

    # Arabic: translate first, retrieve with English as the primary key.
    translated_query = _translate_query_to_english(question)
    if DEBUG:
        print(f"[DEBUG] Arabic query translated for retrieval: {translated_query!r}")
    if translated_query and translated_query.strip().lower() != question.strip().lower():
        evidence = build_context(translated_query)
        if evidence:
            return evidence

    # Fallback: try the original Arabic query directly.
    return build_context(question)


# ---------------------------------------------------------------------------
# Post-generation language enforcement (safety net)
# ---------------------------------------------------------------------------
def _rewrite_in_language(answer_text, question):
    """If the model didn't obey the LANGUAGE INSTRUCTION, rewrite the
    already-generated, already-grounded answer into the correct language.

    This does not re-derive the answer from the context and cannot change
    facts or citations — it only fixes surface language, as a safety net
    on top of the prompt-level language instruction.
    """
    if not OPENROUTER_API_KEY or not answer_text:
        return answer_text

    target_script = _dominant_script(question)
    if _dominant_script(answer_text) == target_script:
        return answer_text  # already correct, nothing to do

    if target_script == "ar":
        lang_name = (
            "Egyptian colloquial Arabic (العامية المصرية)"
            if _is_egyptian_colloquial(question)
            else "Modern Standard Arabic (الفصحى)"
        )
    else:
        lang_name = "English"

    try:
        client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{
                "role": "user",
                "content": (
                    f"Rewrite the following text ENTIRELY in {lang_name}. Preserve every fact "
                    "and every citation marker like [1] or [2] exactly as they are. Do not add, "
                    "remove, or change any information. Reply with ONLY the rewritten text.\n\n"
                    f"Text:\n{answer_text}"
                ),
            }],
            temperature=0.0,
            max_tokens=500,
        )
        rewritten = (resp.choices[0].message.content or "").strip()
        return rewritten or answer_text
    except Exception:
        return answer_text


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def answer_question(question, style="strict"):
    evidence = _retrieve_evidence(question)

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

    # Safety net: if the model still answered in the wrong language despite
    # the LANGUAGE INSTRUCTION (e.g. it drifted toward the context's
    # language), fix the surface language without touching the grounded
    # content or citations.
    ans = _rewrite_in_language(ans, question)

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
