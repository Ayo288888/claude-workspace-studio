import unittest
from claude_client import ClaudeEngine, ClaudeModelError, extract_artifacts, CLAUDE_MODELS, MODEL_DETAILS, EFFORT_LEVELS, SYSTEM_PRESETS

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

    def test_models_and_presets_exist(self):
        self.assertIn("Opus 5", CLAUDE_MODELS)
        self.assertIn("Sonnet 5", CLAUDE_MODELS)
        self.assertIn("Fable 5", CLAUDE_MODELS)
        self.assertEqual(CLAUDE_MODELS["Opus 5"], "claude-opus-5")
        self.assertEqual(CLAUDE_MODELS["Sonnet 5"], "claude-sonnet-5")
        self.assertEqual(CLAUDE_MODELS["Fable 5"], "claude-fable-5")
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
