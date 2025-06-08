"""Process management for APEX agents."""

from __future__ import annotations

import asyncio
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

import psutil

from apex.types import AgentType


class ClaudeProcess:
    """Wrapper for Claude CLI process with streaming JSON output."""

    def __init__(
        self,
        agent_type: AgentType,
        prompt: str,
        mcp_config: Path,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        self.agent_type = agent_type
        self.prompt = prompt
        self.mcp_config = mcp_config
        self.model = model
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[float] = None

        # Build Claude CLI command
        self.command = self._build_command()

    def _build_command(self) -> List[str]:
        """Build Claude CLI command with MCP configuration."""
        return [
            "claude",
            "-p",
            self.prompt,
            "--output-format",
            "stream-json",
            "--model",
            self.model,
            "--mcp-config",
            str(self.mcp_config),
            "--allowedTools",
            self._get_allowed_tools(),
            "--max-turns",
            "50",
            "--verbose",
        ]

    def _get_allowed_tools(self) -> str:
        """Get allowed tools for this agent type."""
        base_tools = [
            "mcp__lmdb__read",
            "mcp__lmdb__write",
            "mcp__lmdb__list",
            "mcp__lmdb__delete",
            "mcp__lmdb__watch",
            "mcp__lmdb__cursor_scan",
            "mcp__lmdb__transaction",
        ]

        # Add agent-specific tools
        if self.agent_type == AgentType.SUPERVISOR:
            base_tools.extend(
                [
                    "Bash",  # For git and gh commands
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
                    "Bash",  # For running tests
                    "mcp__apex__progress",
                    "mcp__apex__complete_task",
                ]
            )
        elif self.agent_type == AgentType.ADVERSARY:
            base_tools.extend(
                [
                    "Read",
                    "Bash",  # For testing and analysis
                    "mcp__apex__sample",
                    "mcp__apex__progress",
                ]
            )

        return ",".join(base_tools)

    async def start(self) -> None:
        """Start the Claude CLI process."""
        if self.process and self.process.poll() is None:
            return

        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )
        self.start_time = time.time()

    def stop(self) -> None:
        """Terminate the process."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def is_running(self) -> bool:
        """Check if the process is running."""
        return bool(self.process and self.process.poll() is None)

    async def restart(self) -> None:
        """Restart the process."""
        self.stop()
        await self.start()

    def memory_usage(self) -> int:
        """Return memory usage in bytes."""
        if self.process and self.is_running():
            try:
                proc = psutil.Process(self.process.pid)
                return proc.memory_info().rss
            except psutil.NoSuchProcess:
                return 0
        return 0

    async def read_json_stream(self) -> AsyncGenerator[Dict, None]:
        """Read streaming JSON output from Claude CLI."""
        if not self.process or not self.process.stdout:
            return

        while self.is_running():
            try:
                line = self.process.stdout.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue

                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        yield event
                    except json.JSONDecodeError:
                        # Skip non-JSON lines (might be debug output)
                        continue
            except Exception:
                break


class ManagedProcess:
    """Legacy wrapper for backward compatibility."""

    def __init__(self, command: List[str]) -> None:
        self.command = command
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[float] = None

    def start(self) -> None:
        """Start the process."""
        if self.process and self.process.poll() is None:
            return
        self.process = subprocess.Popen(self.command)
        self.start_time = time.time()

    def stop(self) -> None:
        """Terminate the process."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def is_running(self) -> bool:
        """Check if the process is running."""
        return bool(self.process and self.process.poll() is None)

    def restart(self) -> None:
        """Restart the process."""
        self.stop()
        self.start()

    def memory_usage(self) -> int:
        """Return memory usage in bytes."""
        if self.process and self.is_running():
            proc = psutil.Process(self.process.pid)
            return proc.memory_info().rss
        return 0


class ProcessManager:
    """Manage multiple agent processes."""

    def __init__(self, mcp_config: Optional[Path] = None) -> None:
        self.processes: Dict[str, ManagedProcess] = {}
        self.claude_processes: Dict[str, ClaudeProcess] = {}
        self._desired_state: Dict[str, bool] = {}
        self.restart_events: Dict[str, int] = {}
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._monitor_interval = 1.0
        self.mcp_config = mcp_config or Path("configs/lmdb_mcp.json")

    def spawn(self, name: str, command: List[str]) -> None:
        """Spawn a new process with given command."""
        proc = ManagedProcess(command)
        proc.start()
        self.processes[name] = proc
        self._desired_state[name] = True

    async def spawn_claude_agent(
        self, agent_type: AgentType, prompt: str, name: Optional[str] = None
    ) -> str:
        """Spawn a Claude CLI agent process.

        Args:
            agent_type: Type of agent to spawn
            prompt: Initial prompt for the agent
            name: Optional name for the process (defaults to agent_type.value)

        Returns:
            Name of the spawned process

        """
        process_name = name or f"{agent_type.value}_agent"

        claude_proc = ClaudeProcess(
            agent_type=agent_type, prompt=prompt, mcp_config=self.mcp_config
        )

        await claude_proc.start()
        self.claude_processes[process_name] = claude_proc
        self._desired_state[process_name] = True

        return process_name

    def stop(self, name: str) -> None:
        """Stop a managed process."""
        if name in self.processes:
            self._desired_state[name] = False
            self.processes[name].stop()
        elif name in self.claude_processes:
            self._desired_state[name] = False
            self.claude_processes[name].stop()

    async def restart_claude(self, name: str) -> None:
        """Restart a Claude process."""
        if name in self.claude_processes:
            self._desired_state[name] = True
            await self.claude_processes[name].restart()

    def restart(self, name: str) -> None:
        """Restart a managed process."""
        if name in self.processes:
            self._desired_state[name] = True
            self.processes[name].restart()

    def health_check(self, name: str) -> bool:
        """Return True if process is running."""
        if name in self.processes:
            proc = self.processes.get(name)
            return bool(proc and proc.is_running())
        elif name in self.claude_processes:
            proc = self.claude_processes.get(name)
            return bool(proc and proc.is_running())
        return False

    def monitor_resources(self) -> Dict[str, int]:
        """Return memory usage per process."""
        usage = {}
        for name, proc in self.processes.items():
            usage[name] = proc.memory_usage()
        for name, proc in self.claude_processes.items():
            usage[name] = proc.memory_usage()
        return usage

    def get_claude_process(self, name: str) -> Optional[ClaudeProcess]:
        """Get a Claude process by name."""
        return self.claude_processes.get(name)

    async def get_claude_stream(
        self, name: str
    ) -> Optional[AsyncGenerator[Dict, None]]:
        """Get streaming JSON output from a Claude process."""
        proc = self.claude_processes.get(name)
        if proc:
            async for event in proc.read_json_stream():
                yield event

    def list_processes(self) -> Dict[str, Dict[str, any]]:
        """List all managed processes with their status."""
        result = {}

        for name, proc in self.processes.items():
            result[name] = {
                "type": "generic",
                "running": proc.is_running(),
                "memory": proc.memory_usage(),
                "command": proc.command,
                "start_time": proc.start_time,
            }

        for name, proc in self.claude_processes.items():
            result[name] = {
                "type": "claude",
                "agent_type": proc.agent_type.value,
                "running": proc.is_running(),
                "memory": proc.memory_usage(),
                "command": proc.command,
                "start_time": proc.start_time,
            }

        return result

    def shutdown(self) -> None:
        """Stop all processes."""
        for name, proc in self.processes.items():
            self._desired_state[name] = False
            proc.stop()
        for name, proc in self.claude_processes.items():
            self._desired_state[name] = False
            proc.stop()
        self.processes.clear()
        self.claude_processes.clear()
        self._desired_state.clear()

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            # Monitor regular processes
            for name, proc in list(self.processes.items()):
                if self._desired_state.get(name) and not proc.is_running():
                    proc.restart()
                    self.restart_events[name] = self.restart_events.get(name, 0) + 1

            # Monitor Claude processes (can't restart synchronously)
            for name, proc in list(self.claude_processes.items()):
                if self._desired_state.get(name) and not proc.is_running():
                    # Note: Claude processes need async restart, this is a limitation
                    # In a real implementation, we'd use asyncio with threading
                    self.restart_events[name] = self.restart_events.get(name, 0) + 1

            time.sleep(self._monitor_interval)

    def monitor(self, start: bool = True, interval: float = 1.0) -> None:
        """Start or stop background monitoring."""
        if start:
            if self._monitor_thread and self._monitor_thread.is_alive():
                return
            self._monitor_interval = interval
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self._monitor_thread.start()
        else:
            self._stop_event.set()
            if self._monitor_thread:
                self._monitor_thread.join()
