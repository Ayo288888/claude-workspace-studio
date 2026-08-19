import json
import unittest
from file_processor import process_raw_file, format_file_for_prompt, build_anthropic_message_content

class TestClaudeFileProcessor(unittest.TestCase):
    def test_process_text_file(self):
        content = b"def add(a, b):\n    return a + b\n"
        res = process_raw_file("calc.py", content)
        self.assertEqual(res["type"], "text")
        self.assertIn("def add", res["content"])
        self.assertEqual(res["name"], "calc.py")

    def test_process_jupyter_notebook(self):
        nb_json = {
            "cells": [
                {"cell_type": "markdown", "source": ["# Analysis\n", "Intro text"]},
                {"cell_type": "code", "source": ["import numpy as np\n", "np.mean([1, 2, 3])"]}
            ]
        }
        nb_bytes = json.dumps(nb_json).encode("utf-8")
        res = process_raw_file("experiment.ipynb", nb_bytes)
        self.assertEqual(res["type"], "text")
        self.assertIn("Notebook Markdown Cell 1", res["content"])
        self.assertIn("Notebook Code Cell 2", res["content"])
        self.assertIn("import numpy as np", res["content"])

    def test_format_file_for_prompt_single_and_list(self):
        file_info = {"type": "text", "name": "sample.md", "content": "# Overview\nSome plan"}
        
        # Test Single Dict
        formatted_single = format_file_for_prompt(file_info)
        self.assertIn("File: sample.md", formatted_single)
        self.assertIn("# Overview", formatted_single)

        # Test List of Dicts
        file_list = [
            {"type": "text", "name": "file1.py", "content": "print('1')"},
            {"type": "text", "name": "file2.py", "content": "print('2')"},
            {"type": "image", "name": "diagram.png", "content": "[Image: diagram.png]"}
        ]
        formatted_list = format_file_for_prompt(file_list)
        self.assertIn("File: file1.py", formatted_list)
        self.assertIn("File: file2.py", formatted_list)
        self.assertIn("[Attached Image: diagram.png]", formatted_list)

    def test_build_anthropic_message_content_multimodal(self):
        # Image attachment should produce Anthropic vision content block
        img_file = {
            "type": "image",
            "name": "screenshot.png",
            "media_type": "image/png",
            "base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "content": "[Image: screenshot.png]"
        }
        blocks = build_anthropic_message_content("Describe this image", [img_file])
        self.assertIsInstance(blocks, list)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["type"], "image")
        self.assertEqual(blocks[0]["source"]["type"], "base64")
        self.assertEqual(blocks[1]["type"], "text")
        self.assertEqual(blocks[1]["text"], "Describe this image")

if __name__ == "__main__":
    unittest.main()
