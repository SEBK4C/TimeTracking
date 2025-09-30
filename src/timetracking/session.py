"""Session management for time tracking."""

from datetime import datetime, timedelta
from typing import Optional

from .storage import Storage


class SessionManager:
    """Manages work session lifecycle and state."""

    def __init__(self, storage: Optional[Storage] = None):
        """Initialize session manager with storage backend."""
        self.storage = storage or Storage()

    def start_session(self, description: str) -> dict:
        """Start a new work session."""
        # Check if there's already an active session
        active = self.storage.load_active_session()
        if active and not active.get("paused", False):
            raise ValueError(
                f"Session #{active['session_id']} is already active. "
                "Stop or pause it first."
            )

        # Create new session
        session_id = self.storage.get_next_session_id()
        now = datetime.now()

        session_data = {
            "session_id": session_id,
            "start_time": now.isoformat(),
            "end_time": "",
            "duration_minutes": 0,
            "description": description,
            "commits": "",
            "notes": "",
            "paused": False,
            "pause_time": None,
            "total_pause_duration": 0,
        }

        self.storage.save_active_session(session_data)
        return session_data

    def stop_session(self) -> dict:
        """Stop the active session and save to CSV."""
        active = self.storage.load_active_session()
        if not active:
            raise ValueError("No active session to stop.")

        # Calculate duration
        start_time = datetime.fromisoformat(active["start_time"])
        end_time = datetime.now()

        # Account for paused time
        total_pause = active.get("total_pause_duration", 0)
        if active.get("paused") and active.get("pause_time"):
            pause_start = datetime.fromisoformat(active["pause_time"])
            total_pause += (end_time - pause_start).total_seconds() / 60

        duration = (end_time - start_time).total_seconds() / 60 - total_pause

        # Update session data
        active["end_time"] = end_time.isoformat()
        active["duration_minutes"] = round(duration, 2)

        # Remove pause-related fields before saving to CSV
        csv_data = {k: v for k, v in active.items()
                    if k not in ["paused", "pause_time", "total_pause_duration"]}

        # Save to CSV and clear active session
        self.storage.append_session_to_csv(csv_data)
        self.storage.clear_active_session()

        return csv_data

    def pause_session(self) -> dict:
        """Pause the active session."""
        active = self.storage.load_active_session()
        if not active:
            raise ValueError("No active session to pause.")

        if active.get("paused"):
            raise ValueError("Session is already paused.")

        active["paused"] = True
        active["pause_time"] = datetime.now().isoformat()

        self.storage.save_active_session(active)
        return active

    def resume_session(self) -> dict:
        """Resume a paused session."""
        active = self.storage.load_active_session()
        if not active:
            raise ValueError("No active session to resume.")

        if not active.get("paused"):
            raise ValueError("Session is not paused.")

        # Calculate pause duration
        pause_start = datetime.fromisoformat(active["pause_time"])
        pause_duration = (datetime.now() - pause_start).total_seconds() / 60

        active["total_pause_duration"] = active.get("total_pause_duration", 0) + pause_duration
        active["paused"] = False
        active["pause_time"] = None

        self.storage.save_active_session(active)
        return active

    def add_note(self, note: str) -> dict:
        """Add a note to the active session."""
        active = self.storage.load_active_session()
        if not active:
            raise ValueError("No active session to add note to.")

        # Append note with semicolon separator
        existing_notes = active.get("notes", "")
        if existing_notes:
            active["notes"] = f"{existing_notes}; {note}"
        else:
            active["notes"] = note

        self.storage.save_active_session(active)
        return active

    def add_commit(self, commit_hash: str, commit_message: str) -> dict:
        """Add a git commit to the active session."""
        active = self.storage.load_active_session()
        if not active:
            # If no active session, we can't add the commit
            return None

        # Format: hash:message
        commit_entry = f"{commit_hash}:{commit_message}"

        # Append commit with pipe separator
        existing_commits = active.get("commits", "")
        if existing_commits:
            active["commits"] = f"{existing_commits}|{commit_entry}"
        else:
            active["commits"] = commit_entry

        self.storage.save_active_session(active)
        return active

    def get_active_session(self) -> Optional[dict]:
        """Get the currently active session."""
        return self.storage.load_active_session()

    def get_session_status(self) -> dict:
        """Get detailed status of the active session."""
        active = self.storage.load_active_session()
        if not active:
            return {"active": False}

        start_time = datetime.fromisoformat(active["start_time"])
        now = datetime.now()

        # Calculate elapsed time
        total_pause = active.get("total_pause_duration", 0)
        if active.get("paused") and active.get("pause_time"):
            pause_start = datetime.fromisoformat(active["pause_time"])
            current_pause = (now - pause_start).total_seconds() / 60
        else:
            current_pause = 0

        elapsed = (now - start_time).total_seconds() / 60 - total_pause - current_pause

        # Count commits
        commits = active.get("commits", "")
        commit_count = len(commits.split("|")) if commits else 0

        return {
            "active": True,
            "session_id": active["session_id"],
            "description": active["description"],
            "start_time": active["start_time"],
            "elapsed_minutes": round(elapsed, 2),
            "paused": active.get("paused", False),
            "commit_count": commit_count,
            "notes": active.get("notes", ""),
        }