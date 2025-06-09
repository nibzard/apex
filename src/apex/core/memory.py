"""Memory management patterns and utilities for APEX."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from apex.core.lmdb_mcp import LMDBMCP
from apex.types import AgentType


class AsyncMCPAdapter:
    """Adapter to make sync LMDBMCP work with async interface."""

    def __init__(self, mcp: LMDBMCP):
        """Initialize with sync MCP instance."""
        self.mcp = mcp

    async def read(self, key: str) -> Optional[str]:
        """Async read that works with sync MCP."""
        data = self.mcp.read(key)
        if data:
            return data.decode()
        return None

    async def write(self, key: str, value: str) -> None:
        """Async write that works with sync MCP."""
        self.mcp.write(key, value.encode())

    async def delete(self, key: str) -> None:
        """Async delete that works with sync MCP."""
        self.mcp.delete(key)

    async def list_keys(self, prefix: str = "") -> List[str]:
        """Async list_keys that works with sync MCP."""
        return self.mcp.list_keys(prefix)


class MemoryPatterns:
    """Common memory access patterns for APEX agents."""

    def __init__(self, mcp: Union[LMDBMCP, AsyncMCPAdapter]):
        """Initialize with LMDB MCP instance or async adapter."""
        if isinstance(mcp, AsyncMCPAdapter):
            self.mcp = mcp
        else:
            # Assume any other object (including LMDBMCP or mocks) needs the adapter
            self.mcp = AsyncMCPAdapter(mcp)

    # Project Management
    async def create_project(
        self, project_id: str, project_data: Dict[str, Any]
    ) -> bool:
        """Create a new project in memory."""
        try:
            # Store project configuration
            config_key = f"/projects/{project_id}/config"
            await self.mcp.write(config_key, json.dumps(project_data))

            # Initialize project structure
            structure_keys = [
                f"/projects/{project_id}/agents/supervisor/state",
                f"/projects/{project_id}/agents/coder/state",
                f"/projects/{project_id}/agents/adversary/state",
                f"/projects/{project_id}/memory/tasks",
                f"/projects/{project_id}/memory/code",
                f"/projects/{project_id}/memory/tests",
                f"/projects/{project_id}/memory/issues",
                f"/projects/{project_id}/memory/status",
                f"/projects/{project_id}/sessions",
                f"/projects/{project_id}/git/branch",
                f"/projects/{project_id}/git/commits",
            ]

            for key in structure_keys:
                if key.endswith("tasks") or key.endswith("commits"):
                    await self.mcp.write(key, json.dumps([]))
                elif key.endswith("state") or key.endswith("branch"):
                    await self.mcp.write(key, json.dumps({}))
                else:
                    await self.mcp.write(key, json.dumps({}))

            return True
        except Exception:
            return False

    async def get_project_config(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project configuration."""
        try:
            config_key = f"/projects/{project_id}/config"
            data = await self.mcp.read(config_key)
            return json.loads(data) if data else None
        except Exception:
            return None

    # Task Management
    async def create_task(
        self, project_id: str, task_data: Dict[str, Any], assigned_to: str = "coder"
    ) -> str:
        """Create a new task and assign it."""
        task_id = str(uuid.uuid4())

        task_record = {
            "id": task_id,
            "description": task_data.get("description", ""),
            "assigned_to": assigned_to,
            "priority": task_data.get("priority", "medium"),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "depends_on": task_data.get("depends_on", []),
            "metadata": task_data.get("metadata", {}),
        }

        # Write to pending tasks
        pending_key = f"/projects/{project_id}/memory/tasks/pending/{task_id}"
        await self.mcp.write(pending_key, json.dumps(task_record))

        # Update task index
        index_key = f"/projects/{project_id}/memory/tasks/index/{task_id}"
        await self.mcp.write(
            index_key,
            json.dumps(
                {
                    "status": "pending",
                    "assigned_to": assigned_to,
                    "priority": task_record["priority"],
                }
            ),
        )

        return task_id

    async def complete_task(
        self,
        project_id: str,
        task_id: str,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark a task as completed and optionally store results."""
        try:
            # Read task from pending
            pending_key = f"/projects/{project_id}/memory/tasks/pending/{task_id}"
            task_data = await self.mcp.read(pending_key)

            if not task_data:
                return False

            task = json.loads(task_data)
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()

            if result_data:
                task["results"] = result_data

            # Move to completed
            completed_key = f"/projects/{project_id}/memory/tasks/completed/{task_id}"
            await self.mcp.write(completed_key, json.dumps(task))

            # Remove from pending
            await self.mcp.delete(pending_key)

            # Update index
            index_key = f"/projects/{project_id}/memory/tasks/index/{task_id}"
            await self.mcp.write(
                index_key,
                json.dumps(
                    {
                        "status": "completed",
                        "assigned_to": task["assigned_to"],
                        "priority": task["priority"],
                    }
                ),
            )

            return True
        except Exception:
            return False

    async def get_pending_tasks(
        self, project_id: str, assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get pending tasks, optionally filtered by assignee."""
        try:
            prefix = f"/projects/{project_id}/memory/tasks/pending/"
            keys = await self.mcp.list_keys(prefix)

            tasks = []
            for key in keys:
                task_data = await self.mcp.read(key)
                if task_data:
                    task = json.loads(task_data)
                    if not assigned_to or task.get("assigned_to") == assigned_to:
                        tasks.append(task)

            # Sort by priority and creation time
            priority_order = {"high": 0, "medium": 1, "low": 2}
            tasks.sort(
                key=lambda t: (
                    priority_order.get(t.get("priority", "medium"), 1),
                    t.get("created_at", ""),
                )
            )

            return tasks
        except Exception:
            return []

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
            code_record = {
                "content": content,
                "file_path": file_path,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
            }

            # Store code content
            code_key = (
                f"/projects/{project_id}/memory/code/{file_path.replace('/', '__')}"
            )
            await self.mcp.write(code_key, json.dumps(code_record))

            # Update code index
            index_key = (
                f"/projects/{project_id}/memory/code/index/"
                f"{file_path.replace('/', '__')}"
            )
            await self.mcp.write(
                index_key,
                json.dumps(
                    {
                        "file_path": file_path,
                        "task_id": task_id,
                        "last_modified": code_record["timestamp"],
                    }
                ),
            )

            return True
        except Exception:
            return False

    async def get_code(
        self, project_id: str, file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Get code file content and metadata."""
        try:
            code_key = (
                f"/projects/{project_id}/memory/code/{file_path.replace('/', '__')}"
            )
            data = await self.mcp.read(code_key)
            return json.loads(data) if data else None
        except Exception:
            return None

    async def list_code_files(self, project_id: str) -> List[Dict[str, Any]]:
        """List all code files in memory."""
        try:
            prefix = f"/projects/{project_id}/memory/code/index/"
            keys = await self.mcp.list_keys(prefix)

            files = []
            for key in keys:
                data = await self.mcp.read(key)
                if data:
                    files.append(json.loads(data))

            return sorted(files, key=lambda f: f.get("last_modified", ""))
        except Exception:
            return []

    # Issue Management
    async def report_issue(
        self, project_id: str, issue_data: Dict[str, Any], severity: str = "medium"
    ) -> str:
        """Report a new issue."""
        issue_id = str(uuid.uuid4())

        issue_record = {
            "id": issue_id,
            "severity": severity,
            "type": issue_data.get("type", "bug"),  # bug, security, performance
            "file": issue_data.get("file"),
            "line": issue_data.get("line"),
            "description": issue_data.get("description", ""),
            "reproduction": issue_data.get("reproduction", ""),
            "suggested_fix": issue_data.get("suggested_fix", ""),
            "created_at": datetime.now().isoformat(),
            "status": "open",
            "metadata": issue_data.get("metadata", {}),
        }

        # Store issue
        issue_key = f"/projects/{project_id}/memory/issues/{severity}/{issue_id}"
        await self.mcp.write(issue_key, json.dumps(issue_record))

        # Update issue count
        count_key = f"/projects/{project_id}/metrics/issues/{severity}"
        try:
            count_data = await self.mcp.read(count_key)
            count = json.loads(count_data) if count_data else 0
        except Exception:
            count = 0

        await self.mcp.write(count_key, json.dumps(count + 1))

        return issue_id

    async def resolve_issue(
        self, project_id: str, issue_id: str, resolution: str
    ) -> bool:
        """Mark an issue as resolved."""
        try:
            # Find issue across severity levels
            for severity in ["critical", "high", "medium", "low"]:
                issue_key = (
                    f"/projects/{project_id}/memory/issues/{severity}/{issue_id}"
                )
                data = await self.mcp.read(issue_key)

                if data:
                    issue = json.loads(data)
                    issue["status"] = "resolved"
                    issue["resolution"] = resolution
                    issue["resolved_at"] = datetime.now().isoformat()

                    await self.mcp.write(issue_key, json.dumps(issue))
                    return True

            return False
        except Exception:
            return False

    async def get_open_issues(
        self, project_id: str, severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get open issues, optionally filtered by severity."""
        try:
            issues = []
            severities = (
                [severity] if severity else ["critical", "high", "medium", "low"]
            )

            for sev in severities:
                prefix = f"/projects/{project_id}/memory/issues/{sev}/"
                keys = await self.mcp.list_keys(prefix)

                for key in keys:
                    data = await self.mcp.read(key)
                    if data:
                        issue = json.loads(data)
                        if issue.get("status") == "open":
                            issues.append(issue)

            # Sort by severity and creation time
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            issues.sort(
                key=lambda i: (
                    severity_order.get(i.get("severity", "medium"), 2),
                    i.get("created_at", ""),
                )
            )

            return issues
        except Exception:
            return []

    # Agent Status Management
    async def update_agent_status(
        self, project_id: str, agent_type: AgentType, status_data: Dict[str, Any]
    ) -> bool:
        """Update agent status information."""
        try:
            status_record = {
                "agent_type": agent_type.value,
                "status": status_data.get("status", "unknown"),
                "current_task": status_data.get("current_task"),
                "last_activity": datetime.now().isoformat(),
                "metadata": status_data.get("metadata", {}),
            }

            # Store agent status
            status_key = f"/projects/{project_id}/agents/{agent_type.value}/status"
            await self.mcp.write(status_key, json.dumps(status_record))

            # Store in global status index
            global_key = f"/projects/{project_id}/memory/status/{agent_type.value}"
            await self.mcp.write(global_key, json.dumps(status_record))

            return True
        except Exception:
            return False

    async def get_agent_status(
        self, project_id: str, agent_type: AgentType
    ) -> Optional[Dict[str, Any]]:
        """Get agent status."""
        try:
            status_key = f"/projects/{project_id}/agents/{agent_type.value}/status"
            data = await self.mcp.read(status_key)
            return json.loads(data) if data else None
        except Exception:
            return None

    async def get_all_agent_status(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """Get status for all agents."""
        try:
            status = {}
            for agent_type in AgentType:
                agent_status = await self.get_agent_status(project_id, agent_type)
                if agent_status:
                    status[agent_type.value] = agent_status
            return status
        except Exception:
            return {}

    # Session Management
    async def create_session(
        self, project_id: str, session_data: Dict[str, Any]
    ) -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4())

        session_record = {
            "id": session_id,
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "metadata": session_data,
        }

        # Store session
        session_key = f"/projects/{project_id}/sessions/{session_id}/metadata"
        await self.mcp.write(session_key, json.dumps(session_record))

        # Initialize session event log
        events_key = f"/projects/{project_id}/sessions/{session_id}/events"
        await self.mcp.write(events_key, json.dumps([]))

        return session_id

    async def append_session_event(
        self, project_id: str, session_id: str, event_data: Dict[str, Any]
    ) -> bool:
        """Append an event to session history."""
        try:
            event_record = {
                "timestamp": datetime.now().isoformat(),
                "event_id": str(uuid.uuid4()),
                **event_data,
            }

            # Read current events
            events_key = f"/projects/{project_id}/sessions/{session_id}/events"
            data = await self.mcp.read(events_key)
            events = json.loads(data) if data else []

            # Append new event
            events.append(event_record)

            # Write back (with size limit)
            max_events = 10000  # Prevent unbounded growth
            if len(events) > max_events:
                events = events[-max_events:]

            await self.mcp.write(events_key, json.dumps(events))
            return True
        except Exception:
            return False

    # Memory Utilities
    async def get_memory_stats(self, project_id: str) -> Dict[str, Any]:
        """Get memory usage statistics for a project."""
        try:
            stats = {
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "tasks": {"pending": 0, "completed": 0},
                "code_files": 0,
                "issues": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "sessions": 0,
            }

            # Count tasks
            pending_tasks = await self.get_pending_tasks(project_id)
            stats["tasks"]["pending"] = len(pending_tasks)

            completed_prefix = f"/projects/{project_id}/memory/tasks/completed/"
            completed_keys = await self.mcp.list_keys(completed_prefix)
            stats["tasks"]["completed"] = len(completed_keys)

            # Count code files
            code_files = await self.list_code_files(project_id)
            stats["code_files"] = len(code_files)

            # Count issues by severity
            for severity in ["critical", "high", "medium", "low"]:
                issues = await self.get_open_issues(project_id, severity)
                stats["issues"][severity] = len(issues)

            # Count sessions
            sessions_prefix = f"/projects/{project_id}/sessions/"
            session_keys = await self.mcp.list_keys(sessions_prefix)
            # Filter to only metadata keys (not event keys)
            session_metadata_keys = [k for k in session_keys if k.endswith("/metadata")]
            stats["sessions"] = len(session_metadata_keys)

            return stats
        except Exception:
            return {}

    async def cleanup_old_data(
        self, project_id: str, days_to_keep: int = 30
    ) -> Dict[str, int]:
        """Clean up old data from memory."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            cleanup_stats = {"deleted_events": 0, "deleted_sessions": 0}

            # Clean up old session events (keep metadata)
            sessions_prefix = f"/projects/{project_id}/sessions/"
            session_keys = await self.mcp.list_keys(sessions_prefix)

            for key in session_keys:
                if key.endswith("/events"):
                    data = await self.mcp.read(key)
                    if data:
                        events = json.loads(data)
                        original_count = len(events)

                        # Filter events newer than cutoff
                        filtered_events = []
                        for event in events:
                            try:
                                event_time = datetime.fromisoformat(
                                    event.get("timestamp", "")
                                ).timestamp()
                                if event_time >= cutoff_date:
                                    filtered_events.append(event)
                            except (ValueError, TypeError):
                                # Keep events with invalid timestamps
                                filtered_events.append(event)

                        if len(filtered_events) < original_count:
                            await self.mcp.write(key, json.dumps(filtered_events))
                            cleanup_stats["deleted_events"] += original_count - len(
                                filtered_events
                            )

            return cleanup_stats
        except Exception:
            return {"error": "Cleanup failed"}


class MemorySnapshot:
    """Create and manage memory snapshots for checkpoints."""

    def __init__(self, mcp: Union[LMDBMCP, AsyncMCPAdapter]):
        """Initialize with LMDB MCP instance or async adapter."""
        if isinstance(mcp, AsyncMCPAdapter):
            self.mcp = mcp
        else:
            # Assume any other object (including LMDBMCP or mocks) needs the adapter
            self.mcp = AsyncMCPAdapter(mcp)

    async def create_snapshot(
        self, project_id: str, snapshot_id: Optional[str] = None
    ) -> str:
        """Create a memory snapshot."""
        if not snapshot_id:
            snapshot_id = str(uuid.uuid4())

        snapshot_data = {
            "id": snapshot_id,
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "keys": {},
        }

        # Get all keys for the project
        project_prefix = f"/projects/{project_id}/"
        keys = await self.mcp.list_keys(project_prefix)

        # Store current values
        for key in keys:
            try:
                value = await self.mcp.read(key)
                if value:
                    snapshot_data["keys"][key] = value
            except Exception:
                continue

        # Store snapshot
        snapshot_key = f"/snapshots/{snapshot_id}"
        await self.mcp.write(snapshot_key, json.dumps(snapshot_data))

        return snapshot_id

    async def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore memory state from a snapshot."""
        try:
            snapshot_key = f"/snapshots/{snapshot_id}"
            data = await self.mcp.read(snapshot_key)

            if not data:
                return False

            snapshot = json.loads(data)

            # Restore all keys
            for key, value in snapshot["keys"].items():
                await self.mcp.write(key, value)

            return True
        except Exception:
            return False

    async def list_snapshots(
        self, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List available snapshots."""
        try:
            prefix = "/snapshots/"
            keys = await self.mcp.list_keys(prefix)

            snapshots = []
            for key in keys:
                data = await self.mcp.read(key)
                if data:
                    snapshot = json.loads(data)
                    # Filter by project if specified
                    if not project_id or snapshot.get("project_id") == project_id:
                        # Only include metadata, not the full keys data
                        snapshot_info = {
                            "id": snapshot["id"],
                            "project_id": snapshot["project_id"],
                            "created_at": snapshot["created_at"],
                            "key_count": len(snapshot.get("keys", {})),
                        }
                        snapshots.append(snapshot_info)

            return sorted(snapshots, key=lambda s: s["created_at"], reverse=True)
        except Exception:
            return []

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a memory snapshot."""
        try:
            snapshot_key = f"/snapshots/{snapshot_id}"
            await self.mcp.delete(snapshot_key)
            return True
        except Exception:
            return False
