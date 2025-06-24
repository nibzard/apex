"""APEX v2.0 Supervisor module.

The Supervisor is the persistent meta-agent that orchestrates the v2.0
Orchestrator-Worker architecture. It manages the entire project lifecycle
through a 5-stage orchestration loop:

PLAN → CONSTRUCT → INVOKE → MONITOR → INTEGRATE

Key components:
- engine.py: Core orchestration loop and task graph management
- planner.py: Task decomposition and dependency resolution
- orchestrator.py: Worker and Utility process management
- briefing.py: TaskBriefing generation system
"""

from .briefing import BriefingGenerator
from .engine import SupervisorEngine
from .orchestrator import ProcessOrchestrator
from .planner import TaskPlanner

__all__ = [
    "SupervisorEngine",
    "TaskPlanner",
    "ProcessOrchestrator",
    "BriefingGenerator",
]
