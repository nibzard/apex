"""Task workflow management for APEX agents."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from apex.core.lmdb_mcp import LMDBMCP
from apex.types import AgentType, TaskInfo


class TaskWorkflow:
    """Manages task assignment and workflow between agents."""

    def __init__(self, lmdb: LMDBMCP) -> None:
        self.lmdb = lmdb

    async def assign_task(
        self,
        description: str,
        assigned_to: AgentType,
        priority: str = "medium",
        depends_on: Optional[List[str]] = None,
        assigned_by: str = "supervisor",
    ) -> str:
        """Assign a new task to an agent.

        Args:
            description: Task description
            assigned_to: Agent type to assign to
            priority: Task priority (low, medium, high)
            depends_on: List of task IDs this depends on
            assigned_by: Agent that assigned this task

        Returns:
            Task ID

        """
        task_id = str(uuid.uuid4())

        task_info = TaskInfo(
            task_id=task_id,
            description=description,
            assigned_to=assigned_to,
            priority=priority,
            depends_on=depends_on or [],
        )

        # Store in pending tasks
        pending_key = f"/tasks/pending/{task_id}"
        await self._write_lmdb(pending_key, task_info.model_dump())

        # Update task index
        index_key = f"/tasks/index/{task_id}"
        index_data = {
            "status": "pending",
            "assigned_to": assigned_to.value,
            "priority": priority,
            "assigned_by": assigned_by,
            "created_at": task_info.created_at.isoformat(),
        }
        await self._write_lmdb(index_key, index_data)

        # Add to agent's pending queue
        queue_key = f"/agents/{assigned_to.value}/tasks/pending"
        pending_tasks = await self._read_lmdb(queue_key) or []
        pending_tasks.append(task_id)
        await self._write_lmdb(queue_key, pending_tasks)

        return task_id

    async def complete_task(
        self, task_id: str, result: Dict[str, Any], completed_by: str
    ) -> bool:
        """Mark a task as completed.

        Args:
            task_id: Task identifier
            result: Task completion result
            completed_by: Agent that completed the task

        Returns:
            True if task was completed successfully

        """
        # Get task from pending
        pending_key = f"/tasks/pending/{task_id}"
        task_data = await self._read_lmdb(pending_key)

        if not task_data:
            return False

        # Update task data
        task_data["status"] = "completed"
        task_data["completed_at"] = datetime.now().isoformat()
        task_data["result"] = result
        task_data["completed_by"] = completed_by

        # Move to completed
        completed_key = f"/tasks/completed/{task_id}"
        await self._write_lmdb(completed_key, task_data)

        # Remove from pending
        await self._delete_lmdb(pending_key)

        # Update index
        index_key = f"/tasks/index/{task_id}"
        index_data = await self._read_lmdb(index_key) or {}
        index_data.update(
            {
                "status": "completed",
                "completed_at": task_data["completed_at"],
                "completed_by": completed_by,
            }
        )
        await self._write_lmdb(index_key, index_data)

        # Remove from agent's pending queue
        assigned_to = task_data.get("assigned_to")
        if assigned_to:
            queue_key = f"/agents/{assigned_to}/tasks/pending"
            pending_tasks = await self._read_lmdb(queue_key) or []
            if task_id in pending_tasks:
                pending_tasks.remove(task_id)
                await self._write_lmdb(queue_key, pending_tasks)

        return True

    async def get_pending_tasks(self, agent_type: AgentType) -> List[Dict[str, Any]]:
        """Get pending tasks for an agent.

        Args:
            agent_type: Agent type to get tasks for

        Returns:
            List of pending task data

        """
        queue_key = f"/agents/{agent_type.value}/tasks/pending"
        task_ids = await self._read_lmdb(queue_key) or []

        tasks = []
        for task_id in task_ids:
            pending_key = f"/tasks/pending/{task_id}"
            task_data = await self._read_lmdb(pending_key)
            if task_data:
                tasks.append(task_data)

        # Sort by priority and creation time
        def priority_sort_key(task):
            priority_order = {"high": 0, "medium": 1, "low": 2}
            return (
                priority_order.get(task.get("priority", "medium"), 1),
                task.get("created_at", ""),
            )

        return sorted(tasks, key=priority_sort_key)

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task.

        Args:
            task_id: Task identifier

        Returns:
            Task status data or None if not found

        """
        # Check pending first
        pending_key = f"/tasks/pending/{task_id}"
        task_data = await self._read_lmdb(pending_key)

        if task_data:
            return task_data

        # Check completed
        completed_key = f"/tasks/completed/{task_id}"
        task_data = await self._read_lmdb(completed_key)

        return task_data

    async def list_all_tasks(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all tasks, optionally filtered by status.

        Args:
            status: Optional status filter (pending, completed)

        Returns:
            List of task data

        """
        tasks = []

        if status is None or status == "pending":
            # Get all pending tasks
            pending_keys = await self._list_keys("/tasks/pending/")
            for key in pending_keys:
                task_data = await self._read_lmdb(key)
                if task_data:
                    tasks.append(task_data)

        if status is None or status == "completed":
            # Get all completed tasks
            completed_keys = await self._list_keys("/tasks/completed/")
            for key in completed_keys:
                task_data = await self._read_lmdb(key)
                if task_data:
                    tasks.append(task_data)

        return tasks

    async def create_supervisor_workflow(
        self, user_request: str, project_context: Dict[str, Any]
    ) -> List[str]:
        """Create a workflow of tasks for a user request.

        This is the main entry point for the Supervisor to break down
        a user request into specific tasks for the Coder and Adversary.

        Args:
            user_request: The user's request
            project_context: Context about the project

        Returns:
            List of created task IDs

        """
        task_ids = []

        # Example workflow breakdown
        # In a real implementation, this would use AI to intelligently break down the request

        # 1. Analysis task for Coder
        analysis_task_id = await self.assign_task(
            description=f"Analyze the following request and plan implementation: {user_request}",
            assigned_to=AgentType.CODER,
            priority="high",
        )
        task_ids.append(analysis_task_id)

        # 2. Implementation task for Coder (depends on analysis)
        impl_task_id = await self.assign_task(
            description=f"Implement the solution for: {user_request}",
            assigned_to=AgentType.CODER,
            priority="high",
            depends_on=[analysis_task_id],
        )
        task_ids.append(impl_task_id)

        # 3. Testing task for Adversary (depends on implementation)
        test_task_id = await self.assign_task(
            description=f"Test and review the implementation for: {user_request}",
            assigned_to=AgentType.ADVERSARY,
            priority="medium",
            depends_on=[impl_task_id],
        )
        task_ids.append(test_task_id)

        return task_ids

    async def _read_lmdb(self, key: str) -> Optional[Any]:
        """Read from LMDB with JSON deserialization."""
        try:
            data = await asyncio.get_event_loop().run_in_executor(
                None, self.lmdb.read, key
            )
            if data:
                return json.loads(data.decode())
            return None
        except Exception:
            return None

    async def _write_lmdb(self, key: str, data: Any) -> None:
        """Write to LMDB with JSON serialization."""
        serialized = json.dumps(data, default=str).encode()
        await asyncio.get_event_loop().run_in_executor(
            None, self.lmdb.write, key, serialized
        )

    async def _delete_lmdb(self, key: str) -> None:
        """Delete from LMDB."""
        await asyncio.get_event_loop().run_in_executor(None, self.lmdb.delete, key)

    async def _list_keys(self, prefix: str) -> List[str]:
        """List keys with prefix from LMDB."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.lmdb.list_keys, prefix
        )


class WorkflowManager:
    """High-level workflow management for APEX system."""

    def __init__(self, task_workflow: TaskWorkflow) -> None:
        self.workflow = task_workflow

    async def start_project_workflow(
        self, user_request: str, project_config: Dict[str, Any]
    ) -> str:
        """Start a complete project workflow.

        Args:
            user_request: User's request
            project_config: Project configuration

        Returns:
            Workflow ID

        """
        workflow_id = str(uuid.uuid4())

        # Create tasks for the request
        task_ids = await self.workflow.create_supervisor_workflow(
            user_request, project_config
        )

        # Store workflow metadata
        workflow_data = {
            "workflow_id": workflow_id,
            "user_request": user_request,
            "task_ids": task_ids,
            "status": "started",
            "created_at": datetime.now().isoformat(),
        }

        workflow_key = f"/workflows/{workflow_id}"
        await self.workflow._write_lmdb(workflow_key, workflow_data)

        return workflow_id

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow status data

        """
        workflow_key = f"/workflows/{workflow_id}"
        workflow_data = await self.workflow._read_lmdb(workflow_key)

        if not workflow_data:
            return None

        # Add current task statuses
        task_statuses = []
        for task_id in workflow_data.get("task_ids", []):
            task_status = await self.workflow.get_task_status(task_id)
            if task_status:
                task_statuses.append(task_status)

        workflow_data["task_statuses"] = task_statuses

        # Determine overall workflow status
        completed_tasks = sum(
            1 for task in task_statuses if task.get("status") == "completed"
        )
        total_tasks = len(task_statuses)

        if completed_tasks == total_tasks and total_tasks > 0:
            workflow_data["status"] = "completed"
        elif completed_tasks > 0:
            workflow_data["status"] = "in_progress"
        else:
            workflow_data["status"] = "pending"

        return workflow_data


# Example usage and testing
async def test_task_workflow():
    """Test the task workflow system."""
    from pathlib import Path

    from apex.core.lmdb_mcp import LMDBMCP

    # Create LMDB instance
    lmdb = LMDBMCP(Path("test_workflow.db"))

    try:
        # Create workflow
        workflow = TaskWorkflow(lmdb)
        manager = WorkflowManager(workflow)

        # Start a workflow
        workflow_id = await manager.start_project_workflow(
            "Create a simple calculator app",
            {"name": "calculator", "tech_stack": ["Python"]},
        )

        print(f"Started workflow: {workflow_id}")

        # Check pending tasks for coder
        coder_tasks = await workflow.get_pending_tasks(AgentType.CODER)
        print(f"Coder has {len(coder_tasks)} pending tasks")

        # Simulate task completion
        if coder_tasks:
            task_id = coder_tasks[0]["task_id"]
            await workflow.complete_task(
                task_id, {"code": "def add(a, b): return a + b"}, "coder_agent"
            )
            print(f"Completed task: {task_id}")

        # Check workflow status
        status = await manager.get_workflow_status(workflow_id)
        print(f"Workflow status: {status['status']}")
        print(
            f"Tasks completed: {len([t for t in status['task_statuses'] if t.get('status') == 'completed'])}"
        )

    finally:
        lmdb.close()


if __name__ == "__main__":
    asyncio.run(test_task_workflow())
