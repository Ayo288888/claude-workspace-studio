# Claude Workspace Studio (Streamlit Web UI)

A high-fidelity Streamlit application that provides the authentic **Claude Web UI** experience powered directly by the **Anthropic API** (consuming your $100 Anthropic Console credit).

---

## 🌟 Features

- **Authentic Claude.ai Aesthetics**: Styled with Anthropic's signature warm stone and terracotta `#DA7756` color palette, clean typography, and elegant message cards.
- **Claude 3.7 Sonnet Hybrid Extended Thinking**: Live stream of Claude's internal reasoning process into a collapsible, monospace thinking panel with configurable token budget.
- **Model Switching**:
  - `Claude 3.7 Sonnet` (Hybrid reasoning, planning & coding)
  - `Claude 3.5 Sonnet` (Fast & high intelligence)
  - `Claude 3.5 Haiku` (Lightning fast & ultra low cost)
  - `Claude 3 Opus` (Deep writing & synthesis)
- **Persistent SQLite Conversation History**: Chat sessions are saved in `claude_chat.db` with auto-titling, past session switching, and deletion.
- **Multimodal File Attachments**: Upload Python files, TypeScript/JSON code, Markdown documents, PDFs (with `pdfplumber`), DOCX files, and images for Claude to review, refactor, or summarize.
- **Artifacts Side Drawer**: Automatically identifies code blocks, architecture plans, and markdown files in Claude's output and renders them with 1-click copy & download.
- **Role Presets**: Pre-configured system personas for *Architecture & Implementation Planner*, *Senior Code & Security Reviewer*, *Document & Policy Analyst*, and *General Assistant*.

---

## 🚀 How to Run

### Option 1: 1-Click Batch Runner (Windows)
Double-click `run_app.bat` in the project root directory.

### Option 2: Terminal Command
```bash
streamlit run app.py
```
Open your browser at **`http://localhost:8501`**.

---

## 🔑 API Key Setup

1. You can paste your key directly into the sidebar in the Web UI: `sk-ant-api03-...`
2. Or create a `.env` file in the project root:
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   ```
