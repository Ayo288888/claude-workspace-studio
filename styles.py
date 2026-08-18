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
            --claude-card: #20201D;
            --claude-card-hover: #282824;
            --claude-border: #2D2D29;
            --claude-border-hover: #3E3E38;
            --claude-btn-bg: #1E1E1C;
            --claude-btn-border: #383834;
            --claude-text: #ECEAE4;
            --claude-muted: #8E8A80;
            --claude-coral: #DA7756;
            --claude-coral-hover: #E08567;
            --claude-blue-btn: #0284C7;
            --claude-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            --claude-shadow-lg: 0 12px 40px rgba(0, 0, 0, 0.4);
        }

        /* Base Application Layout */
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
            border-radius: 8px !important;
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
            background-color: rgba(218, 119, 86, 0.15) !important;
            color: var(--claude-coral) !important;
        }

        div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 8px !important;
            color: var(--claude-text) !important;
        }

        input, textarea {
            color: var(--claude-text) !important;
        }

        /* Standard Buttons */
        .stButton > button {
            border-radius: 8px !important;
            border: 1px solid var(--claude-btn-border) !important;
            background-color: var(--claude-btn-bg) !important;
            color: var(--claude-text) !important;
            font-weight: 500 !important;
            font-size: 0.86rem !important;
            padding: 0.4rem 0.85rem !important;
            transition: all 0.15s ease !important;
        }

        .stButton > button:hover {
            border-color: var(--claude-border-hover) !important;
            background-color: var(--claude-card-hover) !important;
            color: #FFFFFF !important;
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

        /* Popover Trigger Buttons (Exact Replica of Screenshot) */
        div[data-testid="stPopover"] > button {
            background-color: var(--claude-btn-bg) !important;
            border: 1px solid var(--claude-btn-border) !important;
            border-radius: 8px !important;
            color: var(--claude-text) !important;
            font-size: 0.84rem !important;
            font-weight: 500 !important;
            padding: 0.4rem 0.85rem !important;
            box-shadow: none !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            transition: all 0.15s ease !important;
        }

        div[data-testid="stPopover"] > button:hover {
            background-color: var(--claude-card-hover) !important;
            border-color: #4E4E48 !important;
            color: #FFFFFF !important;
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

        /* Attached File Thumbnail / Chip */
        .attached-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: var(--claude-btn-bg);
            border: 1px solid var(--claude-btn-border);
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 0.78rem;
            color: var(--claude-text);
            margin-right: 6px;
            margin-bottom: 6px;
        }

        /* Streamlit Bottom Chat Input Integration */
        div[data-testid="stChatInput"] {
            background-color: transparent !important;
        }

        div[data-testid="stChatInput"] > div {
            background-color: var(--claude-card) !important;
            border: 1px solid var(--claude-border) !important;
            border-radius: 16px !important;
            box-shadow: var(--claude-shadow-lg) !important;
            color: var(--claude-text) !important;
            padding: 4px 6px !important;
        }

        div[data-testid="stChatInput"] > div:focus-within {
            border-color: #4A4A44 !important;
        }

        div[data-testid="stChatInput"] textarea {
            color: var(--claude-text) !important;
            font-size: 0.95rem !important;
        }

        div[data-testid="stChatInput"] button {
            color: var(--claude-coral) !important;
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
