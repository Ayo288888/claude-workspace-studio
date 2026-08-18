import unittest
from claude_client import (
    ClaudeEngine,
    ClaudeModelError,
    extract_artifacts,
    calculate_cost,
    format_cost_badge,
    CLAUDE_MODELS,
    MODEL_DETAILS,
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

    def test_calculate_cost(self):
        # 1,000 input tokens and 500 output tokens on Sonnet 3.7 ($3/MTok in, $15/MTok out)
        in_c, out_c, total_c = calculate_cost("claude-3-7-sonnet-20250219", 1000, 500)
        self.assertAlmostEqual(in_c, 0.003, places=5)
        self.assertAlmostEqual(out_c, 0.0075, places=5)
        self.assertAlmostEqual(total_c, 0.0105, places=5)

    def test_format_cost_badge(self):
        badge = format_cost_badge(1000, 500, 0.0105)
        self.assertIn("1,500 tokens", badge)
        self.assertIn("1,000 in", badge)
        self.assertIn("500 out", badge)
        self.assertIn("$0.0105", badge)

    def test_models_and_presets_exist(self):
        self.assertIn("Opus 5", CLAUDE_MODELS)
        self.assertIn("Sonnet 5", CLAUDE_MODELS)
        self.assertIn("Fable 5", CLAUDE_MODELS)
        self.assertGreaterEqual(len(CLAUDE_MODELS), 10)

    def test_effort_levels(self):
        self.assertIn("Low", EFFORT_LEVELS)
        self.assertIn("Medium", EFFORT_LEVELS)
        self.assertIn("High", EFFORT_LEVELS)
        self.assertLess(EFFORT_LEVELS["Low"]["budget"], EFFORT_LEVELS["Medium"]["budget"])
        self.assertLess(EFFORT_LEVELS["Medium"]["budget"], EFFORT_LEVELS["High"]["budget"])

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
