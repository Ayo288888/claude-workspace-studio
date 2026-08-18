import os
import pytest
from claude_workspace.storage import Database

@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test_chat.db")
    return Database(db_path=db_path)

def test_session_lifecycle(temp_db):
    session_id = temp_db.create_session(
        title="Test Session",
        model="claude-3-7-sonnet-20250219",
        system_prompt="You are a helpful assistant."
    )
    assert session_id is not None

    sessions = temp_db.get_sessions()
    assert len(sessions) == 1
    assert sessions[0]["title"] == "Test Session"
    assert sessions[0]["id"] == session_id

    # Add messages
    temp_db.save_message(session_id, "user", "Hello Claude!")
    temp_db.save_message(session_id, "assistant", "Hello! How can I help?", thinking="Thinking step...")

    messages = temp_db.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello Claude!"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["thinking"] == "Thinking step..."

    # Rename session
    temp_db.update_session_title(session_id, "Updated Title")
    session = temp_db.get_session(session_id)
    assert session["title"] == "Updated Title"

    # Delete session
    temp_db.delete_session(session_id)
    assert len(temp_db.get_sessions()) == 0
    assert len(temp_db.get_messages(session_id)) == 0
