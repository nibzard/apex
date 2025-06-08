"""Process management for APEX agents."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
import threading

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
        self._desired_state: Dict[str, bool] = {}
        self.restart_events: Dict[str, int] = {}
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._monitor_interval = 1.0

    def spawn(self, name: str, command: List[str]) -> None:
        """Spawn a new process with given command."""
        proc = ManagedProcess(command)
        proc.start()
        self.processes[name] = proc
        self._desired_state[name] = True

    def stop(self, name: str) -> None:
        """Stop a managed process."""
        if name in self.processes:
            self._desired_state[name] = False
            self.processes[name].stop()

    def restart(self, name: str) -> None:
        """Restart a managed process."""
        if name in self.processes:
            self._desired_state[name] = True
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
        for name, proc in self.processes.items():
            self._desired_state[name] = False
            proc.stop()
        self.processes.clear()
        self._desired_state.clear()

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            for name, proc in list(self.processes.items()):
                if self._desired_state.get(name) and not proc.is_running():
                    proc.restart()
                    self.restart_events[name] = self.restart_events.get(name, 0) + 1
            time.sleep(self._monitor_interval)

    def monitor(self, start: bool = True, interval: float = 1.0) -> None:
        """Start or stop background monitoring."""
        if start:
            if self._monitor_thread and self._monitor_thread.is_alive():
                return
            self._monitor_interval = interval
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
        else:
            self._stop_event.set()
            if self._monitor_thread:
                self._monitor_thread.join()

