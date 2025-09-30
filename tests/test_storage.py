"""Tests for storage layer."""

import tempfile
from pathlib import Path

import pytest

from timetracking.storage import Storage


@pytest.fixture
def temp_storage():
    """Create a temporary storage instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Storage(data_dir=Path(tmpdir))
        yield storage


def test_storage_initialization(temp_storage):
    """Test that storage initializes correctly."""
    assert temp_storage.data_dir.exists()
    assert temp_storage.csv_file.exists()
    assert not temp_storage.active_session_file.exists()


def test_save_and_load_active_session(temp_storage):
    """Test saving and loading active session."""
    session_data = {
        "session_id": 1,
        "start_time": "2025-09-30T10:00:00",
        "description": "Test session",
    }

    temp_storage.save_active_session(session_data)
    loaded = temp_storage.load_active_session()

    assert loaded is not None
    assert loaded["session_id"] == 1
    assert loaded["description"] == "Test session"


def test_clear_active_session(temp_storage):
    """Test clearing active session."""
    session_data = {"session_id": 1, "description": "Test"}
    temp_storage.save_active_session(session_data)

    assert temp_storage.load_active_session() is not None

    temp_storage.clear_active_session()
    assert temp_storage.load_active_session() is None


def test_append_session_to_csv(temp_storage):
    """Test appending session to CSV."""
    session_data = {
        "session_id": 1,
        "start_time": "2025-09-30T10:00:00",
        "end_time": "2025-09-30T11:00:00",
        "duration_minutes": 60,
        "description": "Test work",
        "commits": "abc123:Initial commit",
        "notes": "Made progress",
    }

    temp_storage.append_session_to_csv(session_data)
    sessions = temp_storage.get_sessions()

    assert len(sessions) == 1
    assert sessions[0]["session_id"] == "1"
    assert sessions[0]["description"] == "Test work"


def test_get_next_session_id(temp_storage):
    """Test getting next session ID."""
    assert temp_storage.get_next_session_id() == 1

    # Add a session
    session_data = {
        "session_id": 1,
        "start_time": "2025-09-30T10:00:00",
        "end_time": "2025-09-30T11:00:00",
        "duration_minutes": 60,
        "description": "Test",
        "commits": "",
        "notes": "",
    }
    temp_storage.append_session_to_csv(session_data)

    assert temp_storage.get_next_session_id() == 2


def test_get_sessions_with_limit(temp_storage):
    """Test retrieving sessions with limit."""
    # Add multiple sessions
    for i in range(5):
        session_data = {
            "session_id": i + 1,
            "start_time": f"2025-09-30T{10+i}:00:00",
            "end_time": f"2025-09-30T{11+i}:00:00",
            "duration_minutes": 60,
            "description": f"Session {i+1}",
            "commits": "",
            "notes": "",
        }
        temp_storage.append_session_to_csv(session_data)

    all_sessions = temp_storage.get_sessions()
    assert len(all_sessions) == 5

    limited = temp_storage.get_sessions(limit=3)
    assert len(limited) == 3