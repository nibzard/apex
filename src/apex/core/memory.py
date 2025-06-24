"""Memory management patterns and utilities for APEX."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from apex.core.lmdb_mcp import LMDBMCP
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


@dataclass
class MemorySchema:
    """Schema definition for LMDB memory structure."""

    # Core project structure
    PROJECT_CONFIG = "/projects/{project_id}/config"
    PROJECT_METADATA = "/projects/{project_id}/metadata"

    # Agent management
    AGENT_STATE = "/projects/{project_id}/agents/{agent_type}/state"
    AGENT_STATUS = "/projects/{project_id}/agents/{agent_type}/status"
    AGENT_PROMPTS = "/projects/{project_id}/agents/{agent_type}/prompts"
    AGENT_HISTORY = "/projects/{project_id}/agents/{agent_type}/history"

    # Task management with priority queues
    TASK_PENDING = "/projects/{project_id}/memory/tasks/pending/{task_id}"
    TASK_IN_PROGRESS = "/projects/{project_id}/memory/tasks/in_progress/{task_id}"
    TASK_COMPLETED = "/projects/{project_id}/memory/tasks/completed/{task_id}"
    TASK_FAILED = "/projects/{project_id}/memory/tasks/failed/{task_id}"
    TASK_INDEX = "/projects/{project_id}/memory/tasks/index/{task_id}"
    TASK_PRIORITY_HIGH = "/projects/{project_id}/memory/tasks/priority/high/{task_id}"
    TASK_PRIORITY_MEDIUM = (
        "/projects/{project_id}/memory/tasks/priority/medium/{task_id}"
    )
    TASK_PRIORITY_LOW = "/projects/{project_id}/memory/tasks/priority/low/{task_id}"

    # Code management with versioning
    CODE_CONTENT = "/projects/{project_id}/memory/code/content/{file_path_hash}"
    CODE_INDEX = "/projects/{project_id}/memory/code/index/{file_path_hash}"
    CODE_VERSIONS = "/projects/{project_id}/memory/code/versions/{file_path_hash}"
    CODE_DEPENDENCIES = (
        "/projects/{project_id}/memory/code/dependencies/{file_path_hash}"
    )

    # Issue tracking with severity levels
    ISSUE_CRITICAL = "/projects/{project_id}/memory/issues/critical/{issue_id}"
    ISSUE_HIGH = "/projects/{project_id}/memory/issues/high/{issue_id}"
    ISSUE_MEDIUM = "/projects/{project_id}/memory/issues/medium/{issue_id}"
    ISSUE_LOW = "/projects/{project_id}/memory/issues/low/{issue_id}"
    ISSUE_INDEX = "/projects/{project_id}/memory/issues/index/{issue_id}"

    # Session management
    SESSION_METADATA = "/projects/{project_id}/sessions/{session_id}/metadata"
    SESSION_EVENTS = "/projects/{project_id}/sessions/{session_id}/events"
    SESSION_CHECKPOINTS = (
        "/projects/{project_id}/sessions/{session_id}/checkpoints/{checkpoint_id}"
    )

    # Git integration
    GIT_BRANCH = "/projects/{project_id}/git/branch"
    GIT_COMMITS = "/projects/{project_id}/git/commits"
    GIT_STATUS = "/projects/{project_id}/git/status"
    GIT_HISTORY = "/projects/{project_id}/git/history"

    # Metrics and monitoring
    METRICS_PERFORMANCE = "/projects/{project_id}/metrics/performance"
    METRICS_USAGE = "/projects/{project_id}/metrics/usage"
    METRICS_ERRORS = "/projects/{project_id}/metrics/errors"

    # Event processing
    EVENTS_STREAM = "/projects/{project_id}/events/stream"
    EVENTS_ARCHIVE = "/projects/{project_id}/events/archive/{date}"

    # Logging
    LOGS_SYSTEM = "/projects/{project_id}/logs/system/{date}"
    LOGS_AGENTS = "/projects/{project_id}/logs/agents/{agent_type}/{date}"
    LOGS_ERRORS = "/projects/{project_id}/logs/errors/{date}"

    # Caching
    CACHE_QUERIES = "/projects/{project_id}/cache/queries/{query_hash}"
    CACHE_COMPUTATIONS = "/projects/{project_id}/cache/computations/{computation_hash}"

    # Context-as-a-Service patterns for v2.0
    CONTEXT_POINTERS = "/projects/{project_id}/context/pointers/{pointer_id}"
    CONTEXT_CHUNKS = "/projects/{project_id}/context/chunks/{chunk_id}"
    CONTEXT_SUMMARIES = "/projects/{project_id}/context/summaries/{content_hash}"
    CONTEXT_INDEX = "/projects/{project_id}/context/index/{category}"

    # Global namespaces
    GLOBAL_PROJECTS = "/global/projects"
    GLOBAL_SCHEMAS = "/global/schemas"
    GLOBAL_CONFIG = "/global/config"

    # Snapshots
    SNAPSHOTS_FULL = "/snapshots/full/{snapshot_id}"
    SNAPSHOTS_INCREMENTAL = "/snapshots/incremental/{snapshot_id}"
    SNAPSHOTS_INDEX = "/snapshots/index"

    @classmethod
    def get_all_patterns(cls) -> List[str]:
        """Get all schema patterns."""
        return [
            value
            for name, value in cls.__dict__.items()
            if isinstance(value, str) and value.startswith("/")
        ]

    @classmethod
    def validate_key(cls, key: str) -> bool:
        """Validate if a key follows the schema patterns."""
        for pattern in cls.get_all_patterns():
            # Simple pattern matching - could be enhanced with regex
            if cls._matches_pattern(key, pattern):
                return True
        return False

    @staticmethod
    def _matches_pattern(key: str, pattern: str) -> bool:
        """Check if key matches pattern with placeholders."""
        # Simple implementation - could be enhanced
        pattern_parts = pattern.split("/")
        key_parts = key.split("/")

        if len(pattern_parts) != len(key_parts):
            return False

        for pattern_part, key_part in zip(pattern_parts, key_parts, strict=False):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                continue  # Placeholder matches anything
            if pattern_part != key_part:
                return False

        return True


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
        self.schema = MemorySchema()

    def _get_file_path_hash(self, file_path: str) -> str:
        """Generate a hash for file path to use as key."""
        import hashlib

        return hashlib.md5(file_path.encode()).hexdigest()

    def _get_query_hash(self, query: Dict[str, Any]) -> str:
        """Generate a hash for query to use as cache key."""
        import hashlib

        query_str = json.dumps(query, sort_keys=True)
        return hashlib.md5(query_str.encode()).hexdigest()

    def _get_date_key(self) -> str:
        """Get current date as key."""
        return datetime.now().strftime("%Y-%m-%d")

    def _format_key(self, pattern: str, **kwargs) -> str:
        """Format a schema pattern with actual values."""
        return pattern.format(**kwargs)

    # Project Management
    async def create_project(
        self, project_id: str, project_data: Dict[str, Any]
    ) -> bool:
        """Create a new project in memory."""
        try:
            # Store project configuration using schema
            config_key = self._format_key(
                self.schema.PROJECT_CONFIG, project_id=project_id
            )
            await self.mcp.write(config_key, json.dumps(project_data))

            # Store project metadata
            metadata_key = self._format_key(
                self.schema.PROJECT_METADATA, project_id=project_id
            )
            metadata = {
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "schema_version": "1.0.0",
                "status": "active",
            }
            await self.mcp.write(metadata_key, json.dumps(metadata))

            # Initialize agent states using schema
            for agent_type in ["supervisor", "coder", "adversary"]:
                state_key = self._format_key(
                    self.schema.AGENT_STATE,
                    project_id=project_id,
                    agent_type=agent_type,
                )
                status_key = self._format_key(
                    self.schema.AGENT_STATUS,
                    project_id=project_id,
                    agent_type=agent_type,
                )
                await self.mcp.write(state_key, json.dumps({}))
                await self.mcp.write(
                    status_key,
                    json.dumps(
                        {"status": "inactive", "created_at": datetime.now().isoformat()}
                    ),
                )

            # Initialize git state
            git_branch_key = self._format_key(
                self.schema.GIT_BRANCH, project_id=project_id
            )
            git_commits_key = self._format_key(
                self.schema.GIT_COMMITS, project_id=project_id
            )
            git_status_key = self._format_key(
                self.schema.GIT_STATUS, project_id=project_id
            )

            await self.mcp.write(git_branch_key, json.dumps("main"))
            await self.mcp.write(git_commits_key, json.dumps([]))
            await self.mcp.write(git_status_key, json.dumps({}))

            # Initialize metrics
            for metric_type in ["performance", "usage", "errors"]:
                if metric_type == "performance":
                    metric_key = self._format_key(
                        self.schema.METRICS_PERFORMANCE, project_id=project_id
                    )
                elif metric_type == "usage":
                    metric_key = self._format_key(
                        self.schema.METRICS_USAGE, project_id=project_id
                    )
                else:
                    metric_key = self._format_key(
                        self.schema.METRICS_ERRORS, project_id=project_id
                    )

                await self.mcp.write(
                    metric_key,
                    json.dumps(
                        {
                            "initialized_at": datetime.now().isoformat(),
                            "counters": {},
                            "gauges": {},
                        }
                    ),
                )

            # Register project globally
            global_projects_key = self.schema.GLOBAL_PROJECTS
            try:
                projects_data = await self.mcp.read(global_projects_key)
                projects = json.loads(projects_data) if projects_data else []
            except Exception:
                projects = []

            if project_id not in projects:
                projects.append(project_id)
                await self.mcp.write(global_projects_key, json.dumps(projects))

            return True
        except Exception:
            # Log error for debugging
            return False

    async def get_project_config(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project configuration."""
        try:
            config_key = self._format_key(
                self.schema.PROJECT_CONFIG, project_id=project_id
            )
            data = await self.mcp.read(config_key)
            return json.loads(data) if data else None
        except Exception:
            return None

    async def get_project_metadata(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project metadata."""
        try:
            metadata_key = self._format_key(
                self.schema.PROJECT_METADATA, project_id=project_id
            )
            data = await self.mcp.read(metadata_key)
            return json.loads(data) if data else None
        except Exception:
            return None

    async def list_all_projects(self) -> List[str]:
        """List all registered projects."""
        try:
            global_projects_key = self.schema.GLOBAL_PROJECTS
            data = await self.mcp.read(global_projects_key)
            return json.loads(data) if data else []
        except Exception:
            return []

    # Task Management with Enhanced Patterns
    async def create_task(
        self, project_id: str, task_data: Dict[str, Any], assigned_to: str = "coder"
    ) -> str:
        """Create a new task and assign it with enhanced priority handling."""
        task_id = str(uuid.uuid4())
        priority = task_data.get("priority", "medium")

        task_record = {
            "id": task_id,
            "description": task_data.get("description", ""),
            "assigned_to": assigned_to,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "depends_on": task_data.get("depends_on", []),
            "metadata": task_data.get("metadata", {}),
            "estimated_duration": task_data.get("estimated_duration"),
            "tags": task_data.get("tags", []),
        }

        # Write to pending tasks using schema
        pending_key = self._format_key(
            self.schema.TASK_PENDING, project_id=project_id, task_id=task_id
        )
        await self.mcp.write(pending_key, json.dumps(task_record))

        # Update task index using schema
        index_key = self._format_key(
            self.schema.TASK_INDEX, project_id=project_id, task_id=task_id
        )
        await self.mcp.write(
            index_key,
            json.dumps(
                {
                    "status": "pending",
                    "assigned_to": assigned_to,
                    "priority": priority,
                    "created_at": task_record["created_at"],
                    "tags": task_record["tags"],
                }
            ),
        )

        # Add to priority queue using schema
        priority_key = None
        if priority == "high":
            priority_key = self._format_key(
                self.schema.TASK_PRIORITY_HIGH, project_id=project_id, task_id=task_id
            )
        elif priority == "medium":
            priority_key = self._format_key(
                self.schema.TASK_PRIORITY_MEDIUM, project_id=project_id, task_id=task_id
            )
        elif priority == "low":
            priority_key = self._format_key(
                self.schema.TASK_PRIORITY_LOW, project_id=project_id, task_id=task_id
            )

        if priority_key:
            await self.mcp.write(
                priority_key,
                json.dumps(
                    {
                        "task_id": task_id,
                        "created_at": task_record["created_at"],
                        "assigned_to": assigned_to,
                    }
                ),
            )

        return task_id

    async def start_task(self, project_id: str, task_id: str) -> bool:
        """Move task from pending to in_progress."""
        try:
            # Read task from pending
            pending_key = self._format_key(
                self.schema.TASK_PENDING, project_id=project_id, task_id=task_id
            )
            task_data = await self.mcp.read(pending_key)

            if not task_data:
                return False

            task = json.loads(task_data)
            task["status"] = "in_progress"
            task["started_at"] = datetime.now().isoformat()
            task["updated_at"] = datetime.now().isoformat()

            # Move to in_progress
            in_progress_key = self._format_key(
                self.schema.TASK_IN_PROGRESS, project_id=project_id, task_id=task_id
            )
            await self.mcp.write(in_progress_key, json.dumps(task))

            # Remove from pending
            await self.mcp.delete(pending_key)

            # Update index
            index_key = self._format_key(
                self.schema.TASK_INDEX, project_id=project_id, task_id=task_id
            )
            index_data = await self.mcp.read(index_key)
            if index_data:
                index = json.loads(index_data)
                index["status"] = "in_progress"
                index["started_at"] = task["started_at"]
                await self.mcp.write(index_key, json.dumps(index))

            return True
        except Exception:
            return False

    async def complete_task(
        self,
        project_id: str,
        task_id: str,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark a task as completed and optionally store results."""
        try:
            # Try to read task from both pending and in_progress
            task_data = None
            source_key = None

            # Check in_progress first
            in_progress_key = self._format_key(
                self.schema.TASK_IN_PROGRESS, project_id=project_id, task_id=task_id
            )
            task_data = await self.mcp.read(in_progress_key)
            if task_data:
                source_key = in_progress_key
            else:
                # Check pending
                pending_key = self._format_key(
                    self.schema.TASK_PENDING, project_id=project_id, task_id=task_id
                )
                task_data = await self.mcp.read(pending_key)
                if task_data:
                    source_key = pending_key

            if not task_data or not source_key:
                return False

            task = json.loads(task_data)
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["updated_at"] = datetime.now().isoformat()

            if result_data:
                task["results"] = result_data

            # Move to completed using schema
            completed_key = self._format_key(
                self.schema.TASK_COMPLETED, project_id=project_id, task_id=task_id
            )
            await self.mcp.write(completed_key, json.dumps(task))

            # Remove from source (pending or in_progress)
            await self.mcp.delete(source_key)

            # Update index
            index_key = self._format_key(
                self.schema.TASK_INDEX, project_id=project_id, task_id=task_id
            )
            index_data = await self.mcp.read(index_key)
            if index_data:
                index = json.loads(index_data)
                index["status"] = "completed"
                index["completed_at"] = task["completed_at"]
                await self.mcp.write(index_key, json.dumps(index))

            return True
        except Exception:
            return False

    async def fail_task(
        self,
        project_id: str,
        task_id: str,
        error_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark a task as failed and store error information."""
        try:
            # Try to read task from both pending and in_progress
            task_data = None
            source_key = None

            # Check in_progress first
            in_progress_key = self._format_key(
                self.schema.TASK_IN_PROGRESS, project_id=project_id, task_id=task_id
            )
            task_data = await self.mcp.read(in_progress_key)
            if task_data:
                source_key = in_progress_key
            else:
                # Check pending
                pending_key = self._format_key(
                    self.schema.TASK_PENDING, project_id=project_id, task_id=task_id
                )
                task_data = await self.mcp.read(pending_key)
                if task_data:
                    source_key = pending_key

            if not task_data or not source_key:
                return False

            task = json.loads(task_data)
            task["status"] = "failed"
            task["failed_at"] = datetime.now().isoformat()
            task["updated_at"] = datetime.now().isoformat()

            if error_data:
                task["error"] = error_data

            # Move to failed using schema
            failed_key = self._format_key(
                self.schema.TASK_FAILED, project_id=project_id, task_id=task_id
            )
            await self.mcp.write(failed_key, json.dumps(task))

            # Remove from source
            await self.mcp.delete(source_key)

            # Update index
            index_key = self._format_key(
                self.schema.TASK_INDEX, project_id=project_id, task_id=task_id
            )
            index_data = await self.mcp.read(index_key)
            if index_data:
                index = json.loads(index_data)
                index["status"] = "failed"
                index["failed_at"] = task["failed_at"]
                await self.mcp.write(index_key, json.dumps(index))

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


class MemoryQuery:
    """Advanced querying and indexing for LMDB memory."""

    def __init__(self, memory_patterns: MemoryPatterns):
        """Initialize with MemoryPatterns instance."""
        self.patterns = memory_patterns
        self.mcp = memory_patterns.mcp
        self.schema = memory_patterns.schema

    async def query_tasks(
        self,
        project_id: str,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query tasks with advanced filtering and sorting."""
        try:
            filters = filters or {}
            tasks = []

            # Determine which task collections to search
            status_filter = filters.get("status")
            if status_filter:
                if isinstance(status_filter, str):
                    status_list = [status_filter]
                else:
                    status_list = status_filter
            else:
                status_list = ["pending", "in_progress", "completed", "failed"]

            # Search in each status collection
            for status in status_list:
                if status == "pending":
                    prefix = self.patterns._format_key(
                        "/projects/{project_id}/memory/tasks/pending/",
                        project_id=project_id,
                    )
                elif status == "in_progress":
                    prefix = self.patterns._format_key(
                        "/projects/{project_id}/memory/tasks/in_progress/",
                        project_id=project_id,
                    )
                elif status == "completed":
                    prefix = self.patterns._format_key(
                        "/projects/{project_id}/memory/tasks/completed/",
                        project_id=project_id,
                    )
                elif status == "failed":
                    prefix = self.patterns._format_key(
                        "/projects/{project_id}/memory/tasks/failed/",
                        project_id=project_id,
                    )
                else:
                    continue

                keys = await self.mcp.list_keys(prefix)
                for key in keys:
                    task_data = await self.mcp.read(key)
                    if task_data:
                        task = json.loads(task_data)
                        if self._matches_filters(task, filters):
                            tasks.append(task)

            # Apply sorting
            if sort_by:
                reverse = sort_by.startswith("-")
                sort_field = sort_by.lstrip("-")
                tasks.sort(key=lambda t: t.get(sort_field, ""), reverse=reverse)

            # Apply pagination
            if offset > 0:
                tasks = tasks[offset:]
            if limit:
                tasks = tasks[:limit]

            return tasks

        except Exception:
            return []

    async def query_by_priority(
        self, project_id: str, priority: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query tasks by priority using priority indexes."""
        try:
            # Use priority indexes for efficient querying
            if priority == "high":
                prefix = self.patterns._format_key(
                    "/projects/{project_id}/memory/tasks/priority/high/",
                    project_id=project_id,
                )
            elif priority == "medium":
                prefix = self.patterns._format_key(
                    "/projects/{project_id}/memory/tasks/priority/medium/",
                    project_id=project_id,
                )
            elif priority == "low":
                prefix = self.patterns._format_key(
                    "/projects/{project_id}/memory/tasks/priority/low/",
                    project_id=project_id,
                )
            else:
                return []

            keys = await self.mcp.list_keys(prefix)
            task_refs = []

            for key in keys:
                ref_data = await self.mcp.read(key)
                if ref_data:
                    ref = json.loads(ref_data)
                    task_refs.append(ref)

            # Get full task data
            tasks = []
            for ref in task_refs:
                task_id = ref["task_id"]

                # Try to find the task in different status collections
                for task_status in ["pending", "in_progress", "completed", "failed"]:
                    if status and task_status != status:
                        continue

                    if task_status == "pending":
                        task_key = self.patterns._format_key(
                            self.schema.TASK_PENDING,
                            project_id=project_id,
                            task_id=task_id,
                        )
                    elif task_status == "in_progress":
                        task_key = self.patterns._format_key(
                            self.schema.TASK_IN_PROGRESS,
                            project_id=project_id,
                            task_id=task_id,
                        )
                    elif task_status == "completed":
                        task_key = self.patterns._format_key(
                            self.schema.TASK_COMPLETED,
                            project_id=project_id,
                            task_id=task_id,
                        )
                    elif task_status == "failed":
                        task_key = self.patterns._format_key(
                            self.schema.TASK_FAILED,
                            project_id=project_id,
                            task_id=task_id,
                        )

                    task_data = await self.mcp.read(task_key)
                    if task_data:
                        task = json.loads(task_data)
                        tasks.append(task)
                        break

            return tasks

        except Exception:
            return []

    async def create_cache_entry(
        self,
        project_id: str,
        query: Dict[str, Any],
        results: Any,
        ttl_seconds: int = 3600,
    ) -> str:
        """Cache query results for performance."""
        try:
            query_hash = self.patterns._get_query_hash(query)
            cache_key = self.patterns._format_key(
                self.schema.CACHE_QUERIES, project_id=project_id, query_hash=query_hash
            )

            cache_entry = {
                "query": query,
                "results": results,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now().timestamp() + ttl_seconds),
                "hit_count": 0,
            }

            await self.mcp.write(cache_key, json.dumps(cache_entry))
            return query_hash

        except Exception:
            return ""

    async def get_cached_results(
        self, project_id: str, query: Dict[str, Any]
    ) -> Optional[Any]:
        """Get cached query results if still valid."""
        try:
            query_hash = self.patterns._get_query_hash(query)
            cache_key = self.patterns._format_key(
                self.schema.CACHE_QUERIES, project_id=project_id, query_hash=query_hash
            )

            cache_data = await self.mcp.read(cache_key)
            if not cache_data:
                return None

            cache_entry = json.loads(cache_data)

            # Check if expired
            if datetime.now().timestamp() > cache_entry.get("expires_at", 0):
                await self.mcp.delete(cache_key)
                return None

            # Update hit count
            cache_entry["hit_count"] += 1
            await self.mcp.write(cache_key, json.dumps(cache_entry))

            return cache_entry["results"]

        except Exception:
            return None

    def _matches_filters(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if an item matches the given filters."""
        for key, value in filters.items():
            if key == "status":
                continue  # Handled separately

            item_value = item.get(key)

            if isinstance(value, list):
                if item_value not in value:
                    return False
            elif isinstance(value, dict):
                # Handle range queries like {"created_at": {"$gte": "2024-01-01"}}
                for op, op_value in value.items():
                    if op == "$gte" and item_value < op_value:
                        return False
                    elif op == "$lte" and item_value > op_value:
                        return False
                    elif op == "$gt" and item_value <= op_value:
                        return False
                    elif op == "$lt" and item_value >= op_value:
                        return False
                    elif op == "$eq" and item_value != op_value:
                        return False
                    elif op == "$ne" and item_value == op_value:
                        return False
            else:
                if item_value != value:
                    return False

        return True


class MemorySnapshot:
    """Create and manage memory snapshots for checkpoints."""

    def __init__(self, mcp: Union[LMDBMCP, AsyncMCPAdapter]):
        """Initialize with LMDB MCP instance or async adapter."""
        if isinstance(mcp, AsyncMCPAdapter):
            self.mcp = mcp
        else:
            # Assume any other object (including LMDBMCP or mocks) needs the adapter
            self.mcp = AsyncMCPAdapter(mcp)
        self.schema = MemorySchema()

    async def create_snapshot(
        self,
        project_id: str,
        snapshot_id: Optional[str] = None,
        snapshot_type: str = "full",
        base_snapshot_id: Optional[str] = None,
    ) -> str:
        """Create a memory snapshot (full or incremental)."""
        if not snapshot_id:
            snapshot_id = str(uuid.uuid4())

        snapshot_data = {
            "id": snapshot_id,
            "project_id": project_id,
            "type": snapshot_type,
            "created_at": datetime.now().isoformat(),
            "base_snapshot_id": base_snapshot_id,
            "keys": {},
            "metadata": {
                "version": "2.0.0",
                "schema_version": "1.0.0",
                "compression": "none",
            },
        }

        # Get all keys for the project
        project_prefix = f"/projects/{project_id}/"
        keys = await self.mcp.list_keys(project_prefix)

        if snapshot_type == "incremental" and base_snapshot_id:
            # For incremental snapshots, only store changed keys
            base_snapshot_key = self.schema.SNAPSHOTS_FULL.format(
                snapshot_id=base_snapshot_id
            )
            base_data = await self.mcp.read(base_snapshot_key)

            if not base_data:
                # Fallback to full snapshot if base not found
                snapshot_type = "full"
                snapshot_data["type"] = "full"
                snapshot_data["base_snapshot_id"] = None
            else:
                base_snapshot = json.loads(base_data)
                base_keys = base_snapshot.get("keys", {})

                # Only store keys that have changed
                for key in keys:
                    try:
                        current_value = await self.mcp.read(key)
                        if current_value:
                            base_value = base_keys.get(key)
                            if current_value != base_value:
                                snapshot_data["keys"][key] = current_value
                    except Exception:
                        continue

        if snapshot_type == "full":
            # Store all current values for full snapshot
            for key in keys:
                try:
                    value = await self.mcp.read(key)
                    if value:
                        snapshot_data["keys"][key] = value
                except Exception:
                    continue

        # Store snapshot using schema
        if snapshot_type == "full":
            snapshot_key = self.schema.SNAPSHOTS_FULL.format(snapshot_id=snapshot_id)
        else:
            snapshot_key = self.schema.SNAPSHOTS_INCREMENTAL.format(
                snapshot_id=snapshot_id
            )

        await self.mcp.write(snapshot_key, json.dumps(snapshot_data))

        # Update snapshot index
        await self._update_snapshot_index(snapshot_data)

        return snapshot_id

    async def _update_snapshot_index(self, snapshot_data: Dict[str, Any]) -> None:
        """Update the global snapshot index."""
        try:
            index_key = self.schema.SNAPSHOTS_INDEX
            index_data = await self.mcp.read(index_key)

            if index_data:
                index = json.loads(index_data)
            else:
                index = {"snapshots": [], "projects": {}}

            # Add snapshot to index
            snapshot_info = {
                "id": snapshot_data["id"],
                "project_id": snapshot_data["project_id"],
                "type": snapshot_data["type"],
                "created_at": snapshot_data["created_at"],
                "base_snapshot_id": snapshot_data.get("base_snapshot_id"),
                "key_count": len(snapshot_data["keys"]),
            }

            index["snapshots"].append(snapshot_info)

            # Update project index
            project_id = snapshot_data["project_id"]
            if project_id not in index["projects"]:
                index["projects"][project_id] = []
            index["projects"][project_id].append(snapshot_data["id"])

            # Keep only last 100 snapshots per project
            if len(index["projects"][project_id]) > 100:
                old_snapshot_id = index["projects"][project_id].pop(0)
                # Remove from global list
                index["snapshots"] = [
                    s for s in index["snapshots"] if s["id"] != old_snapshot_id
                ]

            await self.mcp.write(index_key, json.dumps(index))

        except Exception:
            pass  # Index update failure shouldn't prevent snapshot creation

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
            # Try both full and incremental snapshot keys
            full_key = self.schema.SNAPSHOTS_FULL.format(snapshot_id=snapshot_id)
            incremental_key = self.schema.SNAPSHOTS_INCREMENTAL.format(
                snapshot_id=snapshot_id
            )

            # Try to delete from both locations
            try:
                await self.mcp.delete(full_key)
            except Exception:
                pass

            try:
                await self.mcp.delete(incremental_key)
            except Exception:
                pass

            # Update snapshot index
            await self._remove_from_snapshot_index(snapshot_id)

            return True
        except Exception:
            return False

    async def _remove_from_snapshot_index(self, snapshot_id: str) -> None:
        """Remove snapshot from the global index."""
        try:
            index_key = self.schema.SNAPSHOTS_INDEX
            index_data = await self.mcp.read(index_key)

            if not index_data:
                return

            index = json.loads(index_data)

            # Remove from snapshots list
            index["snapshots"] = [
                s for s in index.get("snapshots", []) if s.get("id") != snapshot_id
            ]

            # Remove from project indexes
            for project_id, snapshot_list in index.get("projects", {}).items():
                if snapshot_id in snapshot_list:
                    index["projects"][project_id] = [
                        s for s in snapshot_list if s != snapshot_id
                    ]

            await self.mcp.write(index_key, json.dumps(index))

        except Exception:
            pass


class MemoryCleanup:
    """Comprehensive memory cleanup and garbage collection."""

    def __init__(self, memory_patterns: MemoryPatterns):
        """Initialize with MemoryPatterns instance."""
        self.patterns = memory_patterns
        self.mcp = memory_patterns.mcp
        self.schema = memory_patterns.schema

    async def cleanup_project(
        self, project_id: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """Comprehensive cleanup for a project."""
        options = options or {}
        stats = {
            "deleted_tasks": 0,
            "deleted_code_versions": 0,
            "deleted_logs": 0,
            "deleted_cache_entries": 0,
            "deleted_sessions": 0,
            "deleted_snapshots": 0,
            "reclaimed_space": 0,
        }

        try:
            # Cleanup old completed/failed tasks
            if options.get("cleanup_old_tasks", True):
                days_to_keep = options.get("task_retention_days", 30)
                task_stats = await self._cleanup_old_tasks(project_id, days_to_keep)
                stats["deleted_tasks"] = task_stats.get("deleted", 0)

            # Cleanup old code versions
            if options.get("cleanup_code_versions", True):
                versions_to_keep = options.get("code_versions_to_keep", 10)
                code_stats = await self._cleanup_code_versions(
                    project_id, versions_to_keep
                )
                stats["deleted_code_versions"] = code_stats.get("deleted", 0)

            # Cleanup old logs
            if options.get("cleanup_logs", True):
                log_retention_days = options.get("log_retention_days", 7)
                log_stats = await self._cleanup_old_logs(project_id, log_retention_days)
                stats["deleted_logs"] = log_stats.get("deleted", 0)

            # Cleanup expired cache entries
            if options.get("cleanup_cache", True):
                cache_stats = await self._cleanup_expired_cache(project_id)
                stats["deleted_cache_entries"] = cache_stats.get("deleted", 0)

            # Cleanup old sessions
            if options.get("cleanup_sessions", True):
                session_retention_days = options.get("session_retention_days", 30)
                session_stats = await self._cleanup_old_sessions(
                    project_id, session_retention_days
                )
                stats["deleted_sessions"] = session_stats.get("deleted", 0)

            # Cleanup old snapshots (keep last N)
            if options.get("cleanup_snapshots", True):
                snapshots_to_keep = options.get("snapshots_to_keep", 20)
                snapshot_stats = await self._cleanup_old_snapshots(
                    project_id, snapshots_to_keep
                )
                stats["deleted_snapshots"] = snapshot_stats.get("deleted", 0)

            return stats

        except Exception:
            return {"error": "Cleanup failed"}

    async def _cleanup_old_tasks(
        self, project_id: str, days_to_keep: int
    ) -> Dict[str, int]:
        """Cleanup old completed and failed tasks."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0

            for status in ["completed", "failed"]:
                if status == "completed":
                    prefix = f"/projects/{project_id}/memory/tasks/completed/"
                else:
                    prefix = f"/projects/{project_id}/memory/tasks/failed/"

                keys = await self.mcp.list_keys(prefix)

                for key in keys:
                    task_data = await self.mcp.read(key)
                    if task_data:
                        task = json.loads(task_data)

                        # Check completion/failure date
                        completion_date_field = f"{status}_at"
                        completion_date_str = task.get(completion_date_field)

                        if completion_date_str:
                            try:
                                completion_date = datetime.fromisoformat(
                                    completion_date_str
                                ).timestamp()
                                if completion_date < cutoff_date:
                                    # Delete task
                                    await self.mcp.delete(key)

                                    # Delete from index
                                    task_id = task.get("id")
                                    if task_id:
                                        index_key = self.patterns._format_key(
                                            self.schema.TASK_INDEX,
                                            project_id=project_id,
                                            task_id=task_id,
                                        )
                                        await self.mcp.delete(index_key)

                                    deleted_count += 1
                            except (ValueError, TypeError):
                                continue

            return {"deleted": deleted_count}

        except Exception:
            return {"deleted": 0}

    async def _cleanup_code_versions(
        self, project_id: str, versions_to_keep: int
    ) -> Dict[str, int]:
        """Cleanup old code versions, keeping the latest N versions per file."""
        try:
            deleted_count = 0

            # Get all code files
            index_prefix = f"/projects/{project_id}/memory/code/index/"
            index_keys = await self.mcp.list_keys(index_prefix)

            for index_key in index_keys:
                index_data = await self.mcp.read(index_key)
                if index_data:
                    file_index = json.loads(index_data)
                    file_path = file_index.get("file_path")

                    if file_path:
                        file_path_hash = self.patterns._get_file_path_hash(file_path)

                        # Get versions for this file
                        versions_key = self.patterns._format_key(
                            self.schema.CODE_VERSIONS,
                            project_id=project_id,
                            file_path_hash=file_path_hash,
                        )

                        versions_data = await self.mcp.read(versions_key)
                        if versions_data:
                            versions = json.loads(versions_data)

                            # Sort by timestamp and keep only latest N
                            if (
                                isinstance(versions, list)
                                and len(versions) > versions_to_keep
                            ):
                                # Sort by timestamp (newest first)
                                versions.sort(
                                    key=lambda v: v.get("timestamp", ""), reverse=True
                                )

                                # Keep only the latest versions
                                versions_to_delete = versions[versions_to_keep:]
                                versions_to_keep_list = versions[:versions_to_keep]

                                # Update versions list
                                await self.mcp.write(
                                    versions_key, json.dumps(versions_to_keep_list)
                                )

                                deleted_count += len(versions_to_delete)

            return {"deleted": deleted_count}

        except Exception:
            return {"deleted": 0}

    async def _cleanup_old_logs(
        self, project_id: str, retention_days: int
    ) -> Dict[str, int]:
        """Cleanup old log entries."""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_date_str = cutoff_date.strftime("%Y-%m-%d")
            deleted_count = 0

            # Cleanup system logs
            system_prefix = f"/projects/{project_id}/logs/system/"
            system_keys = await self.mcp.list_keys(system_prefix)

            for key in system_keys:
                # Extract date from key (assuming format includes date)
                key_parts = key.split("/")
                if len(key_parts) > 0:
                    date_part = key_parts[-1]  # Last part should be date
                    if date_part < cutoff_date_str:
                        await self.mcp.delete(key)
                        deleted_count += 1

            # Cleanup agent logs
            for agent_type in ["supervisor", "coder", "adversary"]:
                agent_prefix = f"/projects/{project_id}/logs/agents/{agent_type}/"
                agent_keys = await self.mcp.list_keys(agent_prefix)

                for key in agent_keys:
                    key_parts = key.split("/")
                    if len(key_parts) > 0:
                        date_part = key_parts[-1]
                        if date_part < cutoff_date_str:
                            await self.mcp.delete(key)
                            deleted_count += 1

            # Cleanup error logs
            error_prefix = f"/projects/{project_id}/logs/errors/"
            error_keys = await self.mcp.list_keys(error_prefix)

            for key in error_keys:
                key_parts = key.split("/")
                if len(key_parts) > 0:
                    date_part = key_parts[-1]
                    if date_part < cutoff_date_str:
                        await self.mcp.delete(key)
                        deleted_count += 1

            return {"deleted": deleted_count}

        except Exception:
            return {"deleted": 0}

    async def _cleanup_expired_cache(self, project_id: str) -> Dict[str, int]:
        """Cleanup expired cache entries."""
        try:
            deleted_count = 0
            current_time = datetime.now().timestamp()

            # Cleanup query cache
            query_prefix = f"/projects/{project_id}/cache/queries/"
            query_keys = await self.mcp.list_keys(query_prefix)

            for key in query_keys:
                cache_data = await self.mcp.read(key)
                if cache_data:
                    cache_entry = json.loads(cache_data)
                    expires_at = cache_entry.get("expires_at", 0)

                    if current_time > expires_at:
                        await self.mcp.delete(key)
                        deleted_count += 1

            # Cleanup computation cache
            comp_prefix = f"/projects/{project_id}/cache/computations/"
            comp_keys = await self.mcp.list_keys(comp_prefix)

            for key in comp_keys:
                cache_data = await self.mcp.read(key)
                if cache_data:
                    cache_entry = json.loads(cache_data)
                    expires_at = cache_entry.get("expires_at", 0)

                    if current_time > expires_at:
                        await self.mcp.delete(key)
                        deleted_count += 1

            return {"deleted": deleted_count}

        except Exception:
            return {"deleted": 0}

    async def _cleanup_old_sessions(
        self, project_id: str, retention_days: int
    ) -> Dict[str, int]:
        """Cleanup old session data."""
        try:
            cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
            deleted_count = 0

            sessions_prefix = f"/projects/{project_id}/sessions/"
            session_keys = await self.mcp.list_keys(sessions_prefix)

            # Group keys by session ID
            session_groups = {}
            for key in session_keys:
                key_parts = key.split("/")
                if len(key_parts) >= 5:  # /projects/{id}/sessions/{session_id}/...
                    session_id = key_parts[4]
                    if session_id not in session_groups:
                        session_groups[session_id] = []
                    session_groups[session_id].append(key)

            # Check each session
            for session_id, keys in session_groups.items():
                metadata_key = f"/projects/{project_id}/sessions/{session_id}/metadata"

                if metadata_key in keys:
                    metadata = await self.mcp.read(metadata_key)
                    if metadata:
                        session_data = json.loads(metadata)
                        created_at_str = session_data.get("created_at")

                        if created_at_str:
                            try:
                                created_at = datetime.fromisoformat(
                                    created_at_str
                                ).timestamp()
                                if created_at < cutoff_date:
                                    # Delete all keys for this session
                                    for key in keys:
                                        await self.mcp.delete(key)
                                        deleted_count += 1
                            except (ValueError, TypeError):
                                continue

            return {"deleted": deleted_count}

        except Exception:
            return {"deleted": 0}

    async def _cleanup_old_snapshots(
        self, project_id: str, snapshots_to_keep: int
    ) -> Dict[str, int]:
        """Cleanup old snapshots, keeping the latest N."""
        try:
            deleted_count = 0

            # Get snapshot index
            index_key = self.schema.SNAPSHOTS_INDEX
            index_data = await self.mcp.read(index_key)

            if not index_data:
                return {"deleted": 0}

            index = json.loads(index_data)
            project_snapshots = []

            # Get snapshots for this project
            for snapshot in index.get("snapshots", []):
                if snapshot.get("project_id") == project_id:
                    project_snapshots.append(snapshot)

            # Sort by creation date (newest first)
            project_snapshots.sort(key=lambda s: s.get("created_at", ""), reverse=True)

            # Delete old snapshots
            if len(project_snapshots) > snapshots_to_keep:
                snapshots_to_delete = project_snapshots[snapshots_to_keep:]

                for snapshot in snapshots_to_delete:
                    snapshot_id = snapshot.get("id")
                    if snapshot_id:
                        # Use MemorySnapshot to delete properly
                        memory_snapshot = MemorySnapshot(self.mcp)
                        if await memory_snapshot.delete_snapshot(snapshot_id):
                            deleted_count += 1

            return {"deleted": deleted_count}

        except Exception:
            return {"deleted": 0}

    async def get_cleanup_recommendations(self, project_id: str) -> Dict[str, Any]:
        """Analyze project and recommend cleanup actions."""
        try:
            recommendations = {"total_size_estimate": 0, "recommendations": []}

            # Analyze tasks
            completed_prefix = f"/projects/{project_id}/memory/tasks/completed/"
            completed_keys = await self.mcp.list_keys(completed_prefix)

            failed_prefix = f"/projects/{project_id}/memory/tasks/failed/"
            failed_keys = await self.mcp.list_keys(failed_prefix)

            old_tasks_count = len(completed_keys) + len(failed_keys)
            if old_tasks_count > 100:
                recommendations["recommendations"].append(
                    {
                        "type": "cleanup_old_tasks",
                        "priority": "medium",
                        "description": f"Found {old_tasks_count} completed/failed tasks that could be cleaned up",
                        "estimated_savings": old_tasks_count * 1024,  # Rough estimate
                    }
                )

            # Analyze cache
            cache_prefix = f"/projects/{project_id}/cache/"
            cache_keys = await self.mcp.list_keys(cache_prefix)

            if len(cache_keys) > 50:
                recommendations["recommendations"].append(
                    {
                        "type": "cleanup_cache",
                        "priority": "low",
                        "description": f"Found {len(cache_keys)} cache entries, some may be expired",
                        "estimated_savings": len(cache_keys) * 512,
                    }
                )

            # Analyze snapshots
            index_key = self.schema.SNAPSHOTS_INDEX
            index_data = await self.mcp.read(index_key)

            if index_data:
                index = json.loads(index_data)
                project_snapshots = [
                    s
                    for s in index.get("snapshots", [])
                    if s.get("project_id") == project_id
                ]

                if len(project_snapshots) > 20:
                    recommendations["recommendations"].append(
                        {
                            "type": "cleanup_snapshots",
                            "priority": "medium",
                            "description": f"Found {len(project_snapshots)} snapshots, consider keeping only recent ones",
                            "estimated_savings": (len(project_snapshots) - 20) * 10240,
                        }
                    )

            # Calculate total estimated savings
            total_savings = sum(
                r.get("estimated_savings", 0)
                for r in recommendations["recommendations"]
            )
            recommendations["total_size_estimate"] = total_savings

            return recommendations

        except Exception:
            return {"recommendations": [], "error": "Analysis failed"}


class ContextPointer:
    """Pointer to content stored in LMDB for Context-as-a-Service."""

    def __init__(
        self,
        pointer_id: str,
        content_key: str,
        content_type: str = "text",
        size_bytes: int = 0,
        checksum: Optional[str] = None,
    ):
        self.pointer_id = pointer_id
        self.content_key = content_key
        self.content_type = content_type
        self.size_bytes = size_bytes
        self.checksum = checksum
        self.created_at = datetime.now().isoformat()
        self.last_accessed = None
        self.access_count = 0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pointer_id": self.pointer_id,
            "content_key": self.content_key,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextPointer":
        """Create from dictionary representation."""
        pointer = cls(
            data["pointer_id"],
            data["content_key"],
            data.get("content_type", "text"),
            data.get("size_bytes", 0),
            data.get("checksum"),
        )
        pointer.created_at = data.get("created_at", pointer.created_at)
        pointer.last_accessed = data.get("last_accessed")
        pointer.access_count = data.get("access_count", 0)
        pointer.metadata = data.get("metadata", {})
        return pointer


class ContextChunk:
    """Chunk of large content for efficient Context-as-a-Service."""

    def __init__(
        self,
        chunk_id: str,
        parent_pointer_id: str,
        chunk_index: int,
        content: str,
        chunk_type: str = "text",
    ):
        self.chunk_id = chunk_id
        self.parent_pointer_id = parent_pointer_id
        self.chunk_index = chunk_index
        self.content = content
        self.chunk_type = chunk_type
        self.size_bytes = len(content.encode("utf-8"))
        self.created_at = datetime.now().isoformat()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chunk_id": self.chunk_id,
            "parent_pointer_id": self.parent_pointer_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "chunk_type": self.chunk_type,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextChunk":
        """Create from dictionary representation."""
        chunk = cls(
            data["chunk_id"],
            data["parent_pointer_id"],
            data["chunk_index"],
            data["content"],
            data.get("chunk_type", "text"),
        )
        chunk.created_at = data.get("created_at", chunk.created_at)
        chunk.metadata = data.get("metadata", {})
        return chunk


class ContextAsAService:
    """Context-as-a-Service optimizations for APEX v2.0.

    This class provides efficient management of large content for Workers,
    implementing pointer-based access patterns to minimize token usage.
    """

    def __init__(self, memory_patterns: MemoryPatterns):
        """Initialize Context-as-a-Service."""
        self.memory = memory_patterns
        self.mcp = memory_patterns.mcp
        self.schema = memory_patterns.schema

        # Configuration
        self.max_chunk_size = 4000  # Max characters per chunk
        self.max_context_window = 16000  # Total context limit for workers
        self.compression_threshold = 10000  # Compress content larger than this
        self.summary_threshold = 20000  # Create summaries for content larger than this

    async def store_large_content(
        self,
        project_id: str,
        content: str,
        content_type: str = "text",
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store large content and return a pointer ID.

        Large content is automatically chunked and can be retrieved via pointer.
        """
        try:
            import hashlib

            # Generate content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            pointer_id = f"ptr-{content_hash[:16]}"

            # Check if content already exists
            existing_pointer = await self._get_context_pointer(project_id, pointer_id)
            if existing_pointer:
                # Update access count and return existing pointer
                existing_pointer.access_count += 1
                existing_pointer.last_accessed = datetime.now().isoformat()
                await self._store_context_pointer(project_id, existing_pointer)
                return pointer_id

            # Create new context pointer
            pointer = ContextPointer(
                pointer_id=pointer_id,
                content_key=f"/projects/{project_id}/content/{content_hash}",
                content_type=content_type,
                size_bytes=len(content.encode("utf-8")),
                checksum=content_hash,
            )
            pointer.metadata = metadata or {}
            pointer.metadata["category"] = category

            # Store full content
            await self.mcp.write(pointer.content_key, content)

            # Create chunks if content is large
            if len(content) > self.max_chunk_size:
                await self._create_content_chunks(project_id, pointer, content)

            # Create summary if content is very large
            if len(content) > self.summary_threshold:
                await self._create_content_summary(project_id, pointer, content)

            # Store pointer
            await self._store_context_pointer(project_id, pointer)

            # Update category index
            await self._update_category_index(project_id, category, pointer_id)

            return pointer_id

        except Exception as e:
            logging.getLogger(__name__).error(f"Error storing large content: {e}")
            return ""

    async def get_content_by_pointer(
        self, project_id: str, pointer_id: str, max_size: Optional[int] = None
    ) -> Optional[str]:
        """Get content by pointer ID, respecting size limits."""
        try:
            pointer = await self._get_context_pointer(project_id, pointer_id)
            if not pointer:
                return None

            # Update access tracking
            pointer.access_count += 1
            pointer.last_accessed = datetime.now().isoformat()
            await self._store_context_pointer(project_id, pointer)

            # Check size limits
            if max_size and pointer.size_bytes > max_size:
                # Return summary if available and under size limit
                summary = await self._get_content_summary(project_id, pointer.checksum)
                if summary and len(summary) <= max_size:
                    return summary

                # Return first chunk if under size limit
                first_chunk = await self._get_content_chunk(project_id, pointer_id, 0)
                if first_chunk and len(first_chunk.content) <= max_size:
                    return (
                        first_chunk.content
                        + "\n\n[Content truncated - use full pointer for complete content]"
                    )

                return f"[Content too large: {pointer.size_bytes} bytes. Use chunked access or request summary.]"

            # Return full content
            content = await self.mcp.read(pointer.content_key)
            return content

        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting content by pointer: {e}")
            return None

    async def get_content_chunks(
        self,
        project_id: str,
        pointer_id: str,
        start_chunk: int = 0,
        max_chunks: int = 5,
    ) -> List[ContextChunk]:
        """Get content chunks for large content."""
        try:
            chunks = []
            for chunk_index in range(start_chunk, start_chunk + max_chunks):
                chunk = await self._get_content_chunk(
                    project_id, pointer_id, chunk_index
                )
                if chunk:
                    chunks.append(chunk)
                else:
                    break  # No more chunks

            return chunks

        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting content chunks: {e}")
            return []

    async def get_content_summary(
        self, project_id: str, pointer_id: str
    ) -> Optional[str]:
        """Get summary of large content."""
        try:
            pointer = await self._get_context_pointer(project_id, pointer_id)
            if not pointer:
                return None

            return await self._get_content_summary(project_id, pointer.checksum)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting content summary: {e}")
            return None

    async def list_pointers_by_category(
        self, project_id: str, category: str
    ) -> List[str]:
        """List all pointer IDs in a category."""
        try:
            index_key = self.schema.CONTEXT_INDEX.format(
                project_id=project_id, category=category
            )
            index_data = await self.mcp.read(index_key)

            if index_data:
                index = json.loads(index_data)
                return index.get("pointer_ids", [])

            return []

        except Exception as e:
            logging.getLogger(__name__).error(
                f"Error listing pointers by category: {e}"
            )
            return []

    async def optimize_context_for_worker(
        self,
        project_id: str,
        pointer_ids: List[str],
        max_context_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Optimize context for worker consumption.

        Returns the best combination of content that fits within context limits.
        """
        try:
            max_size = max_context_size or self.max_context_window
            optimized_context = {
                "full_content": {},
                "summaries": {},
                "chunks": {},
                "truncated": [],
                "total_size": 0,
            }

            # Get pointer information
            pointers = []
            for pointer_id in pointer_ids:
                pointer = await self._get_context_pointer(project_id, pointer_id)
                if pointer:
                    pointers.append(pointer)

            # Sort by size (smallest first for better packing)
            pointers.sort(key=lambda p: p.size_bytes)

            current_size = 0

            for pointer in pointers:
                # Try to fit full content
                if current_size + pointer.size_bytes <= max_size:
                    content = await self.mcp.read(pointer.content_key)
                    if content:
                        optimized_context["full_content"][pointer.pointer_id] = content
                        current_size += pointer.size_bytes
                        optimized_context["total_size"] = current_size
                        continue

                # Try to fit summary
                summary = await self._get_content_summary(project_id, pointer.checksum)
                if summary and current_size + len(summary) <= max_size:
                    optimized_context["summaries"][pointer.pointer_id] = summary
                    current_size += len(summary)
                    optimized_context["total_size"] = current_size
                    continue

                # Try to fit first chunk
                first_chunk = await self._get_content_chunk(
                    project_id, pointer.pointer_id, 0
                )
                if first_chunk and current_size + first_chunk.size_bytes <= max_size:
                    optimized_context["chunks"][pointer.pointer_id] = [
                        first_chunk.to_dict()
                    ]
                    current_size += first_chunk.size_bytes
                    optimized_context["total_size"] = current_size
                    continue

                # Content doesn't fit
                optimized_context["truncated"].append(
                    {
                        "pointer_id": pointer.pointer_id,
                        "size_bytes": pointer.size_bytes,
                        "reason": "exceeds_context_limit",
                    }
                )

            return optimized_context

        except Exception as e:
            logging.getLogger(__name__).error(f"Error optimizing context: {e}")
            return {"error": str(e)}

    async def cleanup_unused_content(
        self, project_id: str, days_unused: int = 30
    ) -> int:
        """Clean up content that hasn't been accessed recently."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_unused * 24 * 60 * 60)
            deleted_count = 0

            # Get all pointers
            pointers_prefix = f"/projects/{project_id}/context/pointers/"
            pointer_keys = await self.mcp.list_keys(pointers_prefix)

            for key in pointer_keys:
                try:
                    pointer_data = await self.mcp.read(key)
                    if pointer_data:
                        pointer = ContextPointer.from_dict(json.loads(pointer_data))

                        # Check last access time
                        if pointer.last_accessed:
                            last_access = datetime.fromisoformat(
                                pointer.last_accessed
                            ).timestamp()
                            if last_access < cutoff_date:
                                await self._delete_content_and_pointer(
                                    project_id, pointer
                                )
                                deleted_count += 1
                        elif pointer.access_count == 0:
                            # Never accessed content older than cutoff
                            created = datetime.fromisoformat(
                                pointer.created_at
                            ).timestamp()
                            if created < cutoff_date:
                                await self._delete_content_and_pointer(
                                    project_id, pointer
                                )
                                deleted_count += 1
                except:
                    continue

            return deleted_count

        except Exception as e:
            logging.getLogger(__name__).error(f"Error cleaning up unused content: {e}")
            return 0

    # Private helper methods

    async def _get_context_pointer(
        self, project_id: str, pointer_id: str
    ) -> Optional[ContextPointer]:
        """Get context pointer by ID."""
        try:
            pointer_key = self.schema.CONTEXT_POINTERS.format(
                project_id=project_id, pointer_id=pointer_id
            )
            data = await self.mcp.read(pointer_key)
            if data:
                return ContextPointer.from_dict(json.loads(data))
            return None
        except:
            return None

    async def _store_context_pointer(
        self, project_id: str, pointer: ContextPointer
    ) -> None:
        """Store context pointer."""
        pointer_key = self.schema.CONTEXT_POINTERS.format(
            project_id=project_id, pointer_id=pointer.pointer_id
        )
        await self.mcp.write(pointer_key, json.dumps(pointer.to_dict()))

    async def _create_content_chunks(
        self, project_id: str, pointer: ContextPointer, content: str
    ) -> None:
        """Create chunks for large content."""
        chunk_size = self.max_chunk_size
        chunks = [
            content[i : i + chunk_size] for i in range(0, len(content), chunk_size)
        ]

        for chunk_index, chunk_content in enumerate(chunks):
            chunk_id = f"{pointer.pointer_id}-chunk-{chunk_index}"
            chunk = ContextChunk(
                chunk_id=chunk_id,
                parent_pointer_id=pointer.pointer_id,
                chunk_index=chunk_index,
                content=chunk_content,
                chunk_type=pointer.content_type,
            )

            chunk_key = self.schema.CONTEXT_CHUNKS.format(
                project_id=project_id, chunk_id=chunk_id
            )
            await self.mcp.write(chunk_key, json.dumps(chunk.to_dict()))

    async def _get_content_chunk(
        self, project_id: str, pointer_id: str, chunk_index: int
    ) -> Optional[ContextChunk]:
        """Get a specific content chunk."""
        try:
            chunk_id = f"{pointer_id}-chunk-{chunk_index}"
            chunk_key = self.schema.CONTEXT_CHUNKS.format(
                project_id=project_id, chunk_id=chunk_id
            )
            data = await self.mcp.read(chunk_key)
            if data:
                return ContextChunk.from_dict(json.loads(data))
            return None
        except:
            return None

    async def _create_content_summary(
        self, project_id: str, pointer: ContextPointer, content: str
    ) -> None:
        """Create summary for very large content."""
        try:
            # Simple extractive summary - take first and last portions
            # In production, this could use an LLM API for better summarization
            max_summary_length = 2000

            if len(content) <= max_summary_length:
                summary = content
            else:
                # Take first 1000 and last 500 characters with separator
                first_part = content[:1000]
                last_part = content[-500:]
                summary = f"{first_part}\n\n[... content truncated ...]\n\n{last_part}"

            summary_key = self.schema.CONTEXT_SUMMARIES.format(
                project_id=project_id, content_hash=pointer.checksum
            )
            await self.mcp.write(summary_key, summary)

        except Exception as e:
            logging.getLogger(__name__).error(f"Error creating content summary: {e}")

    async def _get_content_summary(
        self, project_id: str, content_hash: str
    ) -> Optional[str]:
        """Get content summary by hash."""
        try:
            summary_key = self.schema.CONTEXT_SUMMARIES.format(
                project_id=project_id, content_hash=content_hash
            )
            return await self.mcp.read(summary_key)
        except:
            return None

    async def _update_category_index(
        self, project_id: str, category: str, pointer_id: str
    ) -> None:
        """Update category index with new pointer."""
        try:
            index_key = self.schema.CONTEXT_INDEX.format(
                project_id=project_id, category=category
            )

            try:
                index_data = await self.mcp.read(index_key)
                index = json.loads(index_data) if index_data else {"pointer_ids": []}
            except:
                index = {"pointer_ids": []}

            if pointer_id not in index["pointer_ids"]:
                index["pointer_ids"].append(pointer_id)
                index["updated_at"] = datetime.now().isoformat()
                await self.mcp.write(index_key, json.dumps(index))
        except Exception as e:
            logging.getLogger(__name__).error(f"Error updating category index: {e}")

    async def _delete_content_and_pointer(
        self, project_id: str, pointer: ContextPointer
    ) -> None:
        """Delete content, chunks, summary, and pointer."""
        try:
            # Delete main content
            await self.mcp.delete(pointer.content_key)

            # Delete chunks
            chunk_index = 0
            while True:
                chunk_id = f"{pointer.pointer_id}-chunk-{chunk_index}"
                chunk_key = self.schema.CONTEXT_CHUNKS.format(
                    project_id=project_id, chunk_id=chunk_id
                )

                if await self.mcp.read(chunk_key):
                    await self.mcp.delete(chunk_key)
                    chunk_index += 1
                else:
                    break

            # Delete summary
            summary_key = self.schema.CONTEXT_SUMMARIES.format(
                project_id=project_id, content_hash=pointer.checksum
            )
            await self.mcp.delete(summary_key)

            # Delete pointer
            pointer_key = self.schema.CONTEXT_POINTERS.format(
                project_id=project_id, pointer_id=pointer.pointer_id
            )
            await self.mcp.delete(pointer_key)

        except Exception as e:
            logging.getLogger(__name__).error(
                f"Error deleting content and pointer: {e}"
            )
