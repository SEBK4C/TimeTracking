# TimeTracking

A Python CLI time tracker that logs work sessions and git commits to CSV files. Combines manual time tracking with automatic git commit logging.

## Features

- **Manual Session Tracking**: Start/stop/pause/resume work sessions with descriptions
- **Automatic Git Integration**: Post-commit hook automatically logs commits to active sessions
- **CSV Export**: Real-time CSV updates for easy analysis in spreadsheets
- **Rich Terminal UI**: Beautiful output with tables and formatted text
- **Notes Support**: Add contextual notes during work sessions
- **Flexible Reporting**: Daily/weekly reports and session logs

## Installation

Using UV (recommended):

```bash
# Clone the repository
git clone <repo-url>
cd TimeTracking

# Install with UV
uv pip install -e .

# Or install directly from the repo
uv pip install git+<repo-url>
```

## Quick Start

```bash
# Start a work session
track start "Implementing new feature"

# Check current status
track status

# Add notes as you work
track note "Fixed bug in authentication"

# The git hook automatically logs commits (if installed)
git commit -m "Add user authentication"

# Stop the session when done
track stop

# View your work log
track log

# Generate reports
track report --today
track report --week
```

## Git Hook Setup

To automatically track git commits:

```bash
# First, make sure track is installed (not just running via uv run)
uv pip install -e .

# Then install the hook in current repository
track install-hook

# Or install globally for all repositories
track install-hook --global
```

The hook will automatically append commit information to your active session whenever you make a commit.

**Note**: The git hook requires the `track` command to be available in your PATH. If you're using UV in development mode (`uv run track`), you'll need to install the package first with `uv pip install -e .` for the hook to work.

## Commands

| Command | Description |
|---------|-------------|
| `track start "description"` | Start a new work session |
| `track stop` | Stop the active session |
| `track pause` | Pause the session (break/lunch) |
| `track resume` | Resume a paused session |
| `track note "text"` | Add a note to the current session |
| `track status` | Show current session details |
| `track log [--limit N]` | View recent sessions |
| `track log --today` | View today's sessions |
| `track log --week` | View this week's sessions |
| `track report [--today/--week]` | Generate summary statistics |
| `track install-hook` | Install git post-commit hook |

## Data Storage

All data is stored in `~/.timetrack/`:

- `sessions.csv` - Completed sessions with all details
- `active_session.json` - Current session state (if active)

### CSV Format

```csv
session_id,start_time,end_time,duration_minutes,description,commits,notes
1,2025-09-30T10:00:00,2025-09-30T11:30:00,90.0,"Feature work","abc123:Initial|def456:Fix bug","Made good progress"
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run CLI during development
uv run track <command>
```

## Use Cases

- **Freelance Work**: Track billable hours with detailed commit history
- **Project Management**: Understand time spent on different tasks
- **Personal Analytics**: Review productivity patterns
- **Team Coordination**: Share CSV exports for team reports

## License

See LICENSE file for details.
