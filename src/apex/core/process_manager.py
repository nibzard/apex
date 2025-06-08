"""Process management for APEX agents."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

import psutil


class ManagedProcess:
    """Wrapper around subprocess.Popen with metadata."""

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

    def __init__(self) -> None:
        self.processes: Dict[str, ManagedProcess] = {}

    def spawn(self, name: str, command: List[str]) -> None:
        """Spawn a new process with given command."""
        proc = ManagedProcess(command)
        proc.start()
        self.processes[name] = proc

    def stop(self, name: str) -> None:
        """Stop a managed process."""
        if name in self.processes:
            self.processes[name].stop()

    def restart(self, name: str) -> None:
        """Restart a managed process."""
        if name in self.processes:
            self.processes[name].restart()

    def health_check(self, name: str) -> bool:
        """Return True if process is running."""
        proc = self.processes.get(name)
        return bool(proc and proc.is_running())

    def monitor_resources(self) -> Dict[str, int]:
        """Return memory usage per process."""
        usage = {}
        for name, proc in self.processes.items():
            usage[name] = proc.memory_usage()
        return usage

    def shutdown(self) -> None:
        """Stop all processes."""
        for proc in self.processes.values():
            proc.stop()
        self.processes.clear()
