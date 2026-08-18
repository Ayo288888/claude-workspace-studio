import os
import re
from typing import Any, Dict, Generator, List, Optional

# Custom structured error class for front-end rendering
class ClaudeModelError(Exception):
    def __init__(self, model_name: str, model_id: str, status_code: Optional[int], error_type: str, message: str):
        self.model_name = model_name
        self.model_id = model_id
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        super().__init__(f"[{status_code or 'ERROR'}] {model_name} ({model_id}): {message}")

CLAUDE_MODELS = {
    "Opus 5": "claude-opus-5",
    "Sonnet 5": "claude-sonnet-5",
    "Fable 5": "claude-fable-5",
    "Opus 4.8": "claude-opus-4-8",
    "Opus 4.7": "claude-opus-4-7",
    "Sonnet 4.6": "claude-sonnet-4-6",
    "Opus 4.6": "claude-opus-4-6",
    "Opus 4.5": "claude-opus-4-5",
    "Haiku 4.5": "claude-haiku-4-5",
    "Sonnet 4.5": "claude-sonnet-4-5",
}

MODEL_DETAILS = {
    "Opus 5": {
        "id": "claude-opus-5",
        "badge": "New",
        "tagline": "Flagship model for the hardest problems",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "supports_thinking": True,
    },
    "Sonnet 5": {
        "id": "claude-sonnet-5",
        "badge": None,
        "tagline": "Balanced speed, cost, and intelligence",
        "pricing": "Input $2/MTok • Output $10/MTok",
        "supports_thinking": True,
    },
    "Fable 5": {
        "id": "claude-fable-5",
        "badge": None,
        "tagline": "Powerful model for complex work & creative narrative",
        "pricing": "Input $5/MTok • Output $25/MTok",
        "supports_thinking": True,
    },
    "Opus 4.8": {
        "id": "claude-opus-4-8",
        "badge": None,
        "tagline": "Deep reasoning & multi-step execution",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "supports_thinking": True,
    },
    "Opus 4.7": {
        "id": "claude-opus-4-7",
        "badge": None,
        "tagline": "High-depth analytical processing",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "supports_thinking": True,
    },
    "Sonnet 4.6": {
        "id": "claude-sonnet-4-6",
        "badge": None,
        "tagline": "Fast code generation & synthesis",
        "pricing": "Input $3/MTok • Output $15/MTok",
        "supports_thinking": True,
    },
    "Opus 4.6": {
        "id": "claude-opus-4-6",
        "badge": None,
        "tagline": "Complex problem solving",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "supports_thinking": True,
    },
    "Opus 4.5": {
        "id": "claude-opus-4-5",
        "badge": None,
        "tagline": "High intelligence reasoning engine",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "supports_thinking": True,
    },
    "Haiku 4.5": {
        "id": "claude-haiku-4-5",
        "badge": None,
        "tagline": "Lightning-fast low latency responses",
        "pricing": "Input $0.25/MTok • Output $1.25/MTok",
        "supports_thinking": False,
    },
    "Sonnet 4.5": {
        "id": "claude-sonnet-4-5",
        "badge": None,
        "tagline": "High performance coding & analysis",
        "pricing": "Input $3/MTok • Output $15/MTok",
        "supports_thinking": True,
    },
}

EFFORT_LEVELS = {
    "Low": {
        "label": "Low",
        "budget": 2048,
        "description": "Fast generation with concise reasoning"
    },
    "Medium": {
        "label": "Medium",
        "budget": 8192,
        "description": "Balanced step-by-step reasoning"
    },
    "High": {
        "label": "High",
        "budget": 24576,
        "description": "Deep chain-of-thought analysis"
    }
}

SYSTEM_PRESETS = {
    "General Assistant": "You are Claude, a helpful, thoughtful, and articulate AI assistant created by Anthropic. Answer clearly, accurately, and with structured formatting.",
    "Fable Creative & Narrative": "You are Fable, a master storyteller, world-builder, and creative visionary. Craft deeply immersive narratives, rich dialogue, vivid prose, and evocative concepts.",
    "Architecture & Implementation Planner": "You are a Principal Software Architect. When asked for plans, designs, or technical solutions, provide thorough, step-by-step implementation plans with clear component boundaries, interfaces, database schemas, code snippets, and automated test strategies.",
    "Senior Code & Security Reviewer": "You are an elite Senior Staff Engineer and Security Auditor. Thoroughly inspect code for bugs, edge cases, vulnerabilities (OWASP), performance bottlenecks, and maintainability. Provide specific diffs, explanations, and refactored examples.",
    "Document & Policy Analyst": "You are a Lead Policy & Document Compliance Analyst. Synthesize complex documents, extract key obligations, identify risks, and produce clear executive summaries with structured tables and actionable bullet points.",
}

def extract_artifacts(text: str) -> List[Dict[str, str]]:
    """Extract code blocks, plans, and documents as inspectable artifacts."""
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
    def __init__(self, api_key: str):
        if not api_key or not api_key.strip():
            raise ClaudeModelError(
                model_name="Client Authentication",
                model_id="auth",
                status_code=401,
                error_type="AUTHENTICATION_REQUIRED",
                message="No Anthropic API key provided. Please configure your API key in the sidebar or settings."
            )
        self.api_key = api_key.strip()
        try:
            import anthropic
            self._anthropic = anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            self._anthropic = None
            self.client = None

    def stream_chat(
        self,
        model_name: str,
        model_id: str,
        messages: List[Dict[str, Any]],
        system: str = "",
        effort_level: str = "Medium",
        max_tokens: int = 8192,
        temperature: float = 1.0,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Streams response from Claude directly without silent fallbacks.
        If the model or API fails, yields/raises a structured ClaudeModelError.
        """
        if not self.client:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=500,
                error_type="DEPENDENCY_MISSING",
                message="Anthropic Python SDK is not installed in the current environment."
            )

        effort_config = EFFORT_LEVELS.get(effort_level, EFFORT_LEVELS["Medium"])
        budget = effort_config["budget"]

        kwargs: Dict[str, Any] = {
            "model": model_id,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system

        # Configure Extended Thinking if supported and budget > 0
        model_meta = MODEL_DETAILS.get(model_name, {})
        if model_meta.get("supports_thinking", False) and budget > 0:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": min(budget, max_tokens - 1000)
            }
            # When thinking is enabled, Anthropic requires temperature=1.0
            kwargs["temperature"] = 1.0
        else:
            kwargs["temperature"] = temperature

        try:
            with self.client.messages.stream(**kwargs) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "thinking_delta":
                            yield {"type": "thinking", "delta": delta.thinking}
                        elif delta.type == "text_delta":
                            yield {"type": "text", "delta": delta.text}
                    elif event.type == "message_delta":
                        if hasattr(event, "usage") and event.usage:
                            yield {
                                "type": "usage",
                                "output_tokens": getattr(event.usage, "output_tokens", 0)
                            }
        except self._anthropic.NotFoundError as e:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=404,
                error_type="MODEL_NOT_FOUND",
                message=f"The model '{model_id}' was not found or is not enabled for your API account: {str(e)}"
            )
        except self._anthropic.AuthenticationError as e:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=401,
                error_type="AUTHENTICATION_FAILED",
                message=f"Invalid Anthropic API Key or unauthorized request: {str(e)}"
            )
        except self._anthropic.RateLimitError as e:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=429,
                error_type="RATE_LIMIT_EXCEEDED",
                message=f"Rate limit or token quota exceeded on model '{model_id}': {str(e)}"
            )
        except self._anthropic.PermissionDeniedError as e:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=403,
                error_type="PERMISSION_DENIED",
                message=f"Access to model '{model_id}' is restricted or requires upgraded account tier: {str(e)}"
            )
        except self._anthropic.APIStatusError as e:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=getattr(e, "status_code", 500),
                error_type="API_STATUS_ERROR",
                message=f"Anthropic API returned status {getattr(e, 'status_code', 'Error')}: {str(e)}"
            )
        except Exception as e:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=500,
                error_type="EXECUTION_FAILED",
                message=f"Failed to execute model '{model_id}': {str(e)}"
            )
