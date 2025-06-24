"""BriefingGenerator - TaskBriefing generation system for APEX v2.0.

The BriefingGenerator creates detailed TaskBriefings from high-level task specifications,
including context pointer collection, deliverable specification, and quality criteria.
"""

from __future__ import annotations

import json
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
    """Collects and validates context for task briefings."""

    def __init__(self, memory_patterns: MemoryPatterns):
        self.memory = memory_patterns
        self.logger = logging.getLogger(__name__)

    async def collect_project_context(
        self, project_id: str, task_spec: Dict[str, Any]
    ) -> Dict[str, ContextPointer]:
        """Collect relevant project context for a task."""
        context_pointers = {}

        try:
            # Always include project configuration
            config_key = f"/projects/{project_id}/config"
            config_data = await self.memory.mcp.read(config_key)
            if config_data:
                context_pointers["project_config"] = ContextPointer(
                    key=config_key,
                    description="Project configuration and metadata",
                    content_type="json",
                    size_estimate=len(config_data),
                )

            # Include coding standards if available
            standards_key = f"/projects/{project_id}/docs/coding_standards.md"
            standards_data = await self.memory.mcp.read(standards_key)
            if standards_data:
                context_pointers["coding_standards"] = ContextPointer(
                    key=standards_key,
                    description="Project coding standards and style guide",
                    content_type="markdown",
                    size_estimate=len(standards_data),
                )

            # Include architecture documentation
            arch_key = f"/projects/{project_id}/docs/architecture.md"
            arch_data = await self.memory.mcp.read(arch_key)
            if arch_data:
                context_pointers["architecture"] = ContextPointer(
                    key=arch_key,
                    description="System architecture documentation",
                    content_type="markdown",
                    size_estimate=len(arch_data),
                )

            # Include task-specific context based on task type
            await self._add_task_specific_context(
                project_id, task_spec, context_pointers
            )

        except Exception as e:
            self.logger.error(f"Error collecting project context: {e}")

        return context_pointers

    async def _add_task_specific_context(
        self,
        project_id: str,
        task_spec: Dict[str, Any],
        context_pointers: Dict[str, ContextPointer],
    ) -> None:
        """Add context specific to the task type."""
        task_type = task_spec.get("type", "")
        objective = task_spec.get("description", "").lower()

        # For implementation tasks, include related code files
        if task_type == "implementation" or "implement" in objective:
            await self._add_related_code_context(
                project_id, task_spec, context_pointers
            )

        # For bug fixes, include error logs and related code
        elif task_type == "bug_fix" or "fix" in objective:
            await self._add_bug_context(project_id, task_spec, context_pointers)

        # For testing tasks, include code to test
        elif task_type == "testing" or "test" in objective:
            await self._add_testing_context(project_id, task_spec, context_pointers)

        # For security reviews, include security policies
        elif "security" in objective or "adversary" in objective:
            await self._add_security_context(project_id, task_spec, context_pointers)

    async def _add_related_code_context(
        self,
        project_id: str,
        task_spec: Dict[str, Any],
        context_pointers: Dict[str, ContextPointer],
    ) -> None:
        """Add context for implementation tasks."""
        try:
            # Get existing code files that might be related
            code_prefix = f"/projects/{project_id}/memory/code/"
            code_keys = await self.memory.mcp.list_keys(code_prefix)

            # Limit to most relevant files (avoid context overload)
            relevant_files = []
            objective_words = task_spec.get("description", "").lower().split()

            for key in code_keys[:20]:  # Limit search scope
                try:
                    data = await self.memory.mcp.read(key)
                    if data:
                        code_info = json.loads(data)
                        file_path = code_info.get("file_path", "")

                        # Simple relevance scoring based on filename/path matching
                        relevance_score = 0
                        for word in objective_words:
                            if word in file_path.lower():
                                relevance_score += 1

                        if relevance_score > 0:
                            relevant_files.append((relevance_score, key, code_info))
                except:
                    continue

            # Sort by relevance and add top files
            relevant_files.sort(key=lambda x: x[0], reverse=True)

            for i, (_score, key, code_info) in enumerate(relevant_files[:5]):
                context_pointers[f"related_code_{i}"] = ContextPointer(
                    key=key,
                    description=f"Related code file: {code_info.get('file_path', 'unknown')}",
                    content_type="code",
                    size_estimate=len(json.dumps(code_info)),
                )

        except Exception as e:
            self.logger.error(f"Error adding related code context: {e}")

    async def _add_bug_context(
        self,
        project_id: str,
        task_spec: Dict[str, Any],
        context_pointers: Dict[str, ContextPointer],
    ) -> None:
        """Add context for bug fix tasks."""
        try:
            # Include recent error logs
            error_logs_key = f"/projects/{project_id}/logs/errors/{datetime.now().strftime('%Y-%m-%d')}"
            error_data = await self.memory.mcp.read(error_logs_key)
            if error_data:
                context_pointers["recent_errors"] = ContextPointer(
                    key=error_logs_key,
                    description="Recent error logs from today",
                    content_type="logs",
                    size_estimate=len(error_data),
                )

            # Include open issues
            issues_prefix = f"/projects/{project_id}/memory/issues/"
            issue_keys = await self.memory.mcp.list_keys(issues_prefix)

            for i, key in enumerate(issue_keys[:3]):  # Limit to top 3 issues
                try:
                    issue_data = await self.memory.mcp.read(key)
                    if issue_data:
                        context_pointers[f"open_issue_{i}"] = ContextPointer(
                            key=key,
                            description=f"Open issue #{i + 1}",
                            content_type="json",
                            size_estimate=len(issue_data),
                        )
                except:
                    continue

        except Exception as e:
            self.logger.error(f"Error adding bug context: {e}")

    async def _add_testing_context(
        self,
        project_id: str,
        task_spec: Dict[str, Any],
        context_pointers: Dict[str, ContextPointer],
    ) -> None:
        """Add context for testing tasks."""
        try:
            # Include test configuration
            test_config_key = f"/projects/{project_id}/config/test_config.json"
            test_config = await self.memory.mcp.read(test_config_key)
            if test_config:
                context_pointers["test_config"] = ContextPointer(
                    key=test_config_key,
                    description="Test configuration and framework settings",
                    content_type="json",
                    size_estimate=len(test_config),
                )

            # Include existing test files for reference
            test_prefix = f"/projects/{project_id}/memory/code/"
            keys = await self.memory.mcp.list_keys(test_prefix)

            test_files = []
            for key in keys:
                try:
                    data = await self.memory.mcp.read(key)
                    if data:
                        code_info = json.loads(data)
                        file_path = code_info.get("file_path", "")
                        if "test" in file_path.lower():
                            test_files.append((key, code_info))
                except:
                    continue

            # Add a few example test files
            for i, (key, code_info) in enumerate(test_files[:3]):
                context_pointers[f"example_test_{i}"] = ContextPointer(
                    key=key,
                    description=f"Example test file: {code_info.get('file_path', 'unknown')}",
                    content_type="code",
                    size_estimate=len(json.dumps(code_info)),
                )

        except Exception as e:
            self.logger.error(f"Error adding testing context: {e}")

    async def _add_security_context(
        self,
        project_id: str,
        task_spec: Dict[str, Any],
        context_pointers: Dict[str, ContextPointer],
    ) -> None:
        """Add context for security/adversary tasks."""
        try:
            # Include security policies
            security_policy_key = f"/projects/{project_id}/docs/security_policy.md"
            policy_data = await self.memory.mcp.read(security_policy_key)
            if policy_data:
                context_pointers["security_policy"] = ContextPointer(
                    key=security_policy_key,
                    description="Project security policies and guidelines",
                    content_type="markdown",
                    size_estimate=len(policy_data),
                )

            # Include previous security reports
            security_prefix = f"/projects/{project_id}/memory/security/"
            security_keys = await self.memory.mcp.list_keys(security_prefix)

            for i, key in enumerate(security_keys[:2]):  # Limit to 2 recent reports
                try:
                    report_data = await self.memory.mcp.read(key)
                    if report_data:
                        context_pointers[f"security_report_{i}"] = ContextPointer(
                            key=key,
                            description=f"Previous security report #{i + 1}",
                            content_type="json",
                            size_estimate=len(report_data),
                        )
                except:
                    continue

        except Exception as e:
            self.logger.error(f"Error adding security context: {e}")


class DeliverableSpecifier:
    """Specifies deliverables and quality criteria for tasks."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def specify_deliverables(
        self, task_spec: Dict[str, Any], task_id: str
    ) -> List[Deliverable]:
        """Specify deliverables based on task specification."""
        deliverables = []
        task_type = task_spec.get("type", "")
        role = task_spec.get("role", "")

        # Base output path
        output_prefix = f"/tasks/outputs/{task_id}"

        if role == "Coder":
            deliverables.extend(
                self._specify_coder_deliverables(task_spec, output_prefix)
            )
        elif role == "Adversary":
            deliverables.extend(
                self._specify_adversary_deliverables(task_spec, output_prefix)
            )

        # Add task-specific deliverables
        if task_type == "research":
            deliverables.extend(
                self._specify_research_deliverables(task_spec, output_prefix)
            )
        elif task_type == "implementation":
            deliverables.extend(
                self._specify_implementation_deliverables(task_spec, output_prefix)
            )
        elif task_type == "testing":
            deliverables.extend(
                self._specify_testing_deliverables(task_spec, output_prefix)
            )
        elif task_type == "bug_fix":
            deliverables.extend(
                self._specify_bug_fix_deliverables(task_spec, output_prefix)
            )
        elif task_type == "security_review":
            deliverables.extend(
                self._specify_security_deliverables(task_spec, output_prefix)
            )

        # Ensure all deliverables have unique output keys
        self._ensure_unique_output_keys(deliverables)

        return deliverables

    def _specify_coder_deliverables(
        self, task_spec: Dict[str, Any], output_prefix: str
    ) -> List[Deliverable]:
        """Specify deliverables for Coder role."""
        return [
            Deliverable(
                type=DeliverableType.STATUS_REPORT,
                description="Status report on task completion and decisions made",
                output_key=f"{output_prefix}/status_report.md",
                required=True,
                validation_criteria=[
                    "Clear summary of work done",
                    "Decisions and rationale documented",
                ],
            )
        ]

    def _specify_adversary_deliverables(
        self, task_spec: Dict[str, Any], output_prefix: str
    ) -> List[Deliverable]:
        """Specify deliverables for Adversary role."""
        return [
            Deliverable(
                type=DeliverableType.ISSUE_REPORT,
                description="Issues and vulnerabilities found during review",
                output_key=f"{output_prefix}/issues.json",
                required=True,
                validation_criteria=[
                    "Issues categorized by severity",
                    "Clear reproduction steps",
                ],
            ),
            Deliverable(
                type=DeliverableType.RECOMMENDATION,
                description="Recommendations for improvements",
                output_key=f"{output_prefix}/recommendations.md",
                required=True,
                validation_criteria=[
                    "Actionable recommendations",
                    "Priority levels assigned",
                ],
            ),
        ]

    def _specify_research_deliverables(
        self, task_spec: Dict[str, Any], output_prefix: str
    ) -> List[Deliverable]:
        """Specify deliverables for research tasks."""
        return [
            Deliverable(
                type=DeliverableType.ANALYSIS,
                description="Research findings and analysis",
                output_key=f"{output_prefix}/research_analysis.md",
                required=True,
                validation_criteria=[
                    "Comprehensive research conducted",
                    "Key findings summarized",
                    "Sources cited",
                ],
            ),
            Deliverable(
                type=DeliverableType.RECOMMENDATION,
                description="Technical approach recommendations",
                output_key=f"{output_prefix}/technical_approach.md",
                required=True,
                validation_criteria=[
                    "Multiple approaches considered",
                    "Recommended approach justified",
                ],
            ),
        ]

    def _specify_implementation_deliverables(
        self, task_spec: Dict[str, Any], output_prefix: str
    ) -> List[Deliverable]:
        """Specify deliverables for implementation tasks."""
        deliverables = [
            Deliverable(
                type=DeliverableType.CODE,
                description="Core implementation code",
                output_key=f"{output_prefix}/code/",
                required=True,
                validation_criteria=[
                    "Code follows project standards",
                    "Proper error handling",
                    "Clear documentation",
                ],
            ),
            Deliverable(
                type=DeliverableType.UNIT_TEST,
                description="Unit tests for implemented functionality",
                output_key=f"{output_prefix}/tests/unit/",
                required=True,
                validation_criteria=[
                    "Adequate test coverage",
                    "Edge cases tested",
                    "Tests pass",
                ],
            ),
            Deliverable(
                type=DeliverableType.DOCUMENTATION,
                description="Implementation documentation",
                output_key=f"{output_prefix}/docs/implementation.md",
                required=True,
                validation_criteria=[
                    "API documented",
                    "Usage examples provided",
                    "Configuration explained",
                ],
            ),
        ]

        # Add integration tests for complex implementations
        objective = task_spec.get("description", "").lower()
        if any(
            word in objective for word in ["api", "endpoint", "service", "integration"]
        ):
            deliverables.append(
                Deliverable(
                    type=DeliverableType.INTEGRATION_TEST,
                    description="Integration tests for the implementation",
                    output_key=f"{output_prefix}/tests/integration/",
                    required=False,
                    validation_criteria=[
                        "End-to-end scenarios tested",
                        "Integration points verified",
                    ],
                )
            )

        return deliverables

    def _specify_testing_deliverables(
        self, task_spec: Dict[str, Any], output_prefix: str
    ) -> List[Deliverable]:
        """Specify deliverables for testing tasks."""
        return [
            Deliverable(
                type=DeliverableType.UNIT_TEST,
                description="Comprehensive unit tests",
                output_key=f"{output_prefix}/tests/unit/",
                required=True,
                validation_criteria=[
                    "High code coverage",
                    "Edge cases covered",
                    "All tests pass",
                ],
            ),
            Deliverable(
                type=DeliverableType.ANALYSIS,
                description="Test coverage and quality report",
                output_key=f"{output_prefix}/coverage_report.json",
                required=True,
                validation_criteria=[
                    "Coverage metrics included",
                    "Quality assessment provided",
                ],
            ),
            Deliverable(
                type=DeliverableType.DOCUMENTATION,
                description="Test documentation and usage guide",
                output_key=f"{output_prefix}/test_docs.md",
                required=False,
                validation_criteria=[
                    "Test strategy explained",
                    "How to run tests documented",
                ],
            ),
        ]

    def _specify_bug_fix_deliverables(
        self, task_spec: Dict[str, Any], output_prefix: str
    ) -> List[Deliverable]:
        """Specify deliverables for bug fix tasks."""
        return [
            Deliverable(
                type=DeliverableType.CODE,
                description="Bug fix implementation",
                output_key=f"{output_prefix}/fix/",
                required=True,
                validation_criteria=[
                    "Bug root cause addressed",
                    "Minimal code changes",
                    "No regression introduced",
                ],
            ),
            Deliverable(
                type=DeliverableType.UNIT_TEST,
                description="Tests to verify bug fix and prevent regression",
                output_key=f"{output_prefix}/regression_tests/",
                required=True,
                validation_criteria=[
                    "Bug scenario reproduced in test",
                    "Fix verified",
                    "Regression prevention",
                ],
            ),
            Deliverable(
                type=DeliverableType.ANALYSIS,
                description="Bug analysis and fix explanation",
                output_key=f"{output_prefix}/bug_analysis.md",
                required=True,
                validation_criteria=[
                    "Root cause identified",
                    "Fix approach explained",
                    "Impact assessment provided",
                ],
            ),
        ]

    def _specify_security_deliverables(
        self, task_spec: Dict[str, Any], output_prefix: str
    ) -> List[Deliverable]:
        """Specify deliverables for security review tasks."""
        return [
            Deliverable(
                type=DeliverableType.ISSUE_REPORT,
                description="Security vulnerabilities and issues found",
                output_key=f"{output_prefix}/security_issues.json",
                required=True,
                validation_criteria=[
                    "CVSS scores provided",
                    "Exploitation scenarios described",
                    "Remediation steps included",
                ],
            ),
            Deliverable(
                type=DeliverableType.UNIT_TEST,
                description="Security tests to verify protections",
                output_key=f"{output_prefix}/security_tests/",
                required=True,
                validation_criteria=[
                    "Attack scenarios tested",
                    "Security controls verified",
                    "Input validation tested",
                ],
            ),
            Deliverable(
                type=DeliverableType.ANALYSIS,
                description="Overall security assessment",
                output_key=f"{output_prefix}/security_assessment.md",
                required=True,
                validation_criteria=[
                    "Risk assessment provided",
                    "Security posture evaluated",
                    "Compliance checked",
                ],
            ),
        ]

    def _ensure_unique_output_keys(self, deliverables: List[Deliverable]) -> None:
        """Ensure all deliverables have unique output keys."""
        seen_keys = set()

        for deliverable in deliverables:
            original_key = deliverable.output_key
            counter = 1

            while deliverable.output_key in seen_keys:
                base_key = (
                    original_key.rsplit(".", 1)[0]
                    if "." in original_key
                    else original_key
                )
                extension = (
                    original_key.rsplit(".", 1)[1] if "." in original_key else ""
                )

                if extension:
                    deliverable.output_key = f"{base_key}_{counter}.{extension}"
                else:
                    deliverable.output_key = f"{base_key}_{counter}"

                counter += 1

            seen_keys.add(deliverable.output_key)


class QualityCriteriaGenerator:
    """Generates quality criteria for task briefings."""

    def generate_quality_criteria(self, task_spec: Dict[str, Any]) -> List[str]:
        """Generate quality criteria based on task specification."""
        criteria = []

        # Universal quality criteria
        criteria.extend(
            [
                "Task objective fully achieved",
                "All required deliverables provided",
                "Work follows project coding standards",
                "Clear documentation provided",
            ]
        )

        # Role-specific criteria
        role = task_spec.get("role", "")
        if role == "Coder":
            criteria.extend(
                [
                    "Code is well-structured and maintainable",
                    "Proper error handling implemented",
                    "Security best practices followed",
                    "Performance considerations addressed",
                ]
            )
        elif role == "Adversary":
            criteria.extend(
                [
                    "Thorough security analysis conducted",
                    "Edge cases and error conditions tested",
                    "Potential vulnerabilities identified",
                    "Quality of implementation assessed",
                ]
            )

        # Task-type specific criteria
        task_type = task_spec.get("type", "")
        if task_type == "implementation":
            criteria.extend(
                [
                    "Implementation meets functional requirements",
                    "Code integrates properly with existing system",
                    "Unit tests provide adequate coverage",
                    "API contracts properly defined",
                ]
            )
        elif task_type == "testing":
            criteria.extend(
                [
                    "Test coverage meets or exceeds 80%",
                    "Tests cover happy path and edge cases",
                    "Performance tests included where appropriate",
                    "Tests are maintainable and readable",
                ]
            )
        elif task_type == "bug_fix":
            criteria.extend(
                [
                    "Root cause properly identified and addressed",
                    "Fix is minimal and targeted",
                    "No regression introduced",
                    "Bug reproduction test included",
                ]
            )
        elif task_type == "security_review":
            criteria.extend(
                [
                    "All security domains reviewed (authentication, authorization, input validation, etc.)",
                    "Security issues properly categorized by severity",
                    "Remediation steps are actionable",
                    "Compliance requirements considered",
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
                f"Generating briefing for task: {task_spec.get('description', 'Unknown')}"
            )

            # Create base briefing
            briefing = TaskBriefing(
                role_required=TaskRole(task_spec["role"]),
                objective=task_spec["description"],
                priority=TaskPriority(task_spec.get("priority", "medium")),
            )

            # Set task metadata
            briefing.metadata.update(
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
                f"Generated briefing {briefing.task_id} with {len(context_pointers)} context pointers and {len(deliverables)} deliverables"
            )

            return briefing

        except Exception as e:
            self.logger.error(
                f"Error generating briefing for task {task_spec.get('id', 'unknown')}: {e}"
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
