"""APEX - Adversarial Pair EXecution.

A CLI/TUI orchestration tool for adversarial pair coding with AI agents.
"""

__version__ = "1.0.0"
__author__ = "APEX Team"
__email__ = "wave@nibzard.com"

from apex.config import Config
from apex.types import AgentType, SessionState, ProjectConfig

__all__ = [
    "Config",
    "AgentType", 
    "SessionState",
    "ProjectConfig",
]