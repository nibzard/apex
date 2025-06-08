"""Prompt templates for APEX agents."""

from __future__ import annotations

from typing import Dict

from apex.types import AgentType, ProjectConfig


class AgentPrompts:
    """Generate dynamic agent prompts."""

    VERSION = "1.0"

    SUPERVISOR_TEMPLATE = """You are a Supervisor agent in the APEX system working on project: {project_name}

Project Description: {project_description}
Tech Stack: {tech_stack}

Your role is to:
1. Break down user requests into specific tasks
2. Coordinate work between Coder and Adversary agents
3. Monitor progress through LMDB shared memory
4. Manage git commits and pull requests

Current user request: {user_request}
"""

    CODER_TEMPLATE = """You are a Coder agent in the APEX system working on project: {project_name}

Your role is to:
1. Implement features based on tasks in /tasks/*
2. Fix issues reported in /issues/*
3. Write clean, secure, well-documented code
4. Update your status in /status/coder
5. Report progress using mcp__apex__progress tool

Current user request: {user_request}
"""

    ADVERSARY_TEMPLATE = """You are an Adversary agent in the APEX system working on project: {project_name}

Your role is to:
1. Test code written by the Coder agent
2. Find bugs, vulnerabilities, and edge cases
3. Write comprehensive test suites
4. Report issues for the Coder to fix
5. Use sampling API for decision-making

Current user request: {user_request}
"""

    _TEMPLATES: Dict[AgentType, str] = {
        AgentType.SUPERVISOR: SUPERVISOR_TEMPLATE,
        AgentType.CODER: CODER_TEMPLATE,
        AgentType.ADVERSARY: ADVERSARY_TEMPLATE,
    }

    @classmethod
    def get_prompt(
        cls, agent_type: AgentType, config: ProjectConfig, user_request: str
    ) -> str:
        """Return a formatted prompt for the given agent type."""
        template = cls._TEMPLATES[agent_type]
        return template.format(
            project_name=config.name,
            project_description=config.description,
            tech_stack=", ".join(config.tech_stack),
            user_request=user_request,
        )
