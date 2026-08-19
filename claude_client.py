import copy
import logging
import os
import re
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

# Set up logger for API tracking and cache verification
logger = logging.getLogger("claude_client")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Custom structured error class for front-end rendering
class ClaudeModelError(Exception):
    def __init__(self, model_name: str, model_id: str, status_code: Optional[int], error_type: str, message: str):
        self.model_name = model_name
        self.model_id = model_id
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        super().__init__(f"[{status_code or 'ERROR'}] {model_name} ({model_id}): {message}")

# =========================================================================
# PER-MODEL CONFIGURATION MAP
# Defines adaptive thinking, extended thinking budgets, dynamic max_tokens, and rates
# =========================================================================
MODEL_CONFIG: Dict[str, Dict[str, Any]] = {
    # Adaptive Thinking Models (supportsAdaptive: True)
    "claude-opus-4-7": {
        "supportsAdaptive": True,
        "supportsThinking": True,
        "defaultEffort": "high",
        "input_rate": 10.0,
        "output_rate": 50.0,
        "max_tokens": {"low": 8192, "medium": 24576, "high": 64000},
        "badge": None,
        "tagline": "High-depth analytical processing",
    },
    "claude-sonnet-4-6": {
        "supportsAdaptive": True,
        "supportsThinking": True,
        "defaultEffort": "medium",
        "input_rate": 3.0,
        "output_rate": 15.0,
        "max_tokens": {"low": 8192, "medium": 24576, "high": 64000},
        "badge": None,
        "tagline": "Fast code generation & synthesis",
    },
    "claude-3-7-sonnet-20250219": {
        "supportsAdaptive": True,
        "supportsThinking": True,
        "defaultEffort": "medium",
        "input_rate": 3.0,
        "output_rate": 15.0,
        "max_tokens": {"low": 8192, "medium": 24576, "high": 64000},
        "badge": "Recommended",
        "tagline": "Hybrid reasoning, coding & architecture",
    },
    "claude-opus-5": {
        "supportsAdaptive": True,
        "supportsThinking": True,
        "defaultEffort": "high",
        "input_rate": 10.0,
        "output_rate": 50.0,
        "max_tokens": {"low": 8192, "medium": 24576, "high": 64000},
        "badge": "New",
        "tagline": "Flagship model for the hardest problems",
    },
    "claude-sonnet-5": {
        "supportsAdaptive": True,
        "supportsThinking": True,
        "defaultEffort": "medium",
        "input_rate": 2.0,
        "output_rate": 10.0,
        "max_tokens": {"low": 8192, "medium": 24576, "high": 64000},
        "badge": None,
        "tagline": "Balanced speed, cost, and intelligence",
    },
    "claude-fable-5": {
        "supportsAdaptive": True,
        "supportsThinking": True,
        "defaultEffort": "medium",
        "input_rate": 5.0,
        "output_rate": 25.0,
        "max_tokens": {"low": 8192, "medium": 24576, "high": 64000},
        "badge": None,
        "tagline": "Powerful model for complex work & creative narrative",
    },
    "claude-opus-4-8": {
        "supportsAdaptive": True,
        "supportsThinking": True,
        "defaultEffort": "high",
        "input_rate": 10.0,
        "output_rate": 50.0,
        "max_tokens": {"low": 8192, "medium": 24576, "high": 64000},
        "badge": None,
        "tagline": "Deep reasoning & multi-step execution",
    },
    "claude-opus-4-6": {
        "supportsAdaptive": True,
        "supportsThinking": True,
        "defaultEffort": "high",
        "input_rate": 10.0,
        "output_rate": 50.0,
        "max_tokens": {"low": 8192, "medium": 24576, "high": 64000},
        "badge": None,
        "tagline": "Complex problem solving",
    },

    # Extended Thinking Only Models (supportsAdaptive: False, budget_tokens)
    "claude-opus-4-5-20251101": {
        "supportsAdaptive": False,
        "supportsThinking": True,
        "effort": "high",
        "budget_tokens": 8000,
        "input_rate": 10.0,
        "output_rate": 50.0,
        "max_tokens": {"low": 4096, "medium": 16000, "high": 32000},
        "badge": None,
        "tagline": "High intelligence reasoning engine",
    },
    "claude-opus-4-5": {
        "supportsAdaptive": False,
        "supportsThinking": True,
        "effort": "high",
        "budget_tokens": 8000,
        "input_rate": 10.0,
        "output_rate": 50.0,
        "max_tokens": {"low": 4096, "medium": 16000, "high": 32000},
        "badge": None,
        "tagline": "High intelligence reasoning engine",
    },
    "claude-sonnet-4-5-20250929": {
        "supportsAdaptive": False,
        "supportsThinking": True,
        "budget_tokens": 4000,
        "input_rate": 3.0,
        "output_rate": 15.0,
        "max_tokens": {"low": 4096, "medium": 12000, "high": 32000},
        "badge": None,
        "tagline": "High performance coding & analysis",
    },
    "claude-sonnet-4-5": {
        "supportsAdaptive": False,
        "supportsThinking": True,
        "budget_tokens": 4000,
        "input_rate": 3.0,
        "output_rate": 15.0,
        "max_tokens": {"low": 4096, "medium": 12000, "high": 32000},
        "badge": None,
        "tagline": "High performance coding & analysis",
    },

    # Non-thinking Standard Models
    "claude-3-5-sonnet-20241022": {
        "supportsAdaptive": False,
        "supportsThinking": False,
        "input_rate": 3.0,
        "output_rate": 15.0,
        "max_tokens": {"low": 2048, "medium": 4096, "high": 8192},
        "badge": None,
        "tagline": "Industry-leading intelligence and speed",
    },
    "claude-3-5-haiku-20241022": {
        "supportsAdaptive": False,
        "supportsThinking": False,
        "input_rate": 0.80,
        "output_rate": 4.0,
        "max_tokens": {"low": 2048, "medium": 4096, "high": 8192},
        "badge": None,
        "tagline": "Lightning-fast low latency responses",
    },
    "claude-haiku-4-5-20251001": {
        "supportsAdaptive": False,
        "supportsThinking": False,
        "input_rate": 0.25,
        "output_rate": 1.25,
        "max_tokens": {"low": 2048, "medium": 4096, "high": 8192},
        "badge": None,
        "tagline": "Ultra low-latency responses",
    },
    "claude-3-opus-20240229": {
        "supportsAdaptive": False,
        "supportsThinking": False,
        "input_rate": 15.0,
        "output_rate": 75.0,
        "max_tokens": {"low": 2048, "medium": 4096, "high": 4096},
        "badge": None,
        "tagline": "Deep writing, synthesis & analysis",
    },
}

# Model Display Options for UI
DEFAULT_CLAUDE_MODELS: Dict[str, Dict[str, Any]] = {
    "Claude 3.7 Sonnet (Reasoning)": {"id": "claude-3-7-sonnet-20250219", **MODEL_CONFIG["claude-3-7-sonnet-20250219"]},
    "Claude 3.5 Sonnet": {"id": "claude-3-5-sonnet-20241022", **MODEL_CONFIG["claude-3-5-sonnet-20241022"]},
    "Claude 3.5 Haiku": {"id": "claude-3-5-haiku-20241022", **MODEL_CONFIG["claude-3-5-haiku-20241022"]},
    "Claude 3 Opus": {"id": "claude-3-opus-20240229", **MODEL_CONFIG["claude-3-opus-20240229"]},
    "Opus 5": {"id": "claude-opus-5", **MODEL_CONFIG["claude-opus-5"]},
    "Sonnet 5": {"id": "claude-sonnet-5", **MODEL_CONFIG["claude-sonnet-5"]},
    "Fable 5": {"id": "claude-fable-5", **MODEL_CONFIG["claude-fable-5"]},
    "Opus 4.8": {"id": "claude-opus-4-8", **MODEL_CONFIG["claude-opus-4-8"]},
    "Opus 4.7": {"id": "claude-opus-4-7", **MODEL_CONFIG["claude-opus-4-7"]},
    "Sonnet 4.6": {"id": "claude-sonnet-4-6", **MODEL_CONFIG["claude-sonnet-4-6"]},
    "Opus 4.6": {"id": "claude-opus-4-6", **MODEL_CONFIG["claude-opus-4-6"]},
    "Opus 4.5": {"id": "claude-opus-4-5-20251101", **MODEL_CONFIG["claude-opus-4-5-20251101"]},
    "Haiku 4.5": {"id": "claude-haiku-4-5-20251001", **MODEL_CONFIG["claude-haiku-4-5-20251001"]},
    "Sonnet 4.5": {"id": "claude-sonnet-4-5-20250929", **MODEL_CONFIG["claude-sonnet-4-5-20250929"]},
}

CLAUDE_MODELS = {k: v["id"] for k, v in DEFAULT_CLAUDE_MODELS.items()}
MODEL_DETAILS = DEFAULT_CLAUDE_MODELS

EFFORT_LEVELS = {
    "Low": {
        "label": "Low",
        "description": "Fast generation with concise reasoning"
    },
    "Medium": {
        "label": "Medium",
        "description": "Balanced step-by-step reasoning"
    },
    "High": {
        "label": "High",
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

def get_model_config(model_id: str) -> Dict[str, Any]:
    """Retrieves config for a model ID with intelligent fallbacks."""
    clean_id = model_id.lower().strip()
    if clean_id in MODEL_CONFIG:
        return MODEL_CONFIG[clean_id]
        
    for k, v in MODEL_CONFIG.items():
        if k in clean_id or clean_id in k:
            return v
            
    # Default fallback for custom or unlisted models
    is_reasoning = any(x in clean_id for x in ["3-7", "4-6", "4-7", "4-8", "opus-5", "sonnet-5", "fable-5"])
    return {
        "supportsAdaptive": is_reasoning,
        "supportsThinking": is_reasoning,
        "defaultEffort": "medium" if is_reasoning else None,
        "input_rate": 3.0,
        "output_rate": 15.0,
        "max_tokens": {"low": 4096, "medium": 16384, "high": 64000} if is_reasoning else {"low": 2048, "medium": 4096, "high": 8192}
    }

def get_dynamic_max_tokens(model_id: str, effort_level: str) -> int:
    """Dynamically sets max_tokens based on effort level and model capability."""
    cfg = get_model_config(model_id)
    eff = effort_level.lower() if effort_level else "medium"
    if eff not in ["low", "medium", "high"]:
        eff = "medium"

    token_map = cfg.get("max_tokens", {})
    if token_map and eff in token_map:
        return token_map[eff]

    if cfg.get("supportsAdaptive") or cfg.get("supportsThinking"):
        return {"low": 8192, "medium": 24576, "high": 64000}.get(eff, 24576)
    return {"low": 2048, "medium": 4096, "high": 8192}.get(eff, 4096)

def trim_conversation_history(messages: List[Dict[str, Any]], max_turns: int = 20) -> List[Dict[str, Any]]:
    """
    Truncates conversation history when exceeding max_turns.
    Preserves initial anchor turns and most recent turns so token usage remains bounded.
    """
    if len(messages) <= max_turns:
        return messages

    # Keep initial 2 turns (context anchor) and most recent (max_turns - 3) turns
    anchor_turns = messages[:2]
    recent_turns = messages[-(max_turns - 3):]
    trimmed_indicator = {
        "role": "assistant",
        "content": "[Earlier conversation history collapsed for token optimization]"
    }
    return anchor_turns + [trimmed_indicator] + recent_turns

def apply_prompt_caching_breakpoints(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Adds cache_control: {type: 'ephemeral'} to the last message of the stable prefix
    (before the latest 1-2 turns) so repeated turns hit cache at a 90% discount.
    """
    if len(messages) < 3:
        return messages

    cached_messages = copy.deepcopy(messages)
    # Breakpoint on the last message of stable history (before recent turn)
    target_idx = len(cached_messages) - 2

    target_msg = cached_messages[target_idx]
    content = target_msg.get("content")

    if isinstance(content, str):
        target_msg["content"] = [
            {
                "type": "text",
                "text": content,
                "cache_control": {"type": "ephemeral"}
            }
        ]
    elif isinstance(content, list) and content:
        # Add cache_control to the last block of the target message
        last_block = dict(content[-1])
        last_block["cache_control"] = {"type": "ephemeral"}
        content[-1] = last_block
        target_msg["content"] = content

    return cached_messages

def calculate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0
) -> Tuple[float, float, float]:
    """
    Computes exact costs accounting for Anthropic Prompt Caching rates:
    - Normal Input: 1.0x rate
    - Cache Creation (5m TTL): 1.25x rate
    - Cache Read (Hit): 0.10x rate (90% discount!)
    - Output: 1.0x output rate
    """
    cfg = get_model_config(model_id)
    input_rate = cfg.get("input_rate", 3.0)
    output_rate = cfg.get("output_rate", 15.0)

    # Cost calculations
    normal_input_cost = (input_tokens * input_rate) / 1_000_000.0
    cache_read_cost = (cache_read_tokens * (input_rate * 0.10)) / 1_000_000.0
    cache_creation_cost = (cache_creation_tokens * (input_rate * 1.25)) / 1_000_000.0
    total_input_cost = normal_input_cost + cache_read_cost + cache_creation_cost
    
    output_cost = (output_tokens * output_rate) / 1_000_000.0
    total_cost = total_input_cost + output_cost

    return round(total_input_cost, 6), round(output_cost, 6), round(total_cost, 6)

def format_cost_badge(
    input_tokens: int,
    output_tokens: int,
    cost: float,
    cache_read_tokens: int = 0
) -> str:
    """Formats Workbench-style token and cost display string with cache hit indicator."""
    total_tokens = input_tokens + output_tokens + cache_read_tokens
    if cost < 0.0001 and cost > 0:
        cost_str = "<$0.0001"
    else:
        cost_str = f"${cost:.4f}"

    cache_info = f" • {cache_read_tokens:,} cached" if cache_read_tokens > 0 else ""
    return f"{total_tokens:,} tokens ({input_tokens:,} in, {output_tokens:,} out{cache_info}) • {cost_str}"

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
        max_history_turns: int = 20,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Streams response from Claude with prompt caching, per-model effort branching,
        dynamic max_tokens, history trimming, and token usage logging.
        """
        if not self.client:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=500,
                error_type="DEPENDENCY_MISSING",
                message="Anthropic Python SDK is not installed in the current environment."
            )

        # 1. Clean & Trim conversation history
        raw_clean_messages = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role in ["user", "assistant"]:
                if isinstance(content, list) and content:
                    raw_clean_messages.append({"role": role, "content": content})
                elif content and str(content).strip():
                    raw_clean_messages.append({"role": role, "content": str(content).strip()})

        if not raw_clean_messages:
            raise ClaudeModelError(
                model_name=model_name,
                model_id=model_id,
                status_code=400,
                error_type="INVALID_MESSAGES",
                message="No valid user message to send to the Claude API."
            )

        # Apply History Trimming
        trimmed_messages = trim_conversation_history(raw_clean_messages, max_turns=max_history_turns)

        # Apply Prompt Caching Breakpoint to stable prefix
        clean_messages = apply_prompt_caching_breakpoints(trimmed_messages)

        # 2. Per-Model Effort & Thinking Configuration
        cfg = get_model_config(model_id)
        supports_adaptive = cfg.get("supportsAdaptive", False)
        supports_thinking = cfg.get("supportsThinking", False)
        effort_val = (effort_level or cfg.get("defaultEffort") or "medium").lower()

        # Dynamic max_tokens based on effort level
        actual_max_tokens = max_tokens if max_tokens else get_dynamic_max_tokens(model_id, effort_val)

        kwargs: Dict[str, Any] = {
            "model": model_id,
            "max_tokens": actual_max_tokens,
            "messages": clean_messages,
        }

        # Prompt Caching on System Prompt Block
        if system and system.strip():
            kwargs["system"] = [
                {
                    "type": "text",
                    "text": system.strip(),
                    "cache_control": {"type": "ephemeral"}
                }
            ]

        # Prompt Caching on Tools Array if present
        if tools:
            tools_copy = copy.deepcopy(tools)
            if tools_copy:
                tools_copy[-1]["cache_control"] = {"type": "ephemeral"}
            kwargs["tools"] = tools_copy

        # Branching on supportsAdaptive
        if supports_adaptive:
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["output_config"] = {"effort": effort_val}
        elif supports_thinking:
            budget = cfg.get("budget_tokens")
            if not budget:
                budget = 2048 if effort_val == "low" else 8192 if effort_val == "medium" else 24576
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget
            }
            # Special case: claude-opus-4-5 supports both budget_tokens and effort together
            if "opus-4-5" in model_id.lower():
                kwargs["output_config"] = {"effort": cfg.get("effort", effort_val)}
        else:
            kwargs["temperature"] = temperature

        input_tokens = 0
        output_tokens = 0
        cache_read_input_tokens = 0
        cache_creation_input_tokens = 0

        try:
            with self.client.messages.stream(**kwargs) as stream:
                for event in stream:
                    if event.type == "message_start":
                        if hasattr(event, "message") and hasattr(event.message, "usage"):
                            usage = event.message.usage
                            input_tokens = getattr(usage, "input_tokens", 0)
                            cache_read_input_tokens = getattr(usage, "cache_read_input_tokens", 0) or 0
                            cache_creation_input_tokens = getattr(usage, "cache_creation_input_tokens", 0) or 0
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
                        u = final_msg.usage
                        input_tokens = getattr(u, "input_tokens", input_tokens)
                        output_tokens = getattr(u, "output_tokens", output_tokens)
                        cache_read_input_tokens = getattr(u, "cache_read_input_tokens", cache_read_input_tokens) or 0
                        cache_creation_input_tokens = getattr(u, "cache_creation_input_tokens", cache_creation_input_tokens) or 0
                except Exception:
                    pass

                # Logging after each API call
                log_line = (
                    f"[Anthropic API Usage] Model: {model_id} | Effort: {effort_val} | "
                    f"Input: {input_tokens:,} | Output: {output_tokens:,} | "
                    f"Cache Read: {cache_read_input_tokens:,} | Cache Creation: {cache_creation_input_tokens:,}"
                )
                logger.info(log_line)
                print(log_line, flush=True)

                in_c, out_c, total_c = calculate_cost(
                    model_id=model_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_read_tokens=cache_read_input_tokens,
                    cache_creation_tokens=cache_creation_input_tokens
                )

                yield {
                    "type": "usage_summary",
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_read_tokens": cache_read_input_tokens,
                    "cache_creation_tokens": cache_creation_input_tokens,
                    "total_tokens": input_tokens + output_tokens + cache_read_input_tokens,
                    "cost": total_c,
                    "badge": format_cost_badge(input_tokens, output_tokens, total_c, cache_read_input_tokens)
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
            # Fallback if thinking is rejected
            if "thinking" in str(e).lower() and "thinking" in kwargs:
                del kwargs["thinking"]
                if "output_config" in kwargs:
                    del kwargs["output_config"]
                kwargs["temperature"] = temperature
                kwargs["max_tokens"] = 8192
                try:
                    with self.client.messages.stream(**kwargs) as retry_stream:
                        for event in retry_stream:
                            if event.type == "message_start":
                                if hasattr(event, "message") and hasattr(event.message, "usage"):
                                    u = event.message.usage
                                    input_tokens = getattr(u, "input_tokens", 0)
                                    cache_read_input_tokens = getattr(u, "cache_read_input_tokens", 0) or 0
                                    cache_creation_input_tokens = getattr(u, "cache_creation_input_tokens", 0) or 0
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
                                u = final_msg.usage
                                input_tokens = getattr(u, "input_tokens", input_tokens)
                                output_tokens = getattr(u, "output_tokens", output_tokens)
                                cache_read_input_tokens = getattr(u, "cache_read_input_tokens", cache_read_input_tokens) or 0
                                cache_creation_input_tokens = getattr(u, "cache_creation_input_tokens", cache_creation_input_tokens) or 0
                        except Exception:
                            pass

                        log_line = (
                            f"[Anthropic API Usage Fallback] Model: {model_id} | "
                            f"Input: {input_tokens:,} | Output: {output_tokens:,} | "
                            f"Cache Read: {cache_read_input_tokens:,} | Cache Creation: {cache_creation_input_tokens:,}"
                        )
                        logger.info(log_line)
                        print(log_line, flush=True)

                        in_c, out_c, total_c = calculate_cost(
                            model_id=model_id,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            cache_read_tokens=cache_read_input_tokens,
                            cache_creation_tokens=cache_creation_input_tokens
                        )
                        yield {
                            "type": "usage_summary",
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cache_read_tokens": cache_read_input_tokens,
                            "cache_creation_tokens": cache_creation_input_tokens,
                            "total_tokens": input_tokens + output_tokens + cache_read_input_tokens,
                            "cost": total_c,
                            "badge": format_cost_badge(input_tokens, output_tokens, total_c, cache_read_input_tokens)
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
