"""Utility manager for orchestrating utility execution."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from apex.core.error_handling import ErrorRecoveryManager, error_handler
from apex.core.memory import MemoryPatterns

from .base import UtilityCategory, UtilityResult, UtilityStatus
from .registry import UtilityRegistry


class UtilityExecutionPlan:
    """Plan for executing a set of utilities."""

    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        self.utilities: List[str] = []
        self.dependencies: Dict[str, List[str]] = {}
        self.parallel_groups: List[List[str]] = []
        self.created_at = datetime.now().isoformat()

    def add_utility(self, utility_name: str, dependencies: Optional[List[str]] = None):
        """Add a utility to the execution plan."""
        if utility_name not in self.utilities:
            self.utilities.append(utility_name)

        if dependencies:
            self.dependencies[utility_name] = dependencies

    def resolve_execution_order(self) -> List[List[str]]:
        """Resolve execution order respecting dependencies."""
        if self.parallel_groups:
            return self.parallel_groups

        # Topological sort for dependency resolution
        in_degree = {utility: 0 for utility in self.utilities}
        graph = {utility: [] for utility in self.utilities}

        # Build dependency graph
        for utility, deps in self.dependencies.items():
            for dep in deps:
                if dep in graph:
                    graph[dep].append(utility)
                    in_degree[utility] += 1

        # Group utilities that can run in parallel
        groups = []
        remaining = set(self.utilities)

        while remaining:
            # Find utilities with no dependencies
            ready = [u for u in remaining if in_degree[u] == 0]

            if not ready:
                # Circular dependency or missing dependency
                ready = list(remaining)  # Force execution

            groups.append(ready)

            # Remove ready utilities and update dependencies
            for utility in ready:
                remaining.remove(utility)
                for dependent in graph[utility]:
                    in_degree[dependent] -= 1

        self.parallel_groups = groups
        return groups


class UtilityManager:
    """Manages utility execution and orchestration."""

    def __init__(self, memory: MemoryPatterns):
        self.memory = memory
        self.registry = UtilityRegistry(memory)
        self.error_manager = ErrorRecoveryManager(memory)
        self.logger = logging.getLogger(__name__)

        # Execution tracking
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_results: Dict[str, UtilityResult] = {}

    async def register_builtin_utilities(self) -> None:
        """Register built-in utilities."""
        from .builtin import (
            BuildUtility,
            CodeLinterUtility,
            DeploymentUtility,
            DocumentationGeneratorUtility,
            SecurityScannerUtility,
            TestRunnerUtility,
        )

        builtins = [
            (CodeLinterUtility, "code_linter", UtilityCategory.CODE_ANALYSIS),
            (TestRunnerUtility, "test_runner", UtilityCategory.TESTING),
            (
                DocumentationGeneratorUtility,
                "doc_generator",
                UtilityCategory.DOCUMENTATION,
            ),
            (SecurityScannerUtility, "security_scanner", UtilityCategory.SECURITY),
            (BuildUtility, "build", UtilityCategory.BUILD_AUTOMATION),
            (DeploymentUtility, "deployment", UtilityCategory.DEPLOYMENT),
        ]

        for utility_class, name, category in builtins:
            config = utility_class.get_default_config(name, category)
            await self.registry.register_utility(utility_class, config)

        self.logger.info(f"Registered {len(builtins)} built-in utilities")

    async def execute_utility(
        self, utility_name: str, context: Dict[str, Any], async_execution: bool = False
    ) -> UtilityResult:
        """Execute a single utility.

        Args:
            utility_name: Name of the utility to execute
            context: Execution context
            async_execution: Whether to execute asynchronously

        Returns:
            UtilityResult with execution details

        """
        async with error_handler(
            self.memory,
            component="utility_manager",
            operation="execute_utility",
            context={"utility_name": utility_name, **context},
        ):
            utility = await self.registry.get_utility(utility_name)

            if not utility:
                result = UtilityResult(
                    utility_id=utility_name,
                    status=UtilityStatus.FAILED,
                    started_at=datetime.now().isoformat(),
                )
                result.add_error(f"Utility '{utility_name}' not found")
                result.set_completed(False)
                return result

            # Validate dependencies
            missing_deps = await self.registry.validate_dependencies(utility_name)
            if missing_deps:
                result = UtilityResult(
                    utility_id=utility_name,
                    status=UtilityStatus.FAILED,
                    started_at=datetime.now().isoformat(),
                )
                result.add_error(f"Missing dependencies: {missing_deps}")
                result.set_completed(False)
                return result

            if async_execution:
                # Execute asynchronously
                task = asyncio.create_task(utility.run_with_timeout(context))
                self.active_executions[utility_name] = task

                # Return a pending result
                result = UtilityResult(
                    utility_id=utility_name,
                    status=UtilityStatus.RUNNING,
                    started_at=datetime.now().isoformat(),
                )
                return result
            else:
                # Execute synchronously
                result = await utility.run_with_timeout(context)
                await self._store_execution_result(result, context)
                return result

    async def execute_plan(
        self,
        plan: UtilityExecutionPlan,
        context: Dict[str, Any],
        stop_on_failure: bool = False,
    ) -> Dict[str, UtilityResult]:
        """Execute a utility execution plan.

        Args:
            plan: Execution plan
            context: Execution context
            stop_on_failure: Whether to stop on first failure

        Returns:
            Dictionary of utility results

        """
        results = {}
        execution_order = plan.resolve_execution_order()

        self.logger.info(
            f"Executing plan {plan.plan_id} with {len(execution_order)} groups"
        )

        for group_index, utility_group in enumerate(execution_order):
            self.logger.info(f"Executing group {group_index + 1}: {utility_group}")

            # Execute utilities in parallel within the group
            group_tasks = []
            for utility_name in utility_group:
                task = asyncio.create_task(
                    self.execute_utility(utility_name, context, async_execution=False)
                )
                group_tasks.append((utility_name, task))

            # Wait for group to complete
            for utility_name, task in group_tasks:
                try:
                    result = await task
                    results[utility_name] = result

                    if result.status == UtilityStatus.FAILED and stop_on_failure:
                        self.logger.error(
                            f"Stopping execution due to failure in {utility_name}"
                        )
                        # Cancel remaining tasks
                        for _, remaining_task in group_tasks:
                            if not remaining_task.done():
                                remaining_task.cancel()
                        return results

                except Exception as e:
                    result = UtilityResult(
                        utility_id=utility_name,
                        status=UtilityStatus.FAILED,
                        started_at=datetime.now().isoformat(),
                    )
                    result.add_error(f"Execution failed: {str(e)}")
                    result.set_completed(False)
                    results[utility_name] = result

                    if stop_on_failure:
                        return results

        # Store plan execution results
        await self._store_plan_results(plan, results, context)

        return results

    async def create_execution_plan(
        self, utility_names: List[str], auto_resolve_dependencies: bool = True
    ) -> UtilityExecutionPlan:
        """Create an execution plan for utilities.

        Args:
            utility_names: List of utility names to include
            auto_resolve_dependencies: Whether to automatically include dependencies

        Returns:
            UtilityExecutionPlan

        """
        plan_id = f"plan-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        plan = UtilityExecutionPlan(plan_id)

        utilities_to_add = set(utility_names)

        if auto_resolve_dependencies:
            # Add dependencies recursively
            to_process = list(utility_names)
            processed = set()

            while to_process:
                utility_name = to_process.pop(0)
                if utility_name in processed:
                    continue

                processed.add(utility_name)
                utilities_to_add.add(utility_name)

                dependencies = await self.registry.get_utility_dependencies(
                    utility_name
                )
                for dep in dependencies:
                    if dep not in processed:
                        to_process.append(dep)
                        utilities_to_add.add(dep)

        # Add utilities to plan
        for utility_name in utilities_to_add:
            dependencies = await self.registry.get_utility_dependencies(utility_name)
            # Only include dependencies that are also in the plan
            plan_dependencies = [dep for dep in dependencies if dep in utilities_to_add]
            plan.add_utility(utility_name, plan_dependencies)

        return plan

    async def get_execution_status(self, utility_name: str) -> Optional[UtilityResult]:
        """Get execution status for a utility.

        Args:
            utility_name: Name of the utility

        Returns:
            UtilityResult or None if not found

        """
        # Check active executions
        if utility_name in self.active_executions:
            task = self.active_executions[utility_name]
            if task.done():
                try:
                    result = task.result()
                    self.execution_results[utility_name] = result
                    del self.active_executions[utility_name]
                    return result
                except Exception as e:
                    result = UtilityResult(
                        utility_id=utility_name,
                        status=UtilityStatus.FAILED,
                        started_at=datetime.now().isoformat(),
                    )
                    result.add_error(f"Execution failed: {str(e)}")
                    result.set_completed(False)
                    return result
            else:
                # Still running
                return UtilityResult(
                    utility_id=utility_name,
                    status=UtilityStatus.RUNNING,
                    started_at=datetime.now().isoformat(),
                )

        # Check stored results
        if utility_name in self.execution_results:
            return self.execution_results[utility_name]

        # Try to load from memory
        result_key = f"/utilities/executions/{utility_name}/latest"
        result_json = await self.memory.mcp.read(result_key)

        if result_json:
            result_data = json.loads(result_json)
            return UtilityResult(**result_data)

        return None

    async def cancel_execution(self, utility_name: str) -> bool:
        """Cancel an active utility execution.

        Args:
            utility_name: Name of the utility to cancel

        Returns:
            True if cancellation succeeded, False otherwise

        """
        if utility_name in self.active_executions:
            task = self.active_executions[utility_name]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Create cancelled result
            result = UtilityResult(
                utility_id=utility_name,
                status=UtilityStatus.CANCELLED,
                started_at=datetime.now().isoformat(),
            )
            result.set_completed(False)

            self.execution_results[utility_name] = result
            del self.active_executions[utility_name]

            return True

        return False

    async def get_utility_recommendations(
        self, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get utility recommendations based on context.

        Args:
            context: Execution context

        Returns:
            List of recommended utilities with reasons

        """
        recommendations = []

        # Basic recommendations based on project context
        project_type = context.get("project_type", "")
        has_tests = context.get("has_tests", False)
        has_docs = context.get("has_docs", False)

        # Code analysis is always recommended
        recommendations.append(
            {
                "utility": "code_linter",
                "reason": "Code quality analysis",
                "priority": "high",
            }
        )

        # Security scan for all projects
        recommendations.append(
            {
                "utility": "security_scanner",
                "reason": "Security vulnerability assessment",
                "priority": "high",
            }
        )

        # Test runner if tests exist
        if has_tests:
            recommendations.append(
                {
                    "utility": "test_runner",
                    "reason": "Execute automated tests",
                    "priority": "high",
                }
            )

        # Documentation generation if missing
        if not has_docs:
            recommendations.append(
                {
                    "utility": "doc_generator",
                    "reason": "Generate missing documentation",
                    "priority": "medium",
                }
            )

        # Build utility for certain project types
        if project_type in ["web", "api", "library"]:
            recommendations.append(
                {
                    "utility": "build",
                    "reason": f"Build {project_type} project",
                    "priority": "medium",
                }
            )

        return recommendations

    async def _store_execution_result(
        self, result: UtilityResult, context: Dict[str, Any]
    ) -> None:
        """Store execution result in memory."""
        try:
            # Store latest result
            result_key = f"/utilities/executions/{result.utility_id}/latest"
            await self.memory.mcp.write(result_key, result.model_dump_json())

            # Store timestamped result
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            timestamped_key = (
                f"/utilities/executions/{result.utility_id}/history/{timestamp}"
            )
            await self.memory.mcp.write(timestamped_key, result.model_dump_json())

            # Store execution context
            context_key = (
                f"/utilities/executions/{result.utility_id}/context/{timestamp}"
            )
            await self.memory.mcp.write(context_key, json.dumps(context))

        except Exception as e:
            self.logger.error(f"Failed to store execution result: {e}")

    async def _store_plan_results(
        self,
        plan: UtilityExecutionPlan,
        results: Dict[str, UtilityResult],
        context: Dict[str, Any],
    ) -> None:
        """Store plan execution results."""
        try:
            plan_data = {
                "plan_id": plan.plan_id,
                "created_at": plan.created_at,
                "completed_at": datetime.now().isoformat(),
                "utilities": plan.utilities,
                "execution_order": plan.parallel_groups,
                "results": {
                    name: result.model_dump() for name, result in results.items()
                },
                "context": context,
            }

            plan_key = f"/utilities/plans/{plan.plan_id}/execution"
            await self.memory.mcp.write(plan_key, json.dumps(plan_data))

        except Exception as e:
            self.logger.error(f"Failed to store plan results: {e}")

    async def get_execution_history(
        self, utility_name: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get execution history.

        Args:
            utility_name: Optional utility name filter
            limit: Maximum number of results

        Returns:
            List of execution history entries

        """
        history = []

        try:
            if utility_name:
                pattern = f"/utilities/executions/{utility_name}/history/"
            else:
                pattern = "/utilities/executions/"

            keys = await self.memory.mcp.list_keys(pattern)

            # Sort by timestamp (most recent first)
            keys.sort(reverse=True)

            for key in keys[:limit]:
                if "/history/" in key:
                    result_json = await self.memory.mcp.read(key)
                    if result_json:
                        result_data = json.loads(result_json)
                        history.append(result_data)

        except Exception as e:
            self.logger.error(f"Failed to get execution history: {e}")

        return history
