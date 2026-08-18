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

# Known & Documented Claude Models from Anthropic Console / Platform
DEFAULT_CLAUDE_MODELS: Dict[str, Dict[str, Any]] = {
    "Claude 3.7 Sonnet (Reasoning)": {
        "id": "claude-3-7-sonnet-20250219",
        "badge": "Recommended",
        "tagline": "Hybrid reasoning, coding & architecture",
        "pricing": "Input $3/MTok • Output $15/MTok",
        "supports_thinking": True,
    },
    "Claude 3.5 Sonnet": {
        "id": "claude-3-5-sonnet-20241022",
        "badge": None,
        "tagline": "Industry-leading intelligence and speed",
        "pricing": "Input $3/MTok • Output $15/MTok",
        "supports_thinking": False,
    },
    "Claude 3.5 Haiku": {
        "id": "claude-3-5-haiku-20241022",
        "badge": None,
        "tagline": "Lightning-fast low latency responses",
        "pricing": "Input $0.80/MTok • Output $4/MTok",
        "supports_thinking": False,
    },
    "Claude 3 Opus": {
        "id": "claude-3-opus-20240229",
        "badge": None,
        "tagline": "Deep writing, synthesis & analysis",
        "pricing": "Input $15/MTok • Output $75/MTok",
        "supports_thinking": False,
    },
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
        "id": "claude-opus-4-5-20251101",
        "badge": None,
        "tagline": "High intelligence reasoning engine",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "supports_thinking": True,
    },
    "Haiku 4.5": {
        "id": "claude-haiku-4-5-20251001",
        "badge": None,
        "tagline": "Ultra low-latency responses",
        "pricing": "Input $0.25/MTok • Output $1.25/MTok",
        "supports_thinking": False,
    },
    "Sonnet 4.5": {
        "id": "claude-sonnet-4-5-20250929",
        "badge": None,
        "tagline": "High performance coding & analysis",
        "pricing": "Input $3/MTok • Output $15/MTok",
        "supports_thinking": True,
    },
}

CLAUDE_MODELS = {k: v["id"] for k, v in DEFAULT_CLAUDE_MODELS.items()}
MODEL_DETAILS = DEFAULT_CLAUDE_MODELS

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
                message="No Anthropic API key provided. Please configure your API key in the sidebar."
            )
        self.api_key = api_key.strip()
        try:
            import anthropic
            self._anthropic = anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            self._anthropic = None
            self.client = None

    def fetch_live_models(self) -> List[Dict[str, Any]]:
        """
        Dynamically queries GET /v1/models using client.models.list()
        to return all models available for the authenticated API key.
        """
        if not self.client:
            return []
        try:
            page = self.client.models.list()
            live_models = []
            for item in page.data:
                model_id = getattr(item, "id", "")
                display_name = getattr(item, "display_name", model_id)
                capabilities = getattr(item, "capabilities", None)
                
                supports_thinking = False
                if capabilities:
                    thinking_cap = getattr(capabilities, "thinking", None)
                    if thinking_cap and getattr(thinking_cap, "supported", False):
                        supports_thinking = True
                
                live_models.append({
                    "id": model_id,
                    "display_name": display_name,
                    "supports_thinking": supports_thinking,
                })
            return live_models
        except Exception:
            return []

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
        Streams response from Claude using Anthropic Messages API.
        Validates messages and configures thinking parameters correctly.
        """
        if not self.client:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=500,
                error_type="DEPENDENCY_MISSING",
                message="Anthropic Python SDK is not installed in the current environment."
            )

        # Clean messages history (ensure valid role and non-empty content)
        clean_messages = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role in ["user", "assistant"] and content and str(content).strip():
                clean_messages.append({"role": role, "content": str(content).strip()})

        if not clean_messages:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=400,
                error_type="INVALID_MESSAGES",
                message="No valid user message to send to the Claude API."
            )

        effort_config = EFFORT_LEVELS.get(effort_level, EFFORT_LEVELS["Medium"])
        budget = effort_config["budget"]

        # Determine thinking support
        model_meta = MODEL_DETAILS.get(model_name, {})
        supports_thinking = model_meta.get("supports_thinking", False) or "3-7" in model_id or "opus-4" in model_id or "5" in model_id

        actual_max_tokens = max(max_tokens, budget + 2048) if supports_thinking else max_tokens

        kwargs: Dict[str, Any] = {
            "model": model_id,
            "max_tokens": actual_max_tokens,
            "messages": clean_messages,
        }

        if system and system.strip():
            kwargs["system"] = system.strip()

        # Configure Thinking only if model supports it
        if supports_thinking and budget > 0:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget
            }
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
                message=f"Model '{model_id}' was not found or is not enabled for your API key: {str(e)}"
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
                message=f"Access to model '{model_id}' is restricted or requires an upgraded account tier: {str(e)}"
            )
        except self._anthropic.BadRequestError as e:
            # If thinking was rejected on this model, retry cleanly without thinking parameter
            if "thinking" in str(e).lower() and "thinking" in kwargs:
                del kwargs["thinking"]
                kwargs["temperature"] = temperature
                kwargs["max_tokens"] = 4096
                try:
                    with self.client.messages.stream(**kwargs) as retry_stream:
                        for event in retry_stream:
                            if event.type == "content_block_delta":
                                delta = event.delta
                                if delta.type == "text_delta":
                                    yield {"type": "text", "delta": delta.text}
                    return
                except Exception as retry_err:
                    raise ClaudeModelError(
                        model_name=model_name,
                        model_id=model_id,
                        status_code=400,
                        error_type="BAD_REQUEST",
                        message=f"Bad request: {str(retry_err)}"
                    )
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=400,
                error_type="BAD_REQUEST",
                message=f"Bad request parameters for model '{model_id}': {str(e)}"
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
