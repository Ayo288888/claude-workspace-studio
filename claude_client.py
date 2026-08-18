import os
import re
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

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
        "input_rate": 3.0,
        "output_rate": 15.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
    "Claude 3.5 Sonnet": {
        "id": "claude-3-5-sonnet-20241022",
        "badge": None,
        "tagline": "Industry-leading intelligence and speed",
        "pricing": "Input $3/MTok • Output $15/MTok",
        "input_rate": 3.0,
        "output_rate": 15.0,
        "supports_thinking": False,
        "max_output_tokens": 8192
    },
    "Claude 3.5 Haiku": {
        "id": "claude-3-5-haiku-20241022",
        "badge": None,
        "tagline": "Lightning-fast low latency responses",
        "pricing": "Input $0.80/MTok • Output $4/MTok",
        "input_rate": 0.80,
        "output_rate": 4.0,
        "supports_thinking": False,
        "max_output_tokens": 8192
    },
    "Claude 3 Opus": {
        "id": "claude-3-opus-20240229",
        "badge": None,
        "tagline": "Deep writing, synthesis & analysis",
        "pricing": "Input $15/MTok • Output $75/MTok",
        "input_rate": 15.0,
        "output_rate": 75.0,
        "supports_thinking": False,
        "max_output_tokens": 4096
    },
    "Opus 5": {
        "id": "claude-opus-5",
        "badge": "New",
        "tagline": "Flagship model for the hardest problems",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "input_rate": 10.0,
        "output_rate": 50.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
    "Sonnet 5": {
        "id": "claude-sonnet-5",
        "badge": None,
        "tagline": "Balanced speed, cost, and intelligence",
        "pricing": "Input $2/MTok • Output $10/MTok",
        "input_rate": 2.0,
        "output_rate": 10.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
    "Fable 5": {
        "id": "claude-fable-5",
        "badge": None,
        "tagline": "Powerful model for complex work & creative narrative",
        "pricing": "Input $5/MTok • Output $25/MTok",
        "input_rate": 5.0,
        "output_rate": 25.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
    "Opus 4.8": {
        "id": "claude-opus-4-8",
        "badge": None,
        "tagline": "Deep reasoning & multi-step execution",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "input_rate": 10.0,
        "output_rate": 50.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
    "Opus 4.7": {
        "id": "claude-opus-4-7",
        "badge": None,
        "tagline": "High-depth analytical processing",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "input_rate": 10.0,
        "output_rate": 50.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
    "Sonnet 4.6": {
        "id": "claude-sonnet-4-6",
        "badge": None,
        "tagline": "Fast code generation & synthesis",
        "pricing": "Input $3/MTok • Output $15/MTok",
        "input_rate": 3.0,
        "output_rate": 15.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
    "Opus 4.6": {
        "id": "claude-opus-4-6",
        "badge": None,
        "tagline": "Complex problem solving",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "input_rate": 10.0,
        "output_rate": 50.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
    "Opus 4.5": {
        "id": "claude-opus-4-5-20251101",
        "badge": None,
        "tagline": "High intelligence reasoning engine",
        "pricing": "Input $10/MTok • Output $50/MTok",
        "input_rate": 10.0,
        "output_rate": 50.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
    "Haiku 4.5": {
        "id": "claude-haiku-4-5-20251001",
        "badge": None,
        "tagline": "Ultra low-latency responses",
        "pricing": "Input $0.25/MTok • Output $1.25/MTok",
        "input_rate": 0.25,
        "output_rate": 1.25,
        "supports_thinking": False,
        "max_output_tokens": 8192
    },
    "Sonnet 4.5": {
        "id": "claude-sonnet-4-5-20250929",
        "badge": None,
        "tagline": "High performance coding & analysis",
        "pricing": "Input $3/MTok • Output $15/MTok",
        "input_rate": 3.0,
        "output_rate": 15.0,
        "supports_thinking": True,
        "max_output_tokens": 64000
    },
}

CLAUDE_MODELS = {k: v["id"] for k, v in DEFAULT_CLAUDE_MODELS.items()}
MODEL_DETAILS = DEFAULT_CLAUDE_MODELS

# Calibrated Reasoning Budgets & Max Token Limits
EFFORT_LEVELS = {
    "Low": {
        "label": "Low",
        "budget": 2048,
        "max_tokens": 16384,
        "description": "Fast generation with concise reasoning"
    },
    "Medium": {
        "label": "Medium",
        "budget": 6144,
        "max_tokens": 32768,
        "description": "Balanced step-by-step reasoning"
    },
    "High": {
        "label": "High",
        "budget": 16384,
        "max_tokens": 64000,
        "description": "Deep chain-of-thought analysis"
    }
}

SYSTEM_PRESETS = {
    "None (Default Claude)": "",
    "General Assistant": "You are Claude, a helpful, thoughtful, and articulate AI assistant created by Anthropic. Answer clearly, accurately, and with structured formatting.",
    "Fable Creative & Narrative": "You are Fable, a master storyteller, world-builder, and creative visionary. Craft deeply immersive narratives, rich dialogue, vivid prose, and evocative concepts.",
    "Architecture & Implementation Planner": "You are a Principal Software Architect. When asked for plans, designs, or technical solutions, provide thorough, step-by-step implementation plans with clear component boundaries, interfaces, database schemas, code snippets, and automated test strategies.",
    "Senior Code & Security Reviewer": "You are an elite Senior Staff Engineer and Security Auditor. Thoroughly inspect code for bugs, edge cases, vulnerabilities (OWASP), performance bottlenecks, and maintainability. Provide specific diffs, explanations, and refactored examples.",
    "Document & Policy Analyst": "You are a Lead Policy & Document Compliance Analyst. Synthesize complex documents, extract key obligations, identify risks, and produce clear executive summaries with structured tables and actionable bullet points.",
    "Custom Instructions...": "custom",
}

def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> Tuple[float, float, float]:
    """
    Computes (input_cost, output_cost, total_cost) for a message based on exact model rates.
    """
    input_rate = 3.0
    output_rate = 15.0
    
    clean_id = model_id.lower()
    for name, details in DEFAULT_CLAUDE_MODELS.items():
        if details["id"].lower() in clean_id or clean_id in details["id"].lower():
            input_rate = details.get("input_rate", 3.0)
            output_rate = details.get("output_rate", 15.0)
            break
            
    input_cost = (input_tokens * input_rate) / 1_000_000.0
    output_cost = (output_tokens * output_rate) / 1_000_000.0
    total_cost = input_cost + output_cost
    return round(input_cost, 6), round(output_cost, 6), round(total_cost, 6)

def format_cost_badge(input_tokens: int, output_tokens: int, cost: float) -> str:
    """Formats Workbench-style token and cost display string."""
    total_tokens = input_tokens + output_tokens
    if cost < 0.0001 and cost > 0:
        cost_str = "<$0.0001"
    else:
        cost_str = f"${cost:.4f}"
    return f"{total_tokens:,} tokens ({input_tokens:,} in, {output_tokens:,} out) • {cost_str}"

def extract_artifacts(text: str) -> List[Dict[str, str]]:
    """Extract code blocks, plans, and documents as inspectable artifacts."""
    if not isinstance(text, str):
        return []
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
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Streams response from Claude and computes token usage & costs.
        Ensures ample max_tokens headroom so thinking never consumes all output capacity.
        """
        if not self.client:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=500,
                error_type="DEPENDENCY_MISSING",
                message="Anthropic Python SDK is not installed in the current environment."
            )

        # Clean messages history
        clean_messages = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role in ["user", "assistant"]:
                if isinstance(content, list) and content:
                    clean_messages.append({"role": role, "content": content})
                elif content and str(content).strip():
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
        default_max = effort_config.get("max_tokens", 32768)

        model_meta = MODEL_DETAILS.get(model_name, {})
        supports_thinking = model_meta.get("supports_thinking", False) or "3-7" in model_id or "opus-4" in model_id or "5" in model_id

        # Calculate safe max_tokens
        if supports_thinking:
            # Thinking requires max_tokens strictly greater than budget with generous output room
            actual_max_tokens = max(max_tokens or default_max, budget + 16384)
            # Cap at model limit
            model_limit = model_meta.get("max_output_tokens", 64000)
            actual_max_tokens = min(actual_max_tokens, model_limit)
        else:
            actual_max_tokens = min(max_tokens or 8192, model_meta.get("max_output_tokens", 8192))

        kwargs: Dict[str, Any] = {
            "model": model_id,
            "max_tokens": actual_max_tokens,
            "messages": clean_messages,
        }

        if system and system.strip():
            kwargs["system"] = system.strip()

        if supports_thinking and budget > 0:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget
            }
            kwargs["temperature"] = 1.0
        else:
            kwargs["temperature"] = temperature

        input_tokens = 0
        output_tokens = 0

        try:
            with self.client.messages.stream(**kwargs) as stream:
                for event in stream:
                    if event.type == "message_start":
                        if hasattr(event, "message") and hasattr(event.message, "usage"):
                            input_tokens = getattr(event.message.usage, "input_tokens", 0)
                    elif event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "thinking_delta":
                            yield {"type": "thinking", "delta": delta.thinking}
                        elif delta.type == "text_delta":
                            yield {"type": "text", "delta": delta.text}
                    elif event.type == "message_delta":
                        if hasattr(event, "usage") and event.usage:
                            output_tokens = getattr(event.usage, "output_tokens", output_tokens)

                # Get final usage stats
                try:
                    final_msg = stream.get_final_message()
                    if hasattr(final_msg, "usage"):
                        input_tokens = getattr(final_msg.usage, "input_tokens", input_tokens)
                        output_tokens = getattr(final_msg.usage, "output_tokens", output_tokens)
                except Exception:
                    pass

                in_c, out_c, total_c = calculate_cost(model_id, input_tokens, output_tokens)
                yield {
                    "type": "usage_summary",
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "cost": total_c,
                    "badge": format_cost_badge(input_tokens, output_tokens, total_c)
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
            if "thinking" in str(e).lower() and "thinking" in kwargs:
                del kwargs["thinking"]
                kwargs["temperature"] = temperature
                kwargs["max_tokens"] = 8192
                try:
                    with self.client.messages.stream(**kwargs) as retry_stream:
                        for event in retry_stream:
                            if event.type == "message_start":
                                if hasattr(event, "message") and hasattr(event.message, "usage"):
                                    input_tokens = getattr(event.message.usage, "input_tokens", 0)
                            elif event.type == "content_block_delta":
                                delta = event.delta
                                if delta.type == "text_delta":
                                    yield {"type": "text", "delta": delta.text}
                            elif event.type == "message_delta":
                                if hasattr(event, "usage") and event.usage:
                                    output_tokens = getattr(event.usage, "output_tokens", output_tokens)
                        
                        try:
                            final_msg = retry_stream.get_final_message()
                            if hasattr(final_msg, "usage"):
                                input_tokens = getattr(final_msg.usage, "input_tokens", input_tokens)
                                output_tokens = getattr(final_msg.usage, "output_tokens", output_tokens)
                        except Exception:
                            pass
                            
                        in_c, out_c, total_c = calculate_cost(model_id, input_tokens, output_tokens)
                        yield {
                            "type": "usage_summary",
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": input_tokens + output_tokens,
                            "cost": total_c,
                            "badge": format_cost_badge(input_tokens, output_tokens, total_c)
                        }
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
