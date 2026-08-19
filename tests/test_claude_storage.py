import os
import shutil
import tempfile
import unittest
from storage import Database

class TestClaudeStorage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_chat.db")
        self.db = Database(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_session_lifecycle_with_effort_and_caching(self):
        session_id = self.db.create_session(
            title="Test Session",
            model="claude-3-7-sonnet-20250219",
            effort="High",
            system_prompt="You are a helpful assistant."
        )
        self.assertIsNotNone(session_id)

        sessions = self.db.get_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["title"], "Test Session")
        self.assertEqual(sessions[0]["effort"], "High")

        # Update settings
        self.db.update_session_settings(session_id, "claude-sonnet-4-6", "Medium")
        session = self.db.get_session(session_id)
        self.assertEqual(session["model"], "claude-sonnet-4-6")
        self.assertEqual(session["effort"], "Medium")

        # Add messages with cache tokens
        self.db.save_message(session_id, "user", "Hello Claude!")
        self.db.save_message(
            session_id=session_id,
            role="assistant",
            content="Hello! How can I help?",
            thinking="Thinking step...",
            tokens=120,
            input_tokens=80,
            output_tokens=40,
            cache_read_tokens=500,
            cost=0.0012
        )

        messages = self.db.get_messages(session_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["cache_read_tokens"], 500)
        self.assertEqual(messages[1]["cost"], 0.0012)

        # Delete session
        self.db.delete_session(session_id)
        self.assertEqual(len(self.db.get_sessions()), 0)
        self.assertEqual(len(self.db.get_messages(session_id)), 0)

if __name__ == "__main__":
    unittest.main()
