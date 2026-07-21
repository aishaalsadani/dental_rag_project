"""
streamlit_app.py
DentAI - Smart Dental Patient Assistant (professional modern UI - v3).
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
    page_title="DentAI",
    page_icon="🦷",
    layout="centered",  # <-- changed to centered for better spacing
    initial_sidebar_state="collapsed",
    menu_items={}
)

# ---------------------------------------------------------------------------
# GLOBAL CSS — very aggressive to override Streamlit defaults
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ================================================================
   RESET + BASE
   ================================================================ */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="stMainBlockContainer"] {
    background: #f7f9fc !important;
    color: #0f172a !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Cairo",
                 Tahoma, sans-serif !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header[data-testid="stHeader"],
[data-testid="stToolbar"], [data-testid="stStatusWidget"],
[data-testid="stDecoration"], [data-testid="stActionButton"],
.stDeployButton, [data-testid="stAppDeployButton"] {
    display: none !important;
    visibility: hidden !important;
}

/* Container padding */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 7rem !important;
    max-width: 900px !important;
}

/* ================================================================
   TOP BAR — brand
   ================================================================ */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    background: #ffffff;
    border-radius: 14px;
    border: 1px solid #e6ebf3;
    box-shadow: 0 1px 3px rgba(15,23,42,.04);
    margin-bottom: 24px;
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand-logo {
    width: 42px; height: 42px; border-radius: 10px;
    background: linear-gradient(135deg,#3ea6b8,#2b8fa3);
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 20px;
    box-shadow: 0 2px 6px rgba(46,143,163,.3);
}
.brand-title { font-size: 19px; font-weight: 700; color:#0f172a; line-height:1.1; }
.brand-sub   { font-size: 12.5px; color:#64748b; margin-top: 2px; }

.mode-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 12px; border-radius: 8px;
    background: #eff6ff; color: #1d4ed8;
    font-size: 13px; font-weight: 600;
    border: 1px solid #bfdbfe;
}

/* ================================================================
   MODE PILLS ROW
   ================================================================ */
.mode-row { margin-bottom: 20px; }

/* Force all st.button to look clean */
div[data-testid="stButton"] > button,
div.stButton > button {
    background: #ffffff !important;
    color: #475569 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover,
div.stButton > button:hover {
    background: #f8fafc !important;
    border-color: #cbd5e1 !important;
    color: #0f172a !important;
}
div[data-testid="stButton"] > button[kind="primary"],
div.stButton > button[kind="primary"] {
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #2563eb !important;
    font-weight: 600 !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover,
div.stButton > button[kind="primary"]:hover {
    background: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
}

/* ================================================================
   HERO / WELCOME
   ================================================================ */
.hero { text-align:center; margin: 28px 0 32px 0; padding: 0 20px; }
.hero h1 { font-size: 32px; font-weight: 800; color:#0f172a;
           margin: 0 0 14px 0; letter-spacing: -0.5px; }
.hero p  { font-size: 15.5px; color:#64748b; margin: 4px 0; line-height: 1.6; }
.hero .lang { display: inline-flex; align-items: center; gap: 6px;
              color:#2563eb; font-size: 13.5px; margin-top: 10px;
              background: #eff6ff; padding: 6px 14px;
              border-radius: 20px; border: 1px solid #dbeafe; }

/* ================================================================
   MODE CARDS
   ================================================================ */
.card-grid { display: grid; grid-template-columns: 1fr 1fr 1fr;
             gap: 14px; margin: 20px 0 32px 0; }
.card {
    background:#ffffff; border:1px solid #e6ebf3; border-radius:14px;
    padding:20px 18px; transition: all 0.2s ease;
    cursor: default;
}
.card:hover { border-color:#cbd5e1; transform: translateY(-1px);
              box-shadow: 0 4px 12px rgba(15,23,42,.06); }
.card.active { border:2px solid #2563eb; background:#eff6ff;
               box-shadow: 0 4px 12px rgba(37,99,235,.12); }
.card .ico { font-size: 22px; margin-bottom: 10px; }
.card h3 { font-size:15.5px; font-weight:700; color:#0f172a;
           margin: 0 0 6px 0; }
.card.active h3 { color:#1d4ed8; }
.card p  { font-size:12.5px; color:#64748b; line-height:1.55; margin:0; }

/* ================================================================
   SUGGESTIONS
   ================================================================ */
.section-label {
    text-align:center; font-size:11px; font-weight:700;
    letter-spacing:2.5px; color:#94a3b8;
    margin: 28px 0 16px 0;
}

/* Suggestion buttons override */
.suggestions-wrap div[data-testid="stButton"] > button {
    text-align: left !important;
    padding: 14px 18px !important;
    font-size: 14px !important;
    background: #ffffff !important;
    border: 1px solid #e6ebf3 !important;
    color: #334155 !important;
}
.suggestions-wrap div[data-testid="stButton"] > button:hover {
    border-color: #93c5fd !important;
    background: #f0f7ff !important;
    color: #1d4ed8 !important;
}

/* ================================================================
   CHAT BUBBLES
   ================================================================ */
.chat-container { margin: 20px 0; }

.msg-user, .msg-bot {
    padding: 14px 18px; border-radius: 14px; margin: 10px 0;
    max-width: 82%; line-height: 1.7; font-size: 14.5px;
    word-wrap: break-word;
    box-shadow: 0 1px 3px rgba(15,23,42,.04);
}
.msg-user {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color:#ffffff !important; margin-left:auto;
    border-bottom-right-radius: 4px;
}
.msg-user, .msg-user * { color: #ffffff !important; }

.msg-bot {
    background:#ffffff; color:#0f172a !important;
    border:1px solid #e6ebf3; margin-right:auto;
    border-bottom-left-radius: 4px;
}
.msg-bot, .msg-bot * { color:#0f172a !important; }

.rtl { direction: rtl; text-align: right; }

/* ================================================================
   SOURCES EXPANDER
   ================================================================ */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e6ebf3 !important;
    border-radius: 12px !important;
    margin: 4px 0 14px 0 !important;
    max-width: 82%;
    box-shadow: 0 1px 3px rgba(15,23,42,.03);
}
[data-testid="stExpander"] summary {
    padding: 12px 16px !important;
    color: #475569 !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    background: #ffffff !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary:hover {
    background: #f8fafc !important;
}
[data-testid="stExpander"] summary * {
    color: #475569 !important;
    background: transparent !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"],
[data-testid="stExpander"] div[role="region"] {
    background: #f8fafc !important;
    padding: 14px 18px !important;
    border-top: 1px solid #e6ebf3 !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] *,
[data-testid="stExpander"] div[role="region"] * {
    color: #334155 !important;
    background: transparent !important;
    font-size: 13.5px !important;
}
[data-testid="stExpander"] strong { color: #1d4ed8 !important; }

/* ================================================================
   NEW CHAT (small pill button)
   ================================================================ */
.newchat-row {
    display: flex; justify-content: center;
    margin: 18px 0 8px 0;
}
.newchat-row div[data-testid="stButton"] > button {
    width: auto !important;
    background: #ffffff !important;
    color: #64748b !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 20px !important;
    padding: 7px 18px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    box-shadow: 0 1px 2px rgba(15,23,42,.04) !important;
}
.newchat-row div[data-testid="stButton"] > button:hover {
    background: #f1f5f9 !important;
    color: #dc2626 !important;
    border-color: #fecaca !important;
}

/* ================================================================
   FOOTER NOTE
   ================================================================ */
.footer-note {
    text-align:center; color:#94a3b8; font-size:12.5px;
    margin: 18px 0 8px 0; padding: 12px;
    border-top: 1px solid #e6ebf3;
}

/* ================================================================
   BOTTOM CHAT INPUT — force white/clean
   ================================================================ */
/* Container */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
div[data-testid="stBottom"] > div,
section[data-testid="stBottom"],
.stBottom {
    background: #f7f9fc !important;
    border-top: 1px solid #e6ebf3 !important;
    padding: 12px 20px !important;
}

/* The actual input pill */
[data-testid="stChatInput"],
div[data-testid="stChatInput"],
.stChatInput,
[data-baseweb="textarea"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 24px !important;
    box-shadow: 0 2px 8px rgba(15,23,42,.06) !important;
    overflow: hidden !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #93c5fd !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.1) !important;
}

/* Text area inside */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input,
.stChatInput textarea,
.stChatInput input {
    background: #ffffff !important;
    color: #0f172a !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    font-size: 14.5px !important;
    padding: 12px 16px !important;
    caret-color: #2563eb !important;
}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder {
    color: #94a3b8 !important;
    opacity: 1 !important;
}

/* Send button */
[data-testid="stChatInput"] button {
    background: #2563eb !important;
    color: #ffffff !important;
    border-radius: 50% !important;
    border: none !important;
    width: 36px !important; height: 36px !important;
    margin: 6px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="stChatInput"] button:hover {
    background: #1d4ed8 !important;
}
[data-testid="stChatInput"] button svg,
[data-testid="stChatInput"] button svg path {
    fill: #ffffff !important;
    color: #ffffff !important;
}
[data-testid="stChatInput"] button:disabled {
    background: #cbd5e1 !important;
    cursor: not-allowed !important;
}

/* Kill any dark wrappers */
[data-testid="stChatInputContainer"],
[data-testid="stChatFlexContainer"] {
    background: transparent !important;
    border: none !important;
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

MODE_LABELS = {
    "strict": ("🛡️", "Strict"),
    "better": ("📋", "Better"),
    "weak":   ("⚡", "Weak"),
}
mode_ico, mode_name = MODE_LABELS[st.session_state.mode]

# ---------------------------------------------------------------------------
# TOP BAR (brand + current mode badge)
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="topbar">
    <div class="brand">
        <div class="brand-logo">🦷</div>
        <div>
            <div class="brand-title">DentAI</div>
            <div class="brand-sub">Smart Dental Patient Assistant</div>
        </div>
    </div>
    <div class="mode-badge">{mode_ico} {mode_name} Mode</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# MODE SELECTOR (below top bar, always visible)
# ---------------------------------------------------------------------------
st.markdown('<div class="mode-row">', unsafe_allow_html=True)
mc1, mc2, mc3 = st.columns(3)
with mc1:
    if st.button("🛡️  Strict", key="pill_strict",
                 type="primary" if st.session_state.mode == "strict" else "secondary"):
        st.session_state.mode = "strict"; st.rerun()
with mc2:
    if st.button("📋  Better", key="pill_better",
                 type="primary" if st.session_state.mode == "better" else "secondary"):
        st.session_state.mode = "better"; st.rerun()
with mc3:
    if st.button("⚡  Weak", key="pill_weak",
                 type="primary" if st.session_state.mode == "weak" else "secondary"):
        st.session_state.mode = "weak"; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# WELCOME VIEW
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown("""
    <div class="hero">
        <h1>Welcome to DentAI</h1>
        <p>Your AI-powered dental patient education assistant.</p>
        <p>Ask any dental question and get grounded, cited answers.</p>
        <div class="lang">🌍 Supports English &amp; Arabic (including Egyptian dialect)</div>
    </div>
    """, unsafe_allow_html=True)

    # Mode description cards
    m = st.session_state.mode
    st.markdown(f"""
    <div class="card-grid">
        <div class="card {'active' if m=='strict' else ''}">
            <div class="ico">🛡️</div>
            <h3>Strict Mode</h3>
            <p>Full grounding with role, evidence boundaries, citations, and language detection.</p>
        </div>
        <div class="card {'active' if m=='better' else ''}">
            <div class="ico">📋</div>
            <h3>Better Mode</h3>
            <p>Grounding rules and citation requirements with free-form prose output.</p>
        </div>
        <div class="card {'active' if m=='weak' else ''}">
            <div class="ico">⚡</div>
            <h3>Weak Mode</h3>
            <p>Simple context dump with no rules — the model is free to hallucinate.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">TRY ASKING</div>', unsafe_allow_html=True)

    st.markdown('<div class="suggestions-wrap">', unsafe_allow_html=True)
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
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button(suggestions[i], key=f"sug_{i}"):
                picked = suggestions[i]
        if i + 1 < len(suggestions):
            with col_b:
                if st.button(suggestions[i+1], key=f"sug_{i+1}"):
                    picked = suggestions[i+1]
    st.markdown('</div>', unsafe_allow_html=True)

    if picked:
        st.session_state.messages.append({"role": "user", "content": picked})
        with st.spinner("Thinking..."):
            ans, sources = answer_question(picked, style=st.session_state.mode)
        st.session_state.messages.append({"role": "assistant", "content": ans, "sources": sources})
        st.rerun()

# ---------------------------------------------------------------------------
# CHAT VIEW
# ---------------------------------------------------------------------------
else:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        rtl = "rtl" if is_arabic(msg["content"]) else ""
        if msg["role"] == "user":
            st.markdown(
                f'<div class="msg-user {rtl}">{msg["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            html_content = msg["content"].replace("\n", "<br>")
            st.markdown(
                f'<div class="msg-bot {rtl}">{html_content}</div>',
                unsafe_allow_html=True
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
    st.markdown('</div>', unsafe_allow_html=True)

    # New chat button
    st.markdown('<div class="newchat-row">', unsafe_allow_html=True)
    _, cmid, _ = st.columns([3, 2, 3])
    with cmid:
        if st.button("↻  New chat", key="new_chat_btn"):
            st.session_state.messages = []
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="footer-note">Grounded in retrieved dental sources · '
    'Not a substitute for professional dental advice</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask a dental question... (English or Arabic)")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        ans, sources = answer_question(user_input, style=st.session_state.mode)
    st.session_state.messages.append({"role": "assistant", "content": ans, "sources": sources})
    st.rerun()
