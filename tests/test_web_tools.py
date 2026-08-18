import unittest
from web_tools import extract_urls, is_valid_url, get_web_context_for_prompt

class TestWebTools(unittest.TestCase):
    def test_url_extraction(self):
        text = "Check out https://anthropic.com and http://example.org/docs for details."
        urls = extract_urls(text)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "https://anthropic.com")
        self.assertEqual(urls[1], "http://example.org/docs")

    def test_url_validation(self):
        self.assertTrue(is_valid_url("https://platform.claude.com"))
        self.assertTrue(is_valid_url("http://localhost:8501"))
        self.assertFalse(is_valid_url("not a url"))

if __name__ == "__main__":
    unittest.main()
