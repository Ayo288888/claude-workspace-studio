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
from file_processor import process_raw_file, build_anthropic_message_content
from web_tools import get_web_context_for_prompt
from styles import apply_claude_styles
from security import SessionKeyManager, mask_api_key, validate_anthropic_key

# Page configuration
st.set_page_config(
    page_title="Claude",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Claude Dark CSS styling
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
if "selected_model_name" not in st.session_state:
    st.session_state.selected_model_name = "Claude 3.7 Sonnet (Reasoning)"
if "selected_effort" not in st.session_state:
    st.session_state.selected_effort = "Medium"
if "web_search_active" not in st.session_state:
    st.session_state.web_search_active = True

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

# Messages and session calculations
messages = db.get_messages(st.session_state.current_session_id)
has_messages = len(messages) > 0

# Total session tokens and cost
total_session_tokens = sum(m.get("input_tokens", 0) + m.get("output_tokens", m.get("tokens", 0)) for m in messages)
total_session_cost = sum(m.get("cost", 0.0) for m in messages)

# ==========================================
# SIDEBAR - CLAUDE INTERFACE
# ==========================================
with st.sidebar:
    # Top Branding
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; padding-bottom: 2px;">
        <div style="font-weight: 700; font-size: 1.35rem; color: #ECEAE4; letter-spacing: -0.02em;">Claude</div>
        <div style="font-size: 0.72rem; color: #8E8A80; background: #20201D; padding: 2px 8px; border-radius: 8px; border: 1px solid #2D2D29;">Studio</div>
    </div>
    """, unsafe_allow_html=True)

    # + New Chat Pill Button
    if st.button("+ New", use_container_width=True, type="primary"):
        new_id = db.create_session(
            title="New Chat",
            model=st.session_state.selected_model_name,
            system_prompt=SYSTEM_PRESETS["General Assistant"]
        )
        st.session_state.current_session_id = new_id
        st.session_state.active_starter_prompt = ""
        st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # System Preset / Customize Section
    st.markdown("<div class='sidebar-section-title'>Customize & Presets</div>", unsafe_allow_html=True)
    selected_preset = st.selectbox(
        "System Preset",
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

    # Web Browsing & Search Toggle
    st.markdown("<div class='sidebar-section-title'>Live Web & Search</div>", unsafe_allow_html=True)
    st.session_state.web_search_active = st.toggle(
        "Enable Web Search & URL Reader",
        value=st.session_state.web_search_active,
        help="Allows Claude to search the web in real-time and read URLs passed in prompts."
    )

    st.divider()

    # Usage & Session Metrics Box
    st.markdown("<div class='sidebar-section-title'>Usage & Metrics</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sidebar-usage-box">
        <div class="usage-row">
            <span class="usage-label">Session Tokens:</span>
            <strong>{total_session_tokens:,}</strong>
        </div>
        <div class="usage-row">
            <span class="usage-label">Session Cost:</span>
            <strong>${total_session_cost:.4f}</strong>
        </div>
        <div class="usage-row">
            <span class="usage-label">Messages:</span>
            <span>{len(messages)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Chats and Tasks Section
    st.markdown("<div class='sidebar-section-title'>Chats and tasks</div>", unsafe_allow_html=True)
    
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

    # Authentication & Security
    st.markdown("<div class='sidebar-section-title'>Authentication & Security</div>", unsafe_allow_html=True)
    
    if current_key:
        masked_fingerprint = mask_api_key(current_key)
        st.markdown(f"""
        <div class="security-badge-container">
            <div class="security-badge-header">Key Encrypted & Active</div>
            <div class="security-badge-sub">
                <strong>Fingerprint:</strong> <code>{masked_fingerprint}</code><br/>
                • In-Memory AES-256 cipher<br/>
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
        <div style="font-size: 0.76rem; color: #8E8A80; margin-bottom: 8px;">
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

# Time of day greeting
current_hour = datetime.datetime.now().hour
if current_hour >= 22 or current_hour < 5:
    greeting = "Up late?"
elif current_hour < 12:
    greeting = "Good morning"
elif current_hour < 17:
    greeting = "Good afternoon"
else:
    greeting = "Good evening"

# Top Minimal Bar if chat is ongoing
if has_messages:
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.86rem; color: #8E8A80; padding: 4px 0 10px 0; border-bottom: 1px solid #2D2D29; margin-bottom: 16px;">
        <div>
            <span style="font-weight: 600; color: #ECEAE4;">{st.session_state.selected_model_name}</span>
            <span> • </span>
            <span>Effort: <strong>{st.session_state.selected_effort}</strong></span>
            <span> • </span>
            <span>{selected_preset}</span>
            {"<span> • 🌐 Web Access Active</span>" if st.session_state.web_search_active else ""}
        </div>
        <div style="font-size: 0.78rem; font-family: monospace;">
            Total: {total_session_tokens:,} tokens (${total_session_cost:.4f})
        </div>
    </div>
    """, unsafe_allow_html=True)

# HERO LANDING VIEW (Shown on New Chat with 0 messages)
if not has_messages:
    st.markdown(f"""
    <div class="claude-hero-container">
        <div class="claude-hero-title">
            <span class="claude-hero-asterisk">✳</span>
            <span>{greeting}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Quick Starter Pill Tags beneath the greeting on New Chat
prefill_prompt = st.session_state.active_starter_prompt
if not has_messages:
    pill1, pill2, pill3, pill4, pill5 = st.columns(5)
    with pill1:
        if st.button("Write", key="pill_write", use_container_width=True):
            st.session_state.active_starter_prompt = "Help me write and refine: "
            st.rerun()
    with pill2:
        if st.button("Learn", key="pill_learn", use_container_width=True):
            st.session_state.active_starter_prompt = "Explain in depth with examples: "
            st.rerun()
    with pill3:
        if st.button("Code", key="pill_code", use_container_width=True):
            st.session_state.active_starter_prompt = "Design and implement clean, production-grade code for: "
            st.rerun()
    with pill4:
        if st.button("Analyze", key="pill_data", use_container_width=True):
            st.session_state.active_starter_prompt = "Analyze the following data or text and extract structured insights: "
            st.rerun()
    with pill5:
        if st.button("Claude's choice", key="pill_choice", use_container_width=True):
            st.session_state.active_starter_prompt = "Surprise me with an insightful synthesis on modern AI architecture: "
            st.rerun()

if prefill_prompt and not has_messages:
    st.info(f"Starter Prompt: *{prefill_prompt}* (Type your details below to send)")

# CHAT MESSAGE HISTORY
for msg in messages:
    with st.chat_message(msg["role"]):
        has_text = bool(msg.get("content") and str(msg["content"]).strip())
        has_thinking = bool(msg.get("thinking") and str(msg["thinking"]).strip())

        if has_thinking:
            with st.expander("Extended Thinking Process", expanded=not has_text):
                st.markdown(f"<div class='thinking-panel'>{msg['thinking']}</div>", unsafe_allow_html=True)
        
        # If content is string or multimodal
        if isinstance(msg["content"], str) and msg["content"].strip():
            st.markdown(msg["content"])
            artifacts = extract_artifacts(msg["content"])
            if artifacts:
                for art in artifacts:
                    with st.expander(f"Artifact: {art['title']}", expanded=False):
                        st.code(art["code"], language=art["language"])
        elif isinstance(msg["content"], list):
            for block in msg["content"]:
                if block.get("type") == "image":
                    st.caption("[Attached Image]")
                elif block.get("type") == "text" and block.get("text"):
                    st.markdown(block.get("text"))
        elif not has_text and has_thinking:
            st.markdown("*Claude completed its deep reasoning steps (see thinking process above).*")

        # Display Workbench-style Cost and Token Badge for Assistant Messages
        if msg["role"] == "assistant":
            in_t = msg.get("input_tokens", 0)
            out_t = msg.get("output_tokens", msg.get("tokens", 0))
            cost_val = msg.get("cost", 0.0)
            if in_t > 0 or out_t > 0 or cost_val > 0:
                cost_badge_str = format_cost_badge(in_t, out_t, cost_val)
                st.markdown(f"<div class='cost-token-badge'>{cost_badge_str}</div>", unsafe_allow_html=True)

# =========================================================================
# PERSISTENT STICKY BOTTOM BAR (MODEL & EFFORT + CHAT INPUT + ATTACH)
# =========================================================================

curr_model_display = st.session_state.selected_model_name.split("(")[0].strip()
prompt_placeholder = "Ask anything, @ to mention, / for actions" if not has_messages else "Reply to Claude..."

# Support both object and callable st.bottom across Streamlit versions
bottom_container = getattr(st, "bottom", None)
if bottom_container is not None:
    bottom_ctx = bottom_container() if callable(bottom_container) else bottom_container
else:
    bottom_ctx = st.container()

with bottom_ctx:
    # Sticky Model & Effort Selector Trigger
    col_model_btn, col_spacer = st.columns([0.45, 0.55])
    with col_model_btn:
        with st.popover(f"{curr_model_display} {st.session_state.selected_effort} ⌃ ⌄", help="Configure Model & Reasoning Effort"):
            st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #8E8A80; text-transform: uppercase;'>Model Selection</div>", unsafe_allow_html=True)
            selected_model_label = st.selectbox(
                "Model",
                options=list(model_choices.keys()),
                index=0,
                label_visibility="collapsed",
                key="bottom_model_select"
            )
            if selected_model_label == "Custom Model ID...":
                custom_id_input = st.text_input("Model ID", placeholder="e.g. claude-opus-4-6", key="bottom_custom_id")
                selected_model_id = custom_id_input.strip() if custom_id_input else "claude-3-7-sonnet-20250219"
                selected_model_name = f"Custom ({selected_model_id})"
            else:
                selected_model_id = model_choices[selected_model_label]
                selected_model_name = selected_model_label
            st.session_state.selected_model_name = selected_model_name

            st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #8E8A80; text-transform: uppercase; margin-top: 10px;'>Reasoning Effort</div>", unsafe_allow_html=True)
            selected_effort = st.select_slider(
                "Effort",
                options=list(EFFORT_LEVELS.keys()),
                value=st.session_state.selected_effort if st.session_state.selected_effort in EFFORT_LEVELS else "Medium",
                label_visibility="collapsed",
                key="bottom_effort_slider"
            )
            st.session_state.selected_effort = selected_effort

    # Native persistent file upload attached directly inside chat input (accepts all file types: images, notebooks, code, etc.)
    prompt_input = st.chat_input(
        prompt_placeholder,
        accept_file="multiple"
    )

if prompt_input:
    # Extract query text and uploaded files from ChatInputValue or str
    if isinstance(prompt_input, str):
        user_query_text = prompt_input
        attached_files = []
    else:
        user_query_text = getattr(prompt_input, "text", "") or prompt_input.get("text", "")
        attached_files = getattr(prompt_input, "files", []) or prompt_input.get("files", [])

    if prefill_prompt:
        actual_query = prefill_prompt + user_query_text
        st.session_state.active_starter_prompt = ""
    else:
        actual_query = user_query_text
        
    current_key = get_current_api_key()
    if not current_key:
        st.error("Please enter your Anthropic API Key in the sidebar before sending a message.")
        st.stop()

    # Process all uploaded/attached files (notebooks, code, images, docs, data)
    processed_files_list = []
    if attached_files:
        for f in attached_files:
            p = process_raw_file(f.name, f.read())
            if p:
                processed_files_list.append(p)

    # Retrieve live web context if enabled or URLs present
    web_context_str, web_sources = "", []
    if st.session_state.web_search_active:
        with st.spinner("Checking live web & sources..."):
            web_context_str, web_sources = get_web_context_for_prompt(actual_query, web_search_enabled=True)
        
    # Build exact Claude multimodal vision + text payload
    full_message_payload = build_anthropic_message_content(
        prompt_text=actual_query,
        processed_files=processed_files_list,
        web_context=web_context_str
    )
    
    # Save user message to database
    db.save_message(st.session_state.current_session_id, "user", actual_query if isinstance(full_message_payload, list) else full_message_payload)
    
    with st.chat_message("user"):
        st.markdown(actual_query)
        if processed_files_list:
            st.caption(f"Attached {len(processed_files_list)} file(s) / image(s)")
        if web_sources:
            st.caption(f"Web Sources Referenced: {', '.join(web_sources[:2])}")

    # Prepare chat history for API (including current multimodal message)
    history_messages = []
    for m in db.get_messages(st.session_state.current_session_id)[:-1]:
        history_messages.append({"role": m["role"], "content": m["content"]})
    history_messages.append({"role": "user", "content": full_message_payload})

    # Assistant Response Generation
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        response_placeholder = st.empty()
        cost_placeholder = st.empty()
        error_placeholder = st.empty()
        
        full_text = ""
        full_thinking = ""
        final_usage = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}
        
        target_model_name = st.session_state.selected_model_name
        target_model_id = model_choices.get(target_model_name, CLAUDE_MODELS.get(target_model_name, "claude-3-7-sonnet-20250219"))
        target_effort = st.session_state.selected_effort
        
        try:
            engine = ClaudeEngine(api_key=current_key)
            
            with st.spinner(f"Generating with {target_model_name}..."):
                stream = engine.stream_chat(
                    model_name=target_model_name,
                    model_id=target_model_id,
                    messages=history_messages,
                    system=system_prompt,
                    effort_level=target_effort
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
            if full_text.strip():
                response_placeholder.markdown(full_text)
            elif full_thinking.strip():
                response_placeholder.markdown(f"*Claude completed its deep reasoning steps (see thinking process above).*")
            
            # Save assistant response with exact tokens & cost to DB
            db.save_message(
                session_id=st.session_state.current_session_id,
                role="assistant",
                content=full_text if full_text.strip() else full_thinking,
                thinking=full_thinking,
                tokens=final_usage["output_tokens"],
                input_tokens=final_usage["input_tokens"],
                output_tokens=final_usage["output_tokens"],
                cost=final_usage["cost"]
            )
            
            # Auto-title conversation on first turn
            if len(history_messages) <= 2:
                auto_title = actual_query[:30] + ("..." if len(actual_query) > 30 else "")
                db.update_session_title(st.session_state.current_session_id, auto_title)
                
            # Render any extracted artifacts
            if full_text.strip():
                artifacts = extract_artifacts(full_text)
                for art in artifacts:
                    with st.expander(f"Artifact: {art['title']}", expanded=True):
                        st.code(art["code"], language=art["language"])
                    
        except ClaudeModelError as cme:
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
                    <em>Action: Check your Anthropic API Key account permissions or select an active model from the selector.</em>
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
                    <strong>Model:</strong> {target_model_name} (<code>{target_model_id}</code>)<br/>
                    <strong>Reason:</strong> {str(ex)}
                </div>
            </div>
            """, unsafe_allow_html=True)
