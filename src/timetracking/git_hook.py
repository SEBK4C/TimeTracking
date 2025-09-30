"""Git hook installation and management."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def get_hook_script() -> str:
    """Return the post-commit hook script content."""
    return '''#!/bin/sh
# TimeTracking post-commit hook
# Automatically logs commits to active time tracking session

# Get commit hash and message
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)

# Call the track command to log this commit
# Find the track command in PATH or use absolute path
if command -v track >/dev/null 2>&1; then
    track hook-commit "$COMMIT_HASH" "$COMMIT_MSG" >/dev/null 2>&1
fi
'''


def install_git_hook(global_install: bool = False, repo_path: Optional[str] = None) -> Path:
    """
    Install the post-commit hook.

    Args:
        global_install: If True, install as git template for all new repos
        repo_path: Path to specific repo (defaults to current directory)

    Returns:
        Path to the installed hook file

    Raises:
        ValueError: If git is not available or repo is invalid
        IOError: If hook installation fails
    """
    # Check if git is available
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise ValueError("Git is not installed or not in PATH")

    hook_content = get_hook_script()

    if global_install:
        # Install as template for all new repos
        try:
            result = subprocess.run(
                ["git", "config", "--global", "init.templateDir"],
                capture_output=True,
                text=True,
            )
            template_dir = result.stdout.strip()

            if not template_dir:
                # Set up default template directory
                template_dir = str(Path.home() / ".git-templates")
                subprocess.run(
                    ["git", "config", "--global", "init.templateDir", template_dir],
                    check=True,
                )

            template_dir = Path(template_dir)
            hooks_dir = template_dir / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)

            hook_file = hooks_dir / "post-commit"
            hook_file.write_text(hook_content)
            hook_file.chmod(0o755)

            return hook_file

        except Exception as e:
            raise IOError(f"Failed to install global hook: {e}")

    else:
        # Install in specific repository
        if repo_path:
            repo = Path(repo_path)
        else:
            # Use current directory
            repo = Path.cwd()

        # Find .git directory
        git_dir = repo / ".git"

        if not git_dir.exists() or not git_dir.is_dir():
            # Maybe it's a worktree or bare repo
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--git-dir"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                git_dir = Path(result.stdout.strip())
                if not git_dir.is_absolute():
                    git_dir = repo / git_dir
            except subprocess.CalledProcessError:
                raise ValueError(f"Not a git repository: {repo}")

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_file = hooks_dir / "post-commit"

        # Check if hook already exists
        if hook_file.exists():
            # Backup existing hook
            backup_file = hooks_dir / "post-commit.backup"
            shutil.copy2(hook_file, backup_file)

        hook_file.write_text(hook_content)
        hook_file.chmod(0o755)

        return hook_file


def uninstall_git_hook(global_uninstall: bool = False, repo_path: Optional[str] = None) -> bool:
    """
    Uninstall the post-commit hook.

    Args:
        global_uninstall: If True, remove from git template
        repo_path: Path to specific repo (defaults to current directory)

    Returns:
        True if hook was removed, False if it didn't exist
    """
    if global_uninstall:
        try:
            result = subprocess.run(
                ["git", "config", "--global", "init.templateDir"],
                capture_output=True,
                text=True,
            )
            template_dir = result.stdout.strip()

            if not template_dir:
                return False

            hook_file = Path(template_dir) / "hooks" / "post-commit"
            if hook_file.exists():
                hook_file.unlink()
                return True
            return False

        except Exception:
            return False

    else:
        if repo_path:
            repo = Path(repo_path)
        else:
            repo = Path.cwd()

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            git_dir = Path(result.stdout.strip())
            if not git_dir.is_absolute():
                git_dir = repo / git_dir

            hook_file = git_dir / "hooks" / "post-commit"
            if hook_file.exists():
                hook_file.unlink()
                return True
            return False

        except Exception:
            return False