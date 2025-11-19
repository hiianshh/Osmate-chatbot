# osmate_app.py
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import textwrap

# Load .env from the same folder as this file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=str(env_path))

import streamlit as st

# LLM and helpers (these must exist as in your project)
from osmate_chat import generate_text
from osmate_runner import run_command_safe
from utils import sanitize_text

# Page config
st.set_page_config(
    page_title="OSMate — Operating System Chat",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Refreshed CSS (teal/purple accents, bolder title, no large blank panel) ----------
st.markdown(
    """
    <style>
    :root{
      --bg: #0b1220;
      --panel: #0f1724;
      --muted: #94a3b8;
      --accent: #06b6d4; /* teal */
      --accent2: #7c3aed; /* purple */
      --bubble-text: #f8fafc;
    }
    body { background-color: var(--bg); color: #e6eef8; }

    /* Header styling */
    .osmate-title {
        font-size: 28px !important;
        font-weight: 900 !important;    /* much bolder */
        color: #e6eef8 !important;
        letter-spacing: 0.6px;
    }
    .osmate-sub {
        color: var(--muted);
        font-size: 13px;
    }

    /* Chat area (no large blank box) */
    .chat-wrap {
        border-radius: 10px;
        padding: 6px 6px 12px 6px;
    }

    /* Message bubbles */
    .bubble {
        padding: 12px 14px;
        border-radius: 12px;
        font-size:14px;
        line-height:1.45;
        max-width:78%;
        box-shadow: 0 6px 18px rgba(2,6,23,0.6);
    }
    .bubble.user {
        background: linear-gradient(90deg,#065f46,#0891b2);
        color: #fff;
        margin-left:auto;
    }
    .bubble.assistant {
        background: linear-gradient(90deg,#2b075b,#7c3aed);
        color: #fff;
        margin-right:auto;
    }
    .ts { font-size:11px; color: var(--muted); margin-top:6px; }

    /* Sidebar and quick actions styling */
    .small-muted { color: var(--muted); font-size:12px; }

    /* Input spacing */
    .input-wrap { margin-top:12px; }

    /* responsive tweaks */
    @media (max-width:900px) {
      .bubble { max-width: 72%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Session defaults ----------
if "history" not in st.session_state:
    st.session_state.history = []  # {role, text, ts}
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "processing" not in st.session_state:
    st.session_state.processing = False
if "_system_prompt" not in st.session_state:
    st.session_state["_system_prompt"] = textwrap.dedent(
        """You are OSMate — an expert Operating-System instructor and exam assistant.
Output must be structured and labeled. Use headings: CONTEXT, ANSWER, EXAMPLE_COMMANDS (optional), EXAM_QUESTION (optional), MODEL_ANSWER (optional), MARKING_SCHEME (optional).
When asked for commands, include safe examples in ```bash``` blocks and short risk notes.
When asked for exam questions, include difficulty, expected length, model answer and marking scheme (points total: 10).
Keep tone precise and exam-focused."""
    )

# ---------- helpers ----------
def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def add_message(role: str, text: str):
    st.session_state.history.append({"role": role, "text": text, "ts": now_ts()})

# ---------- main processing callback ----------
def process_input():
    if st.session_state.processing:
        return
    st.session_state.processing = True
    try:
        user_query = st.session_state.input_text.strip()
        if not user_query:
            return

        add_message("user", user_query)

        # Detect safe command
        command_to_run = None
        if st.session_state.get("_run_cmd_checkbox", False):
            if "run:" in user_query:
                command_to_run = user_query.split("run:", 1)[1].strip()
            else:
                first = user_query.split()[0] if user_query.split() else ""
                if first in ["uname","df","ls","whoami","uptime","sw_vers","diskutil","top","ps"]:
                    command_to_run = user_query

        # Build prompt from system_prompt and last history
        system_prompt = st.session_state.get("_system_prompt")
        model = st.session_state.get("_model", "gemini-2.5-flash")
        max_tokens = st.session_state.get("_max_tokens", 512)

        prompt = system_prompt + "\n\n"
        for item in st.session_state.history[-8:]:
            prompt += f"{item['role']}: {item['text']}\n"
        prompt += "assistant:"

        # Call LLM
        assistant_reply = generate_text(prompt, model=model, max_output_tokens=max_tokens)

        add_message("assistant", assistant_reply)

        # If safe command requested, run and append output
        if command_to_run:
            add_message("assistant", f"I detected a command to run: `{command_to_run}`. Attempting safe execution...")
            ok, out = run_command_safe(command_to_run)
            if ok:
                add_message("assistant", f"```\n{out}\n```")
            else:
                add_message("assistant", f"Command blocked/failure:\n```\n{out}\n```")

        # Clear input
        st.session_state.input_text = ""
    finally:
        st.session_state.processing = False

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div style="display:flex;gap:8px;align-items:center;"><div style="font-weight:800;font-size:16px;color:#e6eef8">🛠️ OSMate</div><div class="small-muted">OS tutor & exam assistant</div></div>', unsafe_allow_html=True)
    st.write("---")
    st.session_state["_model"] = st.selectbox("LLM model", ["gemini-2.5-flash","gemini-1.5","gemini-3-pro"], index=0)
    st.session_state["_system_prompt"] = st.text_area("System prompt (editable)", value=st.session_state["_system_prompt"], height=200)
    st.session_state["_max_tokens"] = st.slider("Max tokens", 64, 2048, st.session_state.get("_max_tokens",512))
    st.write("---")
    st.checkbox("Compact input (press Enter to send)", key="_compact_input")
    st.checkbox("Request to run a safe OS command", value=False, key="_run_cmd_checkbox")
    st.write("---")
    st.write("Gemini key loaded:", bool(os.getenv("GEMINI_API_KEY")))
    # screenshot preview using your uploaded file path
    screenshot_path = "/mnt/data/Screenshot 2025-11-20 at 12.50.46 AM.png"
    if Path(screenshot_path).exists():
        st.markdown("**Preview screenshot**")
        st.image(screenshot_path, use_column_width=True, caption="Uploaded screenshot")
    st.write("---")
    if st.button("Clear conversation"):
        st.session_state.history = []

# ---------- Header (bolder title) ----------
st.markdown(f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;"><div><div class="osmate-title">🛠️ OSMate</div><div class="osmate-sub">Interactive OS tutor & safe shell helper</div></div><div class="small-muted">Tip: toggle "Compact input" in the sidebar for Enter-to-send</div></div>', unsafe_allow_html=True)

# ---------- Layout ----------
col_main, col_right = st.columns([3,1])

with col_main:
    # Chat container (no large blank box — only messages)
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

    # Render messages as chat_message components to keep markdown/code rendering intact
    for item in st.session_state.history:
        role = item["role"]
        text = item["text"]
        ts = item.get("ts", "")
        if role == "user":
            st.chat_message("user").write(sanitize_text(text))
            st.markdown(f'<div class="ts" style="text-align:right">{ts}</div>', unsafe_allow_html=True)
        else:
            st.chat_message("assistant").markdown(text)
            st.markdown(f'<div class="ts">{ts}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Input area
    compact = st.session_state.get("_compact_input", False)
    if compact:
        st.text_input("Type and press Enter to send", key="input_text", on_change=process_input)
        st.button("Send", on_click=process_input)
    else:
        st.text_area("Ask OSMate (multi-line)", key="input_text", height=120, placeholder="Explain deadlock; or run: uname -a")
        st.button("Send", on_click=process_input)

with col_right:
    st.markdown("### Quick actions")
    st.markdown("- Ask for **exam questions**: `give me 5 medium exam questions on scheduling`")
    st.markdown("- Ask for **safe commands**: `show me a safe command to list processes`")
    st.markdown("- To run a safe command, check the sidebar checkbox and write `run: uname -a`")
    st.markdown("---")
    st.markdown("### Allowed safe commands")
    st.markdown("`uname`, `df -h`, `whoami`, `uptime`, `ls -la`, `sw_vers`, `diskutil list`, `top -l 1`, `ps aux`")

# ---------- End ----------
