"""
streamlit_app.py

DentAI - AI Dental Assistant (premium SaaS-style UI).
"""

import os
import importlib.util
from pathlib import Path
import streamlit as st

# ---------------------------------------------------------------------------
# Secrets -> env
# ---------------------------------------------------------------------------
try:
    if "OPENROUTER_API_KEY" in st.secrets:
        os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]
    if "OPENROUTER_MODEL" in st.secrets:
        os.environ["OPENROUTER_MODEL"] = st.secrets["OPENROUTER_MODEL"]
except Exception:
    pass

# ---------------------------------------------------------------------------
# Load 07_prompting.py (cached so heavy imports/models load once per process,
# not on every st.rerun() triggered by buttons, chat input, mode switches, etc.)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading models...")
def load_prompting_module():
    here = Path(__file__).parent
    spec = importlib.util.spec_from_file_location("prompting", here / "07_prompting.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

prompting = load_prompting_module()
answer_question = prompting.answer_question
is_arabic = prompting.is_arabic

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DentAI - AI Dental Assistant",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ---- HIDE STREAMLIT HEADER & MENU COMPLETELY ---- */
header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
    visibility: hidden !important;
}
[data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
}
#MainMenu, footer, [data-testid="stStatusWidget"],
[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
}

/* ---- BASE THEME ---- */
html, body, [data-testid="stAppViewContainer"], .stApp,
[data-testid="stBottomBlockContainer"], [data-testid="stBottom"],
[data-testid="stChatInputContainer"], .main, section.main {
    background: #F7F9FC !important;
    background-color: #F7F9FC !important;
    color: #111827 !important;
    font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
}
.stApp { margin-top: 0 !important; }
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 9rem !important;
    max-width: 900px !important;
}

/* ---- BRAND ---- */
.brand { display: flex; align-items: center; gap: 14px; padding: 6px 4px 8px 4px; }
.brand-logo {
    width: 46px; height: 46px; border-radius: 12px;
    background: linear-gradient(135deg, #2563EB, #60A5FA);
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 22px;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.22);
}
.brand-title { font-size: 21px; font-weight: 700; color:#111827; line-height:1.15; letter-spacing: -0.01em; }
.brand-sub   { font-size: 13px; color:#6B7280; font-weight: 500; }

/* ---- HERO ---- */
.hero { text-align:center; margin: 48px 0 8px 0; }
.hero h1 {
    font-size: 34px; font-weight: 800; color:#111827;
    margin-bottom: 14px; letter-spacing: -0.02em;
}
.hero p  { font-size: 16px; color:#6B7280; margin: 4px auto; line-height: 1.7; max-width: 480px; }

.verified-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #EFF6FF; color: #2563EB; border: 1px solid #DBEAFE;
    border-radius: 999px; padding: 7px 16px; font-size: 13px; font-weight: 600;
    margin-top: 20px;
}

.lang-badge {
    text-align:center; color:#9CA3AF; font-size: 13px; margin-top: 14px; font-weight: 500;
}

/* ---- SUGGESTIONS SECTION LABEL ---- */
.section-label {
    text-align:center; font-size:12px; font-weight:700; letter-spacing:1.8px;
    color:#9CA3AF; margin: 44px 0 20px 0; text-transform: uppercase;
}

/* ---- SUGGESTION CARDS ---- */
/* Streamlit buttons are restyled to read as premium feature cards, not
   buttons. The label is authored as three markdown paragraphs
   (icon+title / question / arrow), which Streamlit renders as three
   sibling <p> tags inside the button — each tier gets its own styling
   so the card has real typographic hierarchy instead of one text block. */
.suggest-row { margin-bottom: 8px; }
.suggest-row div[data-testid="column"] { display: flex; }
.suggest-row div.stButton { width: 100%; }
.suggest-row div.stButton > button {
    width: 100% !important;
    height: 172px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    justify-content: flex-start !important;
    gap: 10px !important;
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 16px !important;
    padding: 22px 22px 18px 22px !important;
    text-align: left !important;
    white-space: normal !important;
    box-shadow: 0 1px 2px rgba(17,24,39,.04) !important;
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
}
.suggest-row div.stButton > button p {
    margin: 0 !important;
    text-align: left !important;
    white-space: normal !important;
}
/* tier 1: icon + title */
.suggest-row div.stButton > button p:nth-of-type(1) {
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #111827 !important;
    line-height: 1.4 !important;
}
/* tier 2: the question itself */
.suggest-row div.stButton > button p:nth-of-type(2) {
    font-size: 13.5px !important;
    font-weight: 400 !important;
    color: #6B7280 !important;
    line-height: 1.6 !important;
    flex: 1 1 auto;
}
/* tier 3: arrow, pinned to bottom-right */
.suggest-row div.stButton > button p:nth-of-type(3) {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #2563EB !important;
    align-self: flex-end !important;
    margin-top: auto !important;
}
.suggest-row div.stButton > button:hover {
    border-color: #2563EB !important;
    box-shadow: 0 12px 28px rgba(37,99,235,.14) !important;
    transform: translateY(-3px);
}
.suggest-row div.stButton > button:active {
    transform: translateY(-1px);
}
.suggest-row div.stButton > button:focus-visible {
    outline: 2px solid #2563EB !important;
    outline-offset: 2px !important;
}
@media (prefers-reduced-motion: reduce) {
    .suggest-row div.stButton > button { transition: none !important; }
    .suggest-row div.stButton > button:hover { transform: none !important; }
}

/* ---- CHAT BUBBLES ---- */
.msg-user, .msg-bot {
    padding: 15px 19px; border-radius: 16px; margin: 10px 0;
    max-width: 75%; line-height: 1.7; font-size: 15px;
    box-shadow: 0 1px 3px rgba(17,24,39,.05);
    word-wrap: break-word;
}
.msg-user {
    background:#2563EB; color:#fff !important; margin-left:auto;
    border-bottom-right-radius: 4px;
}
.msg-user * { color: #fff !important; }
.msg-bot {
    background:#FFFFFF; color:#111827 !important;
    border:1px solid #E5E7EB; margin-right:auto;
    border-bottom-left-radius: 4px;
}
.msg-bot * { color:#111827 !important; }
.rtl { direction: rtl; text-align: right;
       font-family: "Segoe UI", "Cairo", Tahoma, sans-serif; }

/* ---- NEW CHAT small button ---- */
.newchat-wrap { margin: 4px 0 18px 0; }
.newchat-wrap div.stButton > button {
    width: auto !important;
    height: auto !important;
    background: #FFFFFF !important;
    color: #6B7280 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 7px 16px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(17,24,39,.03) !important;
}
.newchat-wrap div.stButton > button:hover {
    background: #F9FAFB !important;
    color: #2563EB !important;
    border-color: #2563EB !important;
    transform: none !important;
}

/* ---- FOOTER ---- */
.footer-note {
    text-align:center; color:#9CA3AF; font-size:12.5px;
    margin-top: 36px; letter-spacing: 0.01em;
}

/* ---- CHAT INPUT BAR ---- */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] > div,
div[class*="stBottom"],
section[data-testid="stBottom"],
.stChatFloatingInputContainer,
[data-testid="stChatInputContainer"],
[data-testid="stChatInput"] > div,
div[data-baseweb="base-input"] {
    background: #F7F9FC !important;
    background-color: #F7F9FC !important;
}
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {
    border-top: 1px solid #E5E7EB !important;
}
[data-testid="stChatInput"] {
    background: #FFFFFF !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 16px rgba(17,24,39,.06) !important;
    max-width: 900px !important;
    margin: 0 auto !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.12) !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    background: #FFFFFF !important;
    color: #111827 !important;
    border: none !important;
    caret-color: #2563EB !important;
    font-size: 15px !important;
}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder {
    color: #9CA3AF !important;
}
[data-testid="stChatInput"] button {
    background: #2563EB !important;
    color: #fff !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] button:hover {
    background: #1D4ED8 !important;
}
[data-testid="stChatInput"] button svg {
    fill: #fff !important;
    color: #fff !important;
}

/* Kill any dark/black leftovers */
div[style*="background-color: rgb(14, 17, 23)"],
div[style*="background: rgb(14, 17, 23)"],
div[style*="background-color: rgb(38, 39, 48)"],
div[style*="background: rgb(38, 39, 48)"],
div[style*="background-color: black"] {
    background: #F7F9FC !important;
    background-color: #F7F9FC !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "mode" not in st.session_state:
    # Mode selection is no longer exposed in the UI (patients found it
    # confusing). We keep a single fixed internal quality tier — "strict" —
    # which maps to the most carefully-checked answers. answer_question()
    # still receives style=... exactly as before, so backend behavior for
    # this tier is unchanged.
    st.session_state.mode = "strict"
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Helper: render a single chat message
# ---------------------------------------------------------------------------
def render_message(msg):
    role = msg["role"]
    content = msg["content"]
    rtl = " rtl" if is_arabic(content) else ""
    bubble = "msg-user" if role == "user" else "msg-bot"
    # content is plain text; preserve line breaks for display.
    # Sources are intentionally never rendered in the UI (kept internally
    # on the message dict only, in case they're needed programmatically).
    safe = content.replace("\n", "<br>")
    st.markdown(
        f'<div class="{bubble}{rtl}">{safe}</div>',
        unsafe_allow_html=True
    )


# ---------------------------------------------------------------------------
# Handle a new question (from chat input or a suggestion click)
# ---------------------------------------------------------------------------
def handle_question(question):
    question = (question or "").strip()
    if not question:
        return
    st.session_state.messages.append({"role": "user", "content": question})
    try:
        answer, sources = answer_question(question, style=st.session_state.mode)
    except Exception as exc:  # never let a runtime error blank the whole app
        answer, sources = f"⚠️ Something went wrong while answering: {exc}", []
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )


# A suggestion/chat submission stores its text here; we process it on rerun.
if st.session_state.get("pending_question"):
    handle_question(st.session_state.pop("pending_question"))

# ---------------------------------------------------------------------------
# Top bar (brand only — mode switcher removed)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="brand">
        <div class="brand-logo">🦷</div>
        <div>
            <div class="brand-title">DentAI</div>
            <div class="brand-sub">AI Dental Assistant</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Body: hero + suggestions (empty state)  OR  conversation
# ---------------------------------------------------------------------------
# A tight, mirrored set of six topics (three in English, the same three in
# Arabic) so the grid is always a perfect 3x2 — no half-empty last row, no
# language mixed mid-row. Fewer, symmetric cards read as more premium than
# a full but uneven set.
SUGGESTIONS = [
    ("🦷", "Tooth Extraction", "What should I do after a tooth extraction?"),
    ("👑", "Crowns & Bridges", "How should I care for my new dental crown?"),
    ("😁", "Teeth Whitening", "Is professional teeth whitening safe?"),
    ("🦷", "خلع الأسنان", "ما التعليمات بعد خلع الضرس؟"),
    ("👑", "التركيبات", "كيف أعتني بالتركيبة الجديدة؟"),
    ("😁", "تبييض الأسنان", "هل تبييض الأسنان آمن؟"),
]

if not st.session_state.messages:
    st.markdown(
        """
        <div class="hero">
            <h1>AI Assistant for Dental Patients</h1>
            <p>Ask questions about your treatment, aftercare, oral health,
            medications, and appointments.</p>
            <div class="verified-badge">🛡 Verified Clinical Knowledge</div>
        </div>
        <div class="lang-badge">🌐 English | العربية</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-label">Try asking</div>', unsafe_allow_html=True)

    st.markdown('<div class="suggest-row">', unsafe_allow_html=True)
    s_cols = st.columns(3)
    for idx, (icon, title, question) in enumerate(SUGGESTIONS):
        with s_cols[idx % 3]:
            label = f"{icon}  {title}\n\n{question}\n\n→"
            if st.button(label, key=f"sugg_{idx}"):
                st.session_state.pending_question = question
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # New-chat button
    st.markdown('<div class="newchat-wrap">', unsafe_allow_html=True)
    if st.button("＋ New chat", key="new_chat"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    for msg in st.session_state.messages:
        render_message(msg)

st.markdown(
    '<div class="footer-note">Powered by DentAI • AI for Smarter Dental Care</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Chat input (always pinned at the bottom)
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask DentAI anything...")
if user_input:
    st.session_state.pending_question = user_input
    st.rerun()
