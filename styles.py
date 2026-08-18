import streamlit as st

CLAUDE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Lora:ital,wght@0,500;0,600;1,400&display=swap');

:root {
    --claude-bg: #FAF9F5;
    --claude-surface: #F3EFEA;
    --claude-surface-card: #FFFFFF;
    --claude-sidebar: #EFECE6;
    --claude-border: #E5DFD7;
    --claude-text: #1F1E1D;
    --claude-muted: #75716B;
    --claude-terracotta: #DA7756;
    --claude-terracotta-hover: #C66343;
    --claude-accent-soft: #F9EDE8;
    --claude-code-bg: #21252B;
}

/* Light / Dark Mode support */
@media (prefers-color-scheme: dark) {
    :root {
        --claude-bg: #19191B;
        --claude-surface: #222226;
        --claude-surface-card: #2B2B30;
        --claude-sidebar: #1D1D21;
        --claude-border: #33333A;
        --claude-text: #F0EFEB;
        --claude-muted: #A3A19E;
        --claude-terracotta: #E08264;
        --claude-accent-soft: #38241D;
    }
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Top App Header */
.claude-top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    background: linear-gradient(135deg, var(--claude-surface), var(--claude-surface-card));
    border: 1px solid var(--claude-border);
    border-radius: 14px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

.claude-brand-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'Lora', serif;
    font-weight: 600;
    font-size: 1.35rem;
    color: var(--claude-terracotta);
    letter-spacing: -0.2px;
}

.claude-badge {
    background-color: var(--claude-accent-soft);
    color: var(--claude-terracotta);
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid var(--claude-border);
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: var(--claude-sidebar);
    border-right: 1px solid var(--claude-border);
}

.sidebar-header {
    font-weight: 700;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--claude-muted);
    margin: 16px 0 8px 0;
}

/* Thinking Box (Claude 3.7 Extended Reasoning) */
.thinking-box {
    background: rgba(218, 119, 86, 0.05);
    border-left: 3px solid var(--claude-terracotta);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 8px 0 16px 0;
    font-size: 0.88rem;
    line-height: 1.5;
    color: var(--claude-muted);
    font-family: 'JetBrains Mono', monospace;
}

.thinking-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 700;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--claude-terracotta);
    margin-bottom: 6px;
}

/* Artifacts View */
.artifact-card-preview {
    background-color: var(--claude-surface-card);
    border: 1px solid var(--claude-border);
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}

.artifact-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--claude-border);
}

.artifact-badge {
    background-color: var(--claude-accent-soft);
    color: var(--claude-terracotta);
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    text-transform: uppercase;
}

/* Chat Input Bar Fixes */
.stChatInput {
    border-radius: 16px !important;
}

/* Empty State Greeting */
.claude-hero {
    text-align: center;
    padding: 40px 20px;
    margin: 20px auto;
    max-width: 650px;
}
.claude-hero-title {
    font-family: 'Lora', serif;
    font-size: 2.2rem;
    font-weight: 600;
    color: var(--claude-text);
    margin-bottom: 12px;
}
.claude-hero-sub {
    font-size: 1rem;
    color: var(--claude-muted);
    line-height: 1.6;
}
.claude-prompt-card {
    background: var(--claude-surface);
    border: 1px solid var(--claude-border);
    border-radius: 12px;
    padding: 14px 16px;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9rem;
    color: var(--claude-text);
    margin-bottom: 10px;
}
.claude-prompt-card:hover {
    border-color: var(--claude-terracotta);
    background: var(--claude-accent-soft);
}
</style>
"""

def apply_claude_styles() -> None:
    st.markdown(CLAUDE_CSS, unsafe_allow_html=True)
