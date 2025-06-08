"""Git operations wrapper using GitPython."""

from __future__ import annotations

from pathlib import Path

from git import GitCommandError, Repo


class GitWrapper:
    """Convenient wrapper around :class:`git.Repo`."""

    def __init__(self, repo_path: Path | str = ".") -> None:
        self.repo_path = Path(repo_path)
        try:
            self.repo = Repo(self.repo_path, search_parent_directories=True)
        except GitCommandError:
            self.repo = Repo.init(self.repo_path)

    @property
    def branch(self) -> str:
        """Return current branch name."""
        return self.repo.active_branch.name

    def status(self) -> str:
        """Return ``git status`` output."""
        return self.repo.git.status()

    def add_all(self) -> None:
        """Stage all changes."""
        self.repo.git.add(all=True)

    def commit(self, message: str) -> str:
        """Create commit with ``message`` and return commit SHA."""
        commit_obj = self.repo.index.commit(message)
        return commit_obj.hexsha

    def create_branch(self, name: str, checkout: bool = False) -> None:
        """Create a new branch and optionally check it out."""
        self.repo.git.branch(name)
        if checkout:
            self.repo.git.checkout(name)

    def checkout_branch(self, name: str) -> None:
        """Checkout existing branch."""
        self.repo.git.checkout(name)

    def merge(self, source: str) -> None:
        """Merge ``source`` branch into current branch."""
        self.repo.git.merge(source)


def generate_commit_message(summary: str) -> str:
    """Generate simple commit message from summary."""
    return summary.strip()
