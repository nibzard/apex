"""ProcessOrchestrator - Worker and Utility process management for APEX v2.0.

The ProcessOrchestrator handles spawning, monitoring, and terminating both
intelligent Workers (Claude CLI processes) and deterministic Utilities (Python scripts).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from apex.core.memory import MemoryPatterns
from apex.core.task_briefing import TaskBriefing, TaskRole
from apex.workers.claude_prompts import build_claude_command


class ProcessType(Enum):
    """Types of processes that can be orchestrated."""

    WORKER = "worker"
    UTILITY = "utility"


class ProcessStatus(Enum):
    """Status of orchestrated processes."""

    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    TERMINATED = "terminated"


class WorkerConfig:
    """Configuration for Claude CLI worker processes."""

    def __init__(self):
        """Initialize WorkerConfig with default settings."""
        self.claude_command = "claude"
        self.output_format = "stream-json"
        self.max_tokens = 4000
        self.temperature = 0.1
        self.timeout_seconds = 1800  # 30 minutes default
        self.mcp_config_path = None

        # Worker-specific settings
        self.coder_model = "claude-3-5-sonnet-20241022"
        self.adversary_model = "claude-3-5-sonnet-20241022"
        self.supervisor_model = "claude-3-5-sonnet-20241022"

        # Tool permissions
        self.allowed_tools = [
            "mcp__lmdb__read",
            "mcp__lmdb__write",
            "mcp__lmdb__delete",
            "mcp__lmdb__list",
            "bash",
            "read",
            "write",
            "edit",
        ]


class UtilityConfig:
    """Configuration for utility script processes."""

    def __init__(self):
        """Initialize UtilityConfig with default settings."""
        self.python_command = "python"
        self.timeout_seconds = 600  # 10 minutes default
        self.max_memory_mb = 512
        self.allowed_network_access = False

        # Environment variables
        self.env_vars = {"PYTHONPATH": "", "APEX_MODE": "utility"}


class ProcessInfo:
    """Information about a managed process."""

    def __init__(
        self,
        process_id: str,
        process_type: ProcessType,
        task_id: str,
        role: Optional[TaskRole] = None,
    ):
        """Initialize ProcessInfo with process details."""
        self.process_id = process_id
        self.process_type = process_type
        self.task_id = task_id
        self.role = role
        self.status = ProcessStatus.STARTING
        self.started_at = datetime.now().isoformat()
        self.completed_at: Optional[str] = None
        self.exit_code: Optional[int] = None
        self.error_message: Optional[str] = None
        self.pid: Optional[int] = None
        self.command_line: List[str] = []
        self.output_lines: List[str] = []
        self.error_lines: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "process_id": self.process_id,
            "process_type": self.process_type.value,
            "task_id": self.task_id,
            "role": self.role.value if self.role else None,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "exit_code": self.exit_code,
            "error_message": self.error_message,
            "pid": self.pid,
            "command_line": self.command_line,
            "output_lines": self.output_lines[-100:],  # Keep last 100 lines
            "error_lines": self.error_lines[-100:],
            "metadata": self.metadata,
        }


class ProcessOrchestrator:
    """Orchestrator for Worker and Utility processes in v2.0 architecture."""

    def __init__(self, memory_patterns: MemoryPatterns):
        """Initialize the ProcessOrchestrator."""
        self.memory = memory_patterns
        self.logger = logging.getLogger(__name__)

        # Process tracking
        self.active_processes: Dict[str, ProcessInfo] = {}
        self.process_history: List[ProcessInfo] = []

        # Configuration
        self.worker_config = WorkerConfig()
        self.utility_config = UtilityConfig()

        # Resource limits
        self.max_concurrent_workers = 3
        self.max_concurrent_utilities = 5

        # Remove complex worker factory - we use simple Claude CLI processes

        # Setup MCP config path
        self._setup_mcp_config()

    # Removed complex worker factory - using simple Claude CLI processes

    def _setup_mcp_config(self) -> None:
        """Set up MCP configuration for workers."""
        # Use the existing LMDB MCP config
        config_path = os.path.join(os.getcwd(), "configs", "lmdb_mcp.json")
        if os.path.exists(config_path):
            self.worker_config.mcp_config_path = config_path

    async def spawn_worker(
        self, briefing: TaskBriefing, worker_type: str
    ) -> Optional[Dict[str, Any]]:
        """Spawn a worker or utility process for a task briefing."""
        if worker_type == "Worker":
            # Spawn Claude CLI worker process with minimal prompt
            return await self._spawn_claude_worker(briefing)
        elif worker_type == "Utility":
            return await self._spawn_utility_process(briefing)
        else:
            self.logger.error(f"Unknown worker type: {worker_type}")
            return None

    async def _spawn_claude_worker(
        self, briefing: TaskBriefing
    ) -> Optional[Dict[str, Any]]:
        """Spawn a Claude CLI worker process with minimal prompt."""
        # Check resource limits
        worker_count = sum(
            1
            for p in self.active_processes.values()
            if p.process_type == ProcessType.WORKER
        )
        if worker_count >= self.max_concurrent_workers:
            self.logger.warning("Maximum concurrent workers reached")
            return None

        process_id = f"worker-{str(uuid.uuid4())[:8]}"

        try:
            # Get project ID from briefing metadata
            project_id = briefing.metadata.get("project_id", "default")

            # Store briefing in LMDB first so worker can read it
            briefing_key = f"/projects/{project_id}/briefings/{briefing.task_id}"
            await self.memory.mcp.write(briefing_key, briefing.model_dump_json())

            # Create process info
            process_info = ProcessInfo(
                process_id, ProcessType.WORKER, briefing.task_id, briefing.role_required
            )

            # Build Claude CLI command with minimal prompt
            if not self.worker_config.mcp_config_path:
                self.logger.error("MCP config path not available")
                return None

            command = build_claude_command(
                briefing.role_required,
                project_id,
                briefing.task_id,
                self.worker_config.mcp_config_path,
            )
            process_info.command_line = command

            # Spawn Claude CLI process
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )

            process_info.pid = process.pid
            process_info.status = ProcessStatus.RUNNING
            process_info.metadata = {
                "worker_type": "claude_cli",
                "project_id": project_id,
                "briefing_key": briefing_key,
            }

            # Store process info
            self.active_processes[process_id] = process_info

            # Start monitoring
            asyncio.create_task(self._monitor_process(process_info, process))

            self.logger.info(
                f"Spawned Claude CLI worker {process_id} for task {briefing.task_id} "
                f"(role: {briefing.role_required.value})"
            )

            return {
                "process_id": process_id,
                "process_type": "Worker",
                "worker_type": "claude_cli",
                "pid": process.pid,
                "task_id": briefing.task_id,
                "role": briefing.role_required.value,
                "started_at": process_info.started_at,
                "briefing_key": briefing_key,
            }

        except Exception as e:
            self.logger.error(f"Error spawning Claude CLI worker: {e}")
            return None

    async def _spawn_utility_process(
        self, briefing: TaskBriefing
    ) -> Optional[Dict[str, Any]]:
        """Spawn a utility script process."""
        # Check resource limits
        utility_count = sum(
            1
            for p in self.active_processes.values()
            if p.process_type == ProcessType.UTILITY
        )
        if utility_count >= self.max_concurrent_utilities:
            self.logger.warning("Maximum concurrent utilities reached")
            return None

        process_id = f"utility-{str(uuid.uuid4())[:8]}"

        try:
            # Determine utility script based on task
            utility_script = self._determine_utility_script(briefing)
            if not utility_script:
                self.logger.error(
                    f"No utility script found for task type: {briefing.objective}"
                )
                return None

            # Create process info
            process_info = ProcessInfo(
                process_id,
                ProcessType.UTILITY,
                briefing.task_id,
                briefing.role_required,
            )

            # Build utility command
            command = self._build_utility_command(utility_script, briefing)
            process_info.command_line = command

            # Setup environment
            env = os.environ.copy()
            env.update(self.utility_config.env_vars)
            env["APEX_PROJECT_ID"] = briefing.task_id.split("-")[
                0
            ]  # Extract project context
            env["APEX_TASK_ID"] = briefing.task_id

            # Spawn process
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=os.getcwd(),
            )

            process_info.pid = process.pid
            process_info.status = ProcessStatus.RUNNING

            # Store process info
            self.active_processes[process_id] = process_info

            # Start monitoring
            asyncio.create_task(self._monitor_process(process_info, process))

            self.logger.info(
                f"Spawned utility {process_id} for task {briefing.task_id}"
            )

            return {
                "process_id": process_id,
                "process_type": "Utility",
                "pid": process.pid,
                "task_id": briefing.task_id,
                "utility_script": utility_script,
                "started_at": process_info.started_at,
            }

        except Exception as e:
            self.logger.error(f"Error spawning utility process: {e}")
            return None

    def _determine_utility_script(self, briefing: TaskBriefing) -> Optional[str]:
        """Determine which utility script to use for a task."""
        objective_lower = briefing.objective.lower()

        # Map task types to utility scripts
        if any(
            word in objective_lower for word in ["summarize", "archive", "compress"]
        ):
            return "archivist.py"
        elif any(word in objective_lower for word in ["test", "coverage", "benchmark"]):
            return "test_runner.py"
        elif any(
            word in objective_lower for word in ["git", "commit", "merge", "branch"]
        ):
            return "git_manager.py"
        elif any(word in objective_lower for word in ["format", "lint", "style"]):
            return "code_formatter.py"
        elif any(word in objective_lower for word in ["analyze", "metrics", "profile"]):
            return "analyzer.py"

        # Default fallback
        return None

    def _build_utility_command(
        self, script_name: str, briefing: TaskBriefing
    ) -> List[str]:
        """Build command for utility script execution."""
        command = [self.utility_config.python_command]

        # Add script path
        script_path = os.path.join("src", "apex", "tools", script_name)
        command.append(script_path)

        # Add task ID and briefing key as arguments
        command.extend(["--task-id", briefing.task_id])
        command.extend(["--briefing-key", briefing.get_lmdb_key()])

        # Add memory database path if needed
        command.extend(["--lmdb-path", "data/apex.lmdb"])  # Default path

        return command

    async def _monitor_process(
        self, process_info: ProcessInfo, process: asyncio.subprocess.Process
    ) -> None:
        """Monitor a running process."""
        try:
            # Start monitoring output streams
            stdout_task, stderr_task = await self._start_output_monitoring(
                process_info, process
            )

            # Wait for process completion with timeout handling
            await self._wait_for_process_completion(process_info, process)

            # Clean up monitoring tasks
            stdout_task.cancel()
            stderr_task.cancel()

            # Finalize and store process information
            await self._finalize_process(process_info)

        except Exception as e:
            self.logger.error(
                f"Error monitoring process {process_info.process_id}: {e}"
            )
            process_info.status = ProcessStatus.FAILED
            process_info.error_message = str(e)

    async def _start_output_monitoring(
        self, process_info: ProcessInfo, process: asyncio.subprocess.Process
    ) -> tuple:
        """Start monitoring stdout and stderr streams."""

        async def read_stdout():
            if process.stdout:
                async for line in process.stdout:
                    line_str = line.decode().strip()
                    process_info.output_lines.append(line_str)

                    # Log important events
                    if "TASK COMPLETE" in line_str:
                        self.logger.info(
                            f"Process {process_info.process_id} reported task "
                            f"completion"
                        )
                    elif "ERROR" in line_str.upper():
                        self.logger.warning(
                            f"Process {process_info.process_id} error: {line_str}"
                        )

        async def read_stderr():
            if process.stderr:
                async for line in process.stderr:
                    line_str = line.decode().strip()
                    process_info.error_lines.append(line_str)
                    self.logger.warning(
                        f"Process {process_info.process_id} stderr: {line_str}"
                    )

        # Start reading streams
        stdout_task = asyncio.create_task(read_stdout())
        stderr_task = asyncio.create_task(read_stderr())

        return stdout_task, stderr_task

    async def _wait_for_process_completion(
        self, process_info: ProcessInfo, process: asyncio.subprocess.Process
    ) -> None:
        """Wait for process completion with timeout handling."""
        try:
            timeout = (
                self.worker_config.timeout_seconds
                if process_info.process_type == ProcessType.WORKER
                else self.utility_config.timeout_seconds
            )

            await asyncio.wait_for(process.wait(), timeout=timeout)
            process_info.exit_code = process.returncode

            if process.returncode == 0:
                process_info.status = ProcessStatus.COMPLETED
                self.logger.info(
                    f"Process {process_info.process_id} completed successfully"
                )
            else:
                process_info.status = ProcessStatus.FAILED
                process_info.error_message = (
                    f"Process exited with code {process.returncode}"
                )
                self.logger.error(
                    f"Process {process_info.process_id} failed with exit code "
                    f"{process.returncode}"
                )

        except asyncio.TimeoutError:
            process_info.status = ProcessStatus.TIMEOUT
            process_info.error_message = "Process timeout"
            self.logger.error(f"Process {process_info.process_id} timed out")

            # Terminate the process
            await self._terminate_timed_out_process(process)

    async def _terminate_timed_out_process(
        self, process: asyncio.subprocess.Process
    ) -> None:
        """Terminate a process that has timed out."""
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5)
        except Exception:
            process.kill()
            await process.wait()

    async def _finalize_process(self, process_info: ProcessInfo) -> None:
        """Finalize process information and move to history."""
        process_info.completed_at = datetime.now().isoformat()

        # Move to history and remove from active
        self.process_history.append(process_info)
        if process_info.process_id in self.active_processes:
            del self.active_processes[process_info.process_id]

        # Store process history in LMDB
        await self._store_process_info(process_info)

    async def check_process_status(self, process_id: str) -> Dict[str, Any]:
        """Check the status of a process."""
        if process_id in self.active_processes:
            process_info = self.active_processes[process_id]
            return {
                "process_id": process_id,
                "status": process_info.status.value,
                "completed": False,
                "success": False,
                "exit_code": process_info.exit_code,
                "error": process_info.error_message,
                "runtime_seconds": self._calculate_runtime(process_info),
                "worker_type": process_info.metadata.get("worker_type", "unknown"),
            }

        # Check in history
        for process_info in self.process_history:
            if process_info.process_id == process_id:
                return {
                    "process_id": process_id,
                    "status": process_info.status.value,
                    "completed": True,
                    "success": process_info.status == ProcessStatus.COMPLETED,
                    "exit_code": process_info.exit_code,
                    "error": process_info.error_message,
                    "runtime_seconds": self._calculate_runtime(process_info),
                    "worker_type": process_info.metadata.get("worker_type", "unknown"),
                }

        return {
            "process_id": process_id,
            "status": "not_found",
            "completed": False,
            "success": False,
            "error": "Process not found",
        }

    async def terminate_process(self, process_id: str) -> bool:
        """Terminate a running process."""
        if process_id not in self.active_processes:
            return False

        process_info = self.active_processes[process_id]

        try:
            # Find and terminate the Claude CLI process by PID
            if process_info.pid:
                import psutil

                try:
                    proc = psutil.Process(process_info.pid)
                    proc.terminate()

                    # Wait for graceful termination
                    await asyncio.sleep(2)

                    if proc.is_running():
                        proc.kill()

                    process_info.status = ProcessStatus.TERMINATED
                    process_info.completed_at = datetime.now().isoformat()

                    self.logger.info(f"Terminated process {process_id}")
                    return True

                except psutil.NoSuchProcess:
                    # Process already terminated
                    process_info.status = ProcessStatus.COMPLETED
                    process_info.completed_at = datetime.now().isoformat()
                    return True

        except Exception as e:
            self.logger.error(f"Error terminating process {process_id}: {e}")
            return False

        return False

    async def get_process_output(self, process_id: str) -> Dict[str, Any]:
        """Get output from a process."""
        process_info = None

        if process_id in self.active_processes:
            process_info = self.active_processes[process_id]
        else:
            for info in self.process_history:
                if info.process_id == process_id:
                    process_info = info
                    break

        if not process_info:
            return {"error": "Process not found"}

        return {
            "process_id": process_id,
            "output_lines": process_info.output_lines,
            "error_lines": process_info.error_lines,
            "status": process_info.status.value,
            "total_output_lines": len(process_info.output_lines),
            "total_error_lines": len(process_info.error_lines),
        }

    async def list_active_processes(self) -> List[Dict[str, Any]]:
        """List all active processes."""
        return [
            {
                "process_id": proc.process_id,
                "process_type": proc.process_type.value,
                "task_id": proc.task_id,
                "role": proc.role.value if proc.role else None,
                "status": proc.status.value,
                "started_at": proc.started_at,
                "pid": proc.pid,
                "runtime_seconds": self._calculate_runtime(proc),
            }
            for proc in self.active_processes.values()
        ]

    async def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage."""
        active_workers = sum(
            1
            for p in self.active_processes.values()
            if p.process_type == ProcessType.WORKER
        )
        active_utilities = sum(
            1
            for p in self.active_processes.values()
            if p.process_type == ProcessType.UTILITY
        )

        return {
            "active_workers": active_workers,
            "max_workers": self.max_concurrent_workers,
            "worker_slots_available": self.max_concurrent_workers - active_workers,
            "active_utilities": active_utilities,
            "max_utilities": self.max_concurrent_utilities,
            "utility_slots_available": self.max_concurrent_utilities - active_utilities,
            "total_active_processes": len(self.active_processes),
            "processes_in_history": len(self.process_history),
        }

    def _calculate_runtime(self, process_info: ProcessInfo) -> float:
        """Calculate runtime for a process in seconds."""
        start_time = datetime.fromisoformat(process_info.started_at)

        if process_info.completed_at:
            end_time = datetime.fromisoformat(process_info.completed_at)
        else:
            end_time = datetime.now()

        return (end_time - start_time).total_seconds()

    async def _store_process_info(self, process_info: ProcessInfo) -> None:
        """Store process information in LMDB for auditing."""
        try:
            # Store in process history
            history_key = f"/supervisor/processes/history/{process_info.process_id}"
            await self.memory.mcp.write(history_key, json.dumps(process_info.to_dict()))

            # Update process metrics
            metrics_key = "/supervisor/processes/metrics"

            try:
                metrics_data = await self.memory.mcp.read(metrics_key)
                metrics = json.loads(metrics_data) if metrics_data else {}
            except Exception:
                metrics = {}

            # Update counters
            process_type = process_info.process_type.value
            status = process_info.status.value

            if process_type not in metrics:
                metrics[process_type] = {}
            if status not in metrics[process_type]:
                metrics[process_type][status] = 0

            metrics[process_type][status] += 1
            metrics["last_updated"] = datetime.now().isoformat()

            await self.memory.mcp.write(metrics_key, json.dumps(metrics))

        except Exception as e:
            self.logger.error(f"Error storing process info: {e}")

    async def cleanup_old_processes(self, days_to_keep: int = 7) -> int:
        """Clean up old process history."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0

            # Clean up in-memory history
            self.process_history = [
                proc
                for proc in self.process_history
                if datetime.fromisoformat(proc.started_at).timestamp() >= cutoff_date
            ]

            # Clean up LMDB history
            history_prefix = "/supervisor/processes/history/"
            keys = await self.memory.mcp.list_keys(history_prefix)

            for key in keys:
                try:
                    data = await self.memory.mcp.read(key)
                    if data:
                        proc_data = json.loads(data)
                        started_at = datetime.fromisoformat(
                            proc_data["started_at"]
                        ).timestamp()

                        if started_at < cutoff_date:
                            await self.memory.mcp.delete(key)
                            deleted_count += 1
                except Exception:
                    continue

            return deleted_count

        except Exception as e:
            self.logger.error(f"Error cleaning up old processes: {e}")
            return 0
