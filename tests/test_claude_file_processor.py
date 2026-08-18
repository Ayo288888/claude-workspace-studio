import unittest
from file_processor import process_raw_file, format_file_for_prompt

class TestClaudeFileProcessor(unittest.TestCase):
    def test_process_text_file(self):
        content = b"def add(a, b):\n    return a + b\n"
        res = process_raw_file("calc.py", content)
        self.assertEqual(res["type"], "text")
        self.assertIn("def add", res["content"])
        self.assertEqual(res["name"], "calc.py")

    def test_format_file_for_prompt(self):
        file_info = {"type": "text", "name": "sample.md", "content": "# Overview\nSome plan"}
        formatted = format_file_for_prompt(file_info)
        self.assertIn("File: sample.md", formatted)
        self.assertIn("# Overview", formatted)

if __name__ == "__main__":
    unittest.main()
