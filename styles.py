import streamlit as st

def apply_claude_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global Reset & Claude Colors */
        :root {
            --claude-bg: #FAF9F5;
            --claude-sidebar: #F3F0E6;
            --claude-card: #FFFFFF;
            --claude-border: #E5E0D8;
            --claude-border-hover: #D0C9BE;
            --claude-text: #2C2825;
            --claude-muted: #736E65;
            --claude-coral: #DA7756;
            --claude-coral-hover: #C85B38;
            --claude-coral-light: #FDF4F0;
            --claude-badge-blue: #2563EB;
            --claude-badge-bg: #EFF6FF;
            --claude-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
            --claude-shadow-lg: 0 8px 30px rgba(0, 0, 0, 0.06);
        }

        /* Base Application Layout */
        .stApp {
            background-color: var(--claude-bg) !important;
            color: var(--claude-text) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* Top Header & Chrome Cleaner */
        header[data-testid="stHeader"] {
            background: transparent !important;
            border-bottom: none !important;
        }
        #MainMenu, footer, .stDeployButton {
            display: none !important;
        }

        /* Sidebar Styling - Polished Claude Layout */
        section[data-testid="stSidebar"] {
            background-color: var(--claude-sidebar) !important;
            border-right: 1px solid var(--claude-border) !important;
            padding: 1.5rem 1rem !important;
        }

        section[data-testid="stSidebar"] hr {
            border-color: var(--claude-border) !important;
            margin: 1.2rem 0 !important;
        }

        .sidebar-section-title {
            font-size: 0.76rem;
            font-weight: 700;
            color: var(--claude-muted);
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 0.5rem;
            margin-top: 0.4rem;
        }

        /* Form Inputs & Selectboxes Everywhere */
        div[data-baseweb="select"] > div {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 12px !important;
            color: var(--claude-text) !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            box-shadow: var(--claude-shadow) !important;
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
            border-radius: 8px !important;
            margin: 2px 4px !important;
        }

        li[role="option"]:hover, li[aria-selected="true"] {
            background-color: var(--claude-coral-light) !important;
            color: var(--claude-coral) !important;
        }

        /* Text Inputs with Password Manager Shield */
        div[data-baseweb="input"] > div {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 12px !important;
            color: var(--claude-text) !important;
        }

        input {
            color: var(--claude-text) !important;
        }

        /* Security Card & Badge */
        .security-badge-container {
            background: #F0FDF4;
            border: 1px solid #BBF7D0;
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }

        .security-badge-header {
            font-size: 0.82rem;
            font-weight: 700;
            color: #166534;
            margin-bottom: 3px;
        }

        .security-badge-sub {
            font-size: 0.74rem;
            color: #15803D;
            line-height: 1.35;
        }

        /* Workbench Token Cost Badge */
        .cost-token-badge {
            display: inline-flex;
            align-items: center;
            background-color: var(--claude-sidebar);
            border: 1px solid var(--claude-border);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.76rem;
            font-family: 'Consolas', 'Courier New', monospace;
            color: var(--claude-muted);
            margin-top: 8px;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 12px !important;
            border: 1px solid var(--claude-border) !important;
            background-color: var(--claude-card) !important;
            color: var(--claude-text) !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            padding: 0.5rem 1rem !important;
            box-shadow: var(--claude-shadow) !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        .stButton > button:hover {
            border-color: var(--claude-coral) !important;
            color: var(--claude-coral) !important;
            background-color: var(--claude-coral-light) !important;
            transform: translateY(-1px) !important;
        }

        .stButton > button[kind="primary"] {
            background-color: var(--claude-coral) !important;
            border-color: var(--claude-coral) !important;
            color: #FFFFFF !important;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: var(--claude-coral-hover) !important;
            border-color: var(--claude-coral-hover) !important;
            color: #FFFFFF !important;
        }

        /* Hero Typography */
        .claude-hero-wrapper {
            text-align: center;
            max-width: 760px;
            margin: 2.5rem auto 1.5rem auto;
            padding: 0 1rem;
        }

        .claude-title {
            font-family: 'Instrument Serif', Georgia, serif;
            font-size: 3.25rem;
            font-weight: 400;
            color: var(--claude-text);
            line-height: 1.1;
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
        }

        .claude-subtitle {
            font-size: 1.05rem;
            color: var(--claude-muted);
            font-weight: 400;
        }

        /* Chat Input Container Integration */
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
            border-color: var(--claude-coral) !important;
            box-shadow: 0 6px 24px rgba(218, 119, 86, 0.14) !important;
        }

        div[data-testid="stChatInput"] textarea {
            color: var(--claude-text) !important;
            font-size: 0.95rem !important;
        }

        div[data-testid="stChatInput"] button {
            color: var(--claude-coral) !important;
        }

        /* Inline Chat Attachment Popover / Button */
        div[data-testid="stPopover"] > button {
            border-radius: 12px !important;
            border: 1px solid var(--claude-border) !important;
            background-color: var(--claude-card) !important;
            color: var(--claude-muted) !important;
            font-weight: 600 !important;
            padding: 0.45rem 0.75rem !important;
            box-shadow: var(--claude-shadow) !important;
        }

        div[data-testid="stPopover"] > button:hover {
            border-color: var(--claude-coral) !important;
            color: var(--claude-coral) !important;
        }

        /* File Attachment Chips */
        .attachment-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: var(--claude-card);
            border: 1px solid var(--claude-border);
            border-radius: 20px;
            padding: 4px 12px;
            font-size: 0.8rem;
            color: var(--claude-text);
            margin: 4px 4px 8px 0;
            box-shadow: var(--claude-shadow);
        }

        /* Chat Message Cards */
        .stChatMessage {
            background-color: transparent !important;
            border-radius: 14px !important;
            padding: 1rem 1.25rem !important;
            margin-bottom: 0.75rem !important;
        }

        div[data-testid="stChatMessage"]:nth-child(even) {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            box-shadow: var(--claude-shadow) !important;
        }

        /* Expanders / Artifacts */
        .streamlit-expanderHeader {
            background-color: var(--claude-sidebar) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            color: var(--claude-text) !important;
        }

        .streamlit-expanderContent {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-top: none !important;
            border-bottom-left-radius: 10px !important;
            border-bottom-right-radius: 10px !important;
        }

        /* Model Badge / Pill */
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

        /* Front-End Error Diagnostic Card */
        .claude-error-card {
            background-color: #FEF2F2;
            border: 1px solid #FCA5A5;
            border-left: 5px solid #EF4444;
            border-radius: 14px;
            padding: 18px 20px;
            margin: 16px 0;
            box-shadow: 0 4px 16px rgba(239, 68, 68, 0.08);
        }

        .claude-error-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }

        .claude-error-title {
            font-weight: 700;
            font-size: 1rem;
            color: #991B1B;
        }

        .claude-error-code {
            background: #FEE2E2;
            color: #B91C1C;
            padding: 3px 10px;
            border-radius: 8px;
            font-size: 0.75rem;
            font-family: monospace;
            font-weight: 700;
            border: 1px solid #FECACA;
        }

        .claude-error-body {
            font-size: 0.9rem;
            color: #7F1D1D;
            line-height: 1.55;
        }

        /* Extended Thinking Monospace Panel */
        .thinking-panel {
            background: #F9F8F5;
            border: 1px solid var(--claude-border);
            border-radius: 10px;
            padding: 14px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.83rem;
            color: var(--claude-muted);
            line-height: 1.55;
            max-height: 320px;
            overflow-y: auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
