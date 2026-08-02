"""
streamlit_app.py

DentAI - Smart Dental Patient Assistant (patient-friendly UI).
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
    page_title="DentAI - Smart Dental Patient Assistant",
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

/* ---- FORCE LIGHT THEME EVERYWHERE ---- */
html, body, [data-testid="stAppViewContainer"], .stApp,
[data-testid="stBottomBlockContainer"], [data-testid="stBottom"],
[data-testid="stChatInputContainer"], .main, section.main {
    background: #f5f7fb !important;
    background-color: #f5f7fb !important;
    color: #0f172a !important;
}
.stApp {
    margin-top: 0 !important;
}
.block-container { 
    padding-top: 1.5rem !important; 
    padding-bottom: 8rem !important; 
    max-width: 1100px !important; 
}

/* ---- TOP BAR (brand + pills) ---- */
.brand { display: flex; align-items: center; gap: 12px; padding: 6px 4px; }
.brand-logo {
    width: 44px; height: 44px; border-radius: 10px;
    background: linear-gradient(135deg,#3ea6b8,#2b8fa3);
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 22px;
}
.brand-title { font-size: 20px; font-weight: 700; color:#0f172a; line-height:1.1; }
.brand-sub   { font-size: 13px; color:#64748b; }

/* ---- HERO ---- */
.hero { text-align:center; margin: 30px 0 20px 0; }
.hero h1 { font-size: 32px; font-weight: 800; color:#0f172a; margin-bottom: 12px; }
.hero p  { font-size: 16px; color:#475569; margin: 4px 0; line-height: 1.6; }
.hero .lang { color:#2563eb; font-size: 14px; margin-top: 10px; font-weight: 500; }

/* ---- MODE DESCRIPTION (single line, dynamic) ---- */
.mode-desc {
    text-align: center;
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-radius: 10px;
    padding: 12px 18px;
    margin: 16px auto;
    max-width: 620px;
    color: #075985;
    font-size: 13.5px;
    line-height: 1.55;
}
.mode-desc b { color: #0369a1; font-weight: 600; }

/* ---- SUGGESTIONS ---- */
.section-label {
    text-align:center; font-size:12px; font-weight:700; letter-spacing:2px;
    color:#94a3b8; margin: 30px 0 14px 0;
}
div.stButton > button {
    width:100%; background:#fff !important; color:#334155 !important;
    border:1px solid #e6ebf3 !important; border-radius:12px !important;
    padding: 14px 18px !important; font-size:14.5px !important; font-weight:500 !important;
    text-align:left !important; box-shadow: 0 1px 2px rgba(15,23,42,.03) !important;
    transition:.15s;
}
div.stButton > button:hover {
    border-color:#93c5fd !important; color:#1d4ed8 !important;
    background:#f8fafc !important;
}
div.stButton > button[kind="primary"] {
    background:#eff6ff !important; color:#1d4ed8 !important;
    border:1px solid #bfdbfe !important; font-weight:600 !important;
}

/* ---- CHAT BUBBLES ---- */
.msg-user, .msg-bot {
    padding: 14px 18px; border-radius: 14px; margin: 10px 0;
    max-width: 78%; line-height: 1.65; font-size: 15px;
    box-shadow: 0 1px 3px rgba(15,23,42,.06);
    word-wrap: break-word;
}
.msg-user {
    background:#2563eb; color:#fff !important; margin-left:auto;
    border-bottom-right-radius: 4px;
}
.msg-user * { color: #fff !important; }
.msg-bot {
    background:#ffffff; color:#0f172a !important;
    border:1px solid #e6ebf3; margin-right:auto;
    border-bottom-left-radius: 4px;
}
.msg-bot * { color:#0f172a !important; }
.rtl { direction: rtl; text-align: right;
       font-family: "Segoe UI", "Cairo", Tahoma, sans-serif; }

/* ---- SOURCES EXPANDER ---- */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e6ebf3 !important;
    border-radius: 12px !important;
    margin: 6px 0 12px 0 !important;
    max-width: 78%;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * {
    color: #334155 !important;
    font-weight: 500 !important;
    background: transparent !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: #f8fafc !important;
    color: #0f172a !important;
    padding: 12px 16px !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] * {
    color: #0f172a !important;
    background: transparent !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] strong {
    color: #1d4ed8 !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] hr {
    border-color: #e6ebf3 !important;
}

/* ---- NEW CHAT small button ---- */
.newchat-wrap { margin: 8px 0 4px 0; }
.newchat-wrap div.stButton > button {
    width: auto !important;
    background: transparent !important;
    color: #64748b !important;
    border: 1px solid #e6ebf3 !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
}
.newchat-wrap div.stButton > button:hover {
    background: #f1f5f9 !important;
    color: #1d4ed8 !important;
    border-color: #cbd5e1 !important;
}

/* ---- FOOTER NOTE ---- */
.footer-note {
    text-align:center; color:#64748b; font-size:13px; margin-top: 14px;
}

/* ---- CHAT INPUT BAR - LIGHT ---- */
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
    background: #f5f7fb !important;
    background-color: #f5f7fb !important;
}
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {
    border-top: 1px solid #e6ebf3 !important;
}
[data-testid="stChatInput"] {
    background: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 8px rgba(15,23,42,.06) !important;
    max-width: 1100px !important;
    margin: 0 auto !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.15) !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    background: #ffffff !important;
    color: #0f172a !important;
    border: none !important;
    caret-color: #2563eb !important;
    font-size: 15px !important;
}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder {
    color: #94a3b8 !important;
}
[data-testid="stChatInput"] button {
    background: #2563eb !important;
    color: #fff !important;
    border-radius: 10px !important;
}
[data-testid="stChatInput"] button:hover {
    background: #1d4ed8 !important;
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
    background: #f5f7fb !important;
    background-color: #f5f7fb !important;
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

MODE_LABELS = {
    "strict": ("🛡️", "Safe"),
    "better": ("📋", "Balanced"),
    "weak":   ("⚡", "Quick"),
}

MODE_DESCRIPTIONS = {
    "strict": "🛡️ <b>Safe Mode:</b> Answers are carefully checked and based only on trusted dental sources. Best for accurate, reliable information.",
    "better": "📋 <b>Balanced Mode:</b> Clear answers backed by dental sources, written in an easy-to-read style.",
    "weak":   "⚡ <b>Quick Mode:</b> Faster answers with less checking. Use only for general curiosity, not medical decisions.",
}

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
