"""APEX - Adversarial Pair EXecution.

A CLI/TUI orchestration tool for adversarial pair coding with AI agents.
"""

__version__ = "1.0.0"
__author__ = "APEX Team"
__email__ = "wave@nibzard.com"

from apex.config import Config
from apex.types import AgentType, ProjectConfig, SessionState
from apex.vcs import GitHubClient, GitWrapper, auto_commit, generate_commit_message

__all__ = [
    "Config",
    "AgentType",
    "SessionState",
    "ProjectConfig",
    "GitWrapper",
    "GitHubClient",
    "auto_commit",
    "generate_commit_message",
]
