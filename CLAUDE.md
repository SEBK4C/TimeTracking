# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TimeTracking is a Python CLI time tracker that logs work sessions and git commits to CSV files. It provides a hybrid approach combining manual work session tracking with automatic git commit logging.

## Architecture

The application follows a modular architecture:

- **storage.py**: CSV and JSON persistence layer. Manages `~/.timetrack/sessions.csv` and `~/.timetrack/active_session.json`
- **session.py**: Core session management logic (start/stop/pause/resume/note)
- **cli.py**: Typer-based CLI interface with rich terminal output
- **git_hook.py**: Git post-commit hook installer and handler
- **reports.py**: Advanced reporting and analytics

Sessions are tracked in two stages:
1. Active session stored in JSON (`~/.timetrack/active_session.json`)
2. Completed session appended to CSV (`~/.timetrack/sessions.csv`)

## Commands

### Development Commands

```bash
# Install dependencies and set up environment
uv sync

# Run the CLI (during development)
uv run track <command>

# Install the package locally
uv pip install -e .

# Run tests
uv run pytest
```

### Usage Commands

```bash
track start "description"        # Start new session
track stop                        # Stop active session
track pause                       # Pause session (break/lunch)
track resume                      # Resume paused session
track note "text"                 # Add note to session
track status                      # Show current session
track log [--limit N]             # View recent sessions
track log --today / --week        # Filtered views
track report [--today / --week]   # Summary statistics
track install-hook                # Install git hook (current repo)
track install-hook --global       # Install for all repos
```

## Git Hook Integration

The post-commit hook (`hooks/post-commit` template) automatically calls `track hook-commit <hash> <message>` after each commit, appending commit info to the active session. If no session is active, commits are silently ignored.

Hook installation:
- Local: Installs to `.git/hooks/post-commit` in current repo
- Global: Installs to git template directory for all future repos

## Data Format

**CSV Schema** (`sessions.csv`):
- session_id: Unique integer
- start_time: ISO 8601 timestamp
- end_time: ISO 8601 timestamp
- duration_minutes: Float (excludes pause time)
- description: User-provided work description
- commits: Pipe-separated list of `hash:message` pairs
- notes: Semicolon-separated notes added during session

**Active Session JSON**: Contains additional fields for pause tracking:
- paused: Boolean
- pause_time: ISO timestamp of pause start
- total_pause_duration: Accumulated pause time in minutes