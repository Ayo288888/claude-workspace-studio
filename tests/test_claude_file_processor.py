import io
import pytest
from claude_workspace.file_processor import process_raw_file, format_file_for_prompt

def test_process_text_file():
    content = b"def add(a, b):\n    return a + b\n"
    res = process_raw_file("calc.py", content)
    assert res["type"] == "text"
    assert "def add" in res["content"]
    assert res["name"] == "calc.py"

def test_format_file_for_prompt():
    file_info = {"type": "text", "name": "sample.md", "content": "# Overview\nSome plan"}
    formatted = format_file_for_prompt(file_info)
    assert "File: sample.md" in formatted
    assert "# Overview" in formatted
