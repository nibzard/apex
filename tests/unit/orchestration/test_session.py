"""Tests for SessionManager."""

from apex.orchestration import SessionManager
from apex.types import ProjectConfig


def sample_project() -> ProjectConfig:
    """Create a sample project configuration for testing."""
    return ProjectConfig(
        project_id="proj1",
        name="Test",
        description="desc",
        tech_stack=["python"],
        project_type="lib",
        features=["a"],
    )


def test_create_and_get_session(tmp_path):
    """Test session creation and retrieval."""
    manager = SessionManager(tmp_path)
    config = sample_project()

    session = manager.create(config)
    retrieved = manager.get(session.session_id)

    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    assert retrieved.config.name == "Test"


def test_list_sessions(tmp_path):
    """Test listing multiple sessions."""
    manager = SessionManager(tmp_path)
    config = sample_project()

    manager.create(config)
    manager.create(config)

    sessions = manager.list_sessions()
    assert len(sessions) == 2
