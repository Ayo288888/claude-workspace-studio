import datetime
import os
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv()

from storage import Database
from claude_client import ClaudeEngine, ClaudeModelError, CLAUDE_MODELS, MODEL_DETAILS, EFFORT_LEVELS, SYSTEM_PRESETS, extract_artifacts
from file_processor import process_raw_file, format_file_for_prompt
from styles import apply_claude_styles
from security import SessionKeyManager, mask_api_key, validate_anthropic_key

# Page configuration
st.set_page_config(
    page_title="Claude",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Claude CSS styling
apply_claude_styles()

# Initialize In-Memory Session Key Manager & Database
if "key_manager" not in st.session_state:
    st.session_state.key_manager = SessionKeyManager()

if "encrypted_api_key" not in st.session_state:
    st.session_state.encrypted_api_key = ""

# Check environment variable for initial key if provided locally
if not st.session_state.encrypted_api_key:
    init_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if init_key:
        st.session_state.encrypted_api_key = st.session_state.key_manager.encrypt_key(init_key)

if "db" not in st.session_state:
    st.session_state.db = Database("claude_chat.db")

db: Database = st.session_state.db

# State Initialization
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "active_starter_prompt" not in st.session_state:
    st.session_state.active_starter_prompt = ""
if "uploaded_files_data" not in st.session_state:
    st.session_state.uploaded_files_data = []

# Ensure active session exists
sessions = db.get_sessions()
if not st.session_state.current_session_id:
    if sessions:
        st.session_state.current_session_id = sessions[0]["id"]
    else:
        new_id = db.create_session(
            title="New Chat",
            model="Opus 5",
            system_prompt=SYSTEM_PRESETS["General Assistant"]
        )
        st.session_state.current_session_id = new_id
        sessions = db.get_sessions()

current_session = db.get_session(st.session_state.current_session_id)
if not current_session:
    new_id = db.create_session(
        title="New Chat",
        model="Opus 5",
        system_prompt=SYSTEM_PRESETS["General Assistant"]
    )
    st.session_state.current_session_id = new_id
    current_session = db.get_session(new_id)

# Helper to get decrypted API key in memory
def get_current_api_key() -> str:
    if st.session_state.encrypted_api_key:
        return st.session_state.key_manager.decrypt_key(st.session_state.encrypted_api_key)
    return ""

current_key = get_current_api_key()

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    # Claude Header Branding
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px; padding: 4px 0;">
        <span style="font-size: 24px; color: #DA7756;">✨</span>
        <div>
            <div style="font-weight: 700; font-size: 1.15rem; color: #2C2825; line-height: 1.1;">Claude</div>
            <div style="font-size: 0.75rem; color: #736E65;">Workspace Studio</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Start New Chat Button
    if st.button("➕ Start new chat", use_container_width=True, type="primary"):
        new_id = db.create_session(
            title="New Chat",
            model="Opus 5",
            system_prompt=SYSTEM_PRESETS["General Assistant"]
        )
        st.session_state.current_session_id = new_id
        st.session_state.uploaded_files_data = []
        st.session_state.active_starter_prompt = ""
        st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Conversation History List
    st.markdown("<div style='font-size: 0.8rem; font-weight: 600; color: #736E65; text-transform: uppercase; letter-spacing: 0.05em;'>Recent Chats</div>", unsafe_allow_html=True)
    
    for s in sessions[:25]:
        is_active = s["id"] == st.session_state.current_session_id
        col_btn, col_del = st.columns([0.82, 0.18])
        with col_btn:
            btn_label = f"💬 {s['title'][:22]}..." if len(s['title']) > 22 else f"💬 {s['title']}"
            if st.button(
                btn_label,
                key=f"sess_{s['id']}",
                use_container_width=True,
                type="secondary" if not is_active else "primary"
            ):
                st.session_state.current_session_id = s["id"]
                st.session_state.uploaded_files_data = []
                st.session_state.active_starter_prompt = ""
                st.rerun()
        with col_del:
            if st.button("✕", key=f"del_{s['id']}", help="Delete chat"):
                db.delete_session(s["id"])
                remaining = db.get_sessions()
                st.session_state.current_session_id = remaining[0]["id"] if remaining else None
                st.rerun()

    st.divider()

    # System Role Preset Selector
    selected_preset = st.selectbox(
        "System Preset",
        options=list(SYSTEM_PRESETS.keys()),
        index=0,
        help="Select a specialized system persona for Claude."
    )
    system_prompt = SYSTEM_PRESETS[selected_preset]

    st.divider()

    # Encrypted BYOK Authentication Drawer
    st.markdown("<div style='font-size: 0.8rem; font-weight: 600; color: #736E65; text-transform: uppercase; letter-spacing: 0.05em;'>Authentication & Security</div>", unsafe_allow_html=True)
    
    if current_key:
        st.success(f"🔒 Authenticated: `{mask_api_key(current_key)}`")
    else:
        st.warning("⚠️ API Key required to send messages.")

    with st.expander("🔑 Manage API Key", expanded=not bool(current_key)):
        new_key_input = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-api03-...",
            help="Your API key is encrypted in memory during your active browser session and never saved to disk or database."
        )
        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("Save Key", use_container_width=True):
                if new_key_input:
                    st.session_state.encrypted_api_key = st.session_state.key_manager.encrypt_key(new_key_input)
                    st.success("Key encrypted & saved in session memory!")
                    st.rerun()
        with col_clear:
            if st.button("Clear Key", use_container_width=True):
                st.session_state.encrypted_api_key = ""
                st.info("Key removed from memory.")
                st.rerun()

# ==========================================
# MAIN CANVAS
# ==========================================

# Current session details & message history
messages = db.get_messages(st.session_state.current_session_id)
has_messages = len(messages) > 0

# Greeting calculation for Hero
current_hour = datetime.datetime.now().hour
if current_hour < 12:
    greeting = "Good morning"
elif current_hour < 17:
    greeting = "Good afternoon"
else:
    greeting = "Good evening"

# Top Controls Bar: Model & Effort Level Selector
col_model, col_effort, col_attach = st.columns([0.45, 0.30, 0.25])

with col_model:
    model_options = list(CLAUDE_MODELS.keys())
    selected_model_name = st.selectbox(
        "Model",
        options=model_options,
        index=0,
        label_visibility="collapsed",
        help="Choose Claude model"
    )
    selected_model_id = CLAUDE_MODELS[selected_model_name]
    model_meta = MODEL_DETAILS.get(selected_model_name, {})

with col_effort:
    selected_effort = st.selectbox(
        "Reasoning Effort",
        options=list(EFFORT_LEVELS.keys()),
        index=1,
        label_visibility="collapsed",
        help="Set reasoning effort & thinking budget"
    )

with col_attach:
    uploaded_files = st.file_uploader(
        "Upload files",
        accept_multiple_files=True,
        type=["txt", "md", "py", "js", "ts", "json", "csv", "pdf", "docx"],
        label_visibility="collapsed"
    )

# Model Tagline & Pricing Indicator
tagline = model_meta.get("tagline", "")
pricing = model_meta.get("pricing", "")
badge = model_meta.get("badge")
badge_html = f"<span class='new-badge'>{badge}</span> " if badge else ""

st.markdown(f"""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; padding: 4px 8px; font-size: 0.8rem; color: #736E65; border-bottom: 1px solid #E5E0D8;">
    <div>{badge_html}<strong>{selected_model_name}</strong> — {tagline}</div>
    <div>{pricing} • Effort: <strong>{selected_effort}</strong></div>
</div>
""", unsafe_allow_html=True)

# HERO LANDING VIEW (Shown on New Chat with 0 messages)
if not has_messages:
    st.markdown(f"""
    <div class="claude-hero-container">
        <div class="claude-spark-icon">✨</div>
        <div class="claude-hero-title">{greeting}, how can Claude help?</div>
        <div class="claude-hero-subtitle">Select a prompt below or type your request to begin with {selected_model_name}.</div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Quick Starter Prompt Cards
    card1, card2 = st.columns(2)
    with card1:
        if st.button("📝 Write, Edit & Summarize\nDraft content, polish text, or synthesize long documents", key="card_write", use_container_width=True):
            st.session_state.active_starter_prompt = "Please help me write, structure, and refine a comprehensive document on: "
            st.rerun()
        if st.button("⚡ Architect Systems & Code\nDesign modular software, create APIs, and implement features", key="card_code", use_container_width=True):
            st.session_state.active_starter_prompt = "Act as a Principal Software Architect. Design and implement clean, production-ready code for: "
            st.rerun()
    with card2:
        if st.button("📊 Analyze Data & Documents\nExtract insights, compute statistics, and find key trends", key="card_data", use_container_width=True):
            st.session_state.active_starter_prompt = "Analyze the provided data or document, extract key insights, and produce structured findings: "
            st.rerun()
        if st.button("💡 Brainstorm & Storytelling\nExplore innovative concepts, world-building, and creative narratives", key="card_story", use_container_width=True):
            st.session_state.active_starter_prompt = "Craft an immersive, vivid narrative exploring: "
            st.rerun()

# PROCESS ATTACHMENTS
file_context_str = ""
if uploaded_files:
    processed_files = []
    for f in uploaded_files:
        p = process_raw_file(f.name, f.read())
        if p:
            processed_files.append(p)
    if processed_files:
        file_context_str = "\n\n" + format_file_for_prompt(processed_files)
        st.info(f"📎 {len(processed_files)} file(s) attached to context.")

# CHAT MESSAGE HISTORY
for msg in messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "✨"):
        if msg.get("thinking"):
            with st.expander("💭 Extended Thinking Process", expanded=False):
                st.markdown(f"<div class='thinking-panel'>{msg['thinking']}</div>", unsafe_allow_html=True)
        
        st.markdown(msg["content"])
        
        # Display extracted artifacts
        artifacts = extract_artifacts(msg["content"])
        if artifacts:
            for art in artifacts:
                with st.expander(f"📦 {art['title']}", expanded=False):
                    st.code(art["code"], language=art["language"])

# INPUT HANDLING
prefill_prompt = st.session_state.active_starter_prompt
prompt_input = st.chat_input("Reply to Claude...")

# If starter card clicked or chat input submitted
user_query = prompt_input or (prefill_prompt if prefill_prompt and prompt_input else None)

if prompt_input:
    # Clear starter prompt after sending
    st.session_state.active_starter_prompt = ""
    
    current_key = get_current_api_key()
    if not current_key:
        st.error("🔑 Please provide an Anthropic API Key in the sidebar before sending a message.")
        st.stop()
        
    full_prompt = prompt_input + file_context_str
    
    # Save user message to database
    db.save_message(st.session_state.current_session_id, "user", full_prompt)
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt_input)
        if file_context_str:
            st.caption(f"📎 Attached {len(uploaded_files)} file(s)")

    # Prepare chat history for API
    history_messages = []
    for m in db.get_messages(st.session_state.current_session_id):
        history_messages.append({"role": m["role"], "content": m["content"]})

    # Assistant Response Generation
    with st.chat_message("assistant", avatar="✨"):
        thinking_placeholder = st.empty()
        response_placeholder = st.empty()
        error_placeholder = st.empty()
        
        full_text = ""
        full_thinking = ""
        
        try:
            engine = ClaudeEngine(api_key=current_key)
            
            with st.spinner(f"Claude is generating with {selected_model_name}..."):
                stream = engine.stream_chat(
                    model_name=selected_model_name,
                    model_id=selected_model_id,
                    messages=history_messages,
                    system=system_prompt,
                    effort_level=selected_effort,
                    max_tokens=8192
                )
                
                for chunk in stream:
                    if chunk["type"] == "thinking":
                        full_thinking += chunk["delta"]
                        with thinking_placeholder.expander("💭 Extended Thinking Process", expanded=True):
                            st.markdown(f"<div class='thinking-panel'>{full_thinking}</div>", unsafe_allow_html=True)
                    elif chunk["type"] == "text":
                        full_text += chunk["delta"]
                        response_placeholder.markdown(full_text + "▌")
                        
            # Final output render without cursor
            response_placeholder.markdown(full_text)
            
            # Save assistant response to DB
            db.save_message(
                session_id=st.session_state.current_session_id,
                role="assistant",
                content=full_text,
                thinking=full_thinking
            )
            
            # Auto-title conversation on first turn
            if len(history_messages) <= 2:
                auto_title = prompt_input[:30] + ("..." if len(prompt_input) > 30 else "")
                db.update_session_title(st.session_state.current_session_id, auto_title)
                
            # Render any extracted artifacts
            artifacts = extract_artifacts(full_text)
            for art in artifacts:
                with st.expander(f"📦 {art['title']}", expanded=True):
                    st.code(art["code"], language=art["language"])
                    
        except ClaudeModelError as cme:
            # High-visibility Front-End Diagnostic Error Card
            status_badge = f"{cme.status_code} {cme.error_type}" if cme.status_code else cme.error_type
            error_placeholder.markdown(f"""
            <div class="claude-error-card">
                <div class="claude-error-header">
                    <span>⚠️ Model Execution Failed</span>
                    <span class="claude-error-code">{status_badge}</span>
                </div>
                <div class="claude-error-body">
                    <strong>Model:</strong> {cme.model_name} (<code>{cme.model_id}</code>)<br/>
                    <strong>Reason:</strong> {cme.message}<br/><br/>
                    <em>Action: Check your Anthropic API Key account permissions or select an active model from the top selector.</em>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as ex:
            error_placeholder.markdown(f"""
            <div class="claude-error-card">
                <div class="claude-error-header">
                    <span>⚠️ Unexpected Error</span>
                    <span class="claude-error-code">500 ERROR</span>
                </div>
                <div class="claude-error-body">
                    <strong>Model:</strong> {selected_model_name} (<code>{selected_model_id}</code>)<br/>
                    <strong>Reason:</strong> {str(ex)}
                </div>
            </div>
            """, unsafe_allow_html=True)
