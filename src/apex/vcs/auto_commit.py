"""Automatic commit utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .git_ops import GitWrapper, generate_commit_message


def auto_commit(repo_path: Path | str = ".", message: Optional[str] = None) -> str:
    """Stage all changes and create a commit.

    Parameters
    ----------
    repo_path:
        Path to the git repository.
    message:
        Optional commit message. If not provided a simple message is generated.
    Returns
    -------
    str
        Commit SHA of the created commit.
    """
    wrapper = GitWrapper(repo_path)
    wrapper.add_all()
    commit_message = message or generate_commit_message("Auto commit")
    return wrapper.commit(commit_message)
