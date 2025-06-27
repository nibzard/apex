#!/usr/bin/env python3
"""APEX v2.0 Simple Entry Point

A standalone entry point that avoids complex import dependencies.
This demonstrates the simplified Orchestrator-Worker architecture.
"""

import logging
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("apex")

try:
    import typer
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Warning: typer/rich not available, using basic interface")


# Simple implementation for demonstration
class SimpleTaskSpec:
    """Simple task specification."""

    def __init__(self, task_id: str, task_type: str, description: str, role: str):
        self.id = task_id
        self.type = task_type
        self.description = description
        self.role = role
        self.dependencies = []
        self.estimated_duration = 60

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "role": self.role,
            "dependencies": self.dependencies,
            "estimated_duration": self.estimated_duration,
        }


class SimpleTaskGraph:
    """Simple task graph for demonstration."""

    def __init__(self, goal: str):
        self.goal = goal
        self.tasks = []
        self.created_at = datetime.now().isoformat()

    def add_task(self, task: SimpleTaskSpec):
        self.tasks.append(task)

    def get_next_task(self, completed_task_ids: List[str]) -> Optional[SimpleTaskSpec]:
        for task in self.tasks:
            if task.id in completed_task_ids:
                continue
            if all(dep in completed_task_ids for dep in task.dependencies):
                return task
        return None

    def to_dict(self):
        return {
            "goal": self.goal,
            "created_at": self.created_at,
            "tasks": [task.to_dict() for task in self.tasks],
        }


class SimpleTaskPlanner:
    """Simple task planner for demonstration."""

    def create_implementation_tasks(self, goal: str) -> List[SimpleTaskSpec]:
        """Create implementation task sequence."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        tasks = []

        # Research task
        research_task = SimpleTaskSpec(
            f"task-{timestamp}-research",
            "research",
            f"Research and plan approach for: {goal}",
            "Coder",
        )
        tasks.append(research_task)

        # Implementation task
        impl_task = SimpleTaskSpec(
            f"task-{timestamp}-implement",
            "implementation",
            f"Implement core functionality: {goal}",
            "Coder",
        )
        impl_task.dependencies.append(research_task.id)
        tasks.append(impl_task)

        # Testing task
        test_task = SimpleTaskSpec(
            f"task-{timestamp}-test",
            "testing",
            f"Test and validate implementation: {goal}",
            "Adversary",
        )
        test_task.dependencies.append(impl_task.id)
        tasks.append(test_task)

        return tasks

    def create_bug_fix_tasks(self, goal: str) -> List[SimpleTaskSpec]:
        """Create bug fix task sequence."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        tasks = []

        # Investigation task
        investigate_task = SimpleTaskSpec(
            f"task-{timestamp}-investigate",
            "investigation",
            f"Investigate and reproduce: {goal}",
            "Adversary",
        )
        tasks.append(investigate_task)

        # Fix task
        fix_task = SimpleTaskSpec(
            f"task-{timestamp}-fix", "bug_fix", f"Implement fix for: {goal}", "Coder"
        )
        fix_task.dependencies.append(investigate_task.id)
        tasks.append(fix_task)

        # Verification task
        verify_task = SimpleTaskSpec(
            f"task-{timestamp}-verify",
            "verification",
            f"Verify fix and test for regressions: {goal}",
            "Adversary",
        )
        verify_task.dependencies.append(fix_task.id)
        tasks.append(verify_task)

        return tasks

    def create_task_graph(self, goal: str) -> SimpleTaskGraph:
        """Create task graph for a goal."""
        goal_lower = goal.lower()

        if any(word in goal_lower for word in ["fix", "bug", "error", "issue"]):
            tasks = self.create_bug_fix_tasks(goal)
        elif any(
            word in goal_lower for word in ["implement", "add", "create", "build"]
        ):
            tasks = self.create_implementation_tasks(goal)
        else:
            # Generic tasks
            tasks = self.create_implementation_tasks(goal)

        graph = SimpleTaskGraph(goal)
        for task in tasks:
            graph.add_task(task)

        return graph


class SimpleOrchestrator:
    """Simple orchestrator for demonstration."""

    def __init__(self):
        self.planner = SimpleTaskPlanner()
        self.project_id = None
        self.goal = None
        self.task_graph = None
        self.completed_tasks = []
        self.session_id = None

    def initialize_session(self, project_id: str, goal: str) -> str:
        """Initialize orchestration session."""
        self.project_id = project_id
        self.goal = goal
        self.session_id = str(uuid.uuid4())

        logger.info(f"Initialized session {self.session_id} for project {project_id}")
        logger.info(f"Goal: {goal}")

        return self.session_id

    def plan_tasks(self) -> SimpleTaskGraph:
        """Plan tasks for the goal."""
        logger.info("Planning tasks...")

        self.task_graph = self.planner.create_task_graph(self.goal)

        logger.info(f"Created task graph with {len(self.task_graph.tasks)} tasks:")
        for i, task in enumerate(self.task_graph.tasks, 1):
            deps_str = (
                f" (depends on: {', '.join(task.dependencies)})"
                if task.dependencies
                else ""
            )
            logger.info(f"  {i}. {task.id}: {task.description}{deps_str}")

        return self.task_graph

    def get_next_task(self) -> Optional[SimpleTaskSpec]:
        """Get the next task to execute."""
        if not self.task_graph:
            return None

        return self.task_graph.get_next_task(self.completed_tasks)

    def execute_task(self, task: SimpleTaskSpec) -> bool:
        """Simulate task execution."""
        logger.info(f"Executing task: {task.id}")
        logger.info(f"  Description: {task.description}")
        logger.info(f"  Role: {task.role}")
        logger.info(f"  Type: {task.type}")

        # Simulate work
        import time

        time.sleep(1)  # Simulate task execution time

        # Mark as completed
        self.completed_tasks.append(task.id)
        logger.info(f"Task {task.id} completed successfully")

        return True

    def orchestrate(self) -> Dict[str, Any]:
        """Run the complete orchestration."""
        if not self.goal:
            raise ValueError("No goal set. Call initialize_session first.")

        # Plan tasks
        self.plan_tasks()

        # Execute tasks in order
        logger.info("Starting task execution...")

        max_iterations = 10  # Safety limit
        iteration = 0

        while iteration < max_iterations:
            next_task = self.get_next_task()

            if not next_task:
                logger.info("No more tasks to execute")
                break

            success = self.execute_task(next_task)

            if not success:
                logger.error(f"Task {next_task.id} failed")
                break

            iteration += 1

        completion_percentage = (
            len(self.completed_tasks) / len(self.task_graph.tasks)
        ) * 100

        logger.info(
            f"Orchestration completed: {len(self.completed_tasks)}/{len(self.task_graph.tasks)} tasks ({completion_percentage:.1f}%)"
        )

        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "goal": self.goal,
            "total_tasks": len(self.task_graph.tasks),
            "completed_tasks": len(self.completed_tasks),
            "completion_percentage": completion_percentage,
            "task_list": [task.to_dict() for task in self.task_graph.tasks],
        }


def demonstrate_orchestration():
    """Demonstrate the orchestration system."""
    print("APEX v2.0 Simple Orchestration Demonstration")
    print("=" * 50)

    # Create orchestrator
    orchestrator = SimpleOrchestrator()

    # Test different types of goals
    test_goals = [
        "Implement user authentication system",
        "Fix login validation bug",
        "Create REST API for user management",
    ]

    for i, goal in enumerate(test_goals, 1):
        print(f"\n--- Test {i}: {goal} ---")

        # Initialize session
        project_id = f"demo-project-{i:03d}"
        session_id = orchestrator.initialize_session(project_id, goal)

        # Run orchestration
        result = orchestrator.orchestrate()

        print(f"Result: {result['completion_percentage']:.1f}% complete")
        print(f"Completed {result['completed_tasks']}/{result['total_tasks']} tasks")


def interactive_mode():
    """Run in interactive mode."""
    print("APEX v2.0 Interactive Mode")
    print("=" * 30)

    orchestrator = SimpleOrchestrator()

    while True:
        try:
            goal = input("\nEnter your goal (or 'quit' to exit): ").strip()

            if goal.lower() in ["quit", "exit", "q"]:
                break

            if not goal:
                continue

            project_id = f"interactive-{uuid.uuid4().hex[:8]}"
            orchestrator.initialize_session(project_id, goal)

            result = orchestrator.orchestrate()

            print("\nOrchestration Summary:")
            print(f"  Project ID: {result['project_id']}")
            print(f"  Goal: {result['goal']}")
            print(
                f"  Progress: {result['completed_tasks']}/{result['total_tasks']} tasks ({result['completion_percentage']:.1f}%)"
            )
            print("  Tasks created:")
            for task in result["task_list"]:
                status = "✓" if task["id"] in orchestrator.completed_tasks else "○"
                deps = (
                    f" (deps: {', '.join(task['dependencies'])})"
                    if task["dependencies"]
                    else ""
                )
                print(f"    {status} {task['id']}: {task['description']}{deps}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "demo":
            demonstrate_orchestration()
        elif command == "interactive":
            interactive_mode()
        elif command == "test":
            # Run a quick test
            orchestrator = SimpleOrchestrator()
            orchestrator.initialize_session("test-001", "Test the orchestration system")
            result = orchestrator.orchestrate()
            print(f"Test completed: {result['completion_percentage']:.1f}% success")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: demo, interactive, test")
    else:
        print("APEX v2.0 Simple Orchestrator")
        print("Usage:")
        print("  python apex_simple.py demo        - Run demonstration")
        print("  python apex_simple.py interactive - Interactive mode")
        print("  python apex_simple.py test        - Quick test")


if __name__ == "__main__":
    main()
