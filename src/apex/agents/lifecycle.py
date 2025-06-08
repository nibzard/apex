"""Agent lifecycle management."""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from apex.config import Config
from apex.types import AgentState, AgentType


class AgentLifecycle:
    """Manage agent startup, shutdown and health."""

    def __init__(self, config: Config | None = None) -> None:
        """Create lifecycle manager with optional config."""
        self.config = config or Config.get_default()
        self.states: Dict[AgentType, AgentState] = {}

    def start_agent(self, agent: AgentType) -> AgentState:
        """Start an agent."""
        state = AgentState(
            agent_type=agent,
            status="running",
            started_at=datetime.now(),
        )
        self.states[agent] = state
        return state

    def stop_agent(self, agent: AgentType) -> None:
        """Stop an agent."""
        if agent in self.states:
            self.states[agent].status = "stopped"

    def health_check(self, agent: AgentType) -> bool:
        """Check if an agent is healthy."""
        state = self.states.get(agent)
        return bool(state and state.status == "running")

    def restart_agent(self, agent: AgentType) -> AgentState:
        """Restart an agent."""
        self.stop_agent(agent)
        return self.start_agent(agent)

    def reload_config(self, config: Config) -> None:
        """Hot-reload configuration."""
        self.config = config
