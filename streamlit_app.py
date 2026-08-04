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
#
# NOTE: this loader and everything it calls (answer_question, is_arabic) is
# backend logic and is intentionally left untouched by this fix — only the
# UI/CSS below was modified.
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

/* ---- SUGGESTION CARDS ----
   IMPORTANT: these selectors are scoped to a real Streamlit container
   created with st.container(key="suggest_row"), which renders as an
   actual wrapping <div class="st-key-suggest_row"> around its children
   (columns + buttons). A plain st.markdown('<div>...</div>') does NOT
   nest later st.columns()/st.button() calls inside it -- Streamlit
   renders each element call into its own isolated DOM node, so those
   end up as *siblings*, not children, and any CSS scoped to that div
   silently matches nothing. That mismatch was the root cause of the
   cards showing default (theme-dependent/dark) button styling with
   clipped text. st.container(key=...) avoids that by producing a real
   parent element. */
.st-key-suggest_row div[data-testid="column"] {
    display: flex !important;
}
.st-key-suggest_row div.stButton {
    width: 100% !important;
}
.st-key-suggest_row div.stButton > button {
    all: unset !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
    width: 100% !important;
    height: 172px !important;
    min-height: 172px !important;
    max-height: 172px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    justify-content: flex-start !important;
    gap: 10px !important;
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 16px !important;
    padding: 22px 22px 18px 22px !important;
    text-align: left !important;
    white-space: normal !important;
    overflow: hidden !important;
    box-shadow: 0 1px 2px rgba(17,24,39,.04) !important;
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
}
.st-key-suggest_row div.stButton > button * {
    box-sizing: border-box !important;
}
.st-key-suggest_row div.stButton > button p {
    display: block !important;
    margin: 0 !important;
    text-align: left !important;
    white-space: normal !important;
    overflow-wrap: break-word !important;
}
/* tier 1: icon + title */
.st-key-suggest_row div.stButton > button p:nth-of-type(1) {
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #111827 !important;
    line-height: 1.4 !important;
}
/* tier 2: the question itself */
.st-key-suggest_row div.stButton > button p:nth-of-type(2) {
    font-size: 13.5px !important;
    font-weight: 400 !important;
    color: #6B7280 !important;
    line-height: 1.6 !important;
    flex: 1 1 auto;
}
/* tier 3: arrow, pinned to bottom-right */
.st-key-suggest_row div.stButton > button p:nth-of-type(3) {
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #2563EB !important;
    align-self: flex-end !important;
    margin-top: auto !important;
}
.st-key-suggest_row div.stButton > button:hover {
    border-color: #2563EB !important;
    box-shadow: 0 12px 28px rgba(37,99,235,.14) !important;
    transform: translateY(-3px);
}
.st-key-suggest_row div.stButton > button:active {
    transform: translateY(-1px);
}
.st-key-suggest_row div.stButton > button:focus-visible {
    outline: 2px solid #2563EB !important;
    outline-offset: 2px !important;
}
@media (prefers-reduced-motion: reduce) {
    .st-key-suggest_row div.stButton > button { transition: none !important; }
    .st-key-suggest_row div.stButton > button:hover { transform: none !important; }
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
/* Same st.container(key=...) fix applied here as for the suggestion cards. */
.st-key-newchat_wrap div.stButton > button {
    all: unset !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
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
.st-key-newchat_wrap div.stButton > button p {
    margin: 0 !important;
    color: inherit !important;
}
.st-key-newchat_wrap div.stButton > button:hover {
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

    # st.container(key=...) creates a REAL wrapping DOM element (rendered as
    # <div class="st-key-suggest_row">) that actually contains the columns
    # and buttons created inside it. This is what makes the CSS above able
    # to find and style these specific buttons. (A previous version used
    # st.markdown('<div class="suggest-row">...</div>') around this block,
    # which does NOT nest later widgets inside it -- that mismatch is why
    # the cards were unstyled/black with clipped text.)
    with st.container(key="suggest_row"):
        s_cols = st.columns(3)
        for idx, (icon, title, question) in enumerate(SUGGESTIONS):
            with s_cols[idx % 3]:
                label = f"{icon}  {title}\n\n{question}\n\n→"
                if st.button(label, key=f"sugg_{idx}", use_container_width=True):
                    st.session_state.pending_question = question
                    st.rerun()
else:
    # New-chat button
    with st.container(key="newchat_wrap"):
        if st.button("＋ New chat", key="new_chat"):
            st.session_state.messages = []
            st.rerun()

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
