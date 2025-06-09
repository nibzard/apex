"""Tests for memory management patterns."""

import json
from unittest.mock import MagicMock

import pytest

from apex.core.memory import MemoryPatterns, MemorySnapshot
from apex.types import AgentType


@pytest.fixture
def mock_mcp():
    """Create a mock LMDB MCP instance."""
    mcp = MagicMock()
    mcp.read = MagicMock()
    mcp.write = MagicMock()
    mcp.delete = MagicMock()
    mcp.list_keys = MagicMock()
    return mcp


@pytest.fixture
def memory_patterns(mock_mcp):
    """Create MemoryPatterns instance with mock MCP."""
    return MemoryPatterns(mock_mcp)


@pytest.fixture
def memory_snapshot(mock_mcp):
    """Create MemorySnapshot instance with mock MCP."""
    return MemorySnapshot(mock_mcp)


class TestMemoryPatterns:
    """Test memory access patterns."""

    @pytest.mark.asyncio
    async def test_create_project(self, memory_patterns, mock_mcp):
        """Test project creation."""
        project_id = "test-project"
        project_data = {"name": "Test Project", "description": "A test project"}

        # Mock successful writes
        mock_mcp.write.return_value = None

        result = await memory_patterns.create_project(project_id, project_data)

        assert result is True
        # Verify project config was written (through adapter)
        mock_mcp.write.assert_any_call(
            f"/projects/{project_id}/config", json.dumps(project_data).encode()
        )

    @pytest.mark.asyncio
    async def test_create_task(self, memory_patterns, mock_mcp):
        """Test task creation."""
        project_id = "test-project"
        task_data = {"description": "Implement feature X", "priority": "high"}

        mock_mcp.write.return_value = None

        task_id = await memory_patterns.create_task(project_id, task_data)

        assert task_id is not None
        assert len(task_id) > 0

        # Verify task was written to pending
        pending_calls = [
            call
            for call in mock_mcp.write.call_args_list
            if call[0][0].endswith(f"/pending/{task_id}")
        ]
        assert len(pending_calls) == 1

    @pytest.mark.asyncio
    async def test_complete_task(self, memory_patterns, mock_mcp):
        """Test task completion."""
        project_id = "test-project"
        task_id = "test-task"

        # Mock task data
        task_data = {
            "id": task_id,
            "description": "Test task",
            "status": "pending",
            "assigned_to": "coder",
            "priority": "medium",
        }

        mock_mcp.read.return_value = json.dumps(task_data).encode()
        mock_mcp.write.return_value = None
        mock_mcp.delete.return_value = None

        result = await memory_patterns.complete_task(project_id, task_id)

        assert result is True
        # Verify task was moved to completed
        completed_calls = [
            call for call in mock_mcp.write.call_args_list if "completed" in call[0][0]
        ]
        assert len(completed_calls) >= 1

    @pytest.mark.asyncio
    async def test_get_pending_tasks(self, memory_patterns, mock_mcp):
        """Test getting pending tasks."""
        project_id = "test-project"

        # Mock pending task keys
        mock_mcp.list_keys.return_value = [
            f"/projects/{project_id}/memory/tasks/pending/task1",
            f"/projects/{project_id}/memory/tasks/pending/task2",
        ]

        # Mock task data
        task1 = {"id": "task1", "priority": "high", "assigned_to": "coder"}
        task2 = {"id": "task2", "priority": "medium", "assigned_to": "coder"}

        mock_mcp.read.side_effect = [
            json.dumps(task1).encode(),
            json.dumps(task2).encode(),
        ]

        tasks = await memory_patterns.get_pending_tasks(project_id)

        assert len(tasks) == 2
        # High priority task should be first
        assert tasks[0]["priority"] == "high"
        assert tasks[1]["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_store_code(self, memory_patterns, mock_mcp):
        """Test storing code files."""
        project_id = "test-project"
        file_path = "src/main.py"
        content = "print('hello world')"
        task_id = "test-task"

        mock_mcp.write.return_value = None

        result = await memory_patterns.store_code(
            project_id, file_path, content, task_id
        )

        assert result is True

        # Verify code was written
        code_calls = [
            call
            for call in mock_mcp.write.call_args_list
            if "memory/code/" in call[0][0] and "index" not in call[0][0]
        ]
        assert len(code_calls) == 1

    @pytest.mark.asyncio
    async def test_report_issue(self, memory_patterns, mock_mcp):
        """Test reporting issues."""
        project_id = "test-project"
        issue_data = {
            "type": "security",
            "file": "src/auth.py",
            "line": 42,
            "description": "SQL injection vulnerability",
        }
        severity = "critical"

        mock_mcp.write.return_value = None
        mock_mcp.read.return_value = json.dumps(0).encode()  # Initial count

        issue_id = await memory_patterns.report_issue(project_id, issue_data, severity)

        assert issue_id is not None

        # Verify issue was written
        issue_calls = [
            call
            for call in mock_mcp.write.call_args_list
            if f"issues/{severity}" in call[0][0] and issue_id in call[0][0]
        ]
        assert len(issue_calls) == 1

    @pytest.mark.asyncio
    async def test_update_agent_status(self, memory_patterns, mock_mcp):
        """Test updating agent status."""
        project_id = "test-project"
        agent_type = AgentType.CODER
        status_data = {"status": "coding", "current_task": "Implement authentication"}

        mock_mcp.write.return_value = None

        result = await memory_patterns.update_agent_status(
            project_id, agent_type, status_data
        )

        assert result is True

        # Verify status was written
        status_calls = [
            call
            for call in mock_mcp.write.call_args_list
            if f"agents/{agent_type.value}/status" in call[0][0]
        ]
        assert len(status_calls) == 1


class TestMemorySnapshot:
    """Test memory snapshot functionality."""

    @pytest.mark.asyncio
    async def test_create_snapshot(self, memory_snapshot, mock_mcp):
        """Test creating a memory snapshot."""
        project_id = "test-project"

        # Mock project keys and data
        mock_mcp.list_keys.return_value = [
            f"/projects/{project_id}/config",
            f"/projects/{project_id}/memory/tasks/pending/task1",
        ]

        mock_mcp.read.side_effect = [
            json.dumps({"name": "Test Project"}).encode(),
            json.dumps({"id": "task1", "description": "Test task"}).encode(),
        ]

        mock_mcp.write.return_value = None

        snapshot_id = await memory_snapshot.create_snapshot(project_id)

        assert snapshot_id is not None

        # Verify snapshot was written
        snapshot_calls = [
            call
            for call in mock_mcp.write.call_args_list
            if f"/snapshots/{snapshot_id}" in call[0][0]
        ]
        assert len(snapshot_calls) == 1

    @pytest.mark.asyncio
    async def test_restore_snapshot(self, memory_snapshot, mock_mcp):
        """Test restoring from a snapshot."""
        snapshot_id = "test-snapshot"

        # Mock snapshot data
        snapshot_data = {
            "id": snapshot_id,
            "project_id": "test-project",
            "keys": {
                "/projects/test-project/config": json.dumps({"name": "Test"}),
                "/projects/test-project/memory/tasks/pending/task1": json.dumps(
                    {"id": "task1"}
                ),
            },
        }

        mock_mcp.read.return_value = json.dumps(snapshot_data).encode()
        mock_mcp.write.return_value = None

        result = await memory_snapshot.restore_snapshot(snapshot_id)

        assert result is True

        # Verify all keys were restored
        restore_calls = [
            call
            for call in mock_mcp.write.call_args_list
            if call[0][0].startswith("/projects/test-project/")
        ]
        assert len(restore_calls) == 2

    @pytest.mark.asyncio
    async def test_list_snapshots(self, memory_snapshot, mock_mcp):
        """Test listing snapshots."""
        project_id = "test-project"

        # Mock snapshot keys
        mock_mcp.list_keys.return_value = [
            "/snapshots/snapshot1",
            "/snapshots/snapshot2",
        ]

        # Mock snapshot data
        snapshot1 = {
            "id": "snapshot1",
            "project_id": project_id,
            "created_at": "2024-01-01T00:00:00",
            "keys": {"key1": "value1"},
        }
        snapshot2 = {
            "id": "snapshot2",
            "project_id": "other-project",
            "created_at": "2024-01-02T00:00:00",
            "keys": {"key2": "value2"},
        }

        mock_mcp.read.side_effect = [
            json.dumps(snapshot1).encode(),
            json.dumps(snapshot2).encode(),
        ]

        snapshots = await memory_snapshot.list_snapshots(project_id)

        # Should only return snapshots for the specified project
        assert len(snapshots) == 1
        assert snapshots[0]["id"] == "snapshot1"
        assert snapshots[0]["project_id"] == project_id
        assert "key_count" in snapshots[0]

    @pytest.mark.asyncio
    async def test_delete_snapshot(self, memory_snapshot, mock_mcp):
        """Test deleting a snapshot."""
        snapshot_id = "test-snapshot"

        mock_mcp.delete.return_value = None

        result = await memory_snapshot.delete_snapshot(snapshot_id)

        assert result is True
        mock_mcp.delete.assert_called_once_with(f"/snapshots/{snapshot_id}")
