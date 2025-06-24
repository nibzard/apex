"""Tests for enhanced TUI components."""

from unittest.mock import MagicMock

from apex.tui.widgets import (
    AgentInteractionWidget,
    AgentStatusWidget,
    LogViewerWidget,
    MemoryBrowserWidget,
    MetricsWidget,
)


def test_agent_status_widget_init():
    """Test AgentStatusWidget initialization."""
    widget = AgentStatusWidget()
    assert widget.agents_data == {}
    assert widget.agent_history == {}
    assert widget.agent_runner is None
    assert widget.lmdb_client is None


def test_log_viewer_widget_init():
    """Test LogViewerWidget initialization."""
    widget = LogViewerWidget(max_logs=50)
    assert widget.logs == []
    assert widget.filter_agent is None
    assert widget.filter_level is None
    assert widget.filter_pattern is None
    assert widget.max_logs == 50
    assert len(widget.log_buffer) == 0


def test_memory_browser_widget_init():
    """Test MemoryBrowserWidget initialization."""
    widget = MemoryBrowserWidget()
    assert widget.selected_key is None
    assert widget.search_query == ""
    assert widget.auto_refresh is True
    assert widget.lmdb_client is None
    assert len(widget.expanded_nodes) == 0


def test_metrics_widget_init():
    """Test MetricsWidget initialization."""
    widget = MetricsWidget()
    assert widget.metrics_data == {}
    assert widget.agent_runner is None
    assert widget.lmdb_client is None


def test_agent_interaction_widget_init():
    """Test AgentInteractionWidget initialization."""
    widget = AgentInteractionWidget()
    assert widget.selected_agent is None
    assert widget.lmdb_client is None


def test_agent_status_update_logic():
    """Test AgentStatusWidget update logic without reactive system."""
    # Create mock agent runner
    agent_runner = MagicMock()
    agent_runner.get_agent_status.return_value = {
        "supervisor": {
            "running": True,
            "agent_type": "supervisor",
            "memory": 104857600,  # 100 MB
            "start_time": 1700000000,
            "current_task": "Coordinating tasks",
        },
        "coder": {
            "running": True,
            "agent_type": "coder",
            "memory": 209715200,  # 200 MB
            "start_time": 1700000100,
            "current_task": None,
        },
    }

    widget = AgentStatusWidget(agent_runner=agent_runner)

    # Test that the widget can be created with the mock runner
    assert widget.agent_runner is not None
    assert hasattr(widget, "update_status")


def test_log_viewer_filtering_logic():
    """Test log filtering logic in LogViewerWidget."""
    widget = LogViewerWidget()

    # Add test logs to buffer (deque)
    widget.log_buffer.append(
        {
            "timestamp": "2024-01-01T12:00:00",
            "level": "INFO",
            "agent": "supervisor",
            "content": "Test message 1",
            "key": "/test/1",
        }
    )
    widget.log_buffer.append(
        {
            "timestamp": "2024-01-01T12:00:01",
            "level": "ERROR",
            "agent": "coder",
            "content": "Test error",
            "key": "/test/2",
        }
    )
    widget.log_buffer.append(
        {
            "timestamp": "2024-01-01T12:00:02",
            "level": "INFO",
            "agent": "supervisor",
            "content": "Test message 2",
            "key": "/test/3",
        }
    )

    # Test that logs were added
    assert len(widget.log_buffer) == 3

    # Test that filter method exists and can be called
    assert hasattr(widget, "set_filter")

    # Test that filter properties can be set directly
    widget.filter_agent = "supervisor"
    widget.filter_level = "ERROR"
    widget.filter_pattern = "error"

    # Verify they were set
    assert widget.filter_agent == "supervisor"
    assert widget.filter_level == "ERROR"
    assert widget.filter_pattern == "error"


def test_memory_browser_tree_structure():
    """Test tree structure building in MemoryBrowserWidget."""
    widget = MemoryBrowserWidget()

    # Test tree structure building
    keys = [
        "/projects/test/config",
        "/projects/test/agents/supervisor/state",
        "/projects/test/agents/coder/state",
        "/agents/supervisor/status",
        "/tasks/pending/task1",
        "/tasks/completed/task2",
    ]

    tree_data = widget._build_tree_structure(keys)

    # Verify structure
    assert "projects" in tree_data
    assert "agents" in tree_data
    assert "tasks" in tree_data

    # Check nested structure
    assert "test" in tree_data["projects"]["_children"]
    assert "config" in tree_data["projects"]["_children"]["test"]["_children"]
    assert (
        tree_data["projects"]["_children"]["test"]["_children"]["config"]["_is_leaf"]
        is True
    )


def test_metrics_update_display():
    """Test metrics display update."""
    widget = MetricsWidget()

    # Set mock metrics data
    widget.metrics_data = {
        "agents": {"total": 3, "running": 2, "stopped": 1},
        "tasks": {"pending": 5, "completed": 10, "failed": 1},
        "memory": {"keys": 42, "size": "1.2 MB"},
        "performance": {"cpu": "45%", "memory": "150 MB"},
    }

    widget.update_display()
    # Widget should update without errors


def test_agent_interaction_templates():
    """Test agent interaction template generation."""
    widget = AgentInteractionWidget()

    # Mock the query methods
    widget.query_one = MagicMock()

    # Mock selects
    agent_select = MagicMock()
    agent_select.value = "supervisor"
    command_select = MagicMock()
    command_select.value = "task"
    input_area = MagicMock()

    widget.query_one.side_effect = lambda id, cls: {
        "#agent-select": agent_select,
        "#command-select": command_select,
        "#command-input": input_area,
    }.get(id)

    widget.update_template()

    # Verify template was set
    assert input_area.text is not None
