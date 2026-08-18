import os
import re
from typing import Any, Dict, Generator, List, Optional
import anthropic

CLAUDE_MODELS = {
    "Claude 3.7 Sonnet (Hybrid Reasoning & Coding)": "claude-3-7-sonnet-20250219",
    "Claude 3.5 Sonnet (Fast & High Intelligence)": "claude-3-5-sonnet-20241022",
    "Claude 3.5 Haiku (Lightning Fast & Cheap)": "claude-3-5-haiku-20241022",
    "Claude 3 Opus (Deep Writing & Complex Analysis)": "claude-3-opus-20240229",
}

SYSTEM_PRESETS = {
    "General Assistant": "You are Claude, a helpful, thoughtful, and articulate AI assistant created by Anthropic. Answer clearly, accurately, and with structured formatting.",
    "Architecture & Implementation Planner": "You are a Principal Software Architect. When asked for plans, designs, or technical solutions, provide thorough, step-by-step implementation plans with clear component boundaries, interfaces, database schemas, code snippets, and automated test strategies. Always follow DRY, YAGNI, and TDD principles.",
    "Senior Code & Security Reviewer": "You are an elite Senior Staff Engineer and Security Auditor. Thoroughly inspect code for bugs, edge cases, vulnerabilities (OWASP), performance bottlenecks, and maintainability. Provide specific diffs, explanations, and refactored examples.",
    "Document & Policy Analyst": "You are a Lead Policy & Document Compliance Analyst. Synthesize complex documents, extract key obligations, identify risks, and produce clear executive summaries with structured tables and actionable bullet points.",
}

def extract_artifacts(text: str) -> List[Dict[str, str]]:
    """Extract code blocks, plans, and diagrams as inspectable artifacts."""
    pattern = r"```([a-zA-Z0-9_\-\+\.]*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    artifacts = []
    for i, (lang, code) in enumerate(matches):
        lang_clean = lang.strip() or "text"
        title = f"Artifact {i+1} ({lang_clean})"
        artifacts.append({
            "id": f"artifact_{i+1}",
            "title": title,
            "language": lang_clean,
            "code": code.strip()
        })
    return artifacts

class ClaudeEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError("Anthropic API Key is required.")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def stream_chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        system: str = "",
        thinking_budget: int = 0,
        max_tokens: int = 4096,
        temperature: float = 1.0,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Streams response from Claude, supporting Claude 3.7 Extended Thinking.
        Yields dicts of type:
        {"type": "thinking", "delta": str} or {"type": "text", "delta": str} or {"type": "usage", "input_tokens": int, "output_tokens": int}
        """
        kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        # Extended thinking is only valid on Claude 3.7 Sonnet
        if "3-7" in model and thinking_budget >= 1024:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget
            }
            # Claude API requires max_tokens > budget_tokens
            kwargs["max_tokens"] = max(max_tokens, thinking_budget + 2048)
            # Thinking requires temperature to be omitted or set to 1.0
        else:
            kwargs["temperature"] = temperature

        with self.client.messages.stream(**kwargs) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "thinking_delta":
                        yield {"type": "thinking", "delta": delta.thinking}
                    elif delta.type == "text_delta":
                        yield {"type": "text", "delta": delta.text}
            
            final_message = stream.get_final_message()
            if hasattr(final_message, "usage"):
                yield {
                    "type": "usage",
                    "input_tokens": getattr(final_message.usage, "input_tokens", 0),
                    "output_tokens": getattr(final_message.usage, "output_tokens", 0)
                }

    def generate_title(self, prompt: str) -> str:
        """Generate a short 3-5 word title for a conversation."""
        try:
            res = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=25,
                system="Summarize the user's initial prompt into a clean 3 to 5 word title for a conversation list. Output only the title, no punctuation, no quotes.",
                messages=[{"role": "user", "content": prompt[:300]}]
            )
            title = res.content[0].text.strip()
            return title if title else "New Conversation"
        except Exception:
            return prompt[:30] + ("..." if len(prompt) > 30 else "")
