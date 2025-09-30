"""Tests for session management."""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from timetracking.session import SessionManager
from timetracking.storage import Storage


@pytest.fixture
def session_manager():
    """Create a session manager with temporary storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Storage(data_dir=Path(tmpdir))
        manager = SessionManager(storage=storage)
        yield manager


def test_start_session(session_manager):
    """Test starting a new session."""
    session = session_manager.start_session("Test work")

    assert session["session_id"] == 1
    assert session["description"] == "Test work"
    assert session["start_time"]
    assert session["paused"] is False


def test_cannot_start_session_when_active(session_manager):
    """Test that starting a session when one is active raises error."""
    session_manager.start_session("First session")

    with pytest.raises(ValueError, match="already active"):
        session_manager.start_session("Second session")


def test_stop_session(session_manager):
    """Test stopping a session."""
    session_manager.start_session("Test work")
    stopped = session_manager.stop_session()

    assert stopped["end_time"]
    assert stopped["duration_minutes"] >= 0  # Can be 0 if test runs very fast

    # Should not have active session anymore
    assert session_manager.get_active_session() is None


def test_stop_session_without_active(session_manager):
    """Test stopping when no active session raises error."""
    with pytest.raises(ValueError, match="No active session"):
        session_manager.stop_session()


def test_pause_and_resume(session_manager):
    """Test pausing and resuming a session."""
    session_manager.start_session("Test work")

    # Pause
    paused = session_manager.pause_session()
    assert paused["paused"] is True
    assert paused["pause_time"]

    # Resume
    resumed = session_manager.resume_session()
    assert resumed["paused"] is False
    assert resumed["pause_time"] is None
    assert resumed["total_pause_duration"] > 0


def test_add_note(session_manager):
    """Test adding notes to session."""
    session_manager.start_session("Test work")

    session_manager.add_note("First note")
    session = session_manager.get_active_session()
    assert session["notes"] == "First note"

    session_manager.add_note("Second note")
    session = session_manager.get_active_session()
    assert session["notes"] == "First note; Second note"


def test_add_commit(session_manager):
    """Test adding commits to session."""
    session_manager.start_session("Test work")

    session_manager.add_commit("abc123", "Initial commit")
    session = session_manager.get_active_session()
    assert session["commits"] == "abc123:Initial commit"

    session_manager.add_commit("def456", "Second commit")
    session = session_manager.get_active_session()
    assert "abc123:Initial commit|def456:Second commit" in session["commits"]


def test_add_commit_without_active_session(session_manager):
    """Test adding commit when no active session returns None."""
    result = session_manager.add_commit("abc123", "Test commit")
    assert result is None


def test_get_session_status(session_manager):
    """Test getting session status."""
    # No active session
    status = session_manager.get_session_status()
    assert status["active"] is False

    # Active session
    session_manager.start_session("Test work")
    status = session_manager.get_session_status()

    assert status["active"] is True
    assert status["session_id"] == 1
    assert status["description"] == "Test work"
    assert status["elapsed_minutes"] >= 0
    assert status["commit_count"] == 0


def test_get_session_status_with_commits(session_manager):
    """Test session status includes commit count."""
    session_manager.start_session("Test work")
    session_manager.add_commit("abc123", "Commit 1")
    session_manager.add_commit("def456", "Commit 2")

    status = session_manager.get_session_status()
    assert status["commit_count"] == 2