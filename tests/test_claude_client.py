import pytest
from claude_workspace.claude_client import ClaudeEngine, extract_artifacts, CLAUDE_MODELS, SYSTEM_PRESETS

def test_extract_artifacts():
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
    assert len(artifacts) == 2
    assert artifacts[0]["language"] == "markdown"
    assert "My Plan" in artifacts[0]["code"]
    assert artifacts[1]["language"] == "python"
    assert "def main" in artifacts[1]["code"]

def test_models_and_presets_exist():
    assert len(CLAUDE_MODELS) >= 4
    assert any("3.7" in k for k in CLAUDE_MODELS.keys())
    assert "Architecture & Implementation Planner" in SYSTEM_PRESETS
