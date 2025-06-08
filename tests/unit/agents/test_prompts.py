"""Tests for AgentPrompts."""

from apex.agents.prompts import AgentPrompts
from apex.types import AgentType, ProjectConfig


class TestAgentPrompts:
    """Agent prompt generation tests."""

    def test_generate_supervisor_prompt(self):
        config = ProjectConfig(
            project_id="1",
            name="TestProj",
            description="Demo project",
            tech_stack=["python"],
            project_type="lib",
            features=[],
        )
        prompt = AgentPrompts.get_prompt(
            AgentType.SUPERVISOR, config, "Do the thing"
        )
        assert "Supervisor agent" in prompt
        assert "TestProj" in prompt
        assert "Do the thing" in prompt
