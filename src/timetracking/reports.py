"""Advanced reporting and analytics for time tracking data."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from .storage import Storage


class ReportGenerator:
    """Generate detailed reports from time tracking data."""

    def __init__(self, storage: Optional[Storage] = None):
        """Initialize report generator with storage backend."""
        self.storage = storage or Storage()

    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict:
        """Get summary for a specific day."""
        if date is None:
            date = datetime.now()

        sessions = self.storage.get_sessions()
        daily_sessions = []

        for session in sessions:
            try:
                start = datetime.fromisoformat(session["start_time"])
                if start.date() == date.date():
                    daily_sessions.append(session)
            except (ValueError, KeyError):
                continue

        total_minutes = sum(float(s.get("duration_minutes", 0)) for s in daily_sessions)
        total_commits = sum(
            len(s.get("commits", "").split("|")) if s.get("commits") else 0
            for s in daily_sessions
        )

        return {
            "date": date.date().isoformat(),
            "session_count": len(daily_sessions),
            "total_minutes": total_minutes,
            "total_commits": total_commits,
            "sessions": daily_sessions,
        }

    def get_weekly_summary(self, start_date: Optional[datetime] = None) -> Dict:
        """Get summary for a week (Monday to Sunday)."""
        if start_date is None:
            start_date = datetime.now()

        # Find Monday of the week
        days_since_monday = start_date.weekday()
        monday = (start_date - timedelta(days=days_since_monday)).date()
        sunday = monday + timedelta(days=6)

        sessions = self.storage.get_sessions()
        weekly_sessions = []

        for session in sessions:
            try:
                start = datetime.fromisoformat(session["start_time"])
                if monday <= start.date() <= sunday:
                    weekly_sessions.append(session)
            except (ValueError, KeyError):
                continue

        total_minutes = sum(float(s.get("duration_minutes", 0)) for s in weekly_sessions)
        total_commits = sum(
            len(s.get("commits", "").split("|")) if s.get("commits") else 0
            for s in weekly_sessions
        )

        # Group by day
        by_day = defaultdict(list)
        for session in weekly_sessions:
            try:
                start = datetime.fromisoformat(session["start_time"])
                day_name = start.strftime("%A")
                by_day[day_name].append(session)
            except (ValueError, KeyError):
                continue

        return {
            "week_start": monday.isoformat(),
            "week_end": sunday.isoformat(),
            "session_count": len(weekly_sessions),
            "total_minutes": total_minutes,
            "total_commits": total_commits,
            "days": dict(by_day),
        }

    def get_commit_details(self, session_id: int) -> List[Dict]:
        """Extract commit details from a session."""
        sessions = self.storage.get_sessions()
        session = None

        for s in sessions:
            if s.get("session_id") == str(session_id):
                session = s
                break

        if not session:
            return []

        commits_str = session.get("commits", "")
        if not commits_str:
            return []

        commit_entries = commits_str.split("|")
        commits = []

        for entry in commit_entries:
            if ":" in entry:
                hash_part, message = entry.split(":", 1)
                commits.append({"hash": hash_part.strip(), "message": message.strip()})

        return commits

    def get_productivity_stats(self, days: int = 30) -> Dict:
        """Get productivity statistics for the last N days."""
        sessions = self.storage.get_sessions()
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_sessions = []
        for session in sessions:
            try:
                start = datetime.fromisoformat(session["start_time"])
                if start >= cutoff_date:
                    recent_sessions.append(session)
            except (ValueError, KeyError):
                continue

        if not recent_sessions:
            return {
                "period_days": days,
                "session_count": 0,
                "total_minutes": 0,
                "total_commits": 0,
                "avg_session_minutes": 0,
                "avg_commits_per_session": 0,
                "active_days": 0,
            }

        total_minutes = sum(float(s.get("duration_minutes", 0)) for s in recent_sessions)
        total_commits = sum(
            len(s.get("commits", "").split("|")) if s.get("commits") else 0
            for s in recent_sessions
        )

        # Count unique active days
        active_days = set()
        for session in recent_sessions:
            try:
                start = datetime.fromisoformat(session["start_time"])
                active_days.add(start.date())
            except (ValueError, KeyError):
                continue

        return {
            "period_days": days,
            "session_count": len(recent_sessions),
            "total_minutes": total_minutes,
            "total_commits": total_commits,
            "avg_session_minutes": total_minutes / len(recent_sessions),
            "avg_commits_per_session": total_commits / len(recent_sessions),
            "active_days": len(active_days),
        }

    def export_to_dict(self) -> List[Dict]:
        """Export all sessions as a list of dictionaries."""
        return self.storage.get_sessions()

    def get_longest_sessions(self, limit: int = 5) -> List[Dict]:
        """Get the longest work sessions."""
        sessions = self.storage.get_sessions()

        # Sort by duration
        sorted_sessions = sorted(
            sessions,
            key=lambda s: float(s.get("duration_minutes", 0)),
            reverse=True,
        )

        return sorted_sessions[:limit]