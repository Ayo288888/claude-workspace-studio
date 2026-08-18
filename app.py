import datetime
import os
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv()

from storage import Database
from claude_client import (
    ClaudeEngine,
    ClaudeModelError,
    CLAUDE_MODELS,
    MODEL_DETAILS,
    EFFORT_LEVELS,
    SYSTEM_PRESETS,
    extract_artifacts,
    calculate_cost,
    format_cost_badge
)
from file_processor import process_raw_file, format_file_for_prompt
from styles import apply_claude_styles
from security import SessionKeyManager, mask_api_key, validate_anthropic_key

# Page configuration
st.set_page_config(
    page_title="Claude",
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

if "live_models_cache" not in st.session_state:
    st.session_state.live_models_cache = []

# Check environment variable for initial key if provided locally
if not st.session_state.encrypted_api_key:
    init_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not init_key and hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
        init_key = st.secrets["ANTHROPIC_API_KEY"]
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

# Ensure active session exists
sessions = db.get_sessions()
if not st.session_state.current_session_id:
    if sessions:
        st.session_state.current_session_id = sessions[0]["id"]
    else:
        new_id = db.create_session(
            title="New Chat",
            model="Claude 3.7 Sonnet (Reasoning)",
            system_prompt=SYSTEM_PRESETS["General Assistant"]
        )
        st.session_state.current_session_id = new_id
        sessions = db.get_sessions()

current_session = db.get_session(st.session_state.current_session_id)
if not current_session:
    new_id = db.create_session(
        title="New Chat",
        model="Claude 3.7 Sonnet (Reasoning)",
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

# Fetch live models from Anthropic Console if key is authenticated and cache is empty
if current_key and not st.session_state.live_models_cache:
    try:
        temp_engine = ClaudeEngine(api_key=current_key)
        live = temp_engine.fetch_live_models()
        if live:
            st.session_state.live_models_cache = live
    except Exception:
        pass

# Build Model Choices
model_choices = {}
if st.session_state.live_models_cache:
    for lm in st.session_state.live_models_cache:
        label = f"{lm['display_name']} ({lm['id']})"
        model_choices[label] = lm['id']

for k, v in CLAUDE_MODELS.items():
    if k not in model_choices:
        model_choices[k] = v

model_choices["Custom Model ID..."] = "custom"

# ==========================================
# SIDEBAR - POLISHED CLAUDE.AI LAYOUT
# ==========================================
with st.sidebar:
    # Header Branding
    st.markdown("""
    <div style="margin-bottom: 18px; padding-bottom: 6px;">
        <div style="font-weight: 700; font-size: 1.3rem; color: #2C2825; line-height: 1.1; letter-spacing: -0.02em;">Claude</div>
        <div style="font-size: 0.76rem; color: #736E65; margin-top: 2px;">Workspace Studio</div>
    </div>
    """, unsafe_allow_html=True)

    # Primary Action: Start New Chat
    if st.button("Start new chat", use_container_width=True, type="primary"):
        new_id = db.create_session(
            title="New Chat",
            model="Claude 3.7 Sonnet (Reasoning)",
            system_prompt=SYSTEM_PRESETS["General Assistant"]
        )
        st.session_state.current_session_id = new_id
        st.session_state.active_starter_prompt = ""
        st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Section 1: Model & Reasoning Configuration
    st.markdown("<div class='sidebar-section-title'>Model & Reasoning</div>", unsafe_allow_html=True)
    
    selected_model_label = st.selectbox(
        "Model",
        options=list(model_choices.keys()),
        index=0,
        label_visibility="collapsed"
    )
    
    if selected_model_label == "Custom Model ID...":
        custom_id_input = st.text_input("Model ID", placeholder="e.g. claude-opus-4-6", help="Type exact model identifier from your Claude console.")
        selected_model_id = custom_id_input.strip() if custom_id_input else "claude-3-7-sonnet-20250219"
        selected_model_name = f"Custom ({selected_model_id})"
    else:
        selected_model_id = model_choices[selected_model_label]
        selected_model_name = selected_model_label

    model_meta = MODEL_DETAILS.get(selected_model_name, {})

    selected_effort = st.select_slider(
        "Effort",
        options=list(EFFORT_LEVELS.keys()),
        value="Medium",
        help="Low: Fast & light • Medium: Balanced • High: Deep chain-of-thought"
    )

    badge = model_meta.get("badge")
    badge_html = f"<span class='new-pill'>{badge}</span>" if badge else ""
    st.markdown(f"""
    <div style="font-size: 0.75rem; color: #736E65; margin-top: -6px; margin-bottom: 14px; line-height: 1.4;">
        {badge_html} <em>{model_meta.get('tagline', 'Direct Anthropic Engine')}</em><br/>
        <span style="color: #A09A8F;">Target: <code>{selected_model_id}</code></span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Section 2: Persona & System Preset
    st.markdown("<div class='sidebar-section-title'>System Preset</div>", unsafe_allow_html=True)
    selected_preset = st.selectbox(
        "Preset",
        options=list(SYSTEM_PRESETS.keys()),
        index=0,
        label_visibility="collapsed"
    )
    if selected_preset == "Custom Instructions...":
        custom_system_input = st.text_area(
            "Custom Instructions",
            placeholder="Type custom instructions for Claude...",
            help="Define how Claude should respond in this session."
        )
        system_prompt = custom_system_input.strip() if custom_system_input else ""
    else:
        system_prompt = SYSTEM_PRESETS[selected_preset]

    st.divider()

    # Section 3: Recent Chats List
    st.markdown("<div class='sidebar-section-title'>Recent Chats</div>", unsafe_allow_html=True)
    
    for s in sessions[:15]:
        is_active = s["id"] == st.session_state.current_session_id
        col_btn, col_del = st.columns([0.84, 0.16])
        with col_btn:
            title_text = s['title'][:22] + "..." if len(s['title']) > 22 else s['title']
            if st.button(
                title_text,
                key=f"sess_{s['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_session_id = s["id"]
                st.session_state.active_starter_prompt = ""
                st.rerun()
        with col_del:
            if st.button("x", key=f"del_{s['id']}", help="Delete chat"):
                db.delete_session(s["id"])
                remaining = db.get_sessions()
                st.session_state.current_session_id = remaining[0]["id"] if remaining else None
                st.rerun()

    st.divider()

    # Section 4: In-Memory Encrypted Authentication
    st.markdown("<div class='sidebar-section-title'>Authentication & Security</div>", unsafe_allow_html=True)
    
    if current_key:
        masked_fingerprint = mask_api_key(current_key)
        st.markdown(f"""
        <div class="security-badge-container">
            <div class="security-badge-header">Key Encrypted & Active</div>
            <div class="security-badge-sub">
                <strong>Fingerprint:</strong> <code>{masked_fingerprint}</code><br/>
                • In-Memory AES-256 cipher<br/>
                • Zero disk or database persistence<br/>
                • Auto-purged on session end
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Disconnect Key", use_container_width=True, type="secondary"):
            st.session_state.encrypted_api_key = ""
            st.session_state.live_models_cache = []
            st.rerun()
    else:
        st.markdown("""
        <div style="font-size: 0.78rem; color: #736E65; margin-bottom: 8px;">
            Paste your Anthropic API Key. It is held encrypted in volatile memory only.
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("api_key_secure_form", clear_on_submit=True):
            user_raw_key = st.text_input(
                "API Key Token",
                type="password",
                placeholder="sk-ant-api03-...",
                label_visibility="collapsed"
            )
            submit_key = st.form_submit_button("Authenticate & Encrypt", use_container_width=True, type="primary")
            
            if submit_key:
                if user_raw_key and user_raw_key.strip():
                    st.session_state.encrypted_api_key = st.session_state.key_manager.encrypt_key(user_raw_key.strip())
                    st.session_state.live_models_cache = []
                    del user_raw_key
                    st.rerun()
                else:
                    st.error("Please enter a valid API key.")

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

# Top Minimal Status Header
st.markdown(f"""
<div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.88rem; color: #736E65; padding: 4px 0 10px 0; border-bottom: 1px solid #E5E0D8; margin-bottom: 16px;">
    <div>
        <span style="font-weight: 600; color: #2C2825;">{selected_model_name}</span>
        <span> • </span>
        <span>Effort: <strong>{selected_effort}</strong></span>
        <span> • </span>
        <span>{selected_preset}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# HERO LANDING VIEW (Shown on New Chat with 0 messages)
if not has_messages:
    st.markdown(f"""
    <div class="claude-hero-wrapper">
        <div class="claude-title">{greeting}, how can Claude help?</div>
        <div class="claude-subtitle">Pick a prompt starter below or type your request in the box.</div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Quick Starter Prompt Cards
    card_col1, card_col2 = st.columns(2)
    with card_col1:
        if st.button("Write, Edit & Summarize\nDraft content, polish text, or synthesize documents", key="card_write", use_container_width=True):
            st.session_state.active_starter_prompt = "Please help me write, structure, and refine a comprehensive document on: "
            st.rerun()
        if st.button("Architect Systems & Code\nDesign modular software, create APIs, and implement features", key="card_code", use_container_width=True):
            st.session_state.active_starter_prompt = "Act as a Principal Software Architect. Design and implement clean, production-ready code for: "
            st.rerun()
    with card_col2:
        if st.button("Analyze Data & Documents\nExtract insights, compute statistics, and find key trends", key="card_data", use_container_width=True):
            st.session_state.active_starter_prompt = "Analyze the provided data or document, extract key insights, and produce structured findings: "
            st.rerun()
        if st.button("Brainstorm & Storytelling\nExplore innovative concepts, world-building, and creative narratives", key="card_story", use_container_width=True):
            st.session_state.active_starter_prompt = "Craft an immersive, vivid narrative exploring: "
            st.rerun()

# CHAT MESSAGE HISTORY
for msg in messages:
    with st.chat_message(msg["role"]):
        if msg.get("thinking"):
            with st.expander("Extended Thinking Process", expanded=False):
                st.markdown(f"<div class='thinking-panel'>{msg['thinking']}</div>", unsafe_allow_html=True)
        
        st.markdown(msg["content"])
        
        # Display extracted artifacts
        artifacts = extract_artifacts(msg["content"])
        if artifacts:
            for art in artifacts:
                with st.expander(f"Artifact: {art['title']}", expanded=False):
                    st.code(art["code"], language=art["language"])

        # Display Workbench-style Cost and Token Badge for Assistant Messages
        if msg["role"] == "assistant":
            in_t = msg.get("input_tokens", 0)
            out_t = msg.get("output_tokens", msg.get("tokens", 0))
            cost_val = msg.get("cost", 0.0)
            if in_t > 0 or out_t > 0 or cost_val > 0:
                cost_badge_str = format_cost_badge(in_t, out_t, cost_val)
                st.markdown(f"<div class='cost-token-badge'>{cost_badge_str}</div>", unsafe_allow_html=True)

# =========================================================================
# CHATBOX WITH INLINE ATTACHMENT CONTROLS
# =========================================================================
prefill_prompt = st.session_state.active_starter_prompt
if prefill_prompt and not has_messages:
    st.info(f"Starter Prompt Selected: *{prefill_prompt}* (Type your topic below to send)")

# Integrated chatbox attachment row
col_attach_btn, col_attach_status = st.columns([0.18, 0.82])
with col_attach_btn:
    with st.popover("+ Attach", help="Attach code, markdown, documents or images to prompt"):
        uploaded_files = st.file_uploader(
            "Upload files",
            accept_multiple_files=True,
            type=["txt", "md", "py", "js", "ts", "json", "csv", "pdf", "docx"],
            label_visibility="collapsed",
            key="inline_chat_uploader"
        )

file_context_str = ""
with col_attach_status:
    if uploaded_files:
        processed_files = []
        for f in uploaded_files:
            p = process_raw_file(f.name, f.read())
            if p:
                processed_files.append(p)
        if processed_files:
            file_context_str = "\n\n" + format_file_for_prompt(processed_files)
            file_names = ", ".join([f.name for f in uploaded_files])
            st.markdown(f"<span class='attachment-chip'>Attached: {file_names}</span>", unsafe_allow_html=True)

prompt_input = st.chat_input("Reply to Claude...")

if prompt_input:
    # If starter prompt was active, prepend it
    if prefill_prompt:
        actual_query = prefill_prompt + prompt_input
        st.session_state.active_starter_prompt = ""
    else:
        actual_query = prompt_input
        
    current_key = get_current_api_key()
    if not current_key:
        st.error("Please enter your Anthropic API Key in the sidebar before sending a message.")
        st.stop()
        
    full_prompt = actual_query + file_context_str
    
    # Save user message to database
    db.save_message(st.session_state.current_session_id, "user", full_prompt)
    
    with st.chat_message("user"):
        st.markdown(actual_query)
        if file_context_str and uploaded_files:
            st.caption(f"Attached {len(uploaded_files)} file(s)")

    # Prepare chat history for API
    history_messages = []
    for m in db.get_messages(st.session_state.current_session_id):
        history_messages.append({"role": m["role"], "content": m["content"]})

    # Assistant Response Generation
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        response_placeholder = st.empty()
        cost_placeholder = st.empty()
        error_placeholder = st.empty()
        
        full_text = ""
        full_thinking = ""
        final_usage = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}
        
        try:
            engine = ClaudeEngine(api_key=current_key)
            
            with st.spinner(f"Generating with {selected_model_name}..."):
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
                        with thinking_placeholder.expander("Extended Thinking Process", expanded=True):
                            st.markdown(f"<div class='thinking-panel'>{full_thinking}</div>", unsafe_allow_html=True)
                    elif chunk["type"] == "text":
                        full_text += chunk["delta"]
                        response_placeholder.markdown(full_text + "▌")
                    elif chunk["type"] == "usage_summary":
                        final_usage = chunk
                        cost_placeholder.markdown(f"<div class='cost-token-badge'>{chunk['badge']}</div>", unsafe_allow_html=True)
                        
            # Final output render without cursor
            response_placeholder.markdown(full_text)
            
            # Save assistant response with exact tokens & cost to DB
            db.save_message(
                session_id=st.session_state.current_session_id,
                role="assistant",
                content=full_text,
                thinking=full_thinking,
                tokens=final_usage["output_tokens"],
                input_tokens=final_usage["input_tokens"],
                output_tokens=final_usage["output_tokens"],
                cost=final_usage["cost"]
            )
            
            # Auto-title conversation on first turn
            if len(history_messages) <= 2:
                auto_title = prompt_input[:30] + ("..." if len(prompt_input) > 30 else "")
                db.update_session_title(st.session_state.current_session_id, auto_title)
                
            # Render any extracted artifacts
            artifacts = extract_artifacts(full_text)
            for art in artifacts:
                with st.expander(f"Artifact: {art['title']}", expanded=True):
                    st.code(art["code"], language=art["language"])
                    
        except ClaudeModelError as cme:
            # High-visibility Front-End Diagnostic Error Card
            status_badge = f"{cme.status_code} {cme.error_type}" if cme.status_code else cme.error_type
            error_placeholder.markdown(f"""
            <div class="claude-error-card">
                <div class="claude-error-header">
                    <div class="claude-error-title">
                        Model Execution Failed
                    </div>
                    <div class="claude-error-code">{status_badge}</div>
                </div>
                <div class="claude-error-body">
                    <strong>Model:</strong> {cme.model_name} (<code>{cme.model_id}</code>)<br/>
                    <strong>Reason:</strong> {cme.message}<br/><br/>
                    <em>Action: Check your Anthropic API Key account permissions or select an active model from the sidebar.</em>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as ex:
            error_placeholder.markdown(f"""
            <div class="claude-error-card">
                <div class="claude-error-header">
                    <div class="claude-error-title">
                        Unexpected Error
                    </div>
                    <div class="claude-error-code">500 ERROR</div>
                </div>
                <div class="claude-error-body">
                    <strong>Model:</strong> {selected_model_name} (<code>{selected_model_id}</code>)<br/>
                    <strong>Reason:</strong> {str(ex)}
                </div>
            </div>
            """, unsafe_allow_html=True)
