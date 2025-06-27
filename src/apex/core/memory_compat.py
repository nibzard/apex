"""Compatibility layer for APEX memory patterns using plugin system.

This module provides backward compatibility for existing APEX code while
transitioning to the new plugin-based architecture.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from apex.core.lmdb_mcp import APEXDatabase
from apex.types import AgentType


class MemoryNamespace(Enum):
    """Enumeration of memory namespaces in LMDB."""

    PROJECTS = "projects"
    AGENTS = "agents"
    TASKS = "tasks"
    CODE = "code"
    ISSUES = "issues"
    SESSIONS = "sessions"
    GIT = "git"
    METRICS = "metrics"
    SNAPSHOTS = "snapshots"
    EVENTS = "events"
    LOGS = "logs"
    CACHE = "cache"
    CONTEXT = "context"


class MemoryPatterns:
    """Compatibility wrapper for existing APEX memory patterns.

    This class maintains the existing API while using the new plugin-based
    APEX database underneath. It provides a migration path for existing code.
    """

    def __init__(self, apex_db: APEXDatabase):
        """Initialize with an APEX database instance.

        Args:
            apex_db: Initialized APEX database instance

        """
        self.apex_db = apex_db
        self.project_id = apex_db.project_id

    # Project Management (simplified - APEX database handles setup)

    async def create_project(
        self, project_id: str, project_data: Dict[str, Any]
    ) -> bool:
        """Create a new project in memory."""
        try:
            # Store project metadata
            await self.apex_db._db.store_structured_data(
                namespace="global",
                collection="projects",
                data={
                    "project_id": project_id,
                    **project_data,
                    "created_at": datetime.now().isoformat(),
                    "version": "2.0.0",  # Plugin-based version
                    "status": "active",
                },
                id=project_id,
            )
            return True
        except Exception:
            return False

    async def get_project_config(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project configuration."""
        return await self.apex_db._db.get_structured_data(
            namespace="global", collection="projects", id=project_id
        )

    # Task Management

    async def create_task(
        self, project_id: str, task_data: Dict[str, Any], assigned_to: str = "coder"
    ) -> str:
        """Create a new task."""
        # Use APEX database's task creation
        return await self.apex_db.create_task(task_data, assigned_to)

    async def start_task(self, project_id: str, task_id: str) -> bool:
        """Move task from pending to in_progress."""
        try:
            task = await self.apex_db.get_task(task_id)
            if not task:
                return False

            # Update task status
            await self.apex_db._db.store_structured_data(
                namespace=f"projects/{project_id}",
                collection="tasks",
                data={
                    **task,
                    "status": "in_progress",
                    "started_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
                id=task_id,
            )
            return True
        except Exception:
            return False

    async def complete_task(
        self,
        project_id: str,
        task_id: str,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark a task as completed."""
        try:
            task = await self.apex_db.get_task(task_id)
            if not task:
                return False

            # Update task status
            await self.apex_db._db.store_structured_data(
                namespace=f"projects/{project_id}",
                collection="tasks",
                data={
                    **task,
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "results": result_data or {},
                },
                id=task_id,
            )
            return True
        except Exception:
            return False

    async def fail_task(
        self,
        project_id: str,
        task_id: str,
        error_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark a task as failed."""
        try:
            task = await self.apex_db.get_task(task_id)
            if not task:
                return False

            # Update task status
            await self.apex_db._db.store_structured_data(
                namespace=f"projects/{project_id}",
                collection="tasks",
                data={
                    **task,
                    "status": "failed",
                    "failed_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "error": error_data or {},
                },
                id=task_id,
            )
            return True
        except Exception:
            return False

    async def get_pending_tasks(
        self, project_id: str, assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get pending tasks."""
        return await self.apex_db.get_pending_tasks(assigned_to)

    # Code Management

    async def store_code(
        self,
        project_id: str,
        file_path: str,
        content: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store code file in memory."""
        try:
            await self.apex_db.store_code(file_path, content, task_id, metadata)
            return True
        except Exception:
            return False

    async def get_code(
        self, project_id: str, file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Get code file content."""
        # Search for code by file path
        code_files = await self.apex_db._db.query_data(
            namespace=f"projects/{project_id}", collection="code"
        )

        for code_file in code_files:
            if code_file.get("file_path") == file_path:
                return code_file

        return None

    # Issue Management

    async def report_issue(
        self, project_id: str, issue_data: Dict[str, Any], severity: str = "medium"
    ) -> str:
        """Report a new issue."""
        return await self.apex_db.report_issue(issue_data, severity)

    async def resolve_issue(
        self, project_id: str, issue_id: str, resolution: str
    ) -> bool:
        """Mark an issue as resolved."""
        try:
            issue = await self.apex_db._db.get_structured_data(
                namespace=f"projects/{project_id}", collection="issues", id=issue_id
            )

            if not issue:
                return False

            # Update issue status
            await self.apex_db._db.store_structured_data(
                namespace=f"projects/{project_id}",
                collection="issues",
                data={
                    **issue,
                    "status": "resolved",
                    "resolution": resolution,
                    "resolved_at": datetime.now().isoformat(),
                },
                id=issue_id,
            )
            return True
        except Exception:
            return False

    async def get_open_issues(
        self, project_id: str, severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get open issues."""
        return await self.apex_db.get_open_issues(severity)

    # Agent Status Management

    async def update_agent_status(
        self, project_id: str, agent_type: AgentType, status_data: Dict[str, Any]
    ) -> bool:
        """Update agent status."""
        try:
            await self.apex_db.update_agent_status(
                agent_type.value,
                {
                    **status_data,
                    "last_activity": datetime.now().isoformat(),
                },
            )
            return True
        except Exception:
            return False

    async def get_agent_status(
        self, project_id: str, agent_type: AgentType
    ) -> Optional[Dict[str, Any]]:
        """Get agent status."""
        all_agents = await self.apex_db.get_all_agent_status()
        return all_agents.get(agent_type.value)

    async def get_all_agent_status(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """Get status for all agents."""
        return await self.apex_db.get_all_agent_status()

    # Session Management

    async def create_session(
        self, project_id: str, session_data: Dict[str, Any]
    ) -> str:
        """Create a new session."""
        return await self.apex_db.create_session(session_data)

    async def append_session_event(
        self, project_id: str, session_id: str, event_data: Dict[str, Any]
    ) -> bool:
        """Append an event to session history."""
        try:
            # Get existing session
            session = await self.apex_db._db.get_structured_data(
                namespace=f"projects/{project_id}", collection="sessions", id=session_id
            )

            if not session:
                return False

            # Add event to session metadata
            events = session.get("events", [])
            event_record = {
                "timestamp": datetime.now().isoformat(),
                "event_id": str(uuid.uuid4()),
                **event_data,
            }
            events.append(event_record)

            # Limit events to prevent unbounded growth
            max_events = 1000
            if len(events) > max_events:
                events = events[-max_events:]

            # Update session
            await self.apex_db._db.store_structured_data(
                namespace=f"projects/{project_id}",
                collection="sessions",
                data={
                    **session,
                    "events": events,
                    "updated_at": datetime.now().isoformat(),
                },
                id=session_id,
            )
            return True
        except Exception:
            return False

    # Memory Utilities

    async def get_memory_stats(self, project_id: str) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return await self.apex_db.get_memory_stats()

    async def cleanup_old_data(
        self, project_id: str, days_to_keep: int = 30
    ) -> Dict[str, int]:
        """Clean up old data - simplified for compatibility."""
        return {"note": "Cleanup delegated to plugin system"}

    # Compatibility method for close
    async def close(self) -> None:
        """Close method for compatibility."""
        # APEX database handles its own lifecycle
        pass


# Additional compatibility classes that might be needed


class AsyncMCPAdapter:
    """Compatibility adapter - now delegated to plugin system."""

    def __init__(self, apex_db: APEXDatabase):
        self.apex_db = apex_db

    async def read(self, key: str) -> Optional[str]:
        """Read via plugin system."""
        # This would need to be implemented based on key patterns
        # For now, return None as this is for compatibility
        return None

    async def write(self, key: str, value: str) -> None:
        """Write via plugin system."""
        # This would need to be implemented based on key patterns
        pass

    async def delete(self, key: str) -> None:
        """Delete via plugin system."""
        pass

    async def list_keys(self, prefix: str = "") -> List[str]:
        """List keys via plugin system."""
        return []


# Re-export for compatibility
MemorySchema = None  # The schema is now handled by plugins
MemoryQuery = None  # Advanced queries will be handled by query plugin
MemorySnapshot = None  # Snapshots will be handled by snapshot plugin
MemoryCleanup = None  # Cleanup will be handled by cleanup plugin
ContextAsAService = None  # Context will be handled by context plugin
