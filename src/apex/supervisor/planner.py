"""TaskPlanner - Intelligent task decomposition and dependency management for APEX v2.0.

The TaskPlanner breaks down high-level goals into discrete, executable tasks
with proper dependency relationships and resource requirements.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from apex.core.memory import MemoryPatterns
from apex.core.task_briefing import TaskPriority, TaskRole


class TaskSpec:
    """Specification for a planned task."""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        description: str,
        role: TaskRole,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ):
        self.id = task_id
        self.type = task_type
        self.description = description
        self.role = role
        self.priority = priority
        self.dependencies: List[str] = []
        self.blocks: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.estimated_duration: Optional[int] = None
        self.context_requirements: List[str] = []
        self.deliverable_requirements: List[str] = []

    def add_dependency(self, task_id: str) -> None:
        """Add a dependency to this task."""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def add_blocks(self, task_id: str) -> None:
        """Mark that this task blocks another task."""
        if task_id not in self.blocks:
            self.blocks.append(task_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "role": self.role.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "blocks": self.blocks,
            "metadata": self.metadata,
            "estimated_duration": self.estimated_duration,
            "context_requirements": self.context_requirements,
            "deliverable_requirements": self.deliverable_requirements,
        }


class TaskGraph:
    """Directed acyclic graph of tasks with dependency management."""

    def __init__(self, goal: str):
        self.goal = goal
        self.tasks: Dict[str, TaskSpec] = {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.metadata: Dict[str, Any] = {}

    def add_task(self, task: TaskSpec) -> None:
        """Add a task to the graph."""
        self.tasks[task.id] = task
        self.updated_at = datetime.now().isoformat()

    def add_dependency(self, task_id: str, depends_on: str) -> bool:
        """Add a dependency relationship."""
        if task_id not in self.tasks or depends_on not in self.tasks:
            return False

        # Check for circular dependencies
        if self._would_create_cycle(task_id, depends_on):
            return False

        self.tasks[task_id].add_dependency(depends_on)
        self.tasks[depends_on].add_blocks(task_id)
        self.updated_at = datetime.now().isoformat()
        return True

    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[TaskSpec]:
        """Get tasks that are ready to execute."""
        ready = []
        for task in self.tasks.values():
            if task.id in completed_tasks:
                continue

            # Check if all dependencies are completed
            if all(dep in completed_tasks for dep in task.dependencies):
                ready.append(task)

        # Sort by priority and creation order
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        ready.sort(key=lambda t: (priority_order.get(t.priority.value, 2), t.id))

        return ready

    def get_completion_percentage(self, completed_tasks: Set[str]) -> float:
        """Calculate completion percentage."""
        if not self.tasks:
            return 100.0

        completed_count = sum(
            1 for task_id in self.tasks.keys() if task_id in completed_tasks
        )
        return (completed_count / len(self.tasks)) * 100.0

    def get_critical_path(self) -> List[str]:
        """Get the critical path through the task graph."""
        # Simplified critical path calculation
        # In practice, this would use proper project management algorithms

        # Find tasks with no dependencies (start nodes)
        start_tasks = [task for task in self.tasks.values() if not task.dependencies]

        # Find tasks that block nothing (end nodes)
        end_tasks = [task for task in self.tasks.values() if not task.blocks]

        if not start_tasks or not end_tasks:
            return []

        # For now, return the longest path by task count
        return self._find_longest_path(start_tasks[0].id, set())

    def _would_create_cycle(self, task_id: str, depends_on: str) -> bool:
        """Check if adding dependency would create a cycle."""
        visited = set()

        def has_path(from_task: str, to_task: str) -> bool:
            if from_task == to_task:
                return True
            if from_task in visited:
                return False

            visited.add(from_task)

            if from_task in self.tasks:
                for dep in self.tasks[from_task].dependencies:
                    if has_path(dep, to_task):
                        return True

            return False

        return has_path(depends_on, task_id)

    def _find_longest_path(self, start_task: str, visited: Set[str]) -> List[str]:
        """Find longest path from start_task."""
        if start_task in visited or start_task not in self.tasks:
            return []

        visited.add(start_task)

        max_path = [start_task]
        for blocked_task in self.tasks[start_task].blocks:
            path = self._find_longest_path(blocked_task, visited.copy())
            if len(path) + 1 > len(max_path):
                max_path = [start_task] + path

        return max_path

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "goal": self.goal,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "tasks": [task.to_dict() for task in self.tasks.values()],
        }


class PlanningStrategy:
    """Base class for planning strategies."""

    def analyze_goal(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a goal and extract planning insights."""
        raise NotImplementedError

    def decompose_goal(self, goal: str, context: Dict[str, Any]) -> List[TaskSpec]:
        """Decompose a goal into tasks."""
        raise NotImplementedError

    def optimize_task_order(self, tasks: List[TaskSpec]) -> List[TaskSpec]:
        """Optimize the order of tasks."""
        return tasks


class SoftwareDevelopmentStrategy(PlanningStrategy):
    """Planning strategy specialized for software development tasks."""

    def analyze_goal(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a software development goal."""
        analysis = {
            "goal_type": "software_development",
            "complexity": "medium",
            "estimated_tasks": 5,
            "key_components": [],
            "technical_requirements": [],
            "quality_requirements": [],
        }

        goal_lower = goal.lower()

        # Detect goal type
        if any(word in goal_lower for word in ["implement", "add", "create", "build"]):
            analysis["goal_type"] = "implementation"
        elif any(word in goal_lower for word in ["fix", "bug", "error", "issue"]):
            analysis["goal_type"] = "bug_fix"
        elif any(word in goal_lower for word in ["refactor", "improve", "optimize"]):
            analysis["goal_type"] = "improvement"
        elif any(word in goal_lower for word in ["test", "testing", "coverage"]):
            analysis["goal_type"] = "testing"

        # Estimate complexity
        complexity_indicators = {
            "high": [
                "api",
                "database",
                "authentication",
                "security",
                "distributed",
                "microservice",
            ],
            "medium": ["endpoint", "feature", "component", "integration", "ui"],
            "low": ["function", "utility", "helper", "simple", "basic"],
        }

        for level, indicators in complexity_indicators.items():
            if any(indicator in goal_lower for indicator in indicators):
                analysis["complexity"] = level
                break

        # Estimate task count based on complexity
        task_estimates = {"low": 3, "medium": 5, "high": 8}
        analysis["estimated_tasks"] = task_estimates.get(analysis["complexity"], 5)

        return analysis

    def decompose_goal(self, goal: str, context: Dict[str, Any]) -> List[TaskSpec]:
        """Decompose software development goal into tasks."""
        analysis = self.analyze_goal(goal, context)
        tasks = []

        # Generate task ID prefix
        task_prefix = f"task-{datetime.now().strftime('%Y%m%d')}"

        if analysis["goal_type"] == "implementation":
            tasks.extend(self._create_implementation_tasks(goal, task_prefix, analysis))
        elif analysis["goal_type"] == "bug_fix":
            tasks.extend(self._create_bug_fix_tasks(goal, task_prefix, analysis))
        elif analysis["goal_type"] == "improvement":
            tasks.extend(self._create_improvement_tasks(goal, task_prefix, analysis))
        elif analysis["goal_type"] == "testing":
            tasks.extend(self._create_testing_tasks(goal, task_prefix, analysis))
        else:
            tasks.extend(self._create_generic_tasks(goal, task_prefix, analysis))

        return self.optimize_task_order(tasks)

    def _create_implementation_tasks(
        self, goal: str, prefix: str, analysis: Dict[str, Any]
    ) -> List[TaskSpec]:
        """Create tasks for implementation goals."""
        tasks = []

        # 1. Research and Planning
        research_task = TaskSpec(
            f"{prefix}-research-{str(uuid.uuid4())[:8]}",
            "research",
            f"Research and analyze requirements for: {goal}",
            TaskRole.CODER,
            TaskPriority.HIGH,
        )
        research_task.estimated_duration = 30
        research_task.deliverable_requirements = [
            "requirements_analysis.md",
            "technical_approach.md",
        ]
        tasks.append(research_task)

        # 2. Core Implementation
        impl_task = TaskSpec(
            f"{prefix}-implement-{str(uuid.uuid4())[:8]}",
            "implementation",
            f"Implement core functionality for: {goal}",
            TaskRole.CODER,
            TaskPriority.HIGH,
        )
        impl_task.add_dependency(research_task.id)
        impl_task.estimated_duration = 60
        impl_task.deliverable_requirements = ["source_code", "documentation"]
        tasks.append(impl_task)

        # 3. Testing
        test_task = TaskSpec(
            f"{prefix}-test-{str(uuid.uuid4())[:8]}",
            "testing",
            f"Create comprehensive tests for: {goal}",
            TaskRole.ADVERSARY,
            TaskPriority.HIGH,
        )
        test_task.add_dependency(impl_task.id)
        test_task.estimated_duration = 45
        test_task.deliverable_requirements = ["unit_tests", "integration_tests"]
        tasks.append(test_task)

        # 4. Security Review (for medium/high complexity)
        if analysis["complexity"] in ["medium", "high"]:
            security_task = TaskSpec(
                f"{prefix}-security-{str(uuid.uuid4())[:8]}",
                "security_review",
                f"Security and quality review for: {goal}",
                TaskRole.ADVERSARY,
                TaskPriority.MEDIUM,
            )
            security_task.add_dependency(impl_task.id)
            security_task.estimated_duration = 30
            security_task.deliverable_requirements = [
                "security_report",
                "quality_assessment",
            ]
            tasks.append(security_task)

        # 5. Integration and Documentation
        integration_task = TaskSpec(
            f"{prefix}-integrate-{str(uuid.uuid4())[:8]}",
            "integration",
            f"Integrate and document solution for: {goal}",
            TaskRole.CODER,
            TaskPriority.MEDIUM,
        )
        integration_task.add_dependency(test_task.id)
        if analysis["complexity"] in ["medium", "high"]:
            integration_task.add_dependency(tasks[-1].id)  # security task
        integration_task.estimated_duration = 30
        integration_task.deliverable_requirements = [
            "integration_complete",
            "final_documentation",
        ]
        tasks.append(integration_task)

        return tasks

    def _create_bug_fix_tasks(
        self, goal: str, prefix: str, analysis: Dict[str, Any]
    ) -> List[TaskSpec]:
        """Create tasks for bug fix goals."""
        tasks = []

        # 1. Bug Investigation
        investigate_task = TaskSpec(
            f"{prefix}-investigate-{str(uuid.uuid4())[:8]}",
            "investigation",
            f"Investigate and reproduce bug: {goal}",
            TaskRole.ADVERSARY,
            TaskPriority.HIGH,
        )
        investigate_task.estimated_duration = 30
        investigate_task.deliverable_requirements = [
            "bug_analysis.md",
            "reproduction_steps.md",
        ]
        tasks.append(investigate_task)

        # 2. Fix Implementation
        fix_task = TaskSpec(
            f"{prefix}-fix-{str(uuid.uuid4())[:8]}",
            "bug_fix",
            f"Implement fix for: {goal}",
            TaskRole.CODER,
            TaskPriority.HIGH,
        )
        fix_task.add_dependency(investigate_task.id)
        fix_task.estimated_duration = 45
        fix_task.deliverable_requirements = ["fixed_code", "fix_documentation"]
        tasks.append(fix_task)

        # 3. Verification
        verify_task = TaskSpec(
            f"{prefix}-verify-{str(uuid.uuid4())[:8]}",
            "verification",
            f"Verify fix and test for regressions: {goal}",
            TaskRole.ADVERSARY,
            TaskPriority.HIGH,
        )
        verify_task.add_dependency(fix_task.id)
        verify_task.estimated_duration = 30
        verify_task.deliverable_requirements = [
            "verification_tests",
            "regression_report",
        ]
        tasks.append(verify_task)

        return tasks

    def _create_improvement_tasks(
        self, goal: str, prefix: str, analysis: Dict[str, Any]
    ) -> List[TaskSpec]:
        """Create tasks for improvement goals."""
        tasks = []

        # 1. Current State Analysis
        analyze_task = TaskSpec(
            f"{prefix}-analyze-{str(uuid.uuid4())[:8]}",
            "analysis",
            f"Analyze current state for improvement: {goal}",
            TaskRole.ADVERSARY,
            TaskPriority.MEDIUM,
        )
        analyze_task.estimated_duration = 30
        analyze_task.deliverable_requirements = [
            "current_state_analysis.md",
            "improvement_plan.md",
        ]
        tasks.append(analyze_task)

        # 2. Implementation
        improve_task = TaskSpec(
            f"{prefix}-improve-{str(uuid.uuid4())[:8]}",
            "improvement",
            f"Implement improvements: {goal}",
            TaskRole.CODER,
            TaskPriority.MEDIUM,
        )
        improve_task.add_dependency(analyze_task.id)
        improve_task.estimated_duration = 60
        improve_task.deliverable_requirements = [
            "improved_code",
            "improvement_documentation",
        ]
        tasks.append(improve_task)

        # 3. Performance Validation
        validate_task = TaskSpec(
            f"{prefix}-validate-{str(uuid.uuid4())[:8]}",
            "validation",
            f"Validate improvements and measure impact: {goal}",
            TaskRole.ADVERSARY,
            TaskPriority.MEDIUM,
        )
        validate_task.add_dependency(improve_task.id)
        validate_task.estimated_duration = 30
        validate_task.deliverable_requirements = [
            "performance_metrics",
            "validation_report",
        ]
        tasks.append(validate_task)

        return tasks

    def _create_testing_tasks(
        self, goal: str, prefix: str, analysis: Dict[str, Any]
    ) -> List[TaskSpec]:
        """Create tasks for testing goals."""
        tasks = []

        # 1. Test Planning
        plan_task = TaskSpec(
            f"{prefix}-plan-{str(uuid.uuid4())[:8]}",
            "test_planning",
            f"Plan testing strategy for: {goal}",
            TaskRole.ADVERSARY,
            TaskPriority.HIGH,
        )
        plan_task.estimated_duration = 20
        plan_task.deliverable_requirements = ["test_strategy.md", "test_cases.md"]
        tasks.append(plan_task)

        # 2. Test Implementation
        implement_task = TaskSpec(
            f"{prefix}-implement-tests-{str(uuid.uuid4())[:8]}",
            "test_implementation",
            f"Implement tests for: {goal}",
            TaskRole.ADVERSARY,
            TaskPriority.HIGH,
        )
        implement_task.add_dependency(plan_task.id)
        implement_task.estimated_duration = 60
        implement_task.deliverable_requirements = ["test_code", "test_data"]
        tasks.append(implement_task)

        # 3. Test Execution and Reporting
        execute_task = TaskSpec(
            f"{prefix}-execute-tests-{str(uuid.uuid4())[:8]}",
            "test_execution",
            f"Execute tests and generate reports for: {goal}",
            TaskRole.ADVERSARY,
            TaskPriority.MEDIUM,
        )
        execute_task.add_dependency(implement_task.id)
        execute_task.estimated_duration = 30
        execute_task.deliverable_requirements = ["test_results", "coverage_report"]
        tasks.append(execute_task)

        return tasks

    def _create_generic_tasks(
        self, goal: str, prefix: str, analysis: Dict[str, Any]
    ) -> List[TaskSpec]:
        """Create generic tasks for unclear goals."""
        tasks = []

        # 1. Goal Clarification
        clarify_task = TaskSpec(
            f"{prefix}-clarify-{str(uuid.uuid4())[:8]}",
            "clarification",
            f"Clarify and define specific requirements for: {goal}",
            TaskRole.CODER,
            TaskPriority.HIGH,
        )
        clarify_task.estimated_duration = 20
        clarify_task.deliverable_requirements = ["clarified_requirements.md"]
        tasks.append(clarify_task)

        # 2. Implementation
        implement_task = TaskSpec(
            f"{prefix}-implement-{str(uuid.uuid4())[:8]}",
            "implementation",
            f"Implement solution for: {goal}",
            TaskRole.CODER,
            TaskPriority.MEDIUM,
        )
        implement_task.add_dependency(clarify_task.id)
        implement_task.estimated_duration = 60
        implement_task.deliverable_requirements = ["solution", "documentation"]
        tasks.append(implement_task)

        # 3. Validation
        validate_task = TaskSpec(
            f"{prefix}-validate-{str(uuid.uuid4())[:8]}",
            "validation",
            f"Validate solution for: {goal}",
            TaskRole.ADVERSARY,
            TaskPriority.MEDIUM,
        )
        validate_task.add_dependency(implement_task.id)
        validate_task.estimated_duration = 30
        validate_task.deliverable_requirements = ["validation_report"]
        tasks.append(validate_task)

        return tasks


class TaskPlanner:
    """Intelligent task planner for APEX v2.0 Supervisor."""

    def __init__(self, memory_patterns: MemoryPatterns):
        """Initialize the TaskPlanner."""
        self.memory = memory_patterns
        self.logger = logging.getLogger(__name__)

        # Strategy registry
        self.strategies = {
            "software_development": SoftwareDevelopmentStrategy(),
            "default": SoftwareDevelopmentStrategy(),  # Default to software development
        }

    async def create_task_graph(
        self, project_id: str, goal: str, context: Dict[str, Any]
    ) -> TaskGraph:
        """Create a new task graph for a goal."""
        self.logger.info(f"Creating task graph for goal: {goal}")

        # Determine planning strategy
        strategy = self._select_strategy(goal, context)

        # Decompose goal into tasks
        tasks = strategy.decompose_goal(goal, context)

        # Create task graph
        graph = TaskGraph(goal)

        # Add tasks to graph
        for task in tasks:
            graph.add_task(task)

        # Store graph in LMDB
        await self._store_task_graph(project_id, graph)

        self.logger.info(f"Created task graph with {len(tasks)} tasks")
        return graph

    async def update_task_graph(
        self,
        project_id: str,
        goal: str,
        current_state: Dict[str, Any],
        completed_tasks: List[str],
        failed_tasks: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Update existing task graph based on current state."""
        try:
            # Load existing graph
            graph = await self._load_task_graph(project_id)

            if not graph:
                # Create new graph if none exists
                graph = await self.create_task_graph(project_id, goal, current_state)
                return graph.to_dict()

            # Check if we need to add more tasks based on current state
            completed_set = set(completed_tasks)
            ready_tasks = graph.get_ready_tasks(completed_set)

            # If no ready tasks and not all tasks completed, might need replanning
            if not ready_tasks and len(completed_tasks) < len(graph.tasks):
                self.logger.info("No ready tasks found, checking for replanning needs")

                # Check if failed tasks need alternatives
                for failed_task_id in failed_tasks:
                    if failed_task_id in graph.tasks:
                        await self._handle_failed_task_planning(graph, failed_task_id)

            # Check if goal has evolved and needs additional tasks
            if await self._should_add_tasks(graph, current_state):
                await self._add_adaptive_tasks(graph, current_state)

            # Update and store graph
            graph.updated_at = datetime.now().isoformat()
            await self._store_task_graph(project_id, graph)

            return graph.to_dict()

        except Exception as e:
            self.logger.error(f"Error updating task graph: {e}")
            return None

    async def get_task_dependencies(self, project_id: str, task_id: str) -> List[str]:
        """Get dependencies for a specific task."""
        graph = await self._load_task_graph(project_id)
        if graph and task_id in graph.tasks:
            return graph.tasks[task_id].dependencies
        return []

    async def validate_task_graph(self, project_id: str) -> Dict[str, Any]:
        """Validate task graph for consistency and issues."""
        graph = await self._load_task_graph(project_id)
        if not graph:
            return {"valid": False, "error": "No task graph found"}

        validation = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "statistics": {
                "total_tasks": len(graph.tasks),
                "tasks_with_dependencies": sum(
                    1 for t in graph.tasks.values() if t.dependencies
                ),
                "critical_path_length": len(graph.get_critical_path()),
                "estimated_total_duration": sum(
                    t.estimated_duration or 0 for t in graph.tasks.values()
                ),
            },
        }

        # Check for cycles (should not exist due to validation during creation)
        for task_id, task in graph.tasks.items():
            if self._has_circular_dependency(graph, task_id, set()):
                validation["issues"].append(
                    f"Circular dependency detected for task {task_id}"
                )
                validation["valid"] = False

        # Check for orphaned tasks
        all_dependencies = set()
        for task in graph.tasks.values():
            all_dependencies.update(task.dependencies)

        for dep in all_dependencies:
            if dep not in graph.tasks:
                validation["issues"].append(f"Missing dependency task: {dep}")
                validation["valid"] = False

        # Check for tasks with no path to completion
        start_tasks = [t for t in graph.tasks.values() if not t.dependencies]
        if not start_tasks:
            validation["warnings"].append(
                "No starting tasks found (all tasks have dependencies)"
            )

        return validation

    def _select_strategy(self, goal: str, context: Dict[str, Any]) -> PlanningStrategy:
        """Select appropriate planning strategy based on goal and context."""
        # For now, always use software development strategy
        # Could be enhanced with ML-based strategy selection
        return self.strategies["software_development"]

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
            graph.metadata = graph_data.get("metadata", {})

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
                task.blocks = task_data["blocks"]
                task.metadata = task_data["metadata"]
                task.estimated_duration = task_data["estimated_duration"]
                task.context_requirements = task_data["context_requirements"]
                task.deliverable_requirements = task_data["deliverable_requirements"]

                graph.add_task(task)

            return graph

        except Exception as e:
            self.logger.error(f"Error loading task graph: {e}")
            return None

    async def _handle_failed_task_planning(
        self, graph: TaskGraph, failed_task_id: str
    ) -> None:
        """Handle planning adjustments for failed tasks."""
        if failed_task_id not in graph.tasks:
            return

        failed_task = graph.tasks[failed_task_id]

        # Create alternative task with different approach
        alt_task_id = f"{failed_task_id}-alt-{str(uuid.uuid4())[:8]}"
        alt_task = TaskSpec(
            alt_task_id,
            f"alternative_{failed_task.type}",
            f"Alternative approach for: {failed_task.description}",
            failed_task.role,
            TaskPriority.HIGH,
        )

        # Copy dependencies and requirements
        alt_task.dependencies = failed_task.dependencies.copy()
        alt_task.context_requirements = failed_task.context_requirements.copy()
        alt_task.deliverable_requirements = failed_task.deliverable_requirements.copy()
        alt_task.estimated_duration = failed_task.estimated_duration

        # Add metadata indicating it's an alternative
        alt_task.metadata = {
            "alternative_for": failed_task_id,
            "approach": "alternative_implementation",
            "created_at": datetime.now().isoformat(),
        }

        graph.add_task(alt_task)

        # Update tasks that depended on the failed task
        for task in graph.tasks.values():
            if failed_task_id in task.dependencies:
                task.dependencies.remove(failed_task_id)
                task.add_dependency(alt_task_id)

    async def _should_add_tasks(
        self, graph: TaskGraph, current_state: Dict[str, Any]
    ) -> bool:
        """Determine if additional tasks should be added to the graph."""
        # Simple heuristic: add tasks if completion is high but goal not achieved
        completed_tasks = set(current_state.get("completed_tasks", []))
        completion_percentage = graph.get_completion_percentage(completed_tasks)

        # If 80% complete but goal not achieved, might need additional tasks
        return completion_percentage > 80.0

    async def _add_adaptive_tasks(
        self, graph: TaskGraph, current_state: Dict[str, Any]
    ) -> None:
        """Add adaptive tasks based on current state."""
        # Add cleanup/finalization tasks
        cleanup_task = TaskSpec(
            f"task-cleanup-{str(uuid.uuid4())[:8]}",
            "cleanup",
            "Final cleanup and validation",
            TaskRole.ADVERSARY,
            TaskPriority.LOW,
        )

        # Make cleanup depend on all current tasks
        for task_id in graph.tasks.keys():
            cleanup_task.add_dependency(task_id)

        cleanup_task.estimated_duration = 15
        cleanup_task.deliverable_requirements = ["final_validation_report"]

        graph.add_task(cleanup_task)

    def _has_circular_dependency(
        self, graph: TaskGraph, task_id: str, visited: Set[str]
    ) -> bool:
        """Check for circular dependencies starting from a task."""
        if task_id in visited:
            return True

        if task_id not in graph.tasks:
            return False

        visited.add(task_id)

        for dep in graph.tasks[task_id].dependencies:
            if self._has_circular_dependency(graph, dep, visited.copy()):
                return True

        return False
