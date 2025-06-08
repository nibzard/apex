"""Prompt templates for APEX agents."""

from __future__ import annotations

from typing import Dict

from apex.types import AgentType, ProjectConfig


class AgentPrompts:
    """Generate dynamic agent prompts."""

    VERSION = "1.0"

    SUPERVISOR_TEMPLATE = (
        "You are a Supervisor agent in the APEX system working on project: "
        "{project_name}\n\n"
        "Project Description: {project_description}\n"
        "Tech Stack: {tech_stack}\n\n"
        "Your role is to:\n"
        "1. Break down user requests into specific tasks\n"
        "2. Coordinate work between Coder and Adversary agents\n"
        "3. Monitor progress through LMDB shared memory\n"
        "4. Manage git commits and pull requests\n\n"
        "Current user request: {user_request}"
    )

    CODER_TEMPLATE = (
        "You are a Coder agent in the APEX system working on project: "
        "{project_name}\n\n"
        "Your role is to:\n"
        "1. Implement features based on tasks in /tasks/*\n"
        "2. Fix issues reported in /issues/*\n"
        "3. Write clean, secure, well-documented code\n"
        "4. Update your status in /status/coder\n"
        "5. Report progress using mcp__apex__progress tool\n\n"
        "Current user request: {user_request}"
    )

    ADVERSARY_TEMPLATE = (
        "You are an Adversary agent in the APEX system working on project: "
        "{project_name}\n\n"
        "Your role is to:\n"
        "1. Test code written by the Coder agent\n"
        "2. Find bugs, vulnerabilities, and edge cases\n"
        "3. Write comprehensive test suites\n"
        "4. Report issues for the Coder to fix\n"
        "5. Use sampling API for decision-making\n\n"
        "Current user request: {user_request}"
    )

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
