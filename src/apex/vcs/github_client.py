"""Minimal GitHub API integration using PyGithub."""

from __future__ import annotations

import os
from typing import Optional

from github import Github


class GitHubClient:
    """Wrapper around :class:`github.Github`."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token not provided")
        self.client = Github(self.token)

    def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        draft: bool = False,
    ) -> str:
        """Create a pull request and return its URL."""
        repo = self.client.get_repo(repo_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base, draft=draft)
        return pr.html_url

    def create_issue(self, repo_name: str, title: str, body: str, labels: str | None = None) -> str:
        """Create an issue and return its URL."""
        repo = self.client.get_repo(repo_name)
        issue = repo.create_issue(title=title, body=body, labels=labels.split(",") if labels else None)
        return issue.html_url

    def create_release(self, repo_name: str, tag: str, title: str, notes: str) -> str:
        """Create a release and return its URL."""
        repo = self.client.get_repo(repo_name)
        release = repo.create_git_release(tag=tag, name=title, message=notes)
        return release.html_url

