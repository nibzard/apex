"""Minimal static prompts for Claude CLI workers in APEX v2.0.

These are ultra-lightweight prompts that teach Claude CLI processes how to:
1. Read TaskBriefings from LMDB
2. Execute the specified task
3. Store deliverables to LMDB
4. Signal completion

The entire worker system is based on Claude CLI processes, not Python classes.
"""

from apex.core.task_briefing import TaskRole


def get_worker_prompt(role: TaskRole, project_id: str, task_id: str) -> str:
    """Get minimal prompt for a Claude CLI worker process.

    Args:
        role: Worker role (Coder or Adversary)
        project_id: Project identifier
        task_id: Task identifier

    Returns:
        Minimal prompt string for claude CLI

    """
    briefing_key = f"/projects/{project_id}/briefings/{task_id}"

    base_prompt = f"""You are an ephemeral {role.value} worker in APEX v2.0.

PROTOCOL:
1. Read your TaskBriefing: mcp__lmdb__read {{"key": "{briefing_key}"}}
2. Execute the task as specified in the briefing
3. Store ALL deliverables to the LMDB keys specified in the briefing
4. When complete, output exactly: "TASK COMPLETE"

Your briefing contains:
- objective: What to accomplish
- context_pointers: LMDB keys with context data
- deliverables: Required outputs with their LMDB keys
- quality_criteria: Standards to meet

Start by reading your briefing now."""

    # Add role-specific guidance
    if role == TaskRole.CODER:
        base_prompt += """

CODER SPECIALIZATION:
- Focus on implementation, coding, and development
- Produce clean, well-documented code
- Include tests when specified
- Follow project coding standards from context"""

    elif role == TaskRole.ADVERSARY:
        base_prompt += """

ADVERSARY SPECIALIZATION:
- Focus on security testing and quality assurance
- Find vulnerabilities and edge cases
- Generate comprehensive test cases
- Provide actionable security recommendations"""

    return base_prompt


def get_simple_coder_prompt(briefing_key: str) -> str:
    """Get the simplest possible Coder worker prompt."""
    return f"""You are a Coder worker.

1. Read task: mcp__lmdb__read {{"key": "{briefing_key}"}}
2. Execute the task as specified
3. Store outputs to the LMDB keys in the briefing
4. Reply: "TASK COMPLETE"

Start now."""


def get_simple_adversary_prompt(briefing_key: str) -> str:
    """Get the simplest possible Adversary worker prompt."""
    return f"""You are an Adversary worker for security testing.

1. Read task: mcp__lmdb__read {{"key": "{briefing_key}"}}
2. Test for security issues and quality problems
3. Store findings to the LMDB keys in the briefing
4. Reply: "TASK COMPLETE"

Start now."""


def build_claude_command(
    role: TaskRole, project_id: str, task_id: str, mcp_config_path: str
) -> list[str]:
    """Build the complete claude CLI command for a worker.

    Args:
        role: Worker role
        project_id: Project ID
        task_id: Task ID
        mcp_config_path: Path to MCP configuration

    Returns:
        Command list for subprocess execution

    """
    briefing_key = f"/projects/{project_id}/briefings/{task_id}"

    if role == TaskRole.CODER:
        prompt = get_simple_coder_prompt(briefing_key)
    elif role == TaskRole.ADVERSARY:
        prompt = get_simple_adversary_prompt(briefing_key)
    else:
        prompt = get_worker_prompt(role, project_id, task_id)

    command = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--mcp-config",
        mcp_config_path,
        "--model",
        "claude-3-5-sonnet-20241022",
    ]

    return command
