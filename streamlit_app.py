"""
streamlit_app.py
DentAI — Smart Dental Patient Assistant.
Professional chat UI (ChatGPT-style) with:
  - Left sidebar: brand + New chat + mode selector + footer info
  - Centered chat column with proper max-width
  - Fixed white chat input
  - Clean, modern light theme
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
# Load 07_prompting.py
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("prompting", HERE / "07_prompting.py")
prompting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompting)

answer_question = prompting.answer_question
is_arabic = prompting.is_arabic

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DentAI — Smart Dental Assistant",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS — professional, ChatGPT-style
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ============ RESET / BASE ============ */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: #ffffff !important;
    color: #0f172a !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Cairo",
                 Roboto, "Helvetica Neue", sans-serif;
}
header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
#MainMenu, footer, [data-testid="stStatusWidget"], [data-testid="stToolbar"] {
    visibility: hidden !important;
}

/* ============ SIDEBAR ============ */
[data-testid="stSidebar"] {
    background: #f7f8fa !important;
    border-right: 1px solid #e6ebf3 !important;
    width: 280px !important;
    min-width: 280px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 20px;
}
[data-testid="stSidebar"] * { color: #0f172a !important; }

.sb-brand {
    display: flex; align-items: center; gap: 12px;
    padding: 4px 8px 20px 8px;
    border-bottom: 1px solid #e6ebf3;
    margin-bottom: 18px;
}
.sb-logo {
    width: 40px; height: 40px; border-radius: 10px;
    background: linear-gradient(135deg,#3ea6b8,#2b8fa3);
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 20px;
}
.sb-title { font-size: 17px; font-weight: 700; line-height: 1.1; }
.sb-sub   { font-size: 12px; color:#64748b !important; margin-top: 2px; }

.sb-section-label {
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    color: #94a3b8 !important; margin: 18px 8px 8px 8px;
    text-transform: uppercase;
}

/* Sidebar buttons (New chat + mode selectors) */
[data-testid="stSidebar"] div.stButton > button {
    width: 100% !important;
    background: #ffffff !important;
    color: #334155 !important;
    border: 1px solid #e6ebf3 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    text-align: left !important;
    box-shadow: none !important;
    transition: all .15s;
    margin-bottom: 6px !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: #eff6ff !important;
    border-color: #bfdbfe !important;
    color: #1d4ed8 !important;
}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
    background: #eff6ff !important;
    border-color: #3b82f6 !important;
    color: #1d4ed8 !important;
    font-weight: 600 !important;
}

/* ============ MAIN CENTERED COLUMN ============ */
.main .block-container {
    max-width: 820px !important;
    margin: 0 auto !important;
    padding: 32px 24px 140px 24px !important;
}

/* ============ HERO (welcome screen) ============ */
.hero {
    text-align: center;
    padding: 40px 20px 30px 20px;
}
.hero-icon {
    font-size: 48px;
    margin-bottom: 14px;
}
.hero h1 {
    font-size: 32px; font-weight: 700; color:#0f172a;
    margin: 0 0 12px 0;
}
.hero p {
    font-size: 15px; color:#64748b; margin: 0 auto;
    max-width: 520px; line-height: 1.6;
}
.hero .lang-badge {
    display: inline-block;
    margin-top: 16px;
    background: #eff6ff;
    color: #2563eb;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
}

/* ============ SUGGESTION CARDS ============ */
.suggestion-title {
    text-align: center;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #94a3b8;
    margin: 40px 0 16px 0;
    text-transform: uppercase;
}
.main .block-container div.stButton > button {
    width: 100% !important;
    background: #ffffff !important;
    color: #334155 !important;
    border: 1px solid #e6ebf3 !important;
    border-radius: 12px !important;
    padding: 16px 18px !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    text-align: left !important;
    line-height: 1.5 !important;
    transition: all .15s;
    box-shadow: 0 1px 2px rgba(15,23,42,.02) !important;
}
.main .block-container div.stButton > button:hover {
    border-color: #93c5fd !important;
    color: #1d4ed8 !important;
    background: #f8fafc !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59,130,246,.08) !important;
}

/* ============ CHAT BUBBLES ============ */
.msg-row {
    display: flex;
    margin: 16px 0;
    animation: fadeIn .3s ease;
}
.msg-row.user { justify-content: flex-end; }
.msg-row.bot  { justify-content: flex-start; }

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
}

.msg-user, .msg-bot {
    padding: 14px 18px;
    border-radius: 16px;
    max-width: 85%;
    line-height: 1.65;
    font-size: 15px;
    word-wrap: break-word;
}
.msg-user {
    background: #2563eb;
    color: #ffffff !important;
    border-bottom-right-radius: 4px;
}
.msg-user * { color: #ffffff !important; }
.msg-bot {
    background: #f7f8fa;
    color: #0f172a !important;
    border: 1px solid #e6ebf3;
    border-bottom-left-radius: 4px;
}
.msg-bot * { color: #0f172a !important; }
.msg-bot strong { font-weight: 600 !important; }
.rtl { direction: rtl; text-align: right; font-family: "Cairo","Segoe UI",sans-serif; }

/* ============ SOURCES EXPANDER ============ */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e6ebf3 !important;
    border-radius: 10px !important;
    margin: 4px 0 14px 0 !important;
    max-width: 85%;
    box-shadow: none !important;
}
[data-testid="stExpander"] summary {
    padding: 8px 14px !important;
    font-size: 13px !important;
    color: #64748b !important;
    font-weight: 500 !important;
}
[data-testid="stExpander"] summary:hover { color: #1d4ed8 !important; }
[data-testid="stExpander"] summary * { color: inherit !important; background: transparent !important; }
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: #fafbfc !important;
    padding: 14px 18px !important;
    border-top: 1px solid #e6ebf3 !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] * {
    color: #334155 !important;
    background: transparent !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] strong {
    color: #1d4ed8 !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] hr {
    border: none !important;
    border-top: 1px solid #e6ebf3 !important;
    margin: 10px 0 !important;
}

/* ============ CHAT INPUT (bottom) — FORCE WHITE ============ */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[data-testid="stChatInputContainer"] {
    background: #ffffff !important;
    border-top: 1px solid #e6ebf3 !important;
}
[data-testid="stBottom"] > div {
    max-width: 820px !important;
    margin: 0 auto !important;
    padding: 16px 24px !important;
}
[data-testid="stChatInput"] {
    background: #ffffff !important;
    border: 1px solid #d1d9e6 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 8px rgba(15,23,42,.04) !important;
    transition: border-color .15s, box-shadow .15s;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.1) !important;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    background: #ffffff !important;
    color: #0f172a !important;
    border: none !important;
    font-size: 15px !important;
    caret-color: #2563eb !important;
}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder {
    color: #94a3b8 !important;
}
[data-testid="stChatInput"] button {
    background: #2563eb !important;
    border-radius: 10px !important;
    border: none !important;
    transition: background .15s;
}
[data-testid="stChatInput"] button:hover { background: #1d4ed8 !important; }
[data-testid="stChatInput"] button svg { fill: #ffffff !important; }

/* ============ FOOTER NOTE ============ */
.footer-note {
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
    margin-top: 20px;
    padding: 8px;
}

/* Hide sidebar collapse button label */
[data-testid="collapsedControl"] { color: #64748b !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "mode" not in st.session_state:
    st.session_state.mode = "strict"
if "messages" not in st.session_state:
    st.session_state.messages = []

MODES = {
    "strict": ("🛡️", "Strict", "Full grounding & citations"),
    "better": ("📋", "Better", "Grounding rules + free prose"),
    "weak":   ("⚡", "Weak",   "Context dump, no rules"),
}

# ---------------------------------------------------------------------------
# SIDEBAR — brand, new chat, mode selector
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-logo">🦷</div>
        <div>
            <div class="sb-title">DentAI</div>
            <div class="sb-sub">Dental Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("＋  New chat", key="new_chat_sb", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown('<div class="sb-section-label">Response Mode</div>', unsafe_allow_html=True)

    for key, (ico, name, desc) in MODES.items():
        is_active = st.session_state.mode == key
        if st.button(
            f"{ico}  {name}",
            key=f"mode_{key}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            help=desc,
        ):
            st.session_state.mode = key
            st.rerun()

    st.markdown('<div class="sb-section-label">About</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:12px; color:#64748b; padding:0 8px; line-height:1.6;">'
        'Grounded dental patient education, powered by retrieval + LLM. '
        'Supports English & Egyptian Arabic 🇪🇬'
        '</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# MAIN — welcome screen OR chat view
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    # ---- Welcome screen ----
    st.markdown("""
    <div class="hero">
        <div class="hero-icon">🦷</div>
        <h1>Welcome to DentAI</h1>
        <p>Your AI-powered dental patient education assistant.
        Ask any dental question and get grounded, cited answers.</p>
        <div class="lang-badge">🌍 English & Arabic (Egyptian dialect)</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="suggestion-title">Try asking</div>', unsafe_allow_html=True)

    suggestions = [
        "How should I take care of my new crown?",
        "What should I do after a tooth extraction?",
        "Is teeth whitening safe?",
        "When should my child first visit the dentist?",
        "ازاي اعرف ان علاج اللثة بتاعي بيشتغل؟",
        "ايه اللي المفروض اعمله بعد خلع السنة؟",
    ]

    picked = None
    for i in range(0, len(suggestions), 2):
        col_a, col_b = st.columns(2, gap="small")
        with col_a:
            if st.button(suggestions[i], key=f"sug_{i}", use_container_width=True):
                picked = suggestions[i]
        if i + 1 < len(suggestions):
            with col_b:
                if st.button(suggestions[i+1], key=f"sug_{i+1}", use_container_width=True):
                    picked = suggestions[i+1]

    if picked:
        st.session_state.messages.append({"role": "user", "content": picked})
        with st.spinner("Thinking..."):
            ans, sources = answer_question(picked, style=st.session_state.mode)
        st.session_state.messages.append({"role": "assistant", "content": ans, "sources": sources})
        st.rerun()

else:
    # ---- Chat view ----
    for msg in st.session_state.messages:
        rtl = "rtl" if is_arabic(msg["content"]) else ""
        if msg["role"] == "user":
            st.markdown(
                f'<div class="msg-row user"><div class="msg-user {rtl}">{msg["content"]}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            html_content = msg["content"].replace("\n", "<br>")
            st.markdown(
                f'<div class="msg-row bot"><div class="msg-bot {rtl}">{html_content}</div></div>',
                unsafe_allow_html=True,
            )
            if msg.get("sources"):
                with st.expander(f"📚 View {len(msg['sources'])} source(s)"):
                    for i, s in enumerate(msg["sources"], 1):
                        title = s.get("title") or s.get("source") or f"Source {i}"
                        status = s.get("status", "")
                        txt = s.get("text", "")
                        st.markdown(f"**[{i}] {title}** · _{status}_")
                        st.write(txt[:400] + ("…" if len(txt) > 400 else ""))
                        if i < len(msg["sources"]):
                            st.markdown("---")

# ---------------------------------------------------------------------------
# CHAT INPUT (bottom)
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask a dental question... (English or Arabic)")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        ans, sources = answer_question(user_input, style=st.session_state.mode)
    st.session_state.messages.append({"role": "assistant", "content": ans, "sources": sources})
    st.rerun()

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
mode_ico, mode_name, _ = MODES[st.session_state.mode]
st.markdown(
    f'<div class="footer-note">Mode: {mode_ico} {mode_name} · '
    f'Grounded in retrieved sources · Not a substitute for professional dental advice.</div>',
    unsafe_allow_html=True,
)
