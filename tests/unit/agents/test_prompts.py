"""Tests for AgentPrompts."""

from apex.agents.prompts import AgentPrompts
from apex.types import AgentType, ProjectConfig


def sample_config() -> ProjectConfig:
    """Return a sample project configuration for tests."""
    return ProjectConfig(
        project_id="p1",
        name="Demo",
        description="Demo project",
        tech_stack=["python", "docker"],
        project_type="app",
        features=[],
    )


def test_supervisor_prompt() -> None:
    """Supervisor prompt should include config details and request."""
    config = sample_config()
    prompt = AgentPrompts.supervisor_prompt(config, "add login")
    assert config.name in prompt
    assert config.description in prompt
    assert "python, docker" in prompt
    assert "add login" in prompt
    assert "{project_name}" not in prompt

    # generic accessor should match
    assert prompt == AgentPrompts.get_prompt(AgentType.SUPERVISOR, config, "add login")


def test_coder_prompt() -> None:
    """Coder prompt should include the project name."""
    config = sample_config()
    prompt = AgentPrompts.coder_prompt(config)
    assert config.name in prompt
    assert "{project_name}" not in prompt


def test_adversary_prompt() -> None:
    """Adversary prompt should include the project name."""
    config = sample_config()
    prompt = AgentPrompts.adversary_prompt(config)
    assert config.name in prompt
    assert "{project_name}" not in prompt
