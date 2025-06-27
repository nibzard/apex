"""TaskPlanner - Simple task decomposition for APEX v2.0.

The TaskPlanner breaks down high-level goals into 3-5 discrete, executable tasks
using simple template-based logic instead of complex strategy patterns.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from apex.core.memory import MemoryPatterns
from apex.core.task_briefing import TaskPriority, TaskRole


class TaskSpec:
    """Simple specification for a planned task."""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        description: str,
        role: TaskRole,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ):
        """Initialize TaskSpec with task details."""
        self.id = task_id
        self.type = task_type
        self.description = description
        self.role = role
        self.priority = priority
        self.dependencies: List[str] = []
        self.estimated_duration = 60  # Default 60 minutes
        self.metadata: Dict[str, Any] = {}

    def add_dependency(self, task_id: str) -> None:
        """Add a dependency to this task."""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "role": self.role.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "estimated_duration": self.estimated_duration,
            "metadata": self.metadata,
        }


class TaskGraph:
    """Simple collection of tasks with basic ordering."""

    def __init__(self, goal: str):
        """Initialize TaskGraph with goal."""
        self.goal = goal
        self.tasks: List[TaskSpec] = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def add_task(self, task: TaskSpec) -> None:
        """Add a task to the graph."""
        self.tasks.append(task)
        self.updated_at = datetime.now().isoformat()

    def get_next_task(self, completed_task_ids: List[str]) -> Optional[TaskSpec]:
        """Get the next task to execute."""
        for task in self.tasks:
            if task.id in completed_task_ids:
                continue

            # Check if all dependencies are completed
            if all(dep in completed_task_ids for dep in task.dependencies):
                return task

        return None

    def get_completion_percentage(self, completed_task_ids: List[str]) -> float:
        """Calculate completion percentage."""
        if not self.tasks:
            return 100.0

        completed_count = sum(1 for task in self.tasks if task.id in completed_task_ids)
        return (completed_count / len(self.tasks)) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "goal": self.goal,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tasks": [task.to_dict() for task in self.tasks],
        }


class SimpleTaskTemplates:
    """Simple templates for common development tasks."""

    """Planning strategy specialized for software development tasks."""

    def create_implementation_tasks(self, goal: str) -> List[TaskSpec]:
        """Create implementation task sequence: Research → Implement → Test."""
        return self._create_task_sequence(
            goal,
            [
                (
                    "research",
                    "Research requirements and plan approach",
                    TaskRole.CODER,
                    30,
                ),
                ("implementation", "Implement core functionality", TaskRole.CODER, 90),
                ("testing", "Test and validate implementation", TaskRole.ADVERSARY, 45),
            ],
        )

    def create_bug_fix_tasks(self, goal: str) -> List[TaskSpec]:
        """Create bug fix task sequence: Investigate → Fix → Verify."""
        return self._create_task_sequence(
            goal,
            [
                ("investigation", "Investigate and reproduce", TaskRole.ADVERSARY, 30),
                ("bug_fix", "Implement fix", TaskRole.CODER, 60),
                (
                    "verification",
                    "Verify fix and test for regressions",
                    TaskRole.ADVERSARY,
                    30,
                ),
            ],
        )

    def create_generic_tasks(self, goal: str) -> List[TaskSpec]:
        """Create generic task sequence: Analyze → Implement → Review."""
        return self._create_task_sequence(
            goal,
            [
                ("analysis", "Analyze and clarify requirements", TaskRole.CODER, 30),
                ("implementation", "Implement solution", TaskRole.CODER, 90),
                ("review", "Review and validate solution", TaskRole.ADVERSARY, 30),
            ],
        )

    def _create_task_sequence(
        self, goal: str, task_definitions: List[tuple]
    ) -> List[TaskSpec]:
        """Unified task creation logic to eliminate duplication."""
        task_prefix = f"task-{datetime.now().strftime('%Y%m%d-%H%M')}"
        tasks = []
        prev_task_id = None

        for task_type, description_prefix, role, duration in task_definitions:
            task = TaskSpec(
                f"{task_prefix}-{task_type}",
                task_type,
                f"{description_prefix}: {goal}",
                role,
                TaskPriority.HIGH,
            )
            task.estimated_duration = duration

            # Add dependency to previous task
            if prev_task_id:
                task.add_dependency(prev_task_id)

            tasks.append(task)
            prev_task_id = task.id

        return tasks


class TaskPlanner:
    """Simple task planner for APEX v2.0 Supervisor."""

    def __init__(self, memory_patterns: MemoryPatterns):
        """Initialize the TaskPlanner."""
        self.memory = memory_patterns
        self.logger = logging.getLogger(__name__)
        self.templates = SimpleTaskTemplates()

    async def create_task_graph(
        self, project_id: str, goal: str, context: Dict[str, Any] = None
    ) -> TaskGraph:
        """Create a new task graph for a goal using unified templates."""
        self.logger.info(f"Creating task graph for goal: {goal}")

        # Determine task type from goal keywords
        tasks = self._select_task_template(goal)

        # Create and populate task graph
        graph = TaskGraph(goal)
        for task in tasks:
            graph.add_task(task)

        # Store graph in LMDB
        await self._store_task_graph(project_id, graph)

        self.logger.info(f"Created task graph with {len(tasks)} tasks")
        return graph

    def _select_task_template(self, goal: str) -> List[TaskSpec]:
        """Select appropriate task template based on goal analysis."""
        goal_lower = goal.lower()

        # Bug fix indicators
        if any(
            word in goal_lower for word in ["fix", "bug", "error", "issue", "repair"]
        ):
            return self.templates.create_bug_fix_tasks(goal)

        # Implementation indicators
        elif any(
            word in goal_lower
            for word in ["implement", "add", "create", "build", "develop"]
        ):
            return self.templates.create_implementation_tasks(goal)

        # Default to generic approach
        else:
            return self.templates.create_generic_tasks(goal)

    async def get_next_task(
        self, project_id: str, completed_task_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Get the next task to execute."""
        try:
            graph = await self._load_task_graph(project_id)
            if not graph:
                return None

            next_task = graph.get_next_task(completed_task_ids)
            return next_task.to_dict() if next_task else None

        except Exception as e:
            self.logger.error(f"Error getting next task: {e}")
            return None

    async def get_progress(
        self, project_id: str, completed_task_ids: List[str]
    ) -> Dict[str, Any]:
        """Get progress information for the task graph."""
        try:
            graph = await self._load_task_graph(project_id)
            if not graph:
                return {"error": "No task graph found"}

            completion_percentage = graph.get_completion_percentage(completed_task_ids)

            return {
                "goal": graph.goal,
                "total_tasks": len(graph.tasks),
                "completed_tasks": len(completed_task_ids),
                "completion_percentage": completion_percentage,
                "remaining_tasks": len(graph.tasks) - len(completed_task_ids),
            }

        except Exception as e:
            self.logger.error(f"Error getting progress: {e}")
            return {"error": str(e)}

    async def _store_task_graph(self, project_id: str, graph: TaskGraph) -> None:
        """Store task graph in LMDB."""
        graph_key = f"/projects/{project_id}/supervisor/task_graph"
        await self.memory.mcp.write(graph_key, json.dumps(graph.to_dict()))

    async def _load_task_graph(self, project_id: str) -> Optional[TaskGraph]:
        """Load task graph from LMDB."""
        try:
            graph_key = f"/projects/{project_id}/supervisor/task_graph"
            data = await self.memory.mcp.read(graph_key)

            if not data:
                return None

            graph_data = json.loads(data)

            # Reconstruct TaskGraph object
            graph = TaskGraph(graph_data["goal"])
            graph.created_at = graph_data["created_at"]
            graph.updated_at = graph_data["updated_at"]

            # Reconstruct tasks
            for task_data in graph_data["tasks"]:
                task = TaskSpec(
                    task_data["id"],
                    task_data["type"],
                    task_data["description"],
                    TaskRole(task_data["role"]),
                    TaskPriority(task_data["priority"]),
                )
                task.dependencies = task_data["dependencies"]
                task.estimated_duration = task_data["estimated_duration"]
                task.metadata = task_data["metadata"]

                graph.add_task(task)

            return graph

        except Exception as e:
            self.logger.error(f"Error loading task graph: {e}")
            return None
