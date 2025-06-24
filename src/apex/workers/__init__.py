"""Ephemeral Workers for APEX v2.0 Orchestrator-Worker Architecture.

This module provides minimal prompts for Claude CLI workers in the v2.0
Orchestrator-Worker architecture.

Architecture:
- Workers are ephemeral Claude CLI processes, not Python classes
- Each worker handles exactly one TaskBriefing
- Workers communicate via LMDB using MCP tools
- Lifecycle: spawn → execute → terminate

Worker Types:
- Coder: Implementation, coding, and development tasks
- Adversary: Security testing, quality assurance, and code review
"""

from .claude_prompts import build_claude_command, get_worker_prompt

__all__ = [
    "build_claude_command",
    "get_worker_prompt",
]
