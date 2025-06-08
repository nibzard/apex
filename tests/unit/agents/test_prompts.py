from apex.agents.prompts import AgentPrompts
from apex.types import ProjectConfig


def sample_config() -> ProjectConfig:
    return ProjectConfig(
        project_id="p1",
        name="Demo",
        description="Demo project",
        tech_stack=["python", "docker"],
        project_type="app",
        features=[],
    )


def test_supervisor_prompt() -> None:
    config = sample_config()
    prompt = AgentPrompts.supervisor_prompt(config, "add login")
    assert config.name in prompt
    assert config.description in prompt
    assert "python, docker" in prompt
    assert "add login" in prompt
    assert "{project_name}" not in prompt


def test_coder_prompt() -> None:
    config = sample_config()
    prompt = AgentPrompts.coder_prompt(config)
    assert config.name in prompt
    assert "{project_name}" not in prompt


def test_adversary_prompt() -> None:
    config = sample_config()
    prompt = AgentPrompts.adversary_prompt(config)
    assert config.name in prompt
    assert "{project_name}" not in prompt

