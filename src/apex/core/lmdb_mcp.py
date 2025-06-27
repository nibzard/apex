"""LMDB MCP integration for APEX with plugin support.

This module provides APEX-specific database functionality using the plugin-based
lmdb-mcp package. It maintains backward compatibility while adding new capabilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from lmdb_mcp import AgentDatabase, LMDBWithPlugins

# Import from the external lmdb-mcp package
from lmdb_mcp.core import LMDBMCP as _CoreLMDBMCP

if TYPE_CHECKING:
    from lmdb_mcp.plugins.base import LMDBPlugin


class LMDBMCP:
    """APEX-compatible wrapper around the external LMDB-MCP package.

    This maintains backward compatibility with existing APEX code while
    using the extracted LMDB-MCP package. For new code, consider using
    AgentDatabase or LMDBWithPlugins directly.
    """

    def __init__(self, path: Path, map_size: int = 1_048_576) -> None:
        """Initialize LMDB-based MCP server.

        Args:
            path: Path to LMDB database directory
            map_size: Maximum size database may grow to; used to size the memory mapping

        """
        self._lmdb = _CoreLMDBMCP(path, map_size)

    def read(self, key: str) -> Optional[bytes]:
        """Read value for key."""
        return self._lmdb.read(key)

    def write(self, key: str, value: bytes) -> None:
        """Write value for key."""
        self._lmdb.write(key, value)

    def list_keys(self, prefix: str = "") -> List[str]:
        """List keys starting with prefix."""
        return self._lmdb.list_keys(prefix)

    def delete(self, key: str) -> bool:
        """Delete a key."""
        return self._lmdb.delete(key)

    def cursor_scan(
        self, start: str = "", end: str = "", limit: int = 100
    ) -> List[Tuple[str, bytes]]:
        """Scan a range of keys using cursor.

        Args:
            start: Start key for range (inclusive)
            end: End key for range (inclusive)
            limit: Maximum number of entries to return

        Returns:
            List of (key, value) tuples

        """
        return self._lmdb.cursor_scan(start, end, limit)

    def stat(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database statistics

        """
        return self._lmdb.stat()

    def close(self) -> None:
        """Close environment."""
        self._lmdb.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class APEXDatabase:
    """APEX-optimized database with plugin support.

    This class provides APEX-specific database functionality using the
    plugin architecture. It's designed for APEX's multi-agent orchestration
    patterns and provides higher-level abstractions for common operations.
    """

    def __init__(
        self,
        workspace_path: Path,
        project_id: str,
        map_size: int = 104_857_600,  # 100MB default for APEX
    ):
        """Initialize APEX database.

        Args:
            workspace_path: Path to the database
            project_id: Unique project identifier
            map_size: Maximum database size

        """
        self.project_id = project_id
        self.workspace_path = workspace_path

        # Create plugin-enabled database optimized for coding agents
        self._db = AgentDatabase(
            workspace_path=workspace_path,
            agent_type="coding",  # APEX is primarily for coding
            estimated_size=map_size,
            custom_plugins=[],  # Start with defaults, can be extended
            custom_config={
                "memory_patterns": {
                    "default_namespace": f"projects/{project_id}",
                    "auto_timestamp": True,
                }
            },
        )

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database and plugins."""
        if not self._initialized:
            await self._db.initialize_plugins()

            # Create APEX-specific namespace structure
            await self._setup_apex_namespaces()
            self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown database."""
        if self._initialized:
            await self._db.shutdown()
            self._initialized = False

    async def _setup_apex_namespaces(self) -> None:
        """Setup APEX-specific namespace structure."""
        base_namespace = f"projects/{self.project_id}"

        # Create the main project namespace
        await self._db.create_namespace(base_namespace)

        # Setup collections for APEX entities
        memory_plugin = self._db.get_plugin("memory_patterns")
        if memory_plugin:
            # Tasks collection
            await memory_plugin.create_collection(
                base_namespace,
                "tasks",
                {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "description": {"type": "string"},
                        "assigned_to": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "failed"],
                        },
                        "depends_on": {"type": "array", "items": {"type": "string"}},
                        "metadata": {"type": "object"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                    },
                    "required": [
                        "id",
                        "description",
                        "assigned_to",
                        "priority",
                        "status",
                    ],
                },
            )

            # Agents collection
            await memory_plugin.create_collection(
                base_namespace,
                "agents",
                {
                    "type": "object",
                    "properties": {
                        "agent_type": {"type": "string"},
                        "status": {"type": "string"},
                        "current_task": {"type": "string"},
                        "last_activity": {"type": "string", "format": "date-time"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["agent_type", "status"],
                },
            )

            # Issues collection
            await memory_plugin.create_collection(
                base_namespace,
                "issues",
                {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "high", "medium", "low"],
                        },
                        "type": {"type": "string"},
                        "file": {"type": "string"},
                        "line": {"type": "integer"},
                        "description": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["open", "resolved", "wontfix"],
                        },
                        "created_at": {"type": "string", "format": "date-time"},
                    },
                    "required": ["id", "severity", "description", "status"],
                },
            )

            # Code collection
            await memory_plugin.create_collection(
                base_namespace,
                "code",
                {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                        "task_id": {"type": "string"},
                        "metadata": {"type": "object"},
                        "timestamp": {"type": "string", "format": "date-time"},
                    },
                    "required": ["file_path", "content"],
                },
            )

            # Sessions collection
            await memory_plugin.create_collection(
                base_namespace,
                "sessions",
                {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "project_id": {"type": "string"},
                        "status": {"type": "string"},
                        "metadata": {"type": "object"},
                        "created_at": {"type": "string", "format": "date-time"},
                    },
                    "required": ["id", "project_id", "status"],
                },
            )

    # High-level APEX operations

    async def create_task(
        self, task_data: Dict[str, Any], assigned_to: str = "coder"
    ) -> str:
        """Create a new task."""
        return await self._db.store_structured_data(
            namespace=f"projects/{self.project_id}",
            collection="tasks",
            data={
                **task_data,
                "assigned_to": assigned_to,
                "status": task_data.get("status", "pending"),
                "priority": task_data.get("priority", "medium"),
            },
        )

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID."""
        return await self._db.get_structured_data(
            namespace=f"projects/{self.project_id}", collection="tasks", id=task_id
        )

    async def update_agent_status(
        self, agent_type: str, status_data: Dict[str, Any]
    ) -> str:
        """Update agent status."""
        return await self._db.store_structured_data(
            namespace=f"projects/{self.project_id}",
            collection="agents",
            data={"agent_type": agent_type, **status_data},
            id=agent_type,  # Use agent_type as ID for uniqueness
        )

    async def report_issue(
        self, issue_data: Dict[str, Any], severity: str = "medium"
    ) -> str:
        """Report a new issue."""
        return await self._db.store_structured_data(
            namespace=f"projects/{self.project_id}",
            collection="issues",
            data={
                **issue_data,
                "severity": severity,
                "status": issue_data.get("status", "open"),
            },
        )

    async def store_code(
        self,
        file_path: str,
        content: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store code file content."""
        return await self._db.store_structured_data(
            namespace=f"projects/{self.project_id}",
            collection="code",
            data={
                "file_path": file_path,
                "content": content,
                "task_id": task_id,
                "metadata": metadata or {},
            },
        )

    async def create_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new session."""
        return await self._db.store_structured_data(
            namespace=f"projects/{self.project_id}",
            collection="sessions",
            data={"project_id": self.project_id, "status": "active", **session_data},
        )

    # Query operations

    async def get_pending_tasks(
        self, assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get pending tasks, optionally filtered by assignee."""
        tasks = await self._db.query_data(
            namespace=f"projects/{self.project_id}", collection="tasks"
        )

        # Filter by status and assignee
        filtered = [
            task
            for task in tasks
            if task.get("status") == "pending"
            and (not assigned_to or task.get("assigned_to") == assigned_to)
        ]

        # Sort by priority and creation time
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered.sort(
            key=lambda t: (
                priority_order.get(t.get("priority", "medium"), 1),
                t.get("created_at", ""),
            )
        )

        return filtered

    async def get_open_issues(
        self, severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get open issues, optionally filtered by severity."""
        issues = await self._db.query_data(
            namespace=f"projects/{self.project_id}", collection="issues"
        )

        # Filter by status and severity
        filtered = [
            issue
            for issue in issues
            if issue.get("status") == "open"
            and (not severity or issue.get("severity") == severity)
        ]

        # Sort by severity and creation time
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        filtered.sort(
            key=lambda i: (
                severity_order.get(i.get("severity", "medium"), 2),
                i.get("created_at", ""),
            )
        )

        return filtered

    async def get_all_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all agents."""
        agents = await self._db.query_data(
            namespace=f"projects/{self.project_id}", collection="agents"
        )

        return {agent["agent_type"]: agent for agent in agents}

    # Compatibility methods for existing APEX code

    def get_plugin(self, name: str) -> Optional["LMDBPlugin"]:
        """Get a loaded plugin by name."""
        return self._db.get_plugin(name)

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        summary = await self._db.get_summary()

        # Add APEX-specific stats
        tasks = await self._db.query_data(f"projects/{self.project_id}", "tasks")
        issues = await self._db.query_data(f"projects/{self.project_id}", "issues")

        return {
            **summary,
            "project_id": self.project_id,
            "apex_stats": {
                "total_tasks": len(tasks),
                "pending_tasks": len(
                    [t for t in tasks if t.get("status") == "pending"]
                ),
                "total_issues": len(issues),
                "open_issues": len([i for i in issues if i.get("status") == "open"]),
            },
        }

    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()


# Backwards compatibility exports
__all__ = ["LMDBMCP", "APEXDatabase", "AgentDatabase", "LMDBWithPlugins"]
