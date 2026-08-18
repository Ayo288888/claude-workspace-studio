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

    def test_session_lifecycle(self):
        session_id = self.db.create_session(
            title="Test Session",
            model="claude-3-7-sonnet-20250219",
            system_prompt="You are a helpful assistant."
        )
        self.assertIsNotNone(session_id)

        sessions = self.db.get_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["title"], "Test Session")
        self.assertEqual(sessions[0]["id"], session_id)

        # Add messages
        self.db.save_message(session_id, "user", "Hello Claude!")
        self.db.save_message(session_id, "assistant", "Hello! How can I help?", thinking="Thinking step...")

        messages = self.db.get_messages(session_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello Claude!")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["thinking"], "Thinking step...")

        # Rename session
        self.db.update_session_title(session_id, "Updated Title")
        session = self.db.get_session(session_id)
        self.assertEqual(session["title"], "Updated Title")

        # Delete session
        self.db.delete_session(session_id)
        self.assertEqual(len(self.db.get_sessions()), 0)
        self.assertEqual(len(self.db.get_messages(session_id)), 0)

if __name__ == "__main__":
    unittest.main()
