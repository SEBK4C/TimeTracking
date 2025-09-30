"""CLI interface for time tracking."""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from .session import SessionManager
from .storage import Storage

app = typer.Typer(help="Simple time tracking with git integration")
console = Console()


def format_datetime(iso_string: str) -> str:
    """Format ISO datetime string for display."""
    if not iso_string:
        return ""
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_duration(minutes: float) -> str:
    """Format duration in minutes to human readable format."""
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f}d"


@app.command()
def start(description: str):
    """Start a new work session."""
    manager = SessionManager()
    try:
        session = manager.start_session(description)
        console.print(f"[green]✓[/green] Started session #{session['session_id']}: {description}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise typer.Exit(1)


@app.command()
def stop():
    """Stop the active session."""
    manager = SessionManager()
    try:
        session = manager.stop_session()
        duration = format_duration(session["duration_minutes"])
        console.print(f"[green]✓[/green] Stopped session #{session['session_id']}")
        console.print(f"  Duration: {duration}")
        console.print(f"  Description: {session['description']}")

        # Show commits if any
        commits = session.get("commits", "")
        if commits:
            commit_count = len(commits.split("|"))
            console.print(f"  Commits: {commit_count}")

    except ValueError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise typer.Exit(1)


@app.command()
def pause():
    """Pause the active session."""
    manager = SessionManager()
    try:
        session = manager.pause_session()
        console.print(f"[yellow]⏸[/yellow] Paused session #{session['session_id']}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise typer.Exit(1)


@app.command()
def resume():
    """Resume a paused session."""
    manager = SessionManager()
    try:
        session = manager.resume_session()
        console.print(f"[green]▶[/green] Resumed session #{session['session_id']}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise typer.Exit(1)


@app.command()
def note(text: str):
    """Add a note to the active session."""
    manager = SessionManager()
    try:
        session = manager.add_note(text)
        console.print(f"[green]✓[/green] Note added to session #{session['session_id']}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise typer.Exit(1)


@app.command()
def status():
    """Show the current session status."""
    manager = SessionManager()
    status = manager.get_session_status()

    if not status["active"]:
        console.print("[yellow]No active session[/yellow]")
        console.print("\nStart a new session with: [bold]track start \"description\"[/bold]")
        return

    # Create status display
    console.print(f"\n[bold]Session #{status['session_id']}[/bold]")
    console.print(f"  Description: {status['description']}")
    console.print(f"  Started: {format_datetime(status['start_time'])}")
    console.print(f"  Elapsed: {format_duration(status['elapsed_minutes'])}")

    if status["paused"]:
        console.print("  Status: [yellow]PAUSED[/yellow]")
    else:
        console.print("  Status: [green]ACTIVE[/green]")

    if status["commit_count"] > 0:
        console.print(f"  Commits: {status['commit_count']}")

    if status["notes"]:
        console.print(f"  Notes: {status['notes']}")


@app.command()
def log(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of sessions to show"),
    today: bool = typer.Option(False, "--today", help="Show only today's sessions"),
    week: bool = typer.Option(False, "--week", help="Show this week's sessions"),
):
    """View recent work sessions."""
    storage = Storage()
    sessions = storage.get_sessions()

    if not sessions:
        console.print("[yellow]No sessions recorded yet[/yellow]")
        return

    # Filter by date if requested
    if today or week:
        now = datetime.now()
        filtered = []
        for s in sessions:
            try:
                start = datetime.fromisoformat(s["start_time"])
                if today and start.date() == now.date():
                    filtered.append(s)
                elif week and (now - start).days < 7:
                    filtered.append(s)
            except (ValueError, KeyError):
                continue
        sessions = filtered

    # Apply limit
    sessions = sessions[:limit]

    if not sessions:
        console.print("[yellow]No sessions found for the specified period[/yellow]")
        return

    # Create table
    table = Table(box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Start", style="blue")
    table.add_column("Duration", style="green")
    table.add_column("Description", style="white")
    table.add_column("Commits", style="yellow")

    for session in sessions:
        session_id = session.get("session_id", "")
        start_time = format_datetime(session.get("start_time", ""))
        duration = format_duration(float(session.get("duration_minutes", 0)))
        description = session.get("description", "")
        commits = session.get("commits", "")
        commit_count = str(len(commits.split("|"))) if commits else "0"

        # Truncate description if too long
        if len(description) > 50:
            description = description[:47] + "..."

        table.add_row(session_id, start_time, duration, description, commit_count)

    console.print(table)


@app.command()
def report(
    today: bool = typer.Option(False, "--today", help="Report for today"),
    week: bool = typer.Option(False, "--week", help="Report for this week"),
):
    """Generate a summary report of work sessions."""
    storage = Storage()
    sessions = storage.get_sessions()

    if not sessions:
        console.print("[yellow]No sessions recorded yet[/yellow]")
        return

    # Filter by date if requested
    now = datetime.now()
    filtered = []
    period_name = "all time"

    if today or week:
        for s in sessions:
            try:
                start = datetime.fromisoformat(s["start_time"])
                if today and start.date() == now.date():
                    filtered.append(s)
                elif week and (now - start).days < 7:
                    filtered.append(s)
            except (ValueError, KeyError):
                continue
        sessions = filtered
        period_name = "today" if today else "this week"

    if not sessions:
        console.print(f"[yellow]No sessions found for {period_name}[/yellow]")
        return

    # Calculate statistics
    total_sessions = len(sessions)
    total_minutes = sum(float(s.get("duration_minutes", 0)) for s in sessions)
    total_commits = sum(
        len(s.get("commits", "").split("|")) if s.get("commits") else 0
        for s in sessions
    )

    # Display report
    console.print(f"\n[bold]Work Report ({period_name})[/bold]\n")
    console.print(f"  Total Sessions: {total_sessions}")
    console.print(f"  Total Time: {format_duration(total_minutes)}")
    console.print(f"  Total Commits: {total_commits}")

    if total_sessions > 0:
        avg_duration = total_minutes / total_sessions
        console.print(f"  Average Session: {format_duration(avg_duration)}")


@app.command(name="install-hook")
def install_hook(
    global_install: bool = typer.Option(
        False, "--global", help="Install hook globally for all repos"
    ),
    repo_path: Optional[str] = typer.Option(
        None, "--repo", help="Path to specific git repository"
    ),
):
    """Install git post-commit hook to track commits automatically."""
    from .git_hook import install_git_hook

    try:
        path = install_git_hook(global_install=global_install, repo_path=repo_path)
        if global_install:
            console.print(f"[green]✓[/green] Installed global git hook")
            console.print(f"  Template: {path}")
        else:
            console.print(f"[green]✓[/green] Installed git hook")
            console.print(f"  Hook: {path}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to install hook: {e}", style="red")
        raise typer.Exit(1)


@app.command(name="hook-commit")
def hook_commit(commit_hash: str, commit_message: str):
    """Internal command called by git post-commit hook."""
    manager = SessionManager()
    result = manager.add_commit(commit_hash, commit_message)

    # This runs silently - only output if there's an issue
    if result is None:
        # No active session, that's okay
        pass


if __name__ == "__main__":
    app()