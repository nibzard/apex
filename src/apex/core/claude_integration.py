"""Claude Code integration utilities for APEX."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from apex.types import AgentType, ProjectConfig


class ClaudeCodeIntegration:
    """Integration utilities for Claude Code and APEX."""

    def __init__(self, project_config: ProjectConfig, project_dir: Path):
        """Initialize Claude Code integration.

        Args:
            project_config: APEX project configuration
            project_dir: Project directory path

        """
        self.project_config = project_config
        self.project_dir = project_dir
        self.mcp_config_path = project_dir / ".mcp.json"

    def setup_mcp_configuration(self, lmdb_path: Optional[Path] = None) -> None:
        """Set up MCP configuration for the project.

        Args:
            lmdb_path: Optional custom path for LMDB database

        """
        if lmdb_path is None:
            lmdb_path = self.project_dir / "apex_shared.db"

        mcp_config = {
            "mcpServers": {
                "apex-lmdb": {
                    "command": "python",
                    "args": ["-m", "apex.mcp"],
                    "env": {
                        "APEX_LMDB_PATH": str(lmdb_path),
                        "APEX_LMDB_MAP_SIZE": "1073741824"  # 1GB
                    }
                }
            }
        }

        # Write MCP configuration
        with open(self.mcp_config_path, 'w') as f:
            json.dump(mcp_config, f, indent=2)

        print(f"✅ Created MCP configuration: {self.mcp_config_path}")

    def is_claude_available(self) -> bool:
        """Check if Claude Code is available in the environment."""
        return shutil.which("claude") is not None

    def get_claude_command(self, agent_type: AgentType, prompt: str) -> List[str]:
        """Build Claude Code command for an agent.

        Args:
            agent_type: Type of agent to start
            prompt: Initial prompt for the agent

        Returns:
            Command list for running Claude Code

        """
        if not self.is_claude_available():
            raise RuntimeError("Claude Code is not available. Please install Claude Code.")

        # Build command with project directory and MCP configuration
        command = [
            "claude",
            "--working-directory", str(self.project_dir),
            "--prompt", prompt,
            "--model", "claude-sonnet-4-20250514",
            "--output-format", "stream-json",
            "--max-turns", "50"
        ]

        # Add agent-specific tool allowlist
        allowed_tools = self._get_allowed_tools(agent_type)
        if allowed_tools:
            command.extend(["--allowedTools", ",".join(allowed_tools)])

        return command

    def _get_allowed_tools(self, agent_type: AgentType) -> List[str]:
        """Get allowed tools for agent type.

        Args:
            agent_type: Type of agent

        Returns:
            List of allowed tool names

        """
        # Base APEX MCP tools
        base_tools = [
            "apex_lmdb_read",
            "apex_lmdb_write", 
            "apex_lmdb_list",
            "apex_lmdb_delete",
            "apex_lmdb_scan",
            "apex_project_status"
        ]

        # Add agent-specific tools
        if agent_type == AgentType.SUPERVISOR:
            base_tools.extend([
                "Bash",  # For git and gh commands
                "LS",    # For exploring project structure
                "Read",  # For reading files
            ])
        elif agent_type == AgentType.CODER:
            base_tools.extend([
                "Edit",     # For editing files
                "MultiEdit", # For multiple edits
                "Write",    # For creating files
                "Read",     # For reading files
                "LS",       # For exploring structure
                "Bash",     # For running tests
            ])
        elif agent_type == AgentType.ADVERSARY:
            base_tools.extend([
                "Read",     # For code review
                "LS",       # For exploring structure
                "Bash",     # For running security tests
                "Grep",     # For searching code
                "Glob",     # For finding files
            ])

        return base_tools

    def start_agent_session(self, agent_type: AgentType, prompt: str, background: bool = True) -> subprocess.Popen:
        """Start a Claude Code session for an agent.

        Args:
            agent_type: Type of agent to start
            prompt: Initial prompt for the agent
            background: Whether to run in background

        Returns:
            Subprocess handle

        """
        command = self.get_claude_command(agent_type, prompt)
        
        if background:
            # Run in background with proper stdio handling
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.project_dir
            )
        else:
            # Run interactively
            process = subprocess.Popen(
                command,
                cwd=self.project_dir
            )

        return process

    def check_mcp_server_status(self) -> Dict[str, bool]:
        """Check if MCP servers are properly configured.

        Returns:
            Dictionary with server status

        """
        status = {}

        # Check if .mcp.json exists
        status["mcp_config_exists"] = self.mcp_config_path.exists()

        # Check if apex.mcp module is available
        try:
            import apex.mcp
            status["apex_mcp_available"] = True
        except ImportError:
            status["apex_mcp_available"] = False

        # Check if Claude Code can see the MCP server
        if self.is_claude_available() and self.mcp_config_path.exists():
            try:
                result = subprocess.run(
                    ["claude", "mcp", "list"],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                status["claude_mcp_working"] = result.returncode == 0
            except:
                status["claude_mcp_working"] = False
        else:
            status["claude_mcp_working"] = False

        return status

    def get_agent_prompt(self, agent_type: AgentType) -> str:
        """Get the appropriate prompt for an agent type.

        Args:
            agent_type: Type of agent

        Returns:
            Formatted prompt string

        """
        base_prompt = f"""You are an APEX {agent_type.value} agent working on the project: {self.project_config.name}

Project Description: {self.project_config.description}
Tech Stack: {', '.join(self.project_config.tech_stack)}
Features: {', '.join(self.project_config.features)}

You have access to APEX MCP tools for coordination:
- apex_lmdb_read: Read data from shared memory
- apex_lmdb_write: Write data to shared memory  
- apex_lmdb_list: List keys with optional prefix
- apex_lmdb_scan: Scan key-value pairs
- apex_project_status: Get project status overview

Project ID: {self.project_config.project_id}

Use the shared memory to coordinate with other agents and track progress.
Always use the project ID when reading/writing project-specific data.
"""

        if agent_type == AgentType.SUPERVISOR:
            return base_prompt + """
Role: You are the Supervisor agent responsible for:
- Breaking down user requests into actionable tasks
- Assigning tasks to Coder and Adversary agents
- Monitoring overall project progress
- Making high-level decisions about architecture and approach
- Using git and GitHub for version control operations

Start by reading the current project status and checking for pending tasks.
"""

        elif agent_type == AgentType.CODER:
            return base_prompt + """
Role: You are the Coder agent responsible for:
- Implementing code based on task assignments
- Writing tests for your implementations
- Following coding best practices and project conventions
- Updating documentation as needed
- Running tests to verify your work

Start by checking for tasks assigned to you and begin implementation.
"""

        elif agent_type == AgentType.ADVERSARY:
            return base_prompt + """
Role: You are the Adversary agent responsible for:
- Reviewing code for security vulnerabilities
- Testing edge cases and error conditions
- Ensuring code quality and performance
- Challenging assumptions and implementations
- Running security and quality checks

Start by checking for code that needs review and begin your analysis.
"""

        return base_prompt


def setup_project_mcp(project_dir: Path, project_config: ProjectConfig) -> None:
    """Set up MCP configuration for an APEX project.

    Args:
        project_dir: Project directory
        project_config: Project configuration

    """
    integration = ClaudeCodeIntegration(project_config, project_dir)
    integration.setup_mcp_configuration()

    # Check status and provide feedback
    status = integration.check_mcp_server_status()
    
    print("\n🔧 MCP Setup Status:")
    for check, result in status.items():
        emoji = "✅" if result else "❌"
        print(f"  {emoji} {check.replace('_', ' ').title()}: {result}")
    
    if all(status.values()):
        print("\n🚀 APEX MCP integration is ready!")
    else:
        print("\n⚠️  Some MCP setup issues detected. Check the status above.")

    return integration