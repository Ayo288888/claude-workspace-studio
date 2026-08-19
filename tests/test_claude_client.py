import unittest
from claude_client import (
    ClaudeEngine,
    ClaudeModelError,
    extract_artifacts,
    calculate_cost,
    format_cost_badge,
    get_model_config,
    get_dynamic_max_tokens,
    trim_conversation_history,
    apply_prompt_caching_breakpoints,
    MODEL_CONFIG,
    CLAUDE_MODELS,
    EFFORT_LEVELS,
    SYSTEM_PRESETS
)

class TestClaudeClient(unittest.TestCase):
    def test_extract_artifacts(self):
        sample_text = """Here is the plan:
```markdown
# My Plan
1. Step one
2. Step two
```
And here is code:
```python
def main():
    print("hello")
```
"""
        artifacts = extract_artifacts(sample_text)
        self.assertEqual(len(artifacts), 2)
        self.assertEqual(artifacts[0]["language"], "markdown")
        self.assertIn("My Plan", artifacts[0]["code"])
        self.assertEqual(artifacts[1]["language"], "python")
        self.assertIn("def main", artifacts[1]["code"])

    def test_calculate_cost_with_caching(self):
        # 1,000 normal in, 500 out, 2,000 cached in on Sonnet 3.7 ($3/MTok normal in, $0.30/MTok cached in, $15/MTok out)
        in_c, out_c, total_c = calculate_cost(
            model_id="claude-3-7-sonnet-20250219",
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=2000,
            cache_creation_tokens=0
        )
        # Normal in: 1000 * 3 / 1M = 0.003
        # Cached in: 2000 * 0.3 / 1M = 0.0006
        # Total in: 0.0036
        # Output: 500 * 15 / 1M = 0.0075
        # Total: 0.0111
        self.assertAlmostEqual(in_c, 0.0036, places=5)
        self.assertAlmostEqual(out_c, 0.0075, places=5)
        self.assertAlmostEqual(total_c, 0.0111, places=5)

    def test_format_cost_badge(self):
        badge = format_cost_badge(1000, 500, 0.0111, cache_read_tokens=2000)
        self.assertIn("3,500 tokens", badge)
        self.assertIn("1,000 in", badge)
        self.assertIn("500 out", badge)
        self.assertIn("2,000 cached", badge)
        self.assertIn("$0.0111", badge)

    def test_model_config_adaptive_branching(self):
        sonnet_46 = get_model_config("claude-sonnet-4-6")
        self.assertTrue(sonnet_46["supportsAdaptive"])

        opus_47 = get_model_config("claude-opus-4-7")
        self.assertTrue(opus_47["supportsAdaptive"])

        opus_45 = get_model_config("claude-opus-4-5")
        self.assertFalse(opus_45["supportsAdaptive"])
        self.assertTrue(opus_45["supportsThinking"])
        self.assertEqual(opus_45["budget_tokens"], 8000)

        sonnet_35 = get_model_config("claude-3-5-sonnet-20241022")
        self.assertFalse(sonnet_35["supportsAdaptive"])
        self.assertFalse(sonnet_35["supportsThinking"])

    def test_dynamic_max_tokens(self):
        self.assertEqual(get_dynamic_max_tokens("claude-sonnet-4-6", "low"), 8192)
        self.assertEqual(get_dynamic_max_tokens("claude-sonnet-4-6", "medium"), 24576)
        self.assertEqual(get_dynamic_max_tokens("claude-sonnet-4-6", "high"), 64000)

        self.assertEqual(get_dynamic_max_tokens("claude-3-5-sonnet-20241022", "low"), 2048)
        self.assertEqual(get_dynamic_max_tokens("claude-3-5-sonnet-20241022", "high"), 8192)

    def test_history_trimming(self):
        # Create 25 messages
        msgs = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"} for i in range(25)]
        trimmed = trim_conversation_history(msgs, max_turns=20)
        self.assertLessEqual(len(trimmed), 20)
        self.assertEqual(trimmed[0]["content"], "msg 0")
        self.assertEqual(trimmed[1]["content"], "msg 1")
        self.assertIn("collapsed for token optimization", trimmed[2]["content"])
        self.assertEqual(trimmed[-1]["content"], "msg 24")

    def test_prompt_caching_breakpoints(self):
        msgs = [
            {"role": "user", "content": "Turn 1"},
            {"role": "assistant", "content": "Turn 2"},
            {"role": "user", "content": "Turn 3"},
            {"role": "assistant", "content": "Turn 4"},
            {"role": "user", "content": "Turn 5"}
        ]
        cached_msgs = apply_prompt_caching_breakpoints(msgs)
        # Message at len - 2 (index 3) should have cache_control
        target_content = cached_msgs[3]["content"]
        self.assertIsInstance(target_content, list)
        self.assertEqual(target_content[0]["cache_control"], {"type": "ephemeral"})

    def test_claude_model_error_structure(self):
        err = ClaudeModelError(
            model_name="Opus 5",
            model_id="claude-opus-5",
            status_code=404,
            error_type="MODEL_NOT_FOUND",
            message="Model unavailable"
        )
        self.assertEqual(err.status_code, 404)
        self.assertEqual(err.error_type, "MODEL_NOT_FOUND")
        self.assertIn("Opus 5", str(err))

if __name__ == "__main__":
    unittest.main()
