import unittest
from claude_client import ClaudeEngine, extract_artifacts, CLAUDE_MODELS, SYSTEM_PRESETS

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
        self.assertGreaterEqual(len(CLAUDE_MODELS), 4)
        self.assertTrue(any("3.7" in k for k in CLAUDE_MODELS.keys()))
        self.assertIn("Architecture & Implementation Planner", SYSTEM_PRESETS)

if __name__ == "__main__":
    unittest.main()
