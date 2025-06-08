"""APEX - Adversarial Pair EXecution.

A CLI/TUI orchestration tool for adversarial pair coding with AI agents.
"""

__version__ = "1.0.0"
__author__ = "APEX Team"
__email__ = "wave@nibzard.com"

from apex.config import Config
from apex.types import AgentType, ProjectConfig, SessionState
from apex.agents import (
    AgentCoordinator,
    AgentLifecycle,
    AgentPrompts,
    mcp_apex_progress,
    mcp_apex_sample,
)

__all__ = [
    "Config",
    "AgentType",
    "SessionState",
    "ProjectConfig",
    "AgentPrompts",
    "AgentCoordinator",
    "AgentLifecycle",
    "mcp_apex_progress",
    "mcp_apex_sample",
]
