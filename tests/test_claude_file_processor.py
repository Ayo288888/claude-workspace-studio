import unittest
from file_processor import process_raw_file, format_file_for_prompt

class TestClaudeFileProcessor(unittest.TestCase):
    def test_process_text_file(self):
        content = b"def add(a, b):\n    return a + b\n"
        res = process_raw_file("calc.py", content)
        self.assertEqual(res["type"], "text")
        self.assertIn("def add", res["content"])
        self.assertEqual(res["name"], "calc.py")

    def test_format_file_for_prompt_single_and_list(self):
        file_info = {"type": "text", "name": "sample.md", "content": "# Overview\nSome plan"}
        
        # Test Single Dict
        formatted_single = format_file_for_prompt(file_info)
        self.assertIn("File: sample.md", formatted_single)
        self.assertIn("# Overview", formatted_single)

        # Test List of Dicts (the previous crash case)
        file_list = [
            {"type": "text", "name": "file1.py", "content": "print('1')"},
            {"type": "text", "name": "file2.py", "content": "print('2')"},
            {"type": "image", "name": "diagram.png", "content": "[Image: diagram.png]"}
        ]
        formatted_list = format_file_for_prompt(file_list)
        self.assertIn("File: file1.py", formatted_list)
        self.assertIn("File: file2.py", formatted_list)
        self.assertIn("[Attached Image: diagram.png]", formatted_list)

if __name__ == "__main__":
    unittest.main()
