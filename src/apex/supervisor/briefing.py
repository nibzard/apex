"""BriefingGenerator - TaskBriefing generation system for APEX v2.0.

The BriefingGenerator creates detailed TaskBriefings from high-level
task specifications, including context pointer collection, deliverable
specification, and quality criteria.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from apex.core.memory import MemoryPatterns
from apex.core.task_briefing import (
    ContextPointer,
    Deliverable,
    DeliverableType,
    TaskBriefing,
    TaskPriority,
    TaskRole,
    create_adversary_briefing,
    create_coder_briefing,
)


class ContextCollector:
    """Simplified context collection for task briefings."""

    def __init__(self, memory_patterns: MemoryPatterns):
        """Initialize ContextCollector with MemoryPatterns instance."""
        self.memory = memory_patterns
        self.logger = logging.getLogger(__name__)

    async def collect_project_context(
        self, project_id: str, task_spec: Dict[str, Any]
    ) -> Dict[str, ContextPointer]:
        """Collect essential project context for a task."""
        context_pointers = {}

        # Essential project context keys to check
        essential_contexts = [
            (
                f"/projects/{project_id}/config",
                "project_config",
                "Project configuration",
            ),
            (
                f"/projects/{project_id}/docs/coding_standards.md",
                "coding_standards",
                "Coding standards",
            ),
            (
                f"/projects/{project_id}/docs/architecture.md",
                "architecture",
                "Architecture docs",
            ),
        ]

        for key, name, description in essential_contexts:
            data = await self._try_read_context(key)
            if data:
                context_pointers[name] = ContextPointer(
                    key=key,
                    description=description,
                    content_type="json" if key.endswith(".json") else "markdown",
                    size_estimate=len(data),
                )

        # Add relevant task-specific context (simplified)
        task_context = await self._get_task_specific_context(project_id, task_spec)
        context_pointers.update(task_context)

        return context_pointers

    async def _try_read_context(self, key: str) -> Optional[str]:
        """Safely try to read context data."""
        try:
            return await self.memory.mcp.read(key)
        except Exception:
            return None

    async def _get_task_specific_context(
        self, project_id: str, task_spec: Dict[str, Any]
    ) -> Dict[str, ContextPointer]:
        """Get simplified task-specific context."""
        context_pointers = {}
        task_type = task_spec.get("type", "")

        # Simplified context based on task type
        if task_type in ["implementation", "testing"]:
            # Include recent code files
            code_context = await self._get_recent_code_context(project_id)
            context_pointers.update(code_context)

        elif task_type == "bug_fix":
            # Include error logs
            error_context = await self._get_error_context(project_id)
            context_pointers.update(error_context)

        return context_pointers

    async def _get_recent_code_context(
        self, project_id: str
    ) -> Dict[str, ContextPointer]:
        """Get recent code files for context."""
        context_pointers = {}
        try:
            code_prefix = f"/projects/{project_id}/memory/code/"
            code_keys = await self.memory.mcp.list_keys(code_prefix)

            # Just get the first few code files (simplified)
            for i, key in enumerate(code_keys[:3]):
                data = await self._try_read_context(key)
                if data:
                    context_pointers[f"code_file_{i}"] = ContextPointer(
                        key=key,
                        description=f"Code file {i + 1}",
                        content_type="code",
                        size_estimate=len(data),
                    )
        except Exception as e:
            self.logger.warning(f"Error getting code context: {e}")

        return context_pointers

    async def _get_error_context(self, project_id: str) -> Dict[str, ContextPointer]:
        """Get error logs for bug fix context."""
        context_pointers = {}
        try:
            # Check for recent error logs
            error_key = f"/projects/{project_id}/logs/errors/{datetime.now().strftime('%Y-%m-%d')}"
            error_data = await self._try_read_context(error_key)
            if error_data:
                context_pointers["recent_errors"] = ContextPointer(
                    key=error_key,
                    description="Recent error logs",
                    content_type="logs",
                    size_estimate=len(error_data),
                )
        except Exception as e:
            self.logger.warning(f"Error getting error context: {e}")

        return context_pointers


class DeliverableSpecifier:
    """Simplified deliverable specification for tasks."""

    def __init__(self):
        """Initialize DeliverableSpecifier."""
        self.logger = logging.getLogger(__name__)

    def specify_deliverables(
        self, task_spec: Dict[str, Any], task_id: str
    ) -> List[Deliverable]:
        """Specify essential deliverables based on task specification."""
        output_prefix = f"/tasks/outputs/{task_id}"
        role = task_spec.get("role", "")
        task_type = task_spec.get("type", "")

        # Essential deliverables based on role
        if role == "Coder":
            return [
                Deliverable(
                    type=DeliverableType.CODE,
                    description="Implementation code and documentation",
                    output_key=f"{output_prefix}/code/",
                    required=True,
                    validation_criteria=[
                        "Code follows standards",
                        "Clear documentation",
                    ],
                ),
                Deliverable(
                    type=DeliverableType.STATUS_REPORT,
                    description="Status report on task completion",
                    output_key=f"{output_prefix}/status.md",
                    required=True,
                    validation_criteria=["Clear summary of work done"],
                ),
            ]
        elif role == "Adversary":
            return [
                Deliverable(
                    type=DeliverableType.ISSUE_REPORT,
                    description="Issues and recommendations found",
                    output_key=f"{output_prefix}/issues.json",
                    required=True,
                    validation_criteria=["Issues categorized by severity"],
                ),
                Deliverable(
                    type=DeliverableType.RECOMMENDATION,
                    description="Improvement recommendations",
                    output_key=f"{output_prefix}/recommendations.md",
                    required=True,
                    validation_criteria=["Actionable recommendations"],
                ),
            ]
        else:
            # Generic deliverables
            return [
                Deliverable(
                    type=DeliverableType.STATUS_REPORT,
                    description="Task completion report",
                    output_key=f"{output_prefix}/report.md",
                    required=True,
                    validation_criteria=["Task objective achieved"],
                ),
            ]


class QualityCriteriaGenerator:
    """Simplified quality criteria generation for task briefings."""

    def generate_quality_criteria(self, task_spec: Dict[str, Any]) -> List[str]:
        """Generate essential quality criteria based on task specification."""
        # Base quality criteria for all tasks
        criteria = [
            "Task objective fully achieved",
            "All required deliverables provided",
            "Work follows project standards",
            "Clear documentation provided",
        ]

        # Add role-specific criteria
        role = task_spec.get("role", "")
        if role == "Coder":
            criteria.extend(
                [
                    "Code is well-structured and maintainable",
                    "Proper error handling implemented",
                ]
            )
        elif role == "Adversary":
            criteria.extend(
                [
                    "Thorough analysis conducted",
                    "Issues properly categorized by severity",
                ]
            )

        return criteria


class BriefingGenerator:
    """Main briefing generator for APEX v2.0."""

    def __init__(self, memory_patterns: MemoryPatterns):
        """Initialize the BriefingGenerator."""
        self.memory = memory_patterns
        self.context_collector = ContextCollector(memory_patterns)
        self.deliverable_specifier = DeliverableSpecifier()
        self.quality_generator = QualityCriteriaGenerator()
        self.logger = logging.getLogger(__name__)

    async def generate_briefing(
        self,
        project_id: str,
        task_spec: Dict[str, Any],
        project_context: Dict[str, Any],
    ) -> Optional[TaskBriefing]:
        """Generate a complete TaskBriefing from a task specification."""
        try:
            self.logger.info(
                f"Generating briefing for task: "
                f"{task_spec.get('description', 'Unknown')}"
            )

            # Create base briefing
            briefing = TaskBriefing(
                role_required=TaskRole(task_spec["role"]),
                objective=task_spec["description"],
                priority=TaskPriority(task_spec.get("priority", "medium")),
            )

            # Set task metadata
            briefing.orchestration_metadata.update(
                {
                    "task_type": task_spec.get("type", "unknown"),
                    "estimated_duration": task_spec.get("estimated_duration"),
                    "generated_at": datetime.now().isoformat(),
                    "generator_version": "2.0.0",
                }
            )

            # Collect context pointers
            context_pointers = await self.context_collector.collect_project_context(
                project_id, task_spec
            )
            briefing.context_pointers = context_pointers

            # Specify deliverables
            deliverables = self.deliverable_specifier.specify_deliverables(
                task_spec, briefing.task_id
            )
            briefing.deliverables = deliverables

            # Generate quality criteria
            quality_criteria = self.quality_generator.generate_quality_criteria(
                task_spec
            )
            briefing.quality_criteria = quality_criteria

            # Add dependencies if specified
            dependencies = task_spec.get("dependencies", [])
            for dep_task_id in dependencies:
                briefing.add_dependency(dep_task_id)

            # Add constraints
            constraints = task_spec.get("constraints", {})
            briefing.constraints.update(constraints)

            # Set execution context
            briefing.execution_context = {
                "max_duration_minutes": task_spec.get("estimated_duration", 60),
                "resource_requirements": task_spec.get("resource_requirements", {}),
                "environment": (
                    "production"
                    if project_context.get("environment") == "production"
                    else "development"
                ),
            }

            # Update status to ready for invocation
            briefing.update_status(
                briefing.status
            )  # This will set updated_at timestamp

            self.logger.info(
                f"Generated briefing {briefing.task_id} with "
                f"{len(context_pointers)} context pointers and "
                f"{len(deliverables)} deliverables"
            )

            return briefing

        except Exception as e:
            self.logger.error(
                f"Error generating briefing for task "
                f"{task_spec.get('id', 'unknown')}: {e}"
            )
            return None

    async def generate_coder_briefing(
        self,
        project_id: str,
        objective: str,
        context_keys: Dict[str, str],
        output_files: List[str],
        **kwargs,
    ) -> Optional[TaskBriefing]:
        """Generate a Coder-specific briefing using helper function."""
        try:
            # Validate context keys exist
            validated_context = {}
            for name, key in context_keys.items():
                full_key = (
                    f"/projects/{project_id}{key}"
                    if not key.startswith("/projects/")
                    else key
                )
                data = await self.memory.mcp.read(full_key)
                if data:
                    validated_context[name] = full_key
                else:
                    self.logger.warning(f"Context key not found: {full_key}")

            # Create briefing using helper
            briefing = create_coder_briefing(
                objective, validated_context, output_files, **kwargs
            )

            # Add project-specific context
            project_context = await self.context_collector.collect_project_context(
                project_id,
                {"type": "implementation", "role": "Coder", "description": objective},
            )
            briefing.context_pointers.update(project_context)

            return briefing

        except Exception as e:
            self.logger.error(f"Error generating coder briefing: {e}")
            return None

    async def generate_adversary_briefing(
        self, project_id: str, objective: str, target_code_keys: List[str], **kwargs
    ) -> Optional[TaskBriefing]:
        """Generate an Adversary-specific briefing using helper function."""
        try:
            # Validate target code keys exist
            validated_keys = []
            for key in target_code_keys:
                full_key = (
                    f"/projects/{project_id}{key}"
                    if not key.startswith("/projects/")
                    else key
                )
                data = await self.memory.mcp.read(full_key)
                if data:
                    validated_keys.append(full_key)
                else:
                    self.logger.warning(f"Target code key not found: {full_key}")

            # Create briefing using helper
            briefing = create_adversary_briefing(objective, validated_keys, **kwargs)

            # Add project-specific context
            project_context = await self.context_collector.collect_project_context(
                project_id,
                {
                    "type": "security_review",
                    "role": "Adversary",
                    "description": objective,
                },
            )
            briefing.context_pointers.update(project_context)

            return briefing

        except Exception as e:
            self.logger.error(f"Error generating adversary briefing: {e}")
            return None

    async def update_briefing_with_feedback(
        self, project_id: str, briefing: TaskBriefing, feedback: Dict[str, Any]
    ) -> TaskBriefing:
        """Update a briefing based on feedback or new requirements."""
        try:
            # Add feedback to briefing
            briefing.feedback.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "source": feedback.get("source", "supervisor"),
                    "type": feedback.get("type", "update"),
                    "content": feedback.get("content", ""),
                    "metadata": feedback.get("metadata", {}),
                }
            )

            # Update quality criteria if provided
            if "additional_criteria" in feedback:
                briefing.quality_criteria.extend(feedback["additional_criteria"])

            # Update constraints if provided
            if "constraints" in feedback:
                briefing.constraints.update(feedback["constraints"])

            # Add additional context if provided
            if "additional_context" in feedback:
                for name, key in feedback["additional_context"].items():
                    full_key = (
                        f"/projects/{project_id}{key}"
                        if not key.startswith("/projects/")
                        else key
                    )
                    data = await self.memory.mcp.read(full_key)
                    if data:
                        briefing.add_context_pointer(
                            name, full_key, f"Additional context: {name}"
                        )

            # Update timestamp
            briefing.updated_at = datetime.now().isoformat()

            self.logger.info(f"Updated briefing {briefing.task_id} with feedback")

            return briefing

        except Exception as e:
            self.logger.error(f"Error updating briefing with feedback: {e}")
            return briefing
