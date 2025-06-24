"""SupervisorEngine - Core orchestration engine for APEX v2.0.

The SupervisorEngine implements the 5-stage orchestration loop:
PLAN → CONSTRUCT → INVOKE → MONITOR → INTEGRATE

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
    TaskBriefing,
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
    CONSTRUCT = "construct"
    INVOKE = "invoke"
    MONITOR = "monitor"
    INTEGRATE = "integrate"
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
    """State management for the Supervisor."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.session_id = str(uuid.uuid4())
        self.current_stage = OrchestrationStage.IDLE
        self.current_goal: Optional[str] = None
        self.task_graph: Dict[str, Any] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.event_log: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "workers_spawned": 0,
            "stage_cycles": 0,
            "session_start": datetime.now().isoformat(),
        }
        self.paused = False
        self.stop_requested = False

    def log_event(self, event_type: OrchestrationEvent, data: Dict[str, Any]) -> None:
        """Log an orchestration event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type.value,
            "session_id": self.session_id,
            "stage": self.current_stage.value,
            "data": data,
        }
        self.event_log.append(event)

        # Keep only last 1000 events
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-1000:]

    def update_metrics(self, metric: str, increment: int = 1) -> None:
        """Update orchestration metrics."""
        if metric in self.metrics:
            self.metrics[metric] += increment
        else:
            self.metrics[metric] = increment


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

        # Configuration
        self.config = {
            "max_concurrent_tasks": 3,
            "task_timeout_minutes": 30,
            "stage_timeout_minutes": 60,
            "retry_failed_tasks": True,
            "max_task_retries": 2,
            "auto_cleanup_completed": True,
            "cleanup_after_hours": 24,
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
        """Execute one complete orchestration cycle.

        Returns True if cycle completed successfully, False if stopped.
        """
        if not self.state:
            raise ValueError("Session not initialized")

        if self.state.stop_requested:
            return False

        while self.state.paused:
            await asyncio.sleep(1)

        self.state.metrics["stage_cycles"] += 1
        cycle_start = datetime.now()

        try:
            # Stage 1: PLAN
            await self._execute_plan_stage()

            # Stage 2: CONSTRUCT
            await self._execute_construct_stage()

            # Stage 3: INVOKE
            await self._execute_invoke_stage()

            # Stage 4: MONITOR
            await self._execute_monitor_stage()

            # Stage 5: INTEGRATE
            await self._execute_integrate_stage()

            # Log cycle completion
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.state.log_event(
                OrchestrationEvent.STAGE_COMPLETED,
                {
                    "stage": "full_cycle",
                    "duration_seconds": cycle_duration,
                    "active_tasks": len(self.state.active_tasks),
                    "completed_tasks": len(self.state.completed_tasks),
                },
            )

            return True

        except Exception as e:
            self.logger.error(f"Error in orchestration cycle: {e}")
            self.state.log_event(
                OrchestrationEvent.ERROR_OCCURRED,
                {"error": str(e), "stage": self.state.current_stage.value},
            )
            return False

    async def _execute_plan_stage(self) -> None:
        """Stage 1: PLAN - Analyze current state and plan next actions."""
        self.state.current_stage = OrchestrationStage.PLAN
        self.state.log_event(OrchestrationEvent.STAGE_STARTED, {"stage": "plan"})

        self.logger.info("Executing PLAN stage")

        # Get current project state
        project_state = await self._get_project_state()

        # Check if goal is achieved
        if await self._is_goal_achieved(project_state):
            self.logger.info("Goal achieved, orchestration complete")
            self.state.current_stage = OrchestrationStage.IDLE
            return

        # Update task graph based on current state
        updated_graph = await self.planner.update_task_graph(
            self.state.project_id,
            self.state.current_goal,
            project_state,
            self.state.completed_tasks,
            self.state.failed_tasks,
        )

        if updated_graph:
            self.state.task_graph = updated_graph

        # Identify next tasks to execute
        ready_tasks = await self._get_ready_tasks()

        self.state.log_event(
            OrchestrationEvent.STAGE_COMPLETED,
            {
                "stage": "plan",
                "ready_tasks_count": len(ready_tasks),
                "total_tasks_in_graph": len(self.state.task_graph.get("tasks", [])),
            },
        )

    async def _execute_construct_stage(self) -> None:
        """Stage 2: CONSTRUCT - Create TaskBriefings for ready tasks."""
        self.state.current_stage = OrchestrationStage.CONSTRUCT
        self.state.log_event(OrchestrationEvent.STAGE_STARTED, {"stage": "construct"})

        self.logger.info("Executing CONSTRUCT stage")

        ready_tasks = await self._get_ready_tasks()
        briefings_created = 0

        for task_spec in ready_tasks:
            if len(self.state.active_tasks) >= self.config["max_concurrent_tasks"]:
                break

            # Generate TaskBriefing
            briefing = await self.briefing_generator.generate_briefing(
                self.state.project_id, task_spec, self._get_project_context()
            )

            if briefing:
                # Ensure project_id is in briefing metadata
                briefing.metadata["project_id"] = self.state.project_id

                # Store briefing in LMDB
                await self.briefing_manager.create_briefing(
                    self.state.project_id, briefing
                )

                self.state.log_event(
                    OrchestrationEvent.TASK_CREATED,
                    {
                        "task_id": briefing.task_id,
                        "role": briefing.role_required.value,
                        "objective": briefing.objective,
                    },
                )

                briefings_created += 1
                self.state.update_metrics("tasks_created")

        self.state.log_event(
            OrchestrationEvent.STAGE_COMPLETED,
            {"stage": "construct", "briefings_created": briefings_created},
        )

    async def _execute_invoke_stage(self) -> None:
        """Stage 3: INVOKE - Spawn workers for pending briefings."""
        self.state.current_stage = OrchestrationStage.INVOKE
        self.state.log_event(OrchestrationEvent.STAGE_STARTED, {"stage": "invoke"})

        self.logger.info("Executing INVOKE stage")

        # Get pending briefings ready for invocation
        pending_briefings = await self.briefing_manager.list_briefings(
            self.state.project_id, status=TaskStatus.PENDING_INVOCATION
        )

        workers_spawned = 0

        for briefing_info in pending_briefings:
            if len(self.state.active_tasks) >= self.config["max_concurrent_tasks"]:
                break

            task_id = briefing_info["task_id"]
            briefing = await self.briefing_manager.get_briefing(
                self.state.project_id, task_id
            )

            if not briefing:
                continue

            # Determine worker type (Worker vs Utility)
            worker_type = await self._determine_worker_type(briefing)

            # Spawn appropriate worker/utility
            process_info = await self.orchestrator.spawn_worker(briefing, worker_type)

            if process_info:
                # Update briefing status
                briefing.update_status(
                    TaskStatus.IN_PROGRESS,
                    {
                        "worker_type": worker_type,
                        "process_id": process_info["process_id"],
                        "started_at": datetime.now().isoformat(),
                    },
                )
                await self.briefing_manager.update_briefing(
                    self.state.project_id, briefing
                )

                # Track active task
                self.state.active_tasks[task_id] = {
                    "briefing": briefing,
                    "process_info": process_info,
                    "started_at": datetime.now().isoformat(),
                }

                self.state.log_event(
                    OrchestrationEvent.TASK_STARTED,
                    {
                        "task_id": task_id,
                        "worker_type": worker_type,
                        "process_id": process_info["process_id"],
                    },
                )

                workers_spawned += 1
                self.state.update_metrics("workers_spawned")

        self.state.log_event(
            OrchestrationEvent.STAGE_COMPLETED,
            {
                "stage": "invoke",
                "workers_spawned": workers_spawned,
                "active_tasks": len(self.state.active_tasks),
            },
        )

    async def _execute_monitor_stage(self) -> None:
        """Stage 4: MONITOR - Monitor active workers and processes."""
        self.state.current_stage = OrchestrationStage.MONITOR
        self.state.log_event(OrchestrationEvent.STAGE_STARTED, {"stage": "monitor"})

        self.logger.info("Executing MONITOR stage")

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
                    self.state.log_event(
                        OrchestrationEvent.TASK_COMPLETED,
                        {
                            "task_id": task_id,
                            "exit_code": status.get("exit_code", 0),
                            "duration": status.get("duration", 0),
                        },
                    )
                else:
                    failed_tasks.append(task_id)
                    self.state.log_event(
                        OrchestrationEvent.TASK_FAILED,
                        {
                            "task_id": task_id,
                            "exit_code": status.get("exit_code", 1),
                            "error": status.get("error", "Unknown error"),
                        },
                    )

            # Check for timeouts
            elif await self._is_task_timeout(task_info):
                failed_tasks.append(task_id)
                await self.orchestrator.terminate_process(process_info["process_id"])
                self.state.log_event(
                    OrchestrationEvent.TASK_FAILED,
                    {
                        "task_id": task_id,
                        "reason": "timeout",
                        "duration": self.config["task_timeout_minutes"] * 60,
                    },
                )

        # Update task tracking
        for task_id in completed_tasks:
            del self.state.active_tasks[task_id]
            self.state.completed_tasks.append(task_id)
            self.state.update_metrics("tasks_completed")

        for task_id in failed_tasks:
            del self.state.active_tasks[task_id]
            self.state.failed_tasks.append(task_id)
            self.state.update_metrics("tasks_failed")

        self.state.log_event(
            OrchestrationEvent.STAGE_COMPLETED,
            {
                "stage": "monitor",
                "completed_tasks": len(completed_tasks),
                "failed_tasks": len(failed_tasks),
                "still_active": len(self.state.active_tasks),
            },
        )

    async def _execute_integrate_stage(self) -> None:
        """Stage 5: INTEGRATE - Integrate results and update state."""
        self.state.current_stage = OrchestrationStage.INTEGRATE
        self.state.log_event(OrchestrationEvent.STAGE_STARTED, {"stage": "integrate"})

        self.logger.info("Executing INTEGRATE stage")

        integrated_results = 0

        # Process completed tasks since last integration
        for task_id in self.state.completed_tasks:
            if await self._integrate_task_results(task_id):
                integrated_results += 1

        # Handle failed tasks
        for task_id in self.state.failed_tasks:
            await self._handle_failed_task(task_id)

        # Update project state in LMDB
        await self._update_project_state()

        # Cleanup if configured
        if self.config["auto_cleanup_completed"]:
            await self._cleanup_old_data()

        self.state.log_event(
            OrchestrationEvent.STAGE_COMPLETED,
            {
                "stage": "integrate",
                "integrated_results": integrated_results,
                "total_completed": len(self.state.completed_tasks),
                "total_failed": len(self.state.failed_tasks),
            },
        )

    async def _get_project_state(self) -> Dict[str, Any]:
        """Get current project state for planning."""
        # This would gather current state from LMDB, git, file system, etc.
        state = {
            "project_id": self.state.project_id,
            "goal": self.state.current_goal,
            "completed_tasks": self.state.completed_tasks,
            "failed_tasks": self.state.failed_tasks,
            "active_tasks": list(self.state.active_tasks.keys()),
            "timestamp": datetime.now().isoformat(),
        }

        # Add more detailed state as needed
        return state

    async def _is_goal_achieved(self, project_state: Dict[str, Any]) -> bool:
        """Check if the current goal has been achieved."""
        # This would implement goal achievement detection
        # For now, simple heuristic based on task graph completion
        if not self.state.task_graph.get("tasks"):
            return False

        total_tasks = len(self.state.task_graph["tasks"])
        completed_tasks = len(self.state.completed_tasks)

        # Goal achieved if 90% of tasks completed and no critical failures
        completion_ratio = completed_tasks / total_tasks if total_tasks > 0 else 0
        return completion_ratio >= 0.9 and len(self.state.active_tasks) == 0

    async def _get_ready_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks that are ready to be executed."""
        if not self.state.task_graph.get("tasks"):
            return []

        ready_tasks = []
        for task_spec in self.state.task_graph["tasks"]:
            task_id = task_spec.get("id", "")

            # Skip if already completed, failed, or active
            if (
                task_id in self.state.completed_tasks
                or task_id in self.state.failed_tasks
                or task_id in self.state.active_tasks
            ):
                continue

            # Check dependencies
            dependencies = task_spec.get("dependencies", [])
            if all(dep in self.state.completed_tasks for dep in dependencies):
                ready_tasks.append(task_spec)

        return ready_tasks

    async def _determine_worker_type(self, briefing: TaskBriefing) -> str:
        """Determine whether to use a Worker or Utility for this task."""
        # Simple heuristic - can be made more sophisticated
        if briefing.role_required in [TaskRole.CODER, TaskRole.ADVERSARY]:
            return "Worker"
        else:
            return "Utility"

    async def _is_task_timeout(self, task_info: Dict[str, Any]) -> bool:
        """Check if a task has exceeded its timeout."""
        started_at = datetime.fromisoformat(task_info["started_at"])
        elapsed = (datetime.now() - started_at).total_seconds()
        timeout = self.config["task_timeout_minutes"] * 60
        return elapsed > timeout

    async def _integrate_task_results(self, task_id: str) -> bool:
        """Integrate results from a completed task."""
        try:
            briefing = await self.briefing_manager.get_briefing(
                self.state.project_id, task_id
            )
            if not briefing:
                return False

            # Validate deliverables were created
            for deliverable in briefing.deliverables:
                if deliverable.required:
                    data = await self.memory.mcp.read(
                        f"/projects/{self.state.project_id}{deliverable.output_key}"
                    )
                    if not data:
                        self.logger.warning(
                            f"Required deliverable missing: {deliverable.output_key}"
                        )
                        return False

            # Update briefing status
            briefing.update_status(TaskStatus.COMPLETED)
            await self.briefing_manager.update_briefing(self.state.project_id, briefing)

            return True
        except Exception as e:
            self.logger.error(f"Error integrating results for task {task_id}: {e}")
            return False

    async def _handle_failed_task(self, task_id: str) -> None:
        """Handle a failed task - retry or mark as permanently failed."""
        try:
            briefing = await self.briefing_manager.get_briefing(
                self.state.project_id, task_id
            )
            if not briefing:
                return

            retry_count = briefing.orchestration_metadata.get("retry_count", 0)

            if (
                self.config["retry_failed_tasks"]
                and retry_count < self.config["max_task_retries"]
            ):
                # Retry the task
                briefing.update_status(
                    TaskStatus.PENDING_INVOCATION,
                    {
                        "retry_count": retry_count + 1,
                        "last_failure": datetime.now().isoformat(),
                    },
                )
                await self.briefing_manager.update_briefing(
                    self.state.project_id, briefing
                )

                # Remove from failed list so it can be retried
                if task_id in self.state.failed_tasks:
                    self.state.failed_tasks.remove(task_id)
            else:
                # Mark as permanently failed
                briefing.update_status(TaskStatus.FAILED)
                await self.briefing_manager.update_briefing(
                    self.state.project_id, briefing
                )

        except Exception as e:
            self.logger.error(f"Error handling failed task {task_id}: {e}")

    async def _update_project_state(self) -> None:
        """Update the overall project state in LMDB."""
        state_key = f"/projects/{self.state.project_id}/supervisor/state"
        state_data = {
            "session_id": self.state.session_id,
            "current_stage": self.state.current_stage.value,
            "goal": self.state.current_goal,
            "task_graph": self.state.task_graph,
            "completed_tasks": self.state.completed_tasks,
            "failed_tasks": self.state.failed_tasks,
            "active_tasks": list(self.state.active_tasks.keys()),
            "metrics": self.state.metrics,
            "updated_at": datetime.now().isoformat(),
        }
        await self.memory.mcp.write(state_key, json.dumps(state_data))

    async def _cleanup_old_data(self) -> None:
        """Clean up old completed data."""
        cutoff_hours = self.config["cleanup_after_hours"]
        await self.briefing_manager.cleanup_completed_briefings(
            self.state.project_id, days_to_keep=cutoff_hours // 24
        )

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
        self.state.log_event(
            OrchestrationEvent.USER_INTERVENTION_REQUIRED, {"action": "paused"}
        )

    async def resume_orchestration(self) -> None:
        """Resume orchestration."""
        self.state.paused = False
        self.state.log_event(OrchestrationEvent.STAGE_STARTED, {"action": "resumed"})

    async def stop_orchestration(self) -> None:
        """Stop orchestration gracefully."""
        self.state.stop_requested = True

        # Terminate active processes
        for _task_id, task_info in self.state.active_tasks.items():
            await self.orchestrator.terminate_process(
                task_info["process_info"]["process_id"]
            )

        self.state.log_event(
            OrchestrationEvent.STAGE_COMPLETED,
            {"action": "stopped", "final_metrics": self.state.metrics},
        )

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
            "metrics": self.state.metrics,
            "paused": self.state.paused,
            "stop_requested": self.state.stop_requested,
        }
