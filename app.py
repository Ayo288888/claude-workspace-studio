import os
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv()

from storage import Database
from claude_client import ClaudeEngine, CLAUDE_MODELS, SYSTEM_PRESETS, extract_artifacts
from file_processor import process_raw_file, format_file_for_prompt
from styles import apply_claude_styles

# Page configuration
st.set_page_config(
    page_title="Claude Workspace Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Claude CSS styles
apply_claude_styles()

# Initialize SQLite storage
@st.cache_resource
def get_db():
    return Database("claude_chat.db")

db = get_db()

# Session State Initialization
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "api_key" not in st.session_state:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key and hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
        key = st.secrets["ANTHROPIC_API_KEY"]
    st.session_state.api_key = key
if "uploaded_files_data" not in st.session_state:
    st.session_state.uploaded_files_data = []

# Ensure there is an active session
sessions = db.get_sessions()
if not st.session_state.current_session_id:
    if sessions:
        st.session_state.current_session_id = sessions[0]["id"]
    else:
        new_id = db.create_session(
            title="New Conversation",
            model="claude-3-7-sonnet-20250219",
            system_prompt=SYSTEM_PRESETS["General Assistant"]
        )
        st.session_state.current_session_id = new_id
        sessions = db.get_sessions()

current_session = db.get_session(st.session_state.current_session_id)
if not current_session:
    new_id = db.create_session(
        title="New Conversation",
        model="claude-3-7-sonnet-20250219",
        system_prompt=SYSTEM_PRESETS["General Assistant"]
    )
    st.session_state.current_session_id = new_id
    current_session = db.get_session(new_id)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
        <span style="font-size: 26px;">✨</span>
        <div>
            <div style="font-weight: 700; font-size: 1.1rem; color: #DA7756; line-height: 1.2;">Claude Studio</div>
            <div style="font-size: 0.75rem; color: #888;">Anthropic Console Powered</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # New Chat Button
    if st.button("➕ Start New Chat", use_container_width=True, type="primary"):
        new_id = db.create_session(
            title="New Conversation",
            model="claude-3-7-sonnet-20250219",
            system_prompt=SYSTEM_PRESETS["General Assistant"]
        )
        st.session_state.current_session_id = new_id
        st.session_state.uploaded_files_data = []
        st.rerun()

    st.markdown("<div class='sidebar-header'>Model & Configuration</div>", unsafe_allow_html=True)

    # Model Selector
    model_name = st.selectbox(
        "Select Model",
        options=list(CLAUDE_MODELS.keys()),
        index=0,
        help="Choose the Claude engine model for your conversation."
    )
    selected_model = CLAUDE_MODELS[model_name]

    # Extended Thinking (Claude 3.7)
    thinking_budget = 0
    if "3-7" in selected_model:
        enable_thinking = st.toggle("🧠 Enable Extended Thinking", value=True, help="Enables Claude 3.7's hybrid reasoning engine.")
        if enable_thinking:
            thinking_budget = st.slider(
                "Thinking Budget (tokens)",
                min_value=1024,
                max_value=16384,
                value=2048,
                step=512,
                help="Maximum tokens allocated to Claude's internal reasoning chain before generating the final response."
            )

    # Persona / System Prompt Selector
    preset_choice = st.selectbox(
        "System Persona",
        options=list(SYSTEM_PRESETS.keys()) + ["Custom Persona"],
        index=0
    )
    if preset_choice == "Custom Persona":
        system_prompt = st.text_area(
            "Custom System Prompt",
            value=current_session.get("system_prompt", "") or "You are Claude, a helpful AI assistant.",
            height=100
        )
    else:
        system_prompt = SYSTEM_PRESETS[preset_choice]

    # API Key Management
    st.markdown("<div class='sidebar-header'>API Authentication</div>", unsafe_allow_html=True)
    api_key_input = st.text_input(
        "Anthropic API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="sk-ant-api03-...",
        help="Your key from console.anthropic.com. It is stored in session memory only."
    )
    if api_key_input:
        st.session_state.api_key = api_key_input

    # Session Management / History
    st.markdown("<div class='sidebar-header'>Recent Conversations</div>", unsafe_allow_html=True)
    sessions = db.get_sessions()
    
    for s in sessions[:15]:
        col_btn, col_del = st.columns([5, 1])
        is_active = (s["id"] == st.session_state.current_session_id)
        btn_label = f"💬 {s['title'][:22]}..." if len(s['title']) > 22 else f"💬 {s['title']}"
        
        if col_btn.button(
            btn_label,
            key=f"sess_{s['id']}",
            use_container_width=True,
            type="secondary" if not is_active else "primary"
        ):
            st.session_state.current_session_id = s["id"]
            st.session_state.uploaded_files_data = []
            st.rerun()

        if col_del.button("🗑️", key=f"del_{s['id']}", help="Delete chat"):
            db.delete_session(s["id"])
            if st.session_state.current_session_id == s["id"]:
                st.session_state.current_session_id = None
            st.rerun()

# Check for API Key
if not st.session_state.api_key:
    st.markdown("""
    <div class="claude-hero">
        <div style="font-size: 50px; margin-bottom: 10px;">✨</div>
        <div class="claude-hero-title">Welcome to Claude Workspace</div>
        <div class="claude-hero-sub">
            To get started, please enter your <b>Anthropic API Key</b> in the sidebar on the left.<br>
            <i>Your key is used directly against your $100 Anthropic Console balance.</i>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Initialize Claude Engine
try:
    engine = ClaudeEngine(api_key=st.session_state.api_key)
except Exception as e:
    st.error(f"Error initializing Claude client: {e}")
    st.stop()

# ==========================================
# MAIN INTERFACE
# ==========================================

# Top Header Bar
current_session = db.get_session(st.session_state.current_session_id)
messages = db.get_messages(st.session_state.current_session_id)

st.markdown(f"""
<div class="claude-top-bar">
    <div class="claude-brand-title">
        <span>✨</span> {current_session['title']}
    </div>
    <div style="display: flex; gap: 8px; align-items: center;">
        <span class="claude-badge">{model_name.split(' ')[0]} {model_name.split(' ')[1]}</span>
        {f'<span class="claude-badge" style="background:#FFF0EB; color:#DA7756;">🧠 Thinking: {thinking_budget} tokens</span>' if thinking_budget > 0 else ''}
    </div>
</div>
""", unsafe_allow_html=True)

# Layout Columns: Main Chat + Optional Artifacts Side Panel
chat_col, artifact_col = st.columns([1, 1] if st.session_state.get("show_artifacts", False) else [1, 0.001])

# File Attachment Expander
with st.expander("📎 Attach Documents or Code (PDF, DOCX, Python, Markdown, Images, JSON)", expanded=False):
    uploaded_files = st.file_uploader(
        "Upload files to inspect, review, or summarize",
        type=["py", "js", "ts", "json", "html", "css", "sql", "md", "txt", "pdf", "docx", "png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True
    )
    if uploaded_files:
        st.session_state.uploaded_files_data = []
        for uf in uploaded_files:
            file_bytes = uf.read()
            processed = process_raw_file(uf.name, file_bytes)
            st.session_state.uploaded_files_data.append(processed)
            st.success(f"Attached: `{uf.name}` ({len(file_bytes)} bytes)")

# If conversation is empty, display Claude starter suggestions
if not messages:
    st.markdown("""
    <div class="claude-hero">
        <div style="font-size: 40px; margin-bottom: 8px;">✨</div>
        <div class="claude-hero-title">Good afternoon.</div>
        <div class="claude-hero-sub">How can Claude help you build, design, or review today?</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📐 **Architecture & Implementation Plan**\n\nGenerate an in-depth, step-by-step technical plan for a new feature.", use_container_width=True):
            st.session_state.default_prompt = "Generate a comprehensive, production-ready implementation plan for "
        if st.button("🔍 **Code & Security Review**\n\nAudit a code file or snippet for bugs, race conditions, and vulnerabilities.", use_container_width=True):
            st.session_state.default_prompt = "Review the following code thoroughly for security vulnerabilities, edge cases, and code smells:\n\n"
    with col2:
        if st.button("📄 **Policy & Document Synthesis**\n\nExtract key requirements, risks, and obligations from attached documents.", use_container_width=True):
            st.session_state.default_prompt = "Summarize the attached document, highlighting key requirements, responsibilities, and action items."
        if st.button("💡 **Refactor & Optimize Code**\n\nRefactor code for performance, readability, and testability with diffs.", use_container_width=True):
            st.session_state.default_prompt = "Refactor the following code following DRY and SOLID principles with clean diffs:\n\n"

# Render Conversation Messages
latest_assistant_response = ""

with chat_col:
    for msg in messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "✨"):
            # Display Claude 3.7 Thinking if recorded
            if msg.get("thinking"):
                with st.expander("🧠 **Claude's Reasoning Process**", expanded=False):
                    st.markdown(f"```text\n{msg['thinking']}\n```")
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                latest_assistant_response = msg["content"]

# Chat Input
default_input = st.session_state.pop("default_prompt", "")
prompt = st.chat_input("Message Claude...", key="main_chat_input")
if not prompt and default_input:
    prompt = default_input

if prompt:
    # Build complete user prompt including attached files
    full_prompt_text = prompt
    images_to_send = []

    if st.session_state.uploaded_files_data:
        file_contexts = []
        for file_info in st.session_state.uploaded_files_data:
            if file_info["type"] == "image":
                images_to_send.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": file_info["media_type"],
                        "data": file_info["base64"]
                    }
                })
                file_contexts.append(f"[Attached Image: {file_info['name']}]")
            else:
                file_contexts.append(format_file_for_prompt(file_info))
        
        full_prompt_text = prompt + "\n\n" + "\n".join(file_contexts)

    # Save User message to SQLite
    db.save_message(st.session_state.current_session_id, "user", full_prompt_text)

    # Auto-generate title if first message
    if len(messages) == 0:
        generated_title = engine.generate_title(prompt)
        db.update_session_title(st.session_state.current_session_id, generated_title)

    # Display User message in UI
    with chat_col:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
            if st.session_state.uploaded_files_data:
                for uf in st.session_state.uploaded_files_data:
                    st.caption(f"📎 Attached file: `{uf['name']}`")

    # Clear uploaded files for next message
    st.session_state.uploaded_files_data = []

    # Build messages payload for Anthropic API
    history_messages = db.get_messages(st.session_state.current_session_id)
    api_messages = []
    for m in history_messages:
        api_messages.append({
            "role": m["role"],
            "content": m["content"]
        })

    # Stream Assistant Response
    with chat_col:
        with st.chat_message("assistant", avatar="✨"):
            thinking_placeholder = st.empty()
            response_placeholder = st.empty()
            
            accumulated_thinking = ""
            accumulated_text = ""

            try:
                stream = engine.stream_chat(
                    model=selected_model,
                    messages=api_messages,
                    system=system_prompt,
                    thinking_budget=thinking_budget,
                )

                for chunk in stream:
                    if chunk["type"] == "thinking":
                        accumulated_thinking += chunk["delta"]
                        with thinking_placeholder.container():
                            st.markdown(f"""
                            <div class="thinking-box">
                                <div class="thinking-label">🧠 Thinking...</div>
                                <pre style="white-space: pre-wrap; font-family: monospace; font-size: 0.85rem; max-height: 250px; overflow-y: auto;">{accumulated_thinking}▌</pre>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    elif chunk["type"] == "text":
                        accumulated_text += chunk["delta"]
                        response_placeholder.markdown(accumulated_text + "▌")

                # Final display
                if accumulated_thinking:
                    with thinking_placeholder.container():
                        with st.expander("🧠 **Claude's Reasoning Process**", expanded=False):
                            st.markdown(f"```text\n{accumulated_thinking}\n```")

                response_placeholder.markdown(accumulated_text)

                # Save Assistant message to SQLite
                db.save_message(
                    st.session_state.current_session_id,
                    "assistant",
                    accumulated_text,
                    thinking=accumulated_thinking
                )
                latest_assistant_response = accumulated_text
                st.rerun()

            except Exception as e:
                st.error(f"Anthropic API Error: {e}")

# ==========================================
# ARTIFACTS SIDE PANEL (Claude-Style)
# ==========================================
if latest_assistant_response:
    artifacts = extract_artifacts(latest_assistant_response)
    if artifacts:
        with st.sidebar:
            st.markdown("<div class='sidebar-header'>Generated Artifacts</div>", unsafe_allow_html=True)
            for art in artifacts:
                with st.expander(f"📦 {art['title']}", expanded=False):
                    st.code(art["code"], language=art["language"])
                    st.download_button(
                        f"📥 Download {art['language'].upper()}",
                        data=art["code"],
                        file_name=f"artifact_{art['id']}.{art['language'] if art['language'] != 'markdown' else 'md'}",
                        mime="text/plain",
                        key=f"dl_{art['id']}"
                    )
