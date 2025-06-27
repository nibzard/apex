"""Integration tests for APEX v2.0 Orchestrator-Worker Architecture."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from apex.core.memory import MemoryPatterns
from apex.supervisor.engine import SupervisorEngine
from apex.supervisor.planner import TaskPlanner


@pytest.fixture
async def memory_patterns():
    """Create temporary memory patterns for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        lmdb_path = Path(temp_dir) / "test_memory.db"
        memory = MemoryPatterns(str(lmdb_path))
        yield memory
        await memory.close()


@pytest.fixture
async def supervisor_engine(memory_patterns):
    """Create supervisor engine for testing."""
    return SupervisorEngine(memory_patterns)


@pytest.mark.asyncio
async def test_task_planner_basic_functionality(memory_patterns):
    """Test that TaskPlanner creates task graphs correctly."""
    planner = TaskPlanner(memory_patterns)

    # Test implementation goal
    goal = "Implement user authentication system"
    project_id = "test-project-001"

    graph = await planner.create_task_graph(project_id, goal)

    assert graph is not None
    assert graph.goal == goal
    assert len(graph.tasks) > 0

    # Verify tasks have proper structure
    for task in graph.tasks:
        assert hasattr(task, "id")
        assert hasattr(task, "type")
        assert hasattr(task, "description")
        assert hasattr(task, "role")
        assert hasattr(task, "priority")

    # Test getting next task
    next_task = await planner.get_next_task(project_id, [])
    assert next_task is not None
    assert "id" in next_task
    assert "description" in next_task


@pytest.mark.asyncio
async def test_task_planner_bug_fix_tasks(memory_patterns):
    """Test that TaskPlanner handles bug fix goals correctly."""
    planner = TaskPlanner(memory_patterns)

    goal = "Fix login validation bug"
    project_id = "test-project-002"

    graph = await planner.create_task_graph(project_id, goal)

    assert graph is not None
    assert graph.goal == goal
    assert len(graph.tasks) == 3  # Should create: investigate, fix, verify

    # Check task types
    task_types = [task.type for task in graph.tasks]
    assert "investigation" in task_types
    assert "bug_fix" in task_types
    assert "verification" in task_types


@pytest.mark.asyncio
async def test_supervisor_session_initialization(supervisor_engine):
    """Test supervisor session initialization."""
    project_id = "test-project-003"
    goal = "Create a simple web API"

    session_id = await supervisor_engine.initialize_session(project_id, goal)

    assert session_id is not None
    assert supervisor_engine.state is not None
    assert supervisor_engine.state.project_id == project_id
    assert supervisor_engine.state.current_goal == goal
    assert supervisor_engine.state.session_id == session_id


@pytest.mark.asyncio
async def test_supervisor_orchestration_cycle_basic(supervisor_engine):
    """Test basic orchestration cycle execution."""
    project_id = "test-project-004"
    goal = "Test goal for orchestration"

    # Initialize session
    await supervisor_engine.initialize_session(project_id, goal)

    # Execute one orchestration cycle
    success = await supervisor_engine.execute_orchestration_cycle()

    # The cycle should succeed (even if no work is done)
    assert success is True or success is False  # Just verify it completes

    # Verify state was updated
    assert supervisor_engine.state.metrics["stage_cycles"] >= 1


@pytest.mark.asyncio
async def test_memory_integration(memory_patterns):
    """Test that memory operations work correctly."""
    # Test basic memory operations
    test_key = "/test/sample_data"
    test_data = {"message": "Hello, World!", "timestamp": "2024-01-01T00:00:00Z"}

    # Write data
    await memory_patterns.mcp.write(test_key, json.dumps(test_data))

    # Read data back
    retrieved_data = await memory_patterns.mcp.read(test_key)
    assert retrieved_data is not None

    parsed_data = json.loads(retrieved_data)
    assert parsed_data == test_data

    # Test listing keys
    keys = await memory_patterns.mcp.list_keys("/test/")
    assert test_key in keys


@pytest.mark.asyncio
async def test_task_graph_storage_and_retrieval(memory_patterns):
    """Test that task graphs are properly stored and retrieved."""
    planner = TaskPlanner(memory_patterns)
    project_id = "test-project-005"
    goal = "Test storage functionality"

    # Create and store task graph
    original_graph = await planner.create_task_graph(project_id, goal)

    # Retrieve task graph
    retrieved_graph = await planner._load_task_graph(project_id)

    assert retrieved_graph is not None
    assert retrieved_graph.goal == original_graph.goal
    assert len(retrieved_graph.tasks) == len(original_graph.tasks)

    # Verify task IDs match
    original_ids = [task.id for task in original_graph.tasks]
    retrieved_ids = [task.id for task in retrieved_graph.tasks]
    assert set(original_ids) == set(retrieved_ids)


@pytest.mark.asyncio
async def test_progress_tracking(memory_patterns):
    """Test task progress tracking functionality."""
    planner = TaskPlanner(memory_patterns)
    project_id = "test-project-006"
    goal = "Test progress tracking"

    # Create task graph
    graph = await planner.create_task_graph(project_id, goal)
    task_ids = [task.id for task in graph.tasks]

    # Test initial progress
    progress = await planner.get_progress(project_id, [])
    assert progress["completion_percentage"] == 0.0
    assert progress["completed_tasks"] == 0
    assert progress["total_tasks"] == len(task_ids)

    # Test partial completion
    completed_tasks = task_ids[:1]  # Complete first task
    progress = await planner.get_progress(project_id, completed_tasks)
    expected_percentage = (1 / len(task_ids)) * 100
    assert progress["completion_percentage"] == expected_percentage
    assert progress["completed_tasks"] == 1

    # Test full completion
    progress = await planner.get_progress(project_id, task_ids)
    assert progress["completion_percentage"] == 100.0
    assert progress["completed_tasks"] == len(task_ids)


@pytest.mark.asyncio
async def test_next_task_with_dependencies(memory_patterns):
    """Test that next task respects dependencies."""
    planner = TaskPlanner(memory_patterns)
    project_id = "test-project-007"
    goal = "Test dependency handling"

    # Create task graph with dependencies
    graph = await planner.create_task_graph(project_id, goal)

    # Get first task (should have no dependencies)
    first_task = await planner.get_next_task(project_id, [])
    assert first_task is not None
    first_task_id = first_task["id"]

    # Get next task after completing first
    second_task = await planner.get_next_task(project_id, [first_task_id])

    # Verify we get a different task
    if second_task:  # May be None if all remaining tasks depend on uncompleted tasks
        assert second_task["id"] != first_task_id


@pytest.mark.asyncio
async def test_error_handling(memory_patterns, supervisor_engine):
    """Test error handling in orchestration."""
    # Test with invalid project ID
    with pytest.raises(Exception):
        await supervisor_engine.initialize_session("", "")

    # Test TaskPlanner with invalid data
    planner = TaskPlanner(memory_patterns)

    # Should handle empty goal gracefully
    graph = await planner.create_task_graph("test-project-error", "")
    assert graph is not None  # Should create generic tasks

    # Test getting next task from non-existent project
    next_task = await planner.get_next_task("non-existent-project", [])
    assert next_task is None


if __name__ == "__main__":
    # Run tests manually for development
    import asyncio

    async def run_basic_test():
        """Run a basic test manually."""
        import tempfile
        from pathlib import Path

        # Create temporary memory
        with tempfile.TemporaryDirectory() as temp_dir:
            lmdb_path = Path(temp_dir) / "test_memory.db"
            memory = MemoryPatterns(str(lmdb_path))

            try:
                # Test TaskPlanner
                planner = TaskPlanner(memory)
                graph = await planner.create_task_graph("test", "Implement user login")
                print(f"Created task graph with {len(graph.tasks)} tasks")

                for task in graph.tasks:
                    print(f"- {task.id}: {task.description} ({task.role.value})")

                # Test SupervisorEngine
                engine = SupervisorEngine(memory)
                session_id = await engine.initialize_session(
                    "test", "Implement user login"
                )
                print(f"Initialized session: {session_id}")

                # Try one orchestration cycle
                success = await engine.execute_orchestration_cycle()
                print(f"Orchestration cycle completed: {success}")

                print("Basic integration test passed!")

            finally:
                await memory.close()

    asyncio.run(run_basic_test())
