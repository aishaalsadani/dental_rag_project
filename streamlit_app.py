"""
streamlit_app.py
DentAI - Smart Dental Patient Assistant (clean UI matching the mockup).

Run locally:
    streamlit run streamlit_app.py

Secrets (Streamlit Cloud) or .env (local):
    OPENROUTER_API_KEY = "sk-or-..."
    OPENROUTER_MODEL   = "openai/gpt-4o-mini"   # optional
"""

import os
import re
import importlib.util
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Inject secrets into env BEFORE importing the pipeline module
# ---------------------------------------------------------------------------
try:
    if "OPENROUTER_API_KEY" in st.secrets:
        os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]
    if "OPENROUTER_MODEL" in st.secrets:
        os.environ["OPENROUTER_MODEL"] = st.secrets["OPENROUTER_MODEL"]
except Exception:
    pass  # running locally without secrets is fine

# ---------------------------------------------------------------------------
# Load 07_prompting.py (name starts with a digit → import via spec)
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
    page_title="DentAI - Smart Dental Patient Assistant",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Global CSS  (clean, modern, matches the mockup)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ---- base ---- */
.stApp { background: #f5f7fb; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem; padding-bottom: 8rem; max-width: 1100px; }

/* ---- top bar ---- */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: #ffffff; padding: 14px 22px; border-radius: 14px;
    border: 1px solid #e6ebf3; box-shadow: 0 1px 2px rgba(15,23,42,.04);
    margin-bottom: 28px;
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand-logo {
    width: 44px; height: 44px; border-radius: 10px;
    background: linear-gradient(135deg,#3ea6b8,#2b8fa3);
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 22px;
}
.brand-title { font-size: 20px; font-weight: 700; color:#0f172a; line-height:1.1; }
.brand-sub   { font-size: 13px; color:#64748b; }

.mode-pills { display: flex; gap: 8px; }
.pill {
    padding: 8px 14px; border-radius: 10px; font-size: 14px; font-weight: 500;
    border: 1px solid #e6ebf3; background: #fff; color:#334155;
}
.pill.active { background: #eaf4ff; color:#1d4ed8; border-color:#bfdbfe; }

/* ---- hero ---- */
.hero { text-align:center; margin: 10px 0 30px 0; }
.hero h1 { font-size: 30px; font-weight: 800; color:#0f172a; margin-bottom: 10px; }
.hero p  { font-size: 16px; color:#475569; margin: 4px 0; }
.hero .lang { color:#2563eb; font-size: 14px; margin-top: 6px; }

/* ---- mode cards ---- */
.card {
    background:#fff; border:1px solid #e6ebf3; border-radius:14px;
    padding:22px; height:100%; transition:.15s;
    box-shadow: 0 1px 2px rgba(15,23,42,.03);
}
.card:hover { border-color:#cbd5e1; }
.card.active { border:2px solid #3b82f6; background:#eff6ff; }
.card .ico { font-size: 24px; margin-bottom: 10px; }
.card h3 { font-size:17px; font-weight:700; color:#0f172a; margin: 4px 0 8px 0; }
.card.active h3 { color:#1d4ed8; }
.card p  { font-size:13.5px; color:#64748b; line-height:1.5; margin:0; }

/* ---- try asking ---- */
.section-label {
    text-align:center; font-size:12px; font-weight:700; letter-spacing:2px;
    color:#94a3b8; margin: 34px 0 14px 0;
}
div.stButton > button {
    width:100%; background:#fff; color:#334155; border:1px solid #e6ebf3;
    border-radius:12px; padding: 16px 18px; font-size:14.5px; font-weight:500;
    text-align:left; box-shadow: 0 1px 2px rgba(15,23,42,.03); transition:.15s;
}
div.stButton > button:hover { border-color:#93c5fd; color:#1d4ed8; background:#f8fafc; }

/* ---- chat bubbles ---- */
.msg-user, .msg-bot {
    padding: 14px 18px; border-radius: 14px; margin: 8px 0;
    max-width: 85%; line-height: 1.55; font-size: 15px;
}
.msg-user { background:#2563eb; color:#fff; margin-left:auto; }
.msg-bot  { background:#fff; color:#0f172a; border:1px solid #e6ebf3; margin-right:auto; }
.rtl { direction: rtl; text-align: right; font-family: "Segoe UI", Tahoma, sans-serif; }

/* ---- footer note ---- */
.footer-note {
    text-align:center; color:#64748b; font-size:13px; margin-top: 10px;
}

/* ---- input area at bottom ---- */
div[data-testid="stChatInput"] {
    background: #ffffff; border-top: 1px solid #e6ebf3;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "mode" not in st.session_state:
    st.session_state.mode = "strict"
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts: {role, content, sources?}

def set_mode(m): st.session_state.mode = m

MODE_LABELS = {
    "strict": ("🛡️", "Strict"),
    "better": ("📋", "Better"),
    "weak":   ("⚡", "Weak"),
}

# ---------------------------------------------------------------------------
# Top bar (brand + mode pills)
# ---------------------------------------------------------------------------
top_left, top_right = st.columns([2, 3])
with top_left:
    st.markdown("""
    <div class="brand">
        <div class="brand-logo">🦷</div>
        <div>
            <div class="brand-title">DentAI</div>
            <div class="brand-sub">Smart Dental Patient Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_right:
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(f"🛡️ Strict", key="pill_strict",
                     use_container_width=True,
                     type="primary" if st.session_state.mode == "strict" else "secondary"):
            set_mode("strict"); st.rerun()
    with c2:
        if st.button(f"📋 Better", key="pill_better",
                     use_container_width=True,
                     type="primary" if st.session_state.mode == "better" else "secondary"):
            set_mode("better"); st.rerun()
    with c3:
        if st.button(f"⚡ Weak", key="pill_weak",
                     use_container_width=True,
                     type="primary" if st.session_state.mode == "weak" else "secondary"):
            set_mode("weak"); st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Show hero + cards + suggestions ONLY if no conversation started yet
# ---------------------------------------------------------------------------
if not st.session_state.messages:

    # Hero
    st.markdown("""
    <div class="hero">
        <h1>Welcome to DentAI</h1>
        <p>Your AI-powered dental patient education assistant. Ask any dental</p>
        <p>question and get grounded, cited answers.</p>
        <div class="lang">🌍 Supports English & Arabic (including Egyptian dialect)</div>
    </div>
    """, unsafe_allow_html=True)

    # Mode cards
    m = st.session_state.mode
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="card {'active' if m=='strict' else ''}">
            <div class="ico">🛡️</div>
            <h3>Strict Mode</h3>
            <p>Full grounding with role, evidence boundaries, citations,
            conflict resolution, and language detection.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="card {'active' if m=='better' else ''}">
            <div class="ico">📋</div>
            <h3>Better Mode</h3>
            <p>Adds grounding rules and citation requirements with free-form prose output.</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="card {'active' if m=='weak' else ''}">
            <div class="ico">⚡</div>
            <h3>Weak Mode</h3>
            <p>Simple context dump with no rules — the model is free to hallucinate.</p>
        </div>
        """, unsafe_allow_html=True)

    # Suggested questions
    st.markdown('<div class="section-label">TRY ASKING</div>', unsafe_allow_html=True)

    suggestions = [
        "How should I take care of my new crown?",
        "What should I do after a tooth extraction?",
        "Is teeth whitening safe?",
        "When should my child first visit the dentist?",
        "ازاي أعرف ان علاج اللثة بدأ يجيب نتيجة؟",
        "ايه اللي المفروض اعمله بعد خلع السنة؟",
    ]

    picked = None
    for i in range(0, len(suggestions), 2):
        col_a, col_b = st.columns(2)
        with col_a:
            q = suggestions[i]
            cls = "rtl" if is_arabic(q) else ""
            if st.button(q, key=f"sug_{i}", use_container_width=True):
                picked = q
        if i + 1 < len(suggestions):
            with col_b:
                q2 = suggestions[i+1]
                if st.button(q2, key=f"sug_{i+1}", use_container_width=True):
                    picked = q2

    if picked:
        st.session_state.messages.append({"role": "user", "content": picked})
        with st.spinner("Thinking..."):
            ans, sources = answer_question(picked, style=st.session_state.mode)
        st.session_state.messages.append({"role": "assistant", "content": ans, "sources": sources})
        st.rerun()

# ---------------------------------------------------------------------------
# Conversation view
# ---------------------------------------------------------------------------
else:
    for msg in st.session_state.messages:
        rtl = "rtl" if is_arabic(msg["content"]) else ""
        if msg["role"] == "user":
            st.markdown(f'<div class="msg-user {rtl}">{msg["content"]}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="msg-bot {rtl}">{msg["content"]}</div>',
                        unsafe_allow_html=True)
            if msg.get("sources"):
                with st.expander(f"📚 View {len(msg['sources'])} source(s)"):
                    for i, s in enumerate(msg["sources"], 1):
                        title = s.get("title") or s.get("source") or f"Source {i}"
                        status = s.get("status", "")
                        txt = s.get("text", "")
                        st.markdown(f"**[{i}] {title}** · _{status}_")
                        st.write(txt[:400] + ("…" if len(txt) > 400 else ""))
                        st.markdown("---")

    col_clear, _ = st.columns([1, 5])
    with col_clear:
        if st.button("🗑️ New chat"):
            st.session_state.messages = []
            st.rerun()

# ---------------------------------------------------------------------------
# Bottom input bar (always visible)
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask a dental question... (English or Arabic)")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        ans, sources = answer_question(user_input, style=st.session_state.mode)
    st.session_state.messages.append({"role": "assistant", "content": ans, "sources": sources})
    st.rerun()

# ---------------------------------------------------------------------------
# Footer note
# ---------------------------------------------------------------------------
mode_ico, mode_name = MODE_LABELS[st.session_state.mode]
st.markdown(
    f'<div class="footer-note">Answers are grounded in retrieved dental sources. '
    f'Mode: {mode_ico} <b>{mode_name}</b> · Not a substitute for professional dental advice.</div>',
    unsafe_allow_html=True,
)
