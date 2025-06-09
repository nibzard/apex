"""Tests for OrchestrationEngine."""

from apex.orchestration import EventBus, OrchestrationEngine, SessionManager
from apex.types import ProjectConfig


def sample_project() -> ProjectConfig:
    """Create a sample project configuration for testing."""
    return ProjectConfig(
        project_id="p1",
        name="Engine",
        description="d",
        tech_stack=["py"],
        project_type="lib",
        features=[],
    )


def test_run_workflow(tmp_path):
    """Test workflow execution with session management."""
    session_manager = SessionManager(tmp_path)
    session = session_manager.create(sample_project())

    bus = EventBus()
    seen = []
    bus.subscribe("task_completed", lambda e: seen.append(e["data"]["task"]))

    engine = OrchestrationEngine(session_manager, bus)

    def step_a():
        seen.append("a")

    engine.run_workflow(session.session_id, [step_a])

    assert "a" in seen
    assert "step_a" in seen
