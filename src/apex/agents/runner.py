#!/usr/bin/env python3
"""Agent runner for APEX containers."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Optional

from apex.agents.prompts import AgentPrompts
from apex.types import AgentType, ProjectConfig


class AgentRunner:
    """Runs a single APEX agent in a container."""

    def __init__(self, agent_type: AgentType):
        """Initialize agent runner.

        Args:
            agent_type: Type of agent to run

        """
        self.agent_type = agent_type
        self.process: Optional[asyncio.subprocess.Process] = None
        self.running = False

        # Get configuration from environment
        self.lmdb_path = Path(
            os.getenv("APEX_LMDB_PATH", "/workspace/.apex/lmdb/apex.db")
        )
        self.project_dir = Path("/workspace")
        self.mcp_server_host = os.getenv("MCP_SERVER_HOST", "localhost")
        self.mcp_server_port = int(os.getenv("MCP_SERVER_PORT", "8000"))

        # Create MCP configuration
        self.mcp_config_path = self.project_dir / ".apex" / "mcp-config.json"
        self._create_mcp_config()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _create_mcp_config(self) -> None:
        """Create MCP configuration for this agent."""
        import json

        config = {
            "mcpServers": {
                "lmdb": {
                    "command": "python",
                    "args": ["-m", "apex.mcp.claude_lmdb_server"],
                    "env": {
                        "APEX_LMDB_PATH": str(self.lmdb_path),
                        "APEX_LMDB_MAP_SIZE": "1073741824",
                    },
                }
            }
        }

        # Create config directory
        self.mcp_config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write configuration
        with open(self.mcp_config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        print(f"Received signal {signum}, shutting down agent...")
        self.running = False
        if self.process:
            self.process.terminate()

    def get_agent_prompt(self) -> str:
        """Get the appropriate prompt for this agent type."""
        # Create a basic project config for prompt generation
        project_config = ProjectConfig(
            project_id=os.getenv("APEX_PROJECT_ID", "default"),
            name=os.getenv("APEX_PROJECT_NAME", "APEX Container Project"),
            description=os.getenv(
                "APEX_PROJECT_DESCRIPTION",
                "An APEX project running in containers",
            ),
            tech_stack=["Python", "Docker"],
            features=["Multi-agent coordination", "LMDB storage"],
        )

        prompts = AgentPrompts()
        return prompts.get_agent_prompt(self.agent_type, project_config)

    def get_claude_command(self) -> list[str]:
        """Build Claude Code command for this agent."""
        prompt = self.get_agent_prompt()

        command = [
            "claude",
            "--add-dir",
            str(self.project_dir),
            "--mcp-config",
            str(self.mcp_config_path),
            "--print",
            prompt,
            "--output-format",
            "stream-json",
            "--model",
            "claude-sonnet-4-20250514",
            "--max-turns",
            "100",
            "--allowedTools",
            ",".join(self._get_allowed_tools()),
        ]

        return command

    def _get_allowed_tools(self) -> list[str]:
        """Get allowed tools for this agent type."""
        base_tools = [
            "mcp__lmdb__read",
            "mcp__lmdb__write",
            "mcp__lmdb__list",
            "mcp__lmdb__delete",
            "mcp__lmdb__cursor_scan",
            "mcp__lmdb__watch",
            "mcp__lmdb__project_status",
        ]

        if self.agent_type == AgentType.SUPERVISOR:
            base_tools.extend(
                [
                    "Bash",
                    "LS",
                    "Read",
                    "mcp__apex__assign_task",
                    "mcp__apex__progress",
                ]
            )
        elif self.agent_type == AgentType.CODER:
            base_tools.extend(
                [
                    "Edit",
                    "MultiEdit",
                    "Write",
                    "Read",
                    "LS",
                    "Bash",
                    "mcp__apex__progress",
                    "mcp__apex__complete_task",
                ]
            )
        elif self.agent_type == AgentType.ADVERSARY:
            base_tools.extend(
                [
                    "Read",
                    "LS",
                    "Bash",
                    "Grep",
                    "Glob",
                    "mcp__apex__sample",
                    "mcp__apex__report_issue",
                ]
            )

        return base_tools

    async def run(self) -> None:
        """Run the agent with Claude Code."""
        print(f"Starting {self.agent_type.value} agent...")

        self.running = True
        command = self.get_claude_command()

        try:
            # Start Claude Code process
            self.process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_dir,
            )

            print(f"Agent {self.agent_type.value} started with PID {self.process.pid}")

            # Monitor the process
            while self.running and self.process.returncode is None:
                try:
                    # Read output
                    stdout_line = await asyncio.wait_for(
                        self.process.stdout.readline(), timeout=1.0
                    )
                    if stdout_line:
                        print(
                            f"[{self.agent_type.value}] {stdout_line.decode().strip()}"
                        )

                except asyncio.TimeoutError:
                    # Check if process is still alive
                    if self.process.returncode is not None:
                        break
                    continue

            # Wait for process to complete
            await self.process.wait()
            print(
                f"Agent {self.agent_type.value} exited with code {self.process.returncode}"
            )

        except Exception as e:
            print(f"Error running agent {self.agent_type.value}: {e}")
            raise

    async def stop(self) -> None:
        """Stop the agent gracefully."""
        self.running = False
        if self.process and self.process.returncode is None:
            print(f"Stopping {self.agent_type.value} agent...")
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=10)
            except asyncio.TimeoutError:
                print(f"Force killing {self.agent_type.value} agent...")
                self.process.kill()
                await self.process.wait()


async def main():
    """Main entry point for agent runner."""
    # Get agent type from environment
    agent_type_str = os.getenv("APEX_AGENT_TYPE", "").lower()

    if not agent_type_str:
        print("Error: APEX_AGENT_TYPE environment variable is required")
        sys.exit(1)

    try:
        agent_type = AgentType(agent_type_str)
    except ValueError:
        print(
            f"Error: Invalid agent type '{agent_type_str}'. Must be one of: {[t.value for t in AgentType]}"
        )
        sys.exit(1)

    # Create and run agent
    runner = AgentRunner(agent_type)

    try:
        await runner.run()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Agent runner error: {e}")
        sys.exit(1)
    finally:
        await runner.stop()


if __name__ == "__main__":
    asyncio.run(main())
