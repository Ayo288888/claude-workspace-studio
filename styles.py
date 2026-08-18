import streamlit as st

def apply_claude_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600;700&display=swap');

        /* Claude Dark Theme Variables */
        :root {
            --claude-bg: #181816;
            --claude-sidebar: #131311;
            --claude-card: #222220;
            --claude-card-hover: #292926;
            --claude-border: #2E2E2A;
            --claude-border-hover: #3E3E38;
            --claude-text: #ECEAE4;
            --claude-muted: #8E8A80;
            --claude-coral: #DA7756;
            --claude-coral-hover: #E08567;
            --claude-coral-dim: rgba(218, 119, 86, 0.15);
            --claude-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            --claude-shadow-lg: 0 12px 40px rgba(0, 0, 0, 0.4);
        }

        /* Base Application */
        .stApp {
            background-color: var(--claude-bg) !important;
            color: var(--claude-text) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            border-bottom: none !important;
        }
        #MainMenu, footer, .stDeployButton {
            display: none !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: var(--claude-sidebar) !important;
            border-right: 1px solid var(--claude-border) !important;
            padding: 1.25rem 0.9rem !important;
        }

        section[data-testid="stSidebar"] hr {
            border-color: var(--claude-border) !important;
            margin: 1rem 0 !important;
        }

        .sidebar-section-title {
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--claude-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.5rem;
            margin-top: 0.4rem;
        }

        /* Form Inputs, Selectboxes, Menus */
        div[data-baseweb="select"] > div {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 10px !important;
            color: var(--claude-text) !important;
            font-weight: 500 !important;
            font-size: 0.88rem !important;
            transition: all 0.2s ease !important;
        }

        div[data-baseweb="select"] > div:hover {
            border-color: var(--claude-border-hover) !important;
        }

        div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 12px !important;
            box-shadow: var(--claude-shadow-lg) !important;
            color: var(--claude-text) !important;
        }

        li[role="option"] {
            color: var(--claude-text) !important;
            border-radius: 6px !important;
            margin: 2px 4px !important;
            font-size: 0.88rem !important;
        }

        li[role="option"]:hover, li[aria-selected="true"] {
            background-color: var(--claude-coral-dim) !important;
            color: var(--claude-coral) !important;
        }

        div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 10px !important;
            color: var(--claude-text) !important;
        }

        input, textarea {
            color: var(--claude-text) !important;
        }

        /* Standard Buttons */
        .stButton > button {
            border-radius: 10px !important;
            border: 1px solid var(--claude-border) !important;
            background-color: var(--claude-card) !important;
            color: var(--claude-text) !important;
            font-weight: 500 !important;
            font-size: 0.88rem !important;
            padding: 0.45rem 0.9rem !important;
            box-shadow: var(--claude-shadow) !important;
            transition: all 0.15s ease !important;
        }

        .stButton > button:hover {
            border-color: var(--claude-border-hover) !important;
            background-color: var(--claude-card-hover) !important;
            color: var(--claude-text) !important;
        }

        .stButton > button[kind="primary"] {
            background-color: var(--claude-coral) !important;
            border-color: var(--claude-coral) !important;
            color: #FFFFFF !important;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: var(--claude-coral-hover) !important;
            border-color: var(--claude-coral-hover) !important;
        }

        /* + New Chat Pill Button */
        .new-chat-btn button {
            border-radius: 20px !important;
            font-weight: 600 !important;
            text-align: left !important;
            padding: 0.5rem 1rem !important;
        }

        /* Hero Typography */
        .claude-hero-container {
            text-align: center;
            max-width: 820px;
            margin: 3.5rem auto 1.8rem auto;
            padding: 0 1rem;
        }

        .claude-hero-title {
            font-family: 'Instrument Serif', Georgia, serif;
            font-size: 3.4rem;
            font-weight: 400;
            color: var(--claude-text);
            line-height: 1.1;
            letter-spacing: -0.02em;
            display: inline-flex;
            align-items: center;
            gap: 12px;
        }

        .claude-hero-asterisk {
            color: var(--claude-coral);
            font-size: 2.8rem;
            line-height: 1;
            font-family: 'Inter', sans-serif;
            font-weight: 300;
        }

        /* Unified Chatbox Container */
        .claude-chatbox-card {
            background-color: var(--claude-card);
            border: 1px solid var(--claude-border);
            border-radius: 18px;
            padding: 14px 18px 10px 18px;
            box-shadow: var(--claude-shadow-lg);
            margin: 1.5rem auto;
            max-width: 820px;
            transition: border-color 0.2s ease;
        }

        .claude-chatbox-card:focus-within {
            border-color: var(--claude-border-hover);
        }

        /* Bottom Toolbar inside Chatbox */
        .chatbox-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        .toolbar-left, .toolbar-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Quick Starter Pill Row */
        .starter-pills-row {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
            gap: 8px;
            max-width: 820px;
            margin: 0.8rem auto 2.5rem auto;
        }

        /* Chat Message Cards */
        .stChatMessage {
            background-color: transparent !important;
            border-radius: 12px !important;
            padding: 0.9rem 1.1rem !important;
            margin-bottom: 0.75rem !important;
        }

        div[data-testid="stChatMessage"]:nth-child(even) {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
        }

        /* Extended Thinking Monospace Panel */
        .thinking-panel {
            background: #1C1C1A;
            border: 1px solid var(--claude-border);
            border-radius: 10px;
            padding: 12px 14px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.82rem;
            color: var(--claude-muted);
            line-height: 1.55;
            max-height: 300px;
            overflow-y: auto;
        }

        /* Workbench Token Cost Badge */
        .cost-token-badge {
            display: inline-flex;
            align-items: center;
            background-color: #141412;
            border: 1px solid var(--claude-border);
            padding: 3px 10px;
            border-radius: 16px;
            font-size: 0.74rem;
            font-family: 'Consolas', 'Courier New', monospace;
            color: var(--claude-muted);
            margin-top: 8px;
        }

        /* Security Card & Badge */
        .security-badge-container {
            background: rgba(22, 101, 52, 0.12);
            border: 1px solid rgba(34, 197, 94, 0.25);
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 10px;
        }

        .security-badge-header {
            font-size: 0.8rem;
            font-weight: 700;
            color: #4ADE80;
            margin-bottom: 3px;
        }

        .security-badge-sub {
            font-size: 0.73rem;
            color: #86EFAC;
            line-height: 1.35;
        }

        /* Usage Stats Widget in Sidebar */
        .sidebar-usage-box {
            background-color: var(--claude-card);
            border: 1px solid var(--claude-border);
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 10px;
        }

        .usage-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.78rem;
            color: var(--claude-text);
            margin-bottom: 4px;
        }

        .usage-label {
            color: var(--claude-muted);
        }

        /* Expanders / Artifacts */
        .streamlit-expanderHeader {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            color: var(--claude-text) !important;
            font-size: 0.88rem !important;
        }

        .streamlit-expanderContent {
            background-color: #1A1A18 !important;
            border: 1px solid var(--claude-border) !important;
            border-top: none !important;
            border-bottom-left-radius: 10px !important;
            border-bottom-right-radius: 10px !important;
        }

        /* Streamlit Bottom Chat Input Integration */
        div[data-testid="stChatInput"] {
            background-color: transparent !important;
        }

        div[data-testid="stChatInput"] > div {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 18px !important;
            box-shadow: var(--claude-shadow-lg) !important;
            color: var(--claude-text) !important;
        }

        div[data-testid="stChatInput"] > div:focus-within {
            border-color: var(--claude-border-hover) !important;
        }

        div[data-testid="stChatInput"] textarea {
            color: var(--claude-text) !important;
            font-size: 0.95rem !important;
        }

        div[data-testid="stChatInput"] button {
            color: var(--claude-coral) !important;
        }

        /* New Model Pill */
        .new-pill {
            background: #2563EB;
            color: #FFFFFF;
            font-size: 0.65rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 6px;
            letter-spacing: 0.04em;
            margin-left: 6px;
            vertical-align: middle;
        }

        /* Error Diagnostic Card */
        .claude-error-card {
            background-color: #261414;
            border: 1px solid #7F1D1D;
            border-left: 4px solid #EF4444;
            border-radius: 12px;
            padding: 16px 18px;
            margin: 14px 0;
        }

        .claude-error-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
        }

        .claude-error-title {
            font-weight: 700;
            font-size: 0.95rem;
            color: #F87171;
        }

        .claude-error-code {
            background: #450A0A;
            color: #FCA5A5;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-family: monospace;
            font-weight: 700;
        }

        .claude-error-body {
            font-size: 0.86rem;
            color: #FECACA;
            line-height: 1.5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
