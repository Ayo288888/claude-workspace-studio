import streamlit as st

def apply_claude_styles():
    st.markdown(
        """
        <style>
        /* Claude.ai Core Color Palette & Typography */
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --claude-bg: #FAF9F5;
            --claude-sidebar: #F3F0E6;
            --claude-card: #FFFFFF;
            --claude-border: #E5E0D8;
            --claude-text: #2C2825;
            --claude-muted: #736E65;
            --claude-coral: #DA7756;
            --claude-coral-hover: #C85B38;
            --claude-coral-light: #FDF4F0;
            --claude-badge-blue: #1D4ED8;
            --claude-badge-bg: #EFF6FF;
        }

        /* App Background */
        .stApp {
            background-color: var(--claude-bg);
            color: var(--claude-text);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: var(--claude-sidebar) !important;
            border-right: 1px solid var(--claude-border) !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
            gap: 0.5rem;
        }

        /* Claude.ai Hero Typography */
        .claude-hero-container {
            text-align: center;
            max-width: 720px;
            margin: 40px auto 25px auto;
        }

        .claude-spark-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: var(--claude-coral-light);
            color: var(--claude-coral);
            font-size: 24px;
            margin-bottom: 16px;
        }

        .claude-hero-title {
            font-family: 'Instrument Serif', Georgia, serif;
            font-size: 2.75rem;
            font-weight: 400;
            color: var(--claude-text);
            line-height: 1.15;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }

        .claude-hero-subtitle {
            font-size: 1rem;
            color: var(--claude-muted);
            font-weight: 400;
        }

        /* Quick Starter Cards (2x2 Grid) */
        .starter-card-container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            max-width: 740px;
            margin: 24px auto 30px auto;
        }

        .starter-card {
            background: var(--claude-card);
            border: 1px solid var(--claude-border);
            border-radius: 14px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            text-align: left;
        }

        .starter-card:hover {
            border-color: var(--claude-coral);
            box-shadow: 0 4px 16px rgba(218, 119, 86, 0.08);
            transform: translateY(-1px);
        }

        .starter-card-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--claude-text);
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .starter-card-desc {
            font-size: 0.82rem;
            color: var(--claude-muted);
            line-height: 1.4;
        }

        /* Claude Input Container */
        .claude-prompt-card {
            background: var(--claude-card);
            border: 1px solid var(--claude-border);
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
            margin: 0 auto;
            max-width: 760px;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .claude-prompt-card:focus-within {
            border-color: var(--claude-coral);
            box-shadow: 0 6px 24px rgba(218, 119, 86, 0.12);
        }

        /* Buttons */
        .stButton > button {
            border-radius: 10px;
            border: 1px solid var(--claude-border);
            background-color: var(--claude-card);
            color: var(--claude-text);
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            border-color: var(--claude-coral);
            color: var(--claude-coral);
            background-color: var(--claude-coral-light);
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

        /* Model Badge Pill */
        .model-pill-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--claude-sidebar);
            border: 1px solid var(--claude-border);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--claude-text);
        }

        .new-badge {
            background: var(--claude-badge-bg);
            color: var(--claude-badge-blue);
            font-size: 0.65rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Front-End Error Diagnostic Card */
        .claude-error-card {
            background-color: #FEF2F2;
            border: 1px solid #FCA5A5;
            border-left: 4px solid #EF4444;
            border-radius: 12px;
            padding: 16px;
            margin: 16px 0;
            color: #991B1B;
        }

        .claude-error-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 6px;
        }

        .claude-error-code {
            background: #FEE2E2;
            color: #B91C1C;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-family: monospace;
            font-weight: 700;
        }

        .claude-error-body {
            font-size: 0.88rem;
            color: #7F1D1D;
            line-height: 1.5;
        }

        /* Reasoning / Extended Thinking Panel */
        .thinking-panel {
            background: #F9F8F5;
            border: 1px solid var(--claude-border);
            border-radius: 10px;
            padding: 12px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.82rem;
            color: var(--claude-muted);
            margin-bottom: 12px;
            line-height: 1.5;
            max-height: 300px;
            overflow-y: auto;
        }

        /* Hide Streamlit Default Header and Footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {background: transparent;}
        </style>
        """,
        unsafe_allow_html=True
    )
