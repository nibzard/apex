"""Agent-specific MCP tools."""

from __future__ import annotations

import random
from typing import List


def mcp_apex_progress(task_id: str, percent: float, message: str) -> dict:
    """Return a progress report payload."""
    percent = max(0.0, min(100.0, percent))
    return {"task_id": task_id, "progress": percent, "message": message}


def mcp_apex_sample(prompt: str, options: List[str]) -> str:
    """Sample a decision from the provided options."""
    if not options:
        raise ValueError("options must not be empty")
    return random.choice(options)
