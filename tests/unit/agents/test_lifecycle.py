"""Tests for AgentLifecycle."""

from apex.agents.lifecycle import AgentLifecycle
from apex.types import AgentType


class TestAgentLifecycle:
    """Lifecycle operations tests."""

    def test_start_and_stop_agent(self):
        """Verify agents can start and stop correctly."""
        lifecycle = AgentLifecycle()
        lifecycle.start_agent(AgentType.CODER)
        assert lifecycle.health_check(AgentType.CODER)
        lifecycle.stop_agent(AgentType.CODER)
        assert not lifecycle.health_check(AgentType.CODER)
