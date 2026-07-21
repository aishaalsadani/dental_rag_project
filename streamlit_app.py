"""
streamlit_app.py
Chains the full pipeline (documents -> preprocessing -> chunking -> retrieval ->
context building -> prompting) and serves grounded, source-cited answers.

The API key is read from Streamlit secrets when deployed (exact rubric pattern);
it is never stored in code.

Design: a calm, clinical "teal chart" identity (deep teal + warm ivory + mint,
Fraunces/Manrope for Latin text, Cairo for Arabic) instead of default Streamlit
styling. The assistant answers in whatever language/dialect the patient asks in,
including Egyptian colloquial Arabic (العامية المصرية).
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

st.set_page_config(
    page_title="Dental Patient-Education Assistant",
    page_icon="🦷",
    layout="centered",
)

# ----------------------------------------------------------------------------
# Design tokens + global styling
# ----------------------------------------------------------------------------
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&family=Cairo:wght@500;600;700;800&display=swap" rel="stylesheet">

    <style>
    :root {
        --bg-deep:     #0A1F1C;
        --bg-panel:    #10302A;
        --bg-card:     #163A34;
        --bg-card-2:   #1B443D;
        --line:        #2B5850;
        --text-hi:     #F3EFE2;
        --text-lo:     #9FC4BA;
        --mint:        #5EEAD4;
        --mint-dim:    #2C7A6C;
        --coral:       #FF7A5C;
        --coral-dim:   #7A3A2E;
    }

    html, body, [class*="css"]  { color: var(--text-hi); }

    .stApp {
        background:
            radial-gradient(1200px 520px at 15% -10%, rgba(94,234,212,0.10), transparent 60%),
            radial-gradient(900px 500px at 100% 0%, rgba(255,122,92,0.06), transparent 55%),
            var(--bg-deep);
    }

    /* Hide default chrome for a cleaner surface */
    #MainMenu, header[data-testid="stHeader"] { background: transparent; }

    section.main > div { padding-top: 1.2rem; }

    /* ---------- Hero ---------- */
    .drx-hero {
        display: flex;
        align-items: center;
        gap: 18px;
        padding: 26px 28px;
        border-radius: 20px;
        background: linear-gradient(135deg, var(--bg-panel), var(--bg-card));
        border: 1px solid var(--line);
        margin-bottom: 22px;
        position: relative;
        overflow: hidden;
    }
    .drx-hero::after {
        content: "";
        position: absolute;
        right: -40px; top: -40px;
        width: 160px; height: 160px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(94,234,212,0.18), transparent 70%);
    }
    .drx-tooth {
        font-size: 40px;
        line-height: 1;
        filter: drop-shadow(0 0 14px rgba(94,234,212,0.45));
    }
    .drx-title {
        font-family: 'Fraunces', serif;
        font-weight: 600;
        font-size: 30px;
        letter-spacing: -0.01em;
        color: var(--text-hi);
        margin: 0;
    }
    .drx-title .accent { color: var(--mint); }
    .drx-sub {
        font-family: 'Manrope', sans-serif;
        color: var(--text-lo);
        font-size: 14.5px;
        margin-top: 6px;
        line-height: 1.5;
    }
    .drx-badgebar {
        display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap;
    }
    .drx-pill {
        font-family: 'Manrope', sans-serif;
        font-size: 11.5px;
        font-weight: 700;
        letter-spacing: 0.03em;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid var(--mint-dim);
        color: var(--mint);
        background: rgba(94,234,212,0.07);
    }
    .drx-pill.coral { border-color: var(--coral-dim); color: var(--coral); background: rgba(255,122,92,0.08); }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: var(--bg-panel);
        border-right: 1px solid var(--line);
    }
    section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }
    .drx-side-title {
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        font-size: 13px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mint);
        margin-bottom: 2px;
    }
    .drx-side-sub {
        font-family: 'Manrope', sans-serif;
        font-size: 12.5px;
        color: var(--text-lo);
        margin-bottom: 14px;
    }
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%;
        text-align: left;
        background: var(--bg-card);
        border: 1px solid var(--line);
        color: var(--text-hi);
        border-radius: 12px;
        padding: 10px 12px;
        font-family: 'Manrope', sans-serif;
        font-size: 13px;
        margin-bottom: 8px;
        transition: all 0.15s ease;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        border-color: var(--mint);
        background: var(--bg-card-2);
        color: var(--mint);
    }

    /* ---------- Question card ---------- */
    .drx-card {
        background: var(--bg-panel);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 20px 22px;
        margin-bottom: 18px;
    }
    .drx-label {
        font-family: 'Manrope', sans-serif;
        font-weight: 700;
        font-size: 12.5px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-lo);
        margin-bottom: 8px;
    }
    textarea, .stTextArea textarea {
        background: var(--bg-card) !important;
        color: var(--text-hi) !important;
        border: 1px solid var(--line) !important;
        border-radius: 12px !important;
        font-family: 'Manrope', sans-serif !important;
        font-size: 15px !important;
    }
    textarea:focus { border-color: var(--mint) !important; box-shadow: 0 0 0 1px var(--mint) !important; }

    div.stButton > button[kind="primary"], .drx-card + div div.stButton > button {
        background: linear-gradient(135deg, var(--mint), #37B8A3) !important;
        color: #08201C !important;
        font-family: 'Manrope', sans-serif !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.55rem 1.4rem !important;
        letter-spacing: 0.01em;
    }
    div.stButton > button[kind="primary"]:hover { filter: brightness(1.08); }

    /* ---------- Answer ---------- */
    .drx-answer-card {
        background: linear-gradient(180deg, var(--bg-card), var(--bg-panel));
        border: 1px solid var(--mint-dim);
        border-radius: 18px;
        padding: 22px 24px;
        font-family: 'Manrope', sans-serif;
        font-size: 15.5px;
        line-height: 1.75;
        color: var(--text-hi);
        white-space: pre-wrap;
    }
    .drx-answer-card.rtl {
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
        font-size: 16.5px;
    }
    .drx-answer-head {
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        font-size: 12.5px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mint);
        margin-bottom: 10px;
    }

    /* ---------- Sources ---------- */
    .drx-src {
        display: flex;
        gap: 12px;
        padding: 12px 4px;
        border-bottom: 1px dashed var(--line);
    }
    .drx-src:last-child { border-bottom: none; }
    .drx-src-num {
        min-width: 28px; height: 28px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        font-size: 12.5px;
        border: 2px solid var(--mint);
        color: var(--mint);
        flex-shrink: 0;
    }
    .drx-src-num.outdated { border-color: var(--coral); color: var(--coral); }
    .drx-src-title { font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 14px; color: var(--text-hi); }
    .drx-src-meta { font-family: 'Manrope', sans-serif; font-size: 11.5px; color: var(--text-lo); margin: 2px 0 6px 0; }
    .drx-src-text { font-family: 'Manrope', sans-serif; font-size: 13.5px; color: var(--text-lo); line-height: 1.55; }

    .drx-footer {
        text-align: center;
        color: var(--text-lo);
        font-family: 'Manrope', sans-serif;
        font-size: 11.5px;
        margin-top: 30px;
        opacity: 0.7;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Hero header
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="drx-hero">
        <div class="drx-tooth">🦷</div>
        <div>
            <div class="drx-title">Dental Patient-Education <span class="accent">Assistant</span></div>
            <div class="drx-sub">
                Answers are grounded ONLY in retrieved patient-education handouts,
                prefer CURRENT sources over OUTDATED ones, and always cite where they come from.
            </div>
            <div class="drx-badgebar">
                <span class="drx-pill">🇬🇧 English</span>
                <span class="drx-pill">🇪🇬 العامية المصرية</span>
                <span class="drx-pill coral">Grounded &amp; Cited</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Session state + example questions (bilingual quick-fill chips)
# ----------------------------------------------------------------------------
if "question" not in st.session_state:
    st.session_state.question = ""

EXAMPLES = [
    "How should I take care of my new crown or bridge?",
    "How do I know if my gum disease treatment is actually working?",
    "Can I drink coffee while my aligner trays are in?",
    "Is it okay to sleep with my new dentures in?",
    "لبسي الجديد بيوجعني، ده طبيعي ولا لأ؟",
    "امتى المفروض اروح تاني بعد خلع الضرس؟",
]

with st.sidebar:
    st.markdown('<div class="drx-side-title">Example questions</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="drx-side-sub">Tap a question to try it — in English or Egyptian Arabic.</div>',
        unsafe_allow_html=True,
    )
    for i, ex in enumerate(EXAMPLES):
        if st.button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.question = ex
            st.rerun()

# ----------------------------------------------------------------------------
# Question input
# ----------------------------------------------------------------------------
st.markdown('<div class="drx-card">', unsafe_allow_html=True)
st.markdown('<div class="drx-label">Your question · سؤالك</div>', unsafe_allow_html=True)
question = st.text_area(
    "Your question",
    key="question",
    height=100,
    label_visibility="collapsed",
    placeholder="Ask in English, or اسأل بالعامية المصرية...",
)
if rag.is_arabic(question):
    st.caption("🇪🇬 هيتم الرد بالعامية المصرية بناءً على المصادر المتاحة.")
ask = st.button("Answer · جاوبني", type="primary")
st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Answer + sources
# ----------------------------------------------------------------------------
if ask and question.strip():
    if not rag.OPENROUTER_API_KEY:
        st.warning(
            "OPENROUTER_API_KEY is not configured — showing a grounded extractive fallback. "
            "Add your key in Streamlit → Manage app → Secrets for full LLM answers."
        )
    with st.spinner("Retrieving context and generating a grounded answer..."):
        answer, sources = rag.answer_question(question)

    rtl_class = " rtl" if rag.is_arabic(answer) else ""
    head_label = "الإجابة" if rag.is_arabic(answer) else "Answer"
    st.markdown(
        f"""
        <div class="drx-answer-card{rtl_class}">
            <div class="drx-answer-head">{head_label}</div>
            {answer}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    sources_label = f"المصادر المستخدمة ({len(sources)})" if rag.is_arabic(answer) else f"Sources used ({len(sources)})"
    with st.expander(sources_label, expanded=True):
        if not sources:
            st.write(
                "مفيش مصدر حالي كفاية يجاوب على السؤال ده."
                if rag.is_arabic(answer)
                else "No sufficiently relevant CURRENT source was found."
            )
        for number, e in enumerate(sources, start=1):
            outdated = not e["is_current"]
            status = "OUTDATED" if outdated else "CURRENT"
            num_class = "outdated" if outdated else ""
            st.markdown(
                f"""
                <div class="drx-src">
                    <div class="drx-src-num {num_class}">{number}</div>
                    <div>
                        <div class="drx-src-title">{e['title']}</div>
                        <div class="drx-src-meta">{status} · updated {e['effective_date']}</div>
                        <div class="drx-src-text">{e['text']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown(
    '<div class="drx-footer">For education only — not a substitute for professional dental advice. '
    "Call your clinic for anything urgent.</div>",
    unsafe_allow_html=True,
)
