"""Recovery utilities for APEX orchestration system."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict

from apex.core.error_handling import ErrorRecoveryManager
from apex.core.memory import MemoryPatterns

if TYPE_CHECKING:
    from apex.integration.simple_bridge import IntegratedOrchestrator


class OrchestrationRecoveryManager:
    """Manages recovery for orchestration failures."""

    def __init__(self, memory: MemoryPatterns):
        self.memory = memory
        self.error_manager = ErrorRecoveryManager(memory)
        self.logger = logging.getLogger(__name__)

    async def create_checkpoint(self, orchestrator: IntegratedOrchestrator) -> str:
        """Create a checkpoint of the current orchestration state."""
        if not orchestrator.project_id or not orchestrator.session_id:
            raise ValueError("Orchestrator not properly initialized")

        checkpoint_id = f"checkpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Gather checkpoint data
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "created_at": datetime.now().isoformat(),
            "project_id": orchestrator.project_id,
            "session_id": orchestrator.session_id,
            "orchestrator_state": {
                "completed_tasks": orchestrator.completed_tasks,
                "failed_tasks": orchestrator.failed_tasks,
                "task_graph": (
                    orchestrator.task_graph.to_dict()
                    if orchestrator.task_graph
                    else None
                ),
            },
            "supervisor_state": (
                orchestrator.supervisor_engine.state.__dict__
                if orchestrator.supervisor_engine.state
                else None
            ),
        }

        # Store checkpoint
        checkpoint_key = f"/projects/{orchestrator.project_id}/sessions/{orchestrator.session_id}/checkpoints/{checkpoint_id}"
        await self.memory.mcp.write(checkpoint_key, json.dumps(checkpoint_data))

        self.logger.info(
            f"Created checkpoint {checkpoint_id} for project {orchestrator.project_id}"
        )
        return checkpoint_id

    async def restore_from_checkpoint(
        self, orchestrator: IntegratedOrchestrator, checkpoint_id: str
    ) -> bool:
        """Restore orchestration state from a checkpoint."""
        try:
            # Find checkpoint
            checkpoint_key = None
            if orchestrator.project_id and orchestrator.session_id:
                checkpoint_key = f"/projects/{orchestrator.project_id}/sessions/{orchestrator.session_id}/checkpoints/{checkpoint_id}"
            else:
                # Search for checkpoint across all projects
                all_keys = await self.memory.mcp.list_keys("/projects/")
                for key in all_keys:
                    if f"/checkpoints/{checkpoint_id}" in key:
                        checkpoint_key = key
                        break

            if not checkpoint_key:
                self.logger.error(f"Checkpoint {checkpoint_id} not found")
                return False

            # Load checkpoint data
            checkpoint_json = await self.memory.mcp.read(checkpoint_key)
            if not checkpoint_json:
                self.logger.error(f"Checkpoint {checkpoint_id} data not found")
                return False

            checkpoint_data = json.loads(checkpoint_json)

            # Restore orchestrator state
            orchestrator.project_id = checkpoint_data["project_id"]
            orchestrator.session_id = checkpoint_data["session_id"]

            state_data = checkpoint_data.get("orchestrator_state", {})
            orchestrator.completed_tasks = state_data.get("completed_tasks", [])
            orchestrator.failed_tasks = state_data.get("failed_tasks", [])

            # Restore task graph if available
            if state_data.get("task_graph"):
                from apex.integration.simple_bridge import SimplifiedTaskGraph

                task_graph = SimplifiedTaskGraph("", orchestrator.memory)
                graph_data = state_data["task_graph"]
                task_graph.goal = graph_data["goal"]
                task_graph.created_at = graph_data["created_at"]
                task_graph.project_id = graph_data.get("project_id")

                # Restore tasks
                task_graph.tasks = []
                for task_data in graph_data.get("tasks", []):
                    from apex.integration.simple_bridge import SimplifiedTaskSpec

                    task = SimplifiedTaskSpec.from_dict(task_data)
                    task_graph.add_task(task)

                orchestrator.task_graph = task_graph

            self.logger.info(
                f"Restored orchestration state from checkpoint {checkpoint_id}"
            )
            return True

        except Exception as e:
            await self.error_manager.handle_error(
                error=e,
                context={"checkpoint_id": checkpoint_id},
                component="recovery",
                operation="restore_checkpoint",
            )
            return False

    async def recover_failed_tasks(
        self, orchestrator: IntegratedOrchestrator
    ) -> Dict[str, Any]:
        """Attempt to recover failed tasks."""
        if not orchestrator.project_id or not orchestrator.task_graph:
            return {"error": "Orchestrator not properly initialized"}

        recovery_results = {
            "attempted": 0,
            "recovered": 0,
            "still_failed": 0,
            "details": [],
        }

        for task_id in orchestrator.failed_tasks.copy():
            recovery_results["attempted"] += 1

            try:
                # Find the task in task graph
                task = None
                for t in orchestrator.task_graph.tasks:
                    if t.id == task_id:
                        task = t
                        break

                if not task:
                    recovery_results["details"].append(
                        {
                            "task_id": task_id,
                            "status": "not_found",
                            "message": "Task not found in task graph",
                        }
                    )
                    continue

                # Attempt recovery based on task type and failure reason
                success = await self._attempt_task_recovery(orchestrator, task)

                if success:
                    orchestrator.failed_tasks.remove(task_id)
                    if task_id not in orchestrator.completed_tasks:
                        orchestrator.completed_tasks.append(task_id)
                    recovery_results["recovered"] += 1
                    recovery_results["details"].append(
                        {
                            "task_id": task_id,
                            "status": "recovered",
                            "message": "Task successfully recovered",
                        }
                    )
                else:
                    recovery_results["still_failed"] += 1
                    recovery_results["details"].append(
                        {
                            "task_id": task_id,
                            "status": "still_failed",
                            "message": "Recovery attempt failed",
                        }
                    )

            except Exception as e:
                recovery_results["still_failed"] += 1
                recovery_results["details"].append(
                    {
                        "task_id": task_id,
                        "status": "error",
                        "message": f"Recovery error: {str(e)}",
                    }
                )

        self.logger.info(
            f"Task recovery completed: {recovery_results['recovered']}/{recovery_results['attempted']} tasks recovered"
        )
        return recovery_results

    async def _attempt_task_recovery(
        self, orchestrator: IntegratedOrchestrator, task
    ) -> bool:
        """Attempt to recover a specific task."""
        try:
            # Reset task status
            task.status = "pending"

            # Check if dependencies are still satisfied
            missing_deps = []
            for dep_id in task.dependencies:
                if dep_id not in orchestrator.completed_tasks:
                    missing_deps.append(dep_id)

            if missing_deps:
                self.logger.warning(
                    f"Task {task.id} has unsatisfied dependencies: {missing_deps}"
                )
                return False

            # Attempt to re-execute the task
            success = await orchestrator.execute_task_with_supervisor(task)
            return success

        except Exception as e:
            self.logger.error(f"Failed to recover task {task.id}: {e}")
            return False

    async def auto_recover_orchestration(
        self, orchestrator: IntegratedOrchestrator
    ) -> Dict[str, Any]:
        """Automatically attempt orchestration recovery."""
        recovery_report = {
            "started_at": datetime.now().isoformat(),
            "steps": [],
            "success": False,
            "final_state": {},
        }

        try:
            # Step 1: Create recovery checkpoint
            recovery_report["steps"].append("Creating recovery checkpoint...")
            checkpoint_id = await self.create_checkpoint(orchestrator)
            recovery_report["steps"].append(f"Checkpoint created: {checkpoint_id}")

            # Step 2: Analyze error patterns
            recovery_report["steps"].append("Analyzing error patterns...")
            error_summary = await self.error_manager.get_error_summary(
                orchestrator.project_id
            )
            recovery_report["error_summary"] = error_summary

            # Step 3: Attempt to recover failed tasks
            recovery_report["steps"].append("Attempting task recovery...")
            task_recovery = await self.recover_failed_tasks(orchestrator)
            recovery_report["task_recovery"] = task_recovery

            # Step 4: Check orchestration health
            recovery_report["steps"].append("Checking orchestration health...")
            health_status = await self.check_orchestration_health(orchestrator)
            recovery_report["health_status"] = health_status

            # Step 5: Resume orchestration if healthy
            if health_status.get("healthy", False):
                recovery_report["steps"].append("Resuming orchestration...")
                # Continue orchestration from current state
                # This would typically involve continuing the orchestration loop
                recovery_report["success"] = True
            else:
                recovery_report["steps"].append(
                    "Orchestration not healthy, manual intervention required"
                )

            # Final state
            recovery_report["final_state"] = {
                "completed_tasks": len(orchestrator.completed_tasks),
                "failed_tasks": len(orchestrator.failed_tasks),
                "total_tasks": (
                    len(orchestrator.task_graph.tasks) if orchestrator.task_graph else 0
                ),
            }

        except Exception as e:
            recovery_report["steps"].append(f"Recovery failed: {str(e)}")
            await self.error_manager.handle_error(
                error=e,
                context={"recovery_report": recovery_report},
                component="recovery",
                operation="auto_recover",
            )

        recovery_report["completed_at"] = datetime.now().isoformat()

        # Store recovery report
        if orchestrator.project_id and orchestrator.session_id:
            report_key = f"/projects/{orchestrator.project_id}/sessions/{orchestrator.session_id}/recovery_reports/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            await self.memory.mcp.write(report_key, json.dumps(recovery_report))

        return recovery_report

    async def check_orchestration_health(
        self, orchestrator: IntegratedOrchestrator
    ) -> Dict[str, Any]:
        """Check the health of orchestration system."""
        health_status = {
            "healthy": True,
            "issues": [],
            "warnings": [],
            "checks": {},
        }

        try:
            # Check 1: Memory connectivity
            try:
                await self.memory.mcp.list_keys("/")
                health_status["checks"]["memory_connectivity"] = "OK"
            except Exception as e:
                health_status["healthy"] = False
                health_status["issues"].append(f"Memory connectivity failed: {str(e)}")
                health_status["checks"]["memory_connectivity"] = "FAILED"

            # Check 2: Task graph integrity
            if orchestrator.task_graph:
                total_tasks = len(orchestrator.task_graph.tasks)
                completed_tasks = len(orchestrator.completed_tasks)
                failed_tasks = len(orchestrator.failed_tasks)

                if total_tasks > 0:
                    completion_rate = completed_tasks / total_tasks
                    failure_rate = failed_tasks / total_tasks

                    health_status["checks"]["completion_rate"] = (
                        f"{completion_rate:.2%}"
                    )
                    health_status["checks"]["failure_rate"] = f"{failure_rate:.2%}"

                    if failure_rate > 0.5:  # More than 50% failed
                        health_status["healthy"] = False
                        health_status["issues"].append("High task failure rate")
                    elif failure_rate > 0.2:  # More than 20% failed
                        health_status["warnings"].append("Elevated task failure rate")

                    health_status["checks"]["task_graph"] = "OK"
                else:
                    health_status["warnings"].append("No tasks in task graph")
                    health_status["checks"]["task_graph"] = "EMPTY"
            else:
                health_status["warnings"].append("No task graph available")
                health_status["checks"]["task_graph"] = "MISSING"

            # Check 3: Error rate
            error_summary = await self.error_manager.get_error_summary(
                orchestrator.project_id
            )
            if error_summary.get("total_errors", 0) > 0:
                critical_errors = error_summary.get("by_severity", {}).get(
                    "critical", 0
                )
                high_errors = error_summary.get("by_severity", {}).get("high", 0)

                if critical_errors > 0:
                    health_status["healthy"] = False
                    health_status["issues"].append(
                        f"{critical_errors} critical errors detected"
                    )

                if high_errors > 3:
                    health_status["warnings"].append(
                        f"{high_errors} high-severity errors detected"
                    )

                health_status["checks"]["error_rate"] = (
                    f"{error_summary['total_errors']} total errors"
                )
            else:
                health_status["checks"]["error_rate"] = "No errors detected"

            # Check 4: Supervisor engine state
            if orchestrator.supervisor_engine and orchestrator.supervisor_engine.state:
                state = orchestrator.supervisor_engine.state
                health_status["checks"]["supervisor_state"] = state.current_stage.value

                if state.stop_requested:
                    health_status["warnings"].append("Stop requested")

                if state.paused:
                    health_status["warnings"].append("Orchestration paused")
            else:
                health_status["warnings"].append(
                    "Supervisor engine state not available"
                )
                health_status["checks"]["supervisor_state"] = "UNKNOWN"

        except Exception as e:
            health_status["healthy"] = False
            health_status["issues"].append(f"Health check failed: {str(e)}")

        return health_status

    async def schedule_periodic_checkpoints(
        self, orchestrator: IntegratedOrchestrator, interval_minutes: int = 30
    ) -> None:
        """Schedule periodic checkpoints for the orchestration."""
        self.logger.info(
            f"Scheduling periodic checkpoints every {interval_minutes} minutes"
        )

        while orchestrator.project_id and orchestrator.session_id:
            try:
                await asyncio.sleep(interval_minutes * 60)

                # Check if orchestration is still active
                if orchestrator.task_graph:
                    remaining_tasks = (
                        len(orchestrator.task_graph.tasks)
                        - len(orchestrator.completed_tasks)
                        - len(orchestrator.failed_tasks)
                    )
                    if remaining_tasks > 0:
                        checkpoint_id = await self.create_checkpoint(orchestrator)
                        self.logger.info(
                            f"Periodic checkpoint created: {checkpoint_id}"
                        )
                    else:
                        self.logger.info(
                            "Orchestration completed, stopping periodic checkpoints"
                        )
                        break
                else:
                    break

            except Exception as e:
                self.logger.error(f"Periodic checkpoint failed: {e}")
                break

    async def cleanup_old_checkpoints(
        self, project_id: str, keep_count: int = 10, max_age_days: int = 30
    ) -> int:
        """Clean up old checkpoints to free storage."""
        try:
            # Find all checkpoints for the project
            checkpoint_keys = await self.memory.mcp.list_keys(
                f"/projects/{project_id}/"
            )
            checkpoint_keys = [k for k in checkpoint_keys if "/checkpoints/" in k]

            if len(checkpoint_keys) <= keep_count:
                return 0  # Nothing to clean up

            # Sort by timestamp (assuming checkpoint IDs contain timestamps)
            checkpoint_keys.sort(reverse=True)  # Newest first

            cleanup_count = 0
            cutoff_date = datetime.now() - timedelta(days=max_age_days)

            # Keep the newest checkpoints and remove old ones
            for checkpoint_key in checkpoint_keys[keep_count:]:
                try:
                    checkpoint_json = await self.memory.mcp.read(checkpoint_key)
                    if checkpoint_json:
                        checkpoint_data = json.loads(checkpoint_json)
                        created_at = datetime.fromisoformat(
                            checkpoint_data.get("created_at", "")
                        )

                        if created_at < cutoff_date:
                            await self.memory.mcp.delete(checkpoint_key)
                            cleanup_count += 1

                except Exception as e:
                    self.logger.warning(
                        f"Failed to process checkpoint {checkpoint_key}: {e}"
                    )
                    continue

            self.logger.info(
                f"Cleaned up {cleanup_count} old checkpoints for project {project_id}"
            )
            return cleanup_count

        except Exception as e:
            self.logger.error(f"Checkpoint cleanup failed: {e}")
            return 0
