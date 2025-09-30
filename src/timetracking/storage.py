"""Storage layer for persisting time tracking data."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class Storage:
    """Handles CSV and JSON storage for time tracking sessions."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize storage with data directory."""
        if data_dir is None:
            data_dir = Path.home() / ".timetrack"

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.csv_file = self.data_dir / "sessions.csv"
        self.active_session_file = self.data_dir / "active_session.json"

        # Initialize CSV file with headers if it doesn't exist
        if not self.csv_file.exists():
            self._initialize_csv()

    def _initialize_csv(self):
        """Create CSV file with headers."""
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "session_id",
                "start_time",
                "end_time",
                "duration_minutes",
                "description",
                "commits",
                "notes"
            ])

    def save_active_session(self, session_data: dict):
        """Save the currently active session to JSON."""
        with open(self.active_session_file, "w") as f:
            json.dump(session_data, f, indent=2)

    def load_active_session(self) -> Optional[dict]:
        """Load the active session if one exists."""
        if not self.active_session_file.exists():
            return None

        try:
            with open(self.active_session_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def clear_active_session(self):
        """Remove the active session file."""
        if self.active_session_file.exists():
            self.active_session_file.unlink()

    def append_session_to_csv(self, session_data: dict):
        """Append a completed session to the CSV file."""
        with open(self.csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                session_data.get("session_id", ""),
                session_data.get("start_time", ""),
                session_data.get("end_time", ""),
                session_data.get("duration_minutes", 0),
                session_data.get("description", ""),
                session_data.get("commits", ""),
                session_data.get("notes", "")
            ])

    def update_session_in_csv(self, session_data: dict):
        """Update an existing session in the CSV (used for active session updates)."""
        # Read all rows
        rows = []
        session_id = session_data.get("session_id")
        found = False

        if self.csv_file.exists():
            with open(self.csv_file, "r", newline="") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                for row in reader:
                    if row["session_id"] == str(session_id):
                        # Update this row
                        rows.append({
                            "session_id": session_data.get("session_id", ""),
                            "start_time": session_data.get("start_time", ""),
                            "end_time": session_data.get("end_time", ""),
                            "duration_minutes": session_data.get("duration_minutes", 0),
                            "description": session_data.get("description", ""),
                            "commits": session_data.get("commits", ""),
                            "notes": session_data.get("notes", "")
                        })
                        found = True
                    else:
                        rows.append(row)

        # If not found, append instead
        if not found:
            self.append_session_to_csv(session_data)
            return

        # Write back all rows
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def get_sessions(self, limit: Optional[int] = None) -> list[dict]:
        """Retrieve sessions from CSV, optionally limited to most recent."""
        if not self.csv_file.exists():
            return []

        sessions = []
        with open(self.csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            sessions = list(reader)

        # Return most recent first
        sessions.reverse()

        if limit:
            return sessions[:limit]
        return sessions

    def get_next_session_id(self) -> int:
        """Get the next available session ID."""
        sessions = self.get_sessions()
        if not sessions:
            return 1

        # Get max session_id
        max_id = 0
        for session in sessions:
            try:
                session_id = int(session.get("session_id", 0))
                if session_id > max_id:
                    max_id = session_id
            except (ValueError, TypeError):
                continue

        return max_id + 1