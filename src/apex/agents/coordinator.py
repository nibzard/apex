"""Agent coordination logic."""

from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Dict, List

from apex.types import AgentType, TaskInfo


class AgentCoordinator:
    """Simple in-memory agent coordinator."""

    def __init__(self) -> None:
        """Initialize coordinator with empty task stores."""
        self._tasks: Dict[str, TaskInfo] = {}
        self._agent_tasks: Dict[AgentType, List[str]] = defaultdict(list)

    def assign_task(
        self, description: str, agent: AgentType, priority: str = "medium"
    ) -> TaskInfo:
        """Create and assign a new task."""
        task_id = uuid.uuid4().hex
        task = TaskInfo(
            task_id=task_id,
            description=description,
            assigned_to=agent,
            priority=priority,
        )
        self._tasks[task_id] = task
        self._agent_tasks[agent].append(task_id)
        return task

    def get_tasks_for_agent(self, agent: AgentType) -> List[TaskInfo]:
        """Return tasks assigned to the given agent."""
        return [self._tasks[tid] for tid in self._agent_tasks.get(agent, [])]

    def complete_task(self, task_id: str) -> None:
        """Mark a task as completed."""
        task = self._tasks.get(task_id)
        if task is not None:
            task.status = "completed"
            task.completed_at = task.completed_at or task.created_at

    def all_tasks(self) -> List[TaskInfo]:
        """Return all tracked tasks."""
        return list(self._tasks.values())
