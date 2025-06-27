"""Base classes for the APEX utilities framework."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UtilityCategory(Enum):
    """Categories of utilities in the framework."""

    CODE_ANALYSIS = "code_analysis"
    BUILD_AUTOMATION = "build_automation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATABASE = "database"
    INTEGRATION = "integration"
    MAINTENANCE = "maintenance"
    VALIDATION = "validation"


class UtilityStatus(Enum):
    """Status of utility execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class UtilityResult(BaseModel):
    """Result of utility execution."""

    utility_id: str
    status: UtilityStatus
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    output: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)  # File paths or LMDB keys
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def add_artifact(self, artifact: str) -> None:
        """Add an artifact path or key."""
        self.artifacts.append(artifact)

    def set_completed(self, success: bool = True) -> None:
        """Mark the utility as completed."""
        self.completed_at = datetime.now().isoformat()
        if self.started_at:
            start_time = datetime.fromisoformat(self.started_at)
            end_time = datetime.fromisoformat(self.completed_at)
            self.duration_seconds = (end_time - start_time).total_seconds()

        self.status = UtilityStatus.COMPLETED if success else UtilityStatus.FAILED


class UtilityConfig(BaseModel):
    """Configuration for a utility."""

    name: str
    category: UtilityCategory
    version: str = "1.0.0"
    description: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    parallel_execution: bool = True
    required_tools: List[str] = Field(default_factory=list)
    environment_variables: Dict[str, str] = Field(default_factory=dict)


class BaseUtility(ABC):
    """Base class for all utilities in the framework."""

    def __init__(self, config: UtilityConfig):
        self.config = config
        self.logger = logging.getLogger(f"apex.utilities.{config.name}")
        self.result: Optional[UtilityResult] = None

    @property
    def name(self) -> str:
        """Get utility name."""
        return self.config.name

    @property
    def category(self) -> UtilityCategory:
        """Get utility category."""
        return self.config.category

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute the utility.

        Args:
            context: Execution context including project info, task data, etc.

        Returns:
            UtilityResult with execution details

        """
        pass

    @abstractmethod
    def validate_config(self) -> List[str]:
        """Validate utility configuration.

        Returns:
            List of validation errors (empty if valid)

        """
        pass

    async def pre_execute(self, context: Dict[str, Any]) -> bool:
        """Pre-execution hook.

        Args:
            context: Execution context

        Returns:
            True if pre-execution succeeded, False otherwise

        """
        return True

    async def post_execute(
        self, context: Dict[str, Any], result: UtilityResult
    ) -> None:
        """Post-execution hook.

        Args:
            context: Execution context
            result: Execution result

        """
        pass

    def create_result(self) -> UtilityResult:
        """Create a new utility result."""
        return UtilityResult(
            utility_id=self.name,
            status=UtilityStatus.PENDING,
            started_at=datetime.now().isoformat(),
        )

    async def run_with_timeout(self, context: Dict[str, Any]) -> UtilityResult:
        """Run the utility with timeout handling."""
        result = self.create_result()
        result.status = UtilityStatus.RUNNING

        try:
            # Pre-execution
            if not await self.pre_execute(context):
                result.add_error("Pre-execution failed")
                result.set_completed(False)
                return result

            # Execute with timeout
            if self.config.timeout_seconds > 0:
                result = await asyncio.wait_for(
                    self.execute(context), timeout=self.config.timeout_seconds
                )
            else:
                result = await self.execute(context)

            # Post-execution
            await self.post_execute(context, result)

        except asyncio.TimeoutError:
            result.add_error(
                f"Utility timed out after {self.config.timeout_seconds} seconds"
            )
            result.status = UtilityStatus.TIMEOUT
            result.set_completed(False)

        except Exception as e:
            result.add_error(f"Utility execution failed: {str(e)}")
            result.set_completed(False)

        self.result = result
        return result


class CommandUtility(BaseUtility):
    """Utility that executes shell commands."""

    def __init__(self, config: UtilityConfig, command: str, shell: bool = False):
        super().__init__(config)
        self.command = command
        self.shell = shell

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute shell command."""
        result = self.create_result()

        try:
            # Replace variables in command
            formatted_command = self._format_command(context)

            self.logger.info(f"Executing command: {formatted_command}")

            # Execute command
            if self.shell:
                process = await asyncio.create_subprocess_shell(
                    formatted_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**context.get("env", {}), **self.config.environment_variables},
                )
            else:
                args = formatted_command.split()
                process = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**context.get("env", {}), **self.config.environment_variables},
                )

            stdout, stderr = await process.communicate()

            result.output = {
                "command": formatted_command,
                "return_code": process.returncode,
                "stdout": stdout.decode("utf-8") if stdout else "",
                "stderr": stderr.decode("utf-8") if stderr else "",
            }

            if process.returncode == 0:
                result.set_completed(True)
                self.logger.info("Command completed successfully")
            else:
                result.add_error(
                    f"Command failed with return code {process.returncode}"
                )
                if stderr:
                    result.add_error(stderr.decode("utf-8"))
                result.set_completed(False)

        except Exception as e:
            result.add_error(f"Command execution failed: {str(e)}")
            result.set_completed(False)

        return result

    def _format_command(self, context: Dict[str, Any]) -> str:
        """Format command with context variables."""
        formatted = self.command

        # Replace common variables
        replacements = {
            "{project_id}": context.get("project_id", ""),
            "{project_dir}": context.get("project_dir", "."),
            "{task_id}": context.get("task_id", ""),
            "{session_id}": context.get("session_id", ""),
        }

        # Add custom parameters
        for key, value in self.config.parameters.items():
            replacements[f"{{{key}}}"] = str(value)

        for placeholder, value in replacements.items():
            formatted = formatted.replace(placeholder, value)

        return formatted

    def validate_config(self) -> List[str]:
        """Validate command utility configuration."""
        errors = []

        if not self.command:
            errors.append("Command is required")

        # Check for required tools
        for tool in self.config.required_tools:
            # In a real implementation, you'd check if the tool is available
            pass

        return errors


class PythonUtility(BaseUtility):
    """Utility that executes Python functions."""

    def __init__(self, config: UtilityConfig, function_name: str, module_path: str):
        super().__init__(config)
        self.function_name = function_name
        self.module_path = module_path
        self._function = None

    async def execute(self, context: Dict[str, Any]) -> UtilityResult:
        """Execute Python function."""
        result = self.create_result()

        try:
            # Import and get function
            if not self._function:
                module = __import__(self.module_path, fromlist=[self.function_name])
                self._function = getattr(module, self.function_name)

            # Prepare arguments
            kwargs = {**context, **self.config.parameters}

            # Execute function
            if asyncio.iscoroutinefunction(self._function):
                output = await self._function(**kwargs)
            else:
                output = self._function(**kwargs)

            result.output = {"result": output}
            result.set_completed(True)

        except Exception as e:
            result.add_error(f"Python function execution failed: {str(e)}")
            result.set_completed(False)

        return result

    def validate_config(self) -> List[str]:
        """Validate Python utility configuration."""
        errors = []

        if not self.function_name:
            errors.append("Function name is required")

        if not self.module_path:
            errors.append("Module path is required")

        # Try to import the module and function
        try:
            module = __import__(self.module_path, fromlist=[self.function_name])
            if not hasattr(module, self.function_name):
                errors.append(
                    f"Function '{self.function_name}' not found in module '{self.module_path}'"
                )
        except ImportError as e:
            errors.append(f"Cannot import module '{self.module_path}': {str(e)}")

        return errors
