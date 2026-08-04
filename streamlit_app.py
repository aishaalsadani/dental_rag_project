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
    color: #1E293B !important;
    font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
}
.stApp { margin-top: 0 !important; }
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 9rem !important;
    max-width: 980px !important;
}

/* ---- TOP BAR (brand + mode pills) ---- */
.brand { display: flex; align-items: center; gap: 14px; padding: 6px 4px 18px 4px; }
.brand-logo {
    width: 46px; height: 46px; border-radius: 12px;
    background: linear-gradient(135deg, #2563EB, #60A5FA);
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 22px;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25);
}
.brand-title { font-size: 21px; font-weight: 700; color:#0F172A; line-height:1.15; letter-spacing: -0.01em; }
.brand-sub   { font-size: 13px; color:#64748B; font-weight: 500; }

/* ---- HERO ---- */
.hero { text-align:center; margin: 36px 0 22px 0; }
.hero h1 {
    font-size: 34px; font-weight: 800; color:#0F172A;
    margin-bottom: 14px; letter-spacing: -0.02em;
}
.hero p  { font-size: 16px; color:#64748B; margin: 4px auto; line-height: 1.7; max-width: 520px; }

.verified-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE;
    border-radius: 999px; padding: 7px 16px; font-size: 13px; font-weight: 600;
    margin-top: 18px;
}

.lang-badge {
    text-align:center; color:#94A3B8; font-size: 13px; margin-top: 12px; font-weight: 500;
}

/* ---- MODE PILLS ---- */
div.stButton > button {
    transition: all .15s ease;
}
.mode-row div.stButton > button {
    width:100%; background:#FFFFFF !important; color:#475569 !important;
    border:1px solid #E6EBF3 !important; border-radius:12px !important;
    padding: 10px 14px !important; font-size:14px !important; font-weight:600 !important;
    box-shadow: 0 1px 2px rgba(15,23,42,.03) !important;
}
.mode-row div.stButton > button:hover {
    border-color:#93C5FD !important; color:#2563EB !important;
    background:#F8FAFC !important;
}
.mode-row div.stButton > button[kind="primary"] {
    background:#2563EB !important; color:#FFFFFF !important;
    border:1px solid #2563EB !important; font-weight:700 !important;
    box-shadow: 0 4px 12px rgba(37,99,235,.25) !important;
}

/* ---- MODE DESCRIPTION CARD ---- */
.mode-desc {
    text-align: center;
    background: #FFFFFF;
    border: 1px solid #E6EBF3;
    border-radius: 14px;
    padding: 16px 22px;
    margin: 18px auto 8px auto;
    max-width: 620px;
    color: #475569;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 2px 10px rgba(15,23,42,.04);
}
.mode-desc b { color: #0F172A; font-weight: 700; }

/* ---- SUGGESTIONS ---- */
.section-label {
    text-align:center; font-size:12px; font-weight:700; letter-spacing:1.8px;
    color:#94A3B8; margin: 34px 0 16px 0; text-transform: uppercase;
}
.suggest-row div.stButton > button {
    width:100%; background:#FFFFFF !important; color:#334155 !important;
    border:1px solid #E6EBF3 !important; border-radius:16px !important;
    padding: 18px 20px !important; font-size:14px !important; font-weight:500 !important;
    text-align:left !important; box-shadow: 0 1px 3px rgba(15,23,42,.04) !important;
    transition: all .15s ease; height: auto !important; min-height: 84px;
    white-space: normal !important; line-height: 1.5 !important;
}
.suggest-row div.stButton > button:hover {
    border-color:#93C5FD !important; box-shadow: 0 6px 18px rgba(37,99,235,.12) !important;
    transform: translateY(-2px);
}

/* ---- CHAT BUBBLES ---- */
.msg-user, .msg-bot {
    padding: 15px 19px; border-radius: 16px; margin: 10px 0;
    max-width: 75%; line-height: 1.7; font-size: 15px;
    box-shadow: 0 1px 3px rgba(15,23,42,.05);
    word-wrap: break-word;
}
.msg-user {
    background:#2563EB; color:#fff !important; margin-left:auto;
    border-bottom-right-radius: 4px;
}
.msg-user * { color: #fff !important; }
.msg-bot {
    background:#FFFFFF; color:#0F172A !important;
    border:1px solid #E6EBF3; margin-right:auto;
    border-bottom-left-radius: 4px;
}
.msg-bot * { color:#0F172A !important; }
.rtl { direction: rtl; text-align: right;
       font-family: "Segoe UI", "Cairo", Tahoma, sans-serif; }

/* ---- NEW CHAT small button ---- */
.newchat-wrap { margin: 4px 0 18px 0; }
.newchat-wrap div.stButton > button {
    width: auto !important;
    background: #FFFFFF !important;
    color: #64748B !important;
    border: 1px solid #E6EBF3 !important;
    border-radius: 10px !important;
    padding: 7px 16px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(15,23,42,.03) !important;
}
.newchat-wrap div.stButton > button:hover {
    background: #F8FAFC !important;
    color: #2563EB !important;
    border-color: #93C5FD !important;
}

/* ---- FOOTER NOTE ---- */
.footer-note {
    text-align:center; color:#94A3B8; font-size:12.5px; margin-top: 30px;
    line-height: 1.6;
}
.footer-note b { color: #64748B; }

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
    border-top: 1px solid #E6EBF3 !important;
}
[data-testid="stChatInput"] {
    background: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 16px rgba(15,23,42,.06) !important;
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
    color: #0F172A !important;
    border: none !important;
    caret-color: #2563EB !important;
    font-size: 15px !important;
}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder {
    color: #94A3B8 !important;
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

/* Kill any dark leftovers */
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
    st.session_state.mode = "strict"
if "messages" not in st.session_state:
    st.session_state.messages = []

def set_mode(m):
    st.session_state.mode = m

# NOTE: internal keys ("strict" / "better" / "weak") are unchanged so backend
# logic (answer_question(style=...)) keeps working exactly as before. Only
# the labels/icons/descriptions shown to the user have been renamed.
MODE_LABELS = {
    "strict": ("🛡", "Verified"),
    "better": ("📋", "Balanced"),
    "weak":   ("⚡", "Fast"),
}

MODE_DESCRIPTIONS = {
    "strict": "🛡 <b>Verified:</b> Responses generated only from your clinic's verified clinical knowledge.",
    "better": "📋 <b>Balanced:</b> Reliable answers with clear patient-friendly explanations.",
    "weak":   "⚡ <b>Fast:</b> Quick responses for common dental questions.",
}

# ---------------------------------------------------------------------------
# Top bar (brand + mode pills)
# ---------------------------------------------------------------------------
col_brand, col_pills = st.columns([1.3, 1], vertical_alignment="center")

with col_brand:
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

with col_pills:
    st.markdown('<div class="mode-row">', unsafe_allow_html=True)
    p_cols = st.columns(len(MODE_LABELS))
    for col, (mode_key, (emoji, label)) in zip(p_cols, MODE_LABELS.items()):
        with col:
            st.button(
                f"{emoji} {label}",
                key=f"pill_{mode_key}",
                type="primary" if st.session_state.mode == mode_key else "secondary",
                on_click=set_mode,
                args=(mode_key,),
                use_container_width=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

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
# Body: hero + suggestions (empty state)  OR  conversation
# ---------------------------------------------------------------------------
SUGGESTIONS = [
    ("🦷", "Tooth Extraction", "What should I do after a tooth extraction?"),
    ("👑", "Crowns", "How should I care for my new dental crown?"),
    ("🪥", "Braces", "How do I clean my teeth with braces?"),
    ("🩺", "Root Canal", "Can I eat normally after a root canal treatment?"),
    ("🦷", "خلع الضرس", "ما التعليمات بعد خلع الضرس؟"),
    ("🪥", "التقويم", "ازاي أنضف أسناني وأنا لابس تقويم؟"),
    ("😁", "تبييض الأسنان", "هل تبييض الأسنان آمن؟"),
    ("🩺", "حشو العصب", "امتى أقدر آكل بعد حشو العصب؟"),
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
    st.markdown(
        f'<div class="mode-desc">{MODE_DESCRIPTIONS[st.session_state.mode]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-label">Try asking</div>', unsafe_allow_html=True)

    st.markdown('<div class="suggest-row">', unsafe_allow_html=True)
    s_cols = st.columns(2)
    for idx, (icon, title, question) in enumerate(SUGGESTIONS):
        with s_cols[idx % 2]:
            if st.button(f"{icon}  **{title}**\n\n{question}", key=f"sugg_{idx}"):
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
    '<div class="footer-note"><b>Powered by DentAI</b><br>AI for Smarter Dental Care</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Chat input (always pinned at the bottom)
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask DentAI anything...")
if user_input:
    st.session_state.pending_question = user_input
    st.rerun()
