"""TaskBriefing system for APEX v2.0.

The TaskBriefing is the core API contract between the Supervisor and Workers.
It provides a well-defined JSON schema for task specification, context pointers,
and deliverable requirements.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TaskRole(Enum):
    """Roles that can be assigned to tasks."""

    CODER = "Coder"
    ADVERSARY = "Adversary"
    SUPERVISOR = "Supervisor"


class TaskStatus(Enum):
    """Task lifecycle status."""

    PENDING_CREATION = "pending_creation"
    PENDING_INVOCATION = "pending_invocation"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DeliverableType(Enum):
    """Types of deliverables a task can produce."""

    CODE = "code"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    DOCUMENTATION = "documentation"
    STATUS_REPORT = "status_report"
    ISSUE_REPORT = "issue_report"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    ARTIFACT = "artifact"


class ContextPointer(BaseModel):
    """A pointer to context data stored in LMDB."""

    key: str = Field(..., description="LMDB key where the content is stored")
    description: str = Field(
        ..., description="Human-readable description of the content"
    )
    content_type: str = Field(
        default="text", description="Type of content (text, json, code, etc.)"
    )
    size_estimate: Optional[int] = Field(None, description="Estimated size in bytes")
    last_updated: Optional[str] = Field(
        None, description="ISO timestamp of last update"
    )

    @field_validator("key")
    @classmethod
    def validate_key_format(cls, v):
        """Ensure key follows LMDB schema patterns."""
        if not v.startswith("/"):
            raise ValueError("LMDB key must start with '/'")
        return v


class Deliverable(BaseModel):
    """Specification for a required task deliverable."""

    type: DeliverableType = Field(..., description="Type of deliverable")
    description: str = Field(..., description="What should be delivered")
    output_key: str = Field(..., description="LMDB key where output should be stored")
    required: bool = Field(
        default=True, description="Whether this deliverable is required"
    )
    validation_criteria: Optional[List[str]] = Field(
        None, description="Criteria for validating the deliverable"
    )
    format_requirements: Optional[Dict[str, Any]] = Field(
        None, description="Format-specific requirements"
    )

    @field_validator("output_key")
    @classmethod
    def validate_output_key_format(cls, v):
        """Ensure output key follows task output patterns."""
        if not v.startswith("/tasks/outputs/"):
            raise ValueError("Output key must start with '/tasks/outputs/'")
        return v


class TaskDependency(BaseModel):
    """Dependency relationship between tasks."""

    task_id: str = Field(..., description="ID of the dependent task")
    dependency_type: str = Field(
        default="blocks", description="Type of dependency (blocks, enables, informs)"
    )
    required_status: TaskStatus = Field(
        default=TaskStatus.COMPLETED, description="Required status of dependency"
    )
    description: Optional[str] = Field(
        None, description="Description of the dependency relationship"
    )


class TaskBriefing(BaseModel):
    """Core TaskBriefing schema for v2.0 architecture.

    This is the complete API contract between Supervisor and Workers.
    """

    # Core identification
    task_id: str = Field(
        default_factory=lambda: (
            f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
        )
    )
    role_required: TaskRole = Field(
        ..., description="Role required to execute this task"
    )
    objective: str = Field(..., description="Clear, specific objective for this task")

    # Context and input data
    context_pointers: Dict[str, ContextPointer] = Field(
        default_factory=dict, description="Named pointers to context data in LMDB"
    )

    # Required outputs
    deliverables: List[Deliverable] = Field(
        default_factory=list, description="List of required deliverables"
    )

    # Task metadata
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    estimated_duration: Optional[int] = Field(
        None, description="Estimated duration in minutes"
    )
    max_duration: Optional[int] = Field(
        None, description="Maximum allowed duration in minutes"
    )

    # Dependencies and relationships
    dependencies: List[TaskDependency] = Field(
        default_factory=list, description="Tasks this task depends on"
    )
    blocks: List[str] = Field(
        default_factory=list, description="Task IDs that this task blocks"
    )

    # Status and lifecycle
    status: TaskStatus = Field(default=TaskStatus.PENDING_CREATION)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = Field(None)
    completed_at: Optional[str] = Field(None)
    failed_at: Optional[str] = Field(None)

    # Worker assignment and execution
    assigned_worker_type: Optional[str] = Field(
        None, description="Type of worker assigned (Worker or Utility)"
    )
    assigned_worker_id: Optional[str] = Field(
        None, description="ID of specific worker instance"
    )
    execution_context: Optional[Dict[str, Any]] = Field(
        None, description="Worker-specific execution context"
    )

    # Quality and constraints
    quality_criteria: List[str] = Field(
        default_factory=list, description="Quality criteria for task completion"
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict, description="Constraints and limitations"
    )

    # Results and feedback
    results: Optional[Dict[str, Any]] = Field(
        None, description="Task execution results"
    )
    error_info: Optional[Dict[str, Any]] = Field(
        None, description="Error information if task failed"
    )
    feedback: List[Dict[str, Any]] = Field(
        default_factory=list, description="Feedback from reviews or validation"
    )

    # Supervisor orchestration
    orchestration_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata for Supervisor orchestration"
    )

    def update_status(
        self, new_status: TaskStatus, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update task status with timestamp."""
        self.status = new_status
        self.updated_at = datetime.now().isoformat()

        if new_status == TaskStatus.IN_PROGRESS:
            self.started_at = self.updated_at
        elif new_status == TaskStatus.COMPLETED:
            self.completed_at = self.updated_at
        elif new_status == TaskStatus.FAILED:
            self.failed_at = self.updated_at

        if metadata:
            self.orchestration_metadata.update(metadata)

    def add_context_pointer(
        self, name: str, key: str, description: str, **kwargs
    ) -> None:
        """Add a context pointer to the briefing."""
        self.context_pointers[name] = ContextPointer(
            key=key, description=description, **kwargs
        )

    def add_deliverable(
        self,
        deliverable_type: DeliverableType,
        description: str,
        output_key: str,
        **kwargs,
    ) -> None:
        """Add a deliverable requirement to the briefing."""
        self.deliverables.append(
            Deliverable(
                type=deliverable_type,
                description=description,
                output_key=output_key,
                **kwargs,
            )
        )

    def add_dependency(
        self,
        task_id: str,
        dependency_type: str = "blocks",
        required_status: TaskStatus = TaskStatus.COMPLETED,
        description: Optional[str] = None,
    ) -> None:
        """Add a task dependency."""
        self.dependencies.append(
            TaskDependency(
                task_id=task_id,
                dependency_type=dependency_type,
                required_status=required_status,
                description=description,
            )
        )

    def is_ready_to_execute(self, completed_tasks: List[str]) -> bool:
        """Check if all dependencies are satisfied for execution."""
        for dep in self.dependencies:
            if dep.dependency_type == "blocks" and dep.task_id not in completed_tasks:
                return False
        return True

    def get_lmdb_key(self) -> str:
        """Get the LMDB key where this briefing should be stored."""
        return f"/tasks/briefings/{self.task_id}"

    def get_output_prefix(self) -> str:
        """Get the LMDB key prefix for all task outputs."""
        return f"/tasks/outputs/{self.task_id}/"

    def to_worker_prompt(self) -> str:
        """Generate the minimal prompt for worker invocation."""
        return f"""You are an expert {self.role_required.value} agent in APEX v2.0.

Your mission is to execute a single, well-defined task with complete autonomy.

INSTRUCTIONS:
1. Read your complete task briefing from LMDB key: {self.get_lmdb_key()}
2. Use the 'mcp__lmdb__read' tool to access the briefing and context pointers
3. Execute the task according to the objective and requirements
4. Create all required deliverables at the specified output keys
5. Use 'mcp__lmdb__write' tool to store your deliverables
6. Announce 'TASK COMPLETE' when finished

CRITICAL: You must read the briefing first to understand your specific
objective, context, and deliverable requirements. Do not assume anything."""


class TaskBriefingManager:
    """Manager for TaskBriefing operations with LMDB integration."""

    def __init__(self, memory_patterns):
        """Initialize with MemoryPatterns instance."""
        self.memory = memory_patterns
        self.mcp = memory_patterns.mcp

    async def create_briefing(self, project_id: str, briefing: TaskBriefing) -> str:
        """Create a new task briefing in LMDB."""
        briefing_key = f"/projects/{project_id}{briefing.get_lmdb_key()}"

        # Store the briefing
        await self.mcp.write(briefing_key, briefing.model_dump_json())

        # Update task index
        index_key = f"/projects/{project_id}/tasks/briefings/index/{briefing.task_id}"
        index_data = {
            "task_id": briefing.task_id,
            "role_required": briefing.role_required.value,
            "status": briefing.status.value,
            "priority": briefing.priority.value,
            "created_at": briefing.created_at,
            "objective_summary": (
                briefing.objective[:100] + "..."
                if len(briefing.objective) > 100
                else briefing.objective
            ),
        }
        await self.mcp.write(index_key, json.dumps(index_data))

        return briefing.task_id

    async def get_briefing(
        self, project_id: str, task_id: str
    ) -> Optional[TaskBriefing]:
        """Retrieve a task briefing from LMDB."""
        briefing_key = f"/projects/{project_id}/tasks/briefings/{task_id}"

        data = await self.mcp.read(briefing_key)
        if not data:
            return None

        return TaskBriefing.model_validate_json(data)

    async def update_briefing(self, project_id: str, briefing: TaskBriefing) -> bool:
        """Update an existing task briefing."""
        try:
            briefing.updated_at = datetime.now().isoformat()
            briefing_key = f"/projects/{project_id}{briefing.get_lmdb_key()}"

            await self.mcp.write(briefing_key, briefing.model_dump_json())

            # Update index
            index_key = (
                f"/projects/{project_id}/tasks/briefings/index/{briefing.task_id}"
            )
            index_data = {
                "task_id": briefing.task_id,
                "role_required": briefing.role_required.value,
                "status": briefing.status.value,
                "priority": briefing.priority.value,
                "created_at": briefing.created_at,
                "updated_at": briefing.updated_at,
                "objective_summary": (
                    briefing.objective[:100] + "..."
                    if len(briefing.objective) > 100
                    else briefing.objective
                ),
            }
            await self.mcp.write(index_key, json.dumps(index_data))

            return True
        except Exception:
            return False

    async def list_briefings(
        self,
        project_id: str,
        status: Optional[TaskStatus] = None,
        role: Optional[TaskRole] = None,
    ) -> List[Dict[str, Any]]:
        """List task briefings with optional filtering."""
        try:
            index_prefix = f"/projects/{project_id}/tasks/briefings/index/"
            keys = await self.mcp.list_keys(index_prefix)

            briefings = []
            for key in keys:
                data = await self.mcp.read(key)
                if data:
                    briefing_info = json.loads(data)

                    # Apply filters
                    if status and briefing_info.get("status") != status.value:
                        continue
                    if role and briefing_info.get("role_required") != role.value:
                        continue

                    briefings.append(briefing_info)

            # Sort by priority then creation time
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            briefings.sort(
                key=lambda b: (
                    priority_order.get(b.get("priority", "medium"), 2),
                    b.get("created_at", ""),
                )
            )

            return briefings
        except Exception:
            return []

    async def get_ready_tasks(
        self, project_id: str, completed_tasks: List[str]
    ) -> List[TaskBriefing]:
        """Get tasks that are ready to execute based on dependencies."""
        try:
            # Get all pending briefings
            pending_briefings = await self.list_briefings(
                project_id, status=TaskStatus.PENDING_INVOCATION
            )

            ready_tasks = []
            for briefing_info in pending_briefings:
                briefing = await self.get_briefing(project_id, briefing_info["task_id"])
                if briefing and briefing.is_ready_to_execute(completed_tasks):
                    ready_tasks.append(briefing)

            return ready_tasks
        except Exception:
            return []

    async def cleanup_completed_briefings(
        self, project_id: str, days_to_keep: int = 30
    ) -> int:
        """Clean up old completed briefings."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0

            completed_briefings = await self.list_briefings(
                project_id, status=TaskStatus.COMPLETED
            )

            for briefing_info in completed_briefings:
                if briefing_info.get("completed_at"):
                    try:
                        completed_date = datetime.fromisoformat(
                            briefing_info["completed_at"]
                        ).timestamp()
                        if completed_date < cutoff_date:
                            # Delete briefing and index entry
                            task_id = briefing_info["task_id"]

                            briefing_key = (
                                f"/projects/{project_id}/tasks/briefings/{task_id}"
                            )
                            index_key = (
                                f"/projects/{project_id}/tasks/briefings/"
                                f"index/{task_id}"
                            )

                            await self.mcp.delete(briefing_key)
                            await self.mcp.delete(index_key)

                            deleted_count += 1
                    except (ValueError, TypeError):
                        continue

            return deleted_count
        except Exception:
            return 0


def create_coder_briefing(
    objective: str, context_pointers: Dict[str, str], output_files: List[str], **kwargs
) -> TaskBriefing:
    """Create a Coder task briefing with context and deliverables."""
    briefing = TaskBriefing(role_required=TaskRole.CODER, objective=objective, **kwargs)

    # Add context pointers
    for name, key in context_pointers.items():
        briefing.add_context_pointer(name, key, f"Context: {name}")

    # Add code deliverables
    for output_file in output_files:
        briefing.add_deliverable(
            DeliverableType.CODE,
            f"Implementation for {output_file}",
            f"/tasks/outputs/{briefing.task_id}/code/{output_file}",
        )

    return briefing


def create_adversary_briefing(
    objective: str, target_code_keys: List[str], **kwargs
) -> TaskBriefing:
    """Create an Adversary task briefing for security testing."""
    briefing = TaskBriefing(
        role_required=TaskRole.ADVERSARY, objective=objective, **kwargs
    )

    # Add target code as context
    for i, code_key in enumerate(target_code_keys):
        briefing.add_context_pointer(
            f"target_code_{i}", code_key, f"Code to review: {code_key}"
        )

    # Add standard adversary deliverables
    briefing.add_deliverable(
        DeliverableType.ISSUE_REPORT,
        "Security and quality issues found",
        f"/tasks/outputs/{briefing.task_id}/issues.json",
    )

    briefing.add_deliverable(
        DeliverableType.UNIT_TEST,
        "Unit tests to verify functionality",
        f"/tasks/outputs/{briefing.task_id}/tests/",
    )

    briefing.add_deliverable(
        DeliverableType.RECOMMENDATION,
        "Recommendations for improvements",
        f"/tasks/outputs/{briefing.task_id}/recommendations.md",
    )

    return briefing
