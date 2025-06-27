"""Bridge between simplified components and full LMDB system.

This module provides integration utilities to connect the simplified
orchestrator components with the full APEX LMDB-based system.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from apex.core.error_handling import (
    ErrorRecoveryManager,
    error_handler,
)
from apex.core.memory import MemoryPatterns
from apex.core.recovery import OrchestrationRecoveryManager
from apex.core.task_briefing import TaskBriefing, TaskRole, TaskStatus
from apex.supervisor.engine import SupervisorEngine
from apex.supervisor.planner import TaskPlanner


class SimplifiedTaskSpec:
    """Bridge task specification that works with both systems."""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        description: str,
        role: str,
        dependencies: Optional[List[str]] = None,
        estimated_duration: int = 60,
    ):
        self.id = task_id
        self.type = task_type
        self.description = description
        self.role = role
        self.dependencies = dependencies or []
        self.estimated_duration = estimated_duration
        self.created_at = datetime.now().isoformat()
        self.status = "pending"

    def to_task_briefing(self) -> TaskBriefing:
        """Convert to full TaskBriefing for LMDB system."""
        role_mapping = {
            "Coder": TaskRole.CODER,
            "Adversary": TaskRole.ADVERSARY,
            "Supervisor": TaskRole.SUPERVISOR,
        }

        return TaskBriefing(
            task_id=self.id,
            role=role_mapping.get(self.role, TaskRole.CODER),
            description=self.description,
            context={"type": self.type, "estimated_duration": self.estimated_duration},
            dependencies=self.dependencies,
            status=TaskStatus.PENDING,
            created_at=self.created_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "role": self.role,
            "dependencies": self.dependencies,
            "estimated_duration": self.estimated_duration,
            "created_at": self.created_at,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SimplifiedTaskSpec:
        """Create from dictionary."""
        task = cls(
            task_id=data["id"],
            task_type=data["type"],
            description=data["description"],
            role=data["role"],
            dependencies=data.get("dependencies", []),
            estimated_duration=data.get("estimated_duration", 60),
        )
        task.created_at = data.get("created_at", task.created_at)
        task.status = data.get("status", "pending")
        return task


class SimplifiedTaskGraph:
    """Bridge task graph that integrates with LMDB."""

    def __init__(self, goal: str, memory: Optional[MemoryPatterns] = None):
        self.goal = goal
        self.tasks: List[SimplifiedTaskSpec] = []
        self.created_at = datetime.now().isoformat()
        self.memory = memory
        self.project_id: Optional[str] = None

    def add_task(self, task: SimplifiedTaskSpec):
        """Add task to the graph."""
        self.tasks.append(task)

    def get_next_task(
        self, completed_task_ids: List[str]
    ) -> Optional[SimplifiedTaskSpec]:
        """Get the next task to execute."""
        for task in self.tasks:
            if task.id in completed_task_ids:
                continue
            if all(dep in completed_task_ids for dep in task.dependencies):
                return task
        return None

    async def persist_to_lmdb(self, project_id: str) -> None:
        """Persist task graph to LMDB system."""
        if not self.memory:
            return

        self.project_id = project_id

        # Store task graph metadata
        graph_key = f"/projects/{project_id}/supervisor/task_graph"
        graph_data = {
            "goal": self.goal,
            "created_at": self.created_at,
            "tasks": [task.to_dict() for task in self.tasks],
        }
        await self.memory.mcp.write(graph_key, json.dumps(graph_data))

        # Store individual tasks in LMDB task queues
        for task in self.tasks:
            task_key = f"/projects/{project_id}/memory/tasks/pending/{task.id}"
            task_briefing = task.to_task_briefing()
            await self.memory.mcp.write(task_key, task_briefing.model_dump_json())

    async def load_from_lmdb(self, project_id: str) -> bool:
        """Load task graph from LMDB system."""
        if not self.memory:
            return False

        try:
            graph_key = f"/projects/{project_id}/supervisor/task_graph"
            graph_json = await self.memory.mcp.read(graph_key)

            if not graph_json:
                return False

            graph_data = json.loads(graph_json)
            self.goal = graph_data["goal"]
            self.created_at = graph_data["created_at"]
            self.project_id = project_id

            # Load tasks
            self.tasks = []
            for task_data in graph_data.get("tasks", []):
                task = SimplifiedTaskSpec.from_dict(task_data)
                self.tasks.append(task)

            return True

        except Exception as e:
            logging.error(f"Failed to load task graph from LMDB: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "goal": self.goal,
            "created_at": self.created_at,
            "project_id": self.project_id,
            "tasks": [task.to_dict() for task in self.tasks],
        }


class IntegratedOrchestrator:
    """Orchestrator that bridges simplified and full systems."""

    def __init__(self, memory_patterns: MemoryPatterns):
        self.memory = memory_patterns
        self.supervisor_engine = SupervisorEngine(memory_patterns)
        self.task_planner = TaskPlanner(memory_patterns)
        self.error_manager = ErrorRecoveryManager(memory_patterns)
        self.recovery_manager = OrchestrationRecoveryManager(memory_patterns)
        self.logger = logging.getLogger(__name__)

        # Bridge state
        self.project_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.task_graph: Optional[SimplifiedTaskGraph] = None
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []

        # Error handling and recovery
        self.auto_recovery_enabled: bool = True
        self.checkpoint_interval: int = 30  # minutes

    async def initialize_session(self, project_id: str, goal: str) -> str:
        """Initialize integrated orchestration session."""
        self.project_id = project_id
        self.session_id = str(uuid.uuid4())

        # Initialize full supervisor engine
        await self.supervisor_engine.initialize_session(project_id, goal)

        # Store session metadata
        session_key = f"/projects/{project_id}/sessions/{self.session_id}/metadata"
        session_data = {
            "session_id": self.session_id,
            "project_id": project_id,
            "goal": goal,
            "created_at": datetime.now().isoformat(),
            "orchestrator_type": "integrated",
        }
        await self.memory.mcp.write(session_key, json.dumps(session_data))

        self.logger.info(
            f"Initialized integrated session {self.session_id} for project {project_id}"
        )
        return self.session_id

    async def create_simplified_task_graph(self, goal: str) -> SimplifiedTaskGraph:
        """Create a simplified task graph using the full planner."""
        # Use the full task planner to generate sophisticated tasks
        task_briefings = await self.task_planner.generate_task_sequence(
            goal, self.project_id or "default"
        )

        # Convert to simplified format
        task_graph = SimplifiedTaskGraph(goal, self.memory)

        for briefing in task_briefings:
            role_mapping = {
                TaskRole.CODER: "Coder",
                TaskRole.ADVERSARY: "Adversary",
                TaskRole.SUPERVISOR: "Supervisor",
            }

            task = SimplifiedTaskSpec(
                task_id=briefing.task_id,
                task_type=briefing.context.get("type", "implementation"),
                description=briefing.description,
                role=role_mapping.get(briefing.role, "Coder"),
                dependencies=briefing.dependencies,
                estimated_duration=briefing.context.get("estimated_duration", 60),
            )
            task_graph.add_task(task)

        # Persist to LMDB
        if self.project_id:
            await task_graph.persist_to_lmdb(self.project_id)

        self.task_graph = task_graph
        return task_graph

    async def execute_task_with_supervisor(self, task: SimplifiedTaskSpec) -> bool:
        """Execute task using the full supervisor engine."""
        if not self.project_id:
            return False

        async with error_handler(
            self.memory,
            component="integrated_orchestrator",
            operation="execute_task",
            context={
                "task_id": task.id,
                "task_type": task.type,
                "project_id": self.project_id,
            },
        ) as error_mgr:
            try:
                # Update task status to in-progress
                task.status = "in_progress"

                # Move task in LMDB
                pending_key = (
                    f"/projects/{self.project_id}/memory/tasks/pending/{task.id}"
                )
                in_progress_key = (
                    f"/projects/{self.project_id}/memory/tasks/in_progress/{task.id}"
                )

                task_data = await self.memory.mcp.read(pending_key)
                if task_data:
                    await self.memory.mcp.write(in_progress_key, task_data)
                    await self.memory.mcp.delete(pending_key)

                # Execute using supervisor engine with timeout
                try:
                    success = await asyncio.wait_for(
                        self.supervisor_engine.execute_orchestration_cycle(),
                        timeout=300,  # 5 minute timeout
                    )
                except asyncio.TimeoutError:
                    self.logger.warning(f"Task {task.id} execution timed out")
                    success = False

                if success:
                    task.status = "completed"
                    self.completed_tasks.append(task.id)

                    # Move to completed in LMDB
                    completed_key = (
                        f"/projects/{self.project_id}/memory/tasks/completed/{task.id}"
                    )
                    await self.memory.mcp.write(completed_key, task_data or "")
                    if task_data:
                        await self.memory.mcp.delete(in_progress_key)

                    self.logger.info(f"Task {task.id} completed successfully")
                else:
                    task.status = "failed"
                    self.failed_tasks.append(task.id)

                    # Move to failed in LMDB
                    failed_key = (
                        f"/projects/{self.project_id}/memory/tasks/failed/{task.id}"
                    )
                    await self.memory.mcp.write(failed_key, task_data or "")
                    if task_data:
                        await self.memory.mcp.delete(in_progress_key)

                    self.logger.error(f"Task {task.id} failed")

                    # Attempt automatic recovery if enabled
                    if self.auto_recovery_enabled and len(self.failed_tasks) > 3:
                        self.logger.info(
                            "Multiple task failures detected, attempting auto-recovery"
                        )
                        recovery_result = (
                            await self.recovery_manager.auto_recover_orchestration(self)
                        )
                        if recovery_result.get("success"):
                            self.logger.info("Auto-recovery succeeded")
                        else:
                            self.logger.warning(
                                "Auto-recovery failed, manual intervention may be required"
                            )

                return success

            except Exception:
                # Error context is automatically handled by error_handler
                task.status = "failed"
                if task.id not in self.failed_tasks:
                    self.failed_tasks.append(task.id)
                return False

    async def orchestrate(self) -> Dict[str, Any]:
        """Run complete integrated orchestration."""
        if not self.project_id or not self.task_graph:
            raise ValueError("Session not initialized. Call initialize_session first.")

        self.logger.info("Starting integrated orchestration...")

        max_iterations = 20  # Safety limit
        iteration = 0

        while iteration < max_iterations:
            next_task = self.task_graph.get_next_task(self.completed_tasks)

            if not next_task:
                self.logger.info("No more tasks to execute")
                break

            self.logger.info(f"Executing task: {next_task.id}")
            success = await self.execute_task_with_supervisor(next_task)

            if not success:
                self.logger.error(f"Task {next_task.id} failed, continuing...")

            iteration += 1

        completion_percentage = (
            len(self.completed_tasks) / len(self.task_graph.tasks)
        ) * 100

        result = {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "goal": self.task_graph.goal,
            "total_tasks": len(self.task_graph.tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "completion_percentage": completion_percentage,
            "task_list": [task.to_dict() for task in self.task_graph.tasks],
        }

        # Store final result
        result_key = f"/projects/{self.project_id}/sessions/{self.session_id}/result"
        await self.memory.mcp.write(result_key, json.dumps(result))

        self.logger.info(
            f"Integrated orchestration completed: {len(self.completed_tasks)}/{len(self.task_graph.tasks)} tasks ({completion_percentage:.1f}%)"
        )

        return result

    async def resume_session(self, project_id: str, session_id: str) -> bool:
        """Resume a previous orchestration session."""
        try:
            # Load session metadata
            session_key = f"/projects/{project_id}/sessions/{session_id}/metadata"
            session_data = await self.memory.mcp.read(session_key)

            if not session_data:
                return False

            session_info = json.loads(session_data)
            self.project_id = project_id
            self.session_id = session_id

            # Load task graph
            task_graph = SimplifiedTaskGraph("", self.memory)
            if await task_graph.load_from_lmdb(project_id):
                self.task_graph = task_graph

                # Load completed/failed tasks
                self.completed_tasks = []
                self.failed_tasks = []

                # Check task statuses in LMDB
                for task in self.task_graph.tasks:
                    completed_key = (
                        f"/projects/{project_id}/memory/tasks/completed/{task.id}"
                    )
                    failed_key = f"/projects/{project_id}/memory/tasks/failed/{task.id}"

                    if await self.memory.mcp.read(completed_key):
                        self.completed_tasks.append(task.id)
                        task.status = "completed"
                    elif await self.memory.mcp.read(failed_key):
                        self.failed_tasks.append(task.id)
                        task.status = "failed"

                self.logger.info(
                    f"Resumed session {session_id} for project {project_id}"
                )
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to resume session: {e}")
            return False

    async def get_session_status(self) -> Dict[str, Any]:
        """Get current session status."""
        if not self.project_id or not self.session_id:
            return {"error": "No active session"}

        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "goal": self.task_graph.goal if self.task_graph else None,
            "total_tasks": len(self.task_graph.tasks) if self.task_graph else 0,
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "active": True,
        }
