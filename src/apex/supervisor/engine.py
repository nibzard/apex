"""SupervisorEngine - Core orchestration engine for APEX v2.0.

The SupervisorEngine implements a simplified 3-stage orchestration loop:
PLAN → EXECUTE → MONITOR

This is the heart of the v2.0 Orchestrator-Worker architecture.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from apex.core.memory import MemoryPatterns
from apex.core.task_briefing import (
    TaskBriefingManager,
    TaskRole,
    TaskStatus,
)
from apex.supervisor.briefing import BriefingGenerator
from apex.supervisor.orchestrator import ProcessOrchestrator
from apex.supervisor.planner import TaskPlanner


class OrchestrationStage(Enum):
    """Stages of the orchestration loop."""

    PLAN = "plan"
    EXECUTE = "execute"
    MONITOR = "monitor"
    IDLE = "idle"


class OrchestrationEvent(Enum):
    """Events that can occur during orchestration."""

    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    WORKER_SPAWNED = "worker_spawned"
    WORKER_TERMINATED = "worker_terminated"
    ERROR_OCCURRED = "error_occurred"
    USER_INTERVENTION_REQUIRED = "user_intervention_required"


class SupervisorState:
    """Simplified state management for the Supervisor."""

    def __init__(self, project_id: str):
        """Initialize SupervisorState with project ID."""
        self.project_id = project_id
        self.session_id = str(uuid.uuid4())
        self.current_stage = OrchestrationStage.IDLE
        self.current_goal: Optional[str] = None
        self.task_graph: Dict[str, Any] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.paused = False
        self.stop_requested = False

        # Simplified metrics
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "tasks_completed": 0,
            "tasks_failed": 0,
        }


class SupervisorEngine:
    """Core orchestration engine implementing the 5-stage loop.

    The engine coordinates between TaskPlanner, BriefingGenerator, and
    ProcessOrchestrator to execute high-level goals through intelligent
    task dispatch.
    """

    def __init__(self, memory_patterns: MemoryPatterns):
        """Initialize the SupervisorEngine."""
        self.memory = memory_patterns
        self.briefing_manager = TaskBriefingManager(memory_patterns)
        self.planner = TaskPlanner(memory_patterns)
        self.orchestrator = ProcessOrchestrator(memory_patterns)
        self.briefing_generator = BriefingGenerator(memory_patterns)

        self.logger = logging.getLogger(__name__)
        self.state: Optional[SupervisorState] = None

        # Simplified configuration
        self.config = {
            "max_concurrent_tasks": 2,
            "task_timeout_minutes": 45,
            "retry_failed_tasks": True,
        }

    async def initialize_session(self, project_id: str, goal: str) -> str:
        """Initialize a new orchestration session."""
        self.state = SupervisorState(project_id)
        self.state.current_goal = goal

        self.logger.info(f"Initializing Supervisor session for project {project_id}")
        self.logger.info(f"Goal: {goal}")

        # ProcessOrchestrator is ready to spawn Claude CLI workers

        # Store session metadata in LMDB
        session_key = (
            f"/projects/{project_id}/supervisor/sessions/{self.state.session_id}"
        )
        session_data = {
            "session_id": self.state.session_id,
            "project_id": project_id,
            "goal": goal,
            "started_at": datetime.now().isoformat(),
            "status": "active",
        }
        await self.memory.mcp.write(session_key, json.dumps(session_data))

        self.state.log_event(
            OrchestrationEvent.STAGE_STARTED, {"stage": "initialization", "goal": goal}
        )

        return self.state.session_id

    async def execute_orchestration_cycle(self) -> bool:
        """Execute one simplified orchestration cycle.

        Returns True if cycle completed successfully, False if stopped.
        """
        if not self.state:
            raise ValueError("Session not initialized")

        if self.state.stop_requested:
            return False

        while self.state.paused:
            await asyncio.sleep(1)

        try:
            # Stage 1: PLAN - Identify next task to execute
            next_task = await self._plan_next_task()
            if not next_task:
                return await self._check_completion()

            # Stage 2: EXECUTE - Create briefing and spawn worker
            if len(self.state.active_tasks) < self.config["max_concurrent_tasks"]:
                success = await self._execute_task(next_task)
                if not success:
                    self.logger.error(f"Failed to execute task: {next_task['id']}")

            # Stage 3: MONITOR - Check active tasks for completion
            await self._monitor_active_tasks()

            return True

        except Exception as e:
            self.logger.error(f"Error in orchestration cycle: {e}")
            return False

    async def _plan_next_task(self) -> Optional[Dict[str, Any]]:
        """Plan and return the next task to execute."""
        self.state.current_stage = OrchestrationStage.PLAN

        # Create task graph if needed
        if not self.state.task_graph or not self.state.task_graph.get("tasks"):
            graph = await self.planner.create_task_graph(
                self.state.project_id, self.state.current_goal
            )
            self.state.task_graph = graph.to_dict()

        # Get next ready task
        return await self.planner.get_next_task(
            self.state.project_id, self.state.completed_tasks
        )

    async def _execute_task(self, task_spec: Dict[str, Any]) -> bool:
        """Execute a single task by creating briefing and spawning worker."""
        self.state.current_stage = OrchestrationStage.EXECUTE

        try:
            # Generate TaskBriefing
            briefing = await self.briefing_generator.generate_briefing(
                self.state.project_id, task_spec, self._get_project_context()
            )

            if not briefing:
                return False

            # Store briefing
            briefing.metadata["project_id"] = self.state.project_id
            await self.briefing_manager.create_briefing(self.state.project_id, briefing)

            # Spawn worker
            worker_type = (
                "Worker"
                if briefing.role_required in [TaskRole.CODER, TaskRole.ADVERSARY]
                else "Utility"
            )
            process_info = await self.orchestrator.spawn_worker(briefing, worker_type)

            if process_info:
                # Update briefing status
                briefing.update_status(
                    TaskStatus.IN_PROGRESS,
                    {
                        "process_id": process_info["process_id"],
                        "started_at": datetime.now().isoformat(),
                    },
                )
                await self.briefing_manager.update_briefing(
                    self.state.project_id, briefing
                )

                # Track active task
                self.state.active_tasks[briefing.task_id] = {
                    "briefing": briefing,
                    "process_info": process_info,
                    "started_at": datetime.now().isoformat(),
                }

                self.logger.info(
                    f"Started task {briefing.task_id} with worker {worker_type}"
                )
                return True

            return False

        except Exception as e:
            self.logger.error(
                f"Error executing task {task_spec.get('id', 'unknown')}: {e}"
            )
            return False

    async def _monitor_active_tasks(self) -> None:
        """Monitor active tasks and update their status."""
        self.state.current_stage = OrchestrationStage.MONITOR

        completed_tasks = []
        failed_tasks = []

        for task_id, task_info in list(self.state.active_tasks.items()):
            process_info = task_info["process_info"]

            # Check process status
            status = await self.orchestrator.check_process_status(
                process_info["process_id"]
            )

            if status["completed"]:
                if status["success"]:
                    completed_tasks.append(task_id)
                    self.logger.info(f"Task {task_id} completed successfully")
                else:
                    failed_tasks.append(task_id)
                    self.logger.error(
                        f"Task {task_id} failed: {status.get('error', 'Unknown error')}"
                    )

            # Check for timeouts
            elif await self._is_task_timeout(task_info):
                failed_tasks.append(task_id)
                await self.orchestrator.terminate_process(process_info["process_id"])
                self.logger.warning(f"Task {task_id} timed out")

        # Update task tracking
        for task_id in completed_tasks:
            await self._handle_completed_task(task_id)

        for task_id in failed_tasks:
            await self._handle_failed_task(task_id)

    async def _check_completion(self) -> bool:
        """Check if orchestration is complete."""
        # If no active tasks and no more ready tasks, we're done
        if not self.state.active_tasks:
            total_tasks = len(self.state.task_graph.get("tasks", []))
            completed_tasks = len(self.state.completed_tasks)

            if completed_tasks >= total_tasks * 0.9:  # 90% completion threshold
                self.logger.info("Goal achieved - orchestration complete")
                self.state.current_stage = OrchestrationStage.IDLE
                return False  # Stop orchestration

        return True  # Continue orchestration

    async def _is_task_timeout(self, task_info: Dict[str, Any]) -> bool:
        """Check if a task has exceeded its timeout."""
        started_at = datetime.fromisoformat(task_info["started_at"])
        elapsed = (datetime.now() - started_at).total_seconds()
        timeout = self.config["task_timeout_minutes"] * 60
        return elapsed > timeout

    async def _handle_completed_task(self, task_id: str) -> None:
        """Handle a completed task."""
        try:
            del self.state.active_tasks[task_id]
            self.state.completed_tasks.append(task_id)
            self.state.stats["tasks_completed"] += 1

            # Update briefing status
            briefing = await self.briefing_manager.get_briefing(
                self.state.project_id, task_id
            )
            if briefing:
                briefing.update_status(TaskStatus.COMPLETED)
                await self.briefing_manager.update_briefing(
                    self.state.project_id, briefing
                )

        except Exception as e:
            self.logger.error(f"Error handling completed task {task_id}: {e}")

    async def _handle_failed_task(self, task_id: str) -> None:
        """Handle a failed task - retry if configured."""
        try:
            del self.state.active_tasks[task_id]

            briefing = await self.briefing_manager.get_briefing(
                self.state.project_id, task_id
            )
            if not briefing:
                return

            retry_count = briefing.orchestration_metadata.get("retry_count", 0)

            if self.config["retry_failed_tasks"] and retry_count == 0:
                # Retry once
                briefing.update_status(
                    TaskStatus.PENDING_INVOCATION,
                    {
                        "retry_count": 1,
                        "last_failure": datetime.now().isoformat(),
                    },
                )
                await self.briefing_manager.update_briefing(
                    self.state.project_id, briefing
                )
                self.logger.info(f"Retrying failed task {task_id}")
            else:
                # Mark as permanently failed
                self.state.failed_tasks.append(task_id)
                self.state.stats["tasks_failed"] += 1
                briefing.update_status(TaskStatus.FAILED)
                await self.briefing_manager.update_briefing(
                    self.state.project_id, briefing
                )

        except Exception as e:
            self.logger.error(f"Error handling failed task {task_id}: {e}")

    def _get_project_context(self) -> Dict[str, Any]:
        """Get project context for briefing generation."""
        return {
            "project_id": self.state.project_id,
            "goal": self.state.current_goal,
            "completed_tasks": self.state.completed_tasks,
            "task_graph": self.state.task_graph,
            "session_id": self.state.session_id,
        }

    # Public control methods
    async def pause_orchestration(self) -> None:
        """Pause orchestration after current stage."""
        self.state.paused = True
        self.logger.info("Orchestration paused")

    async def resume_orchestration(self) -> None:
        """Resume orchestration."""
        self.state.paused = False
        self.logger.info("Orchestration resumed")

    async def stop_orchestration(self) -> None:
        """Stop orchestration gracefully."""
        self.state.stop_requested = True

        # Terminate active processes
        for task_id, task_info in self.state.active_tasks.items():
            await self.orchestrator.terminate_process(
                task_info["process_info"]["process_id"]
            )
            self.logger.info(f"Terminated task {task_id}")

        self.logger.info("Orchestration stopped")

    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status."""
        if not self.state:
            return {"status": "not_initialized"}

        return {
            "session_id": self.state.session_id,
            "project_id": self.state.project_id,
            "goal": self.state.current_goal,
            "current_stage": self.state.current_stage.value,
            "active_tasks": len(self.state.active_tasks),
            "completed_tasks": len(self.state.completed_tasks),
            "failed_tasks": len(self.state.failed_tasks),
            "stats": self.state.stats,
            "paused": self.state.paused,
            "stop_requested": self.state.stop_requested,
        }
