"""Tests for AgentCoordinator."""

from apex.agents.coordinator import AgentCoordinator
from apex.types import AgentType


class TestAgentCoordinator:
    """Coordinator behavior tests."""

    def test_assign_and_complete_task(self):
        """Ensure tasks can be assigned and completed."""
        coordinator = AgentCoordinator()
        task = coordinator.assign_task("Implement feature", AgentType.CODER)
        tasks = coordinator.get_tasks_for_agent(AgentType.CODER)
        assert tasks[0].task_id == task.task_id
        coordinator.complete_task(task.task_id)
        assert tasks[0].status == "completed"
