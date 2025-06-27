"""Robust error handling and recovery mechanisms for APEX."""

from __future__ import annotations

import asyncio
import json
import logging
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field

from apex.core.memory import MemoryPatterns

T = TypeVar("T")


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""

    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    VALIDATION = "validation"
    ORCHESTRATION = "orchestration"
    AGENT = "agent"
    USER = "user"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    USER_INTERVENTION = "user_intervention"


class ErrorContext(BaseModel):
    """Context information for errors."""

    error_id: str = Field(
        default_factory=lambda: f"err-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    operation: str
    error_type: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_strategy: Optional[RecoveryStrategy] = None
    retry_count: int = 0
    max_retries: int = 3
    resolved: bool = False
    resolution_notes: Optional[str] = None


class RecoveryAction(BaseModel):
    """Recovery action definition."""

    action_id: str
    strategy: RecoveryStrategy
    description: str
    handler: Optional[str] = None  # Function name for custom handlers
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = 30
    fallback_action: Optional[str] = None


class ErrorRecoveryManager:
    """Manages error handling and recovery strategies."""

    def __init__(self, memory: MemoryPatterns):
        self.memory = memory
        self.logger = logging.getLogger(__name__)
        self.error_handlers: Dict[str, Callable] = {}
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        self.active_errors: Dict[str, ErrorContext] = {}

        # Register default recovery actions
        self._register_default_actions()

    def _register_default_actions(self) -> None:
        """Register default recovery actions."""
        self.recovery_actions.update(
            {
                "retry_with_backoff": RecoveryAction(
                    action_id="retry_with_backoff",
                    strategy=RecoveryStrategy.RETRY,
                    description="Retry operation with exponential backoff",
                    timeout=60,
                ),
                "fallback_to_simple": RecoveryAction(
                    action_id="fallback_to_simple",
                    strategy=RecoveryStrategy.FALLBACK,
                    description="Fallback to simplified operation mode",
                    timeout=30,
                ),
                "skip_and_continue": RecoveryAction(
                    action_id="skip_and_continue",
                    strategy=RecoveryStrategy.SKIP,
                    description="Skip failed operation and continue",
                    timeout=5,
                ),
                "abort_with_cleanup": RecoveryAction(
                    action_id="abort_with_cleanup",
                    strategy=RecoveryStrategy.ABORT,
                    description="Abort operation with proper cleanup",
                    timeout=30,
                ),
                "request_user_intervention": RecoveryAction(
                    action_id="request_user_intervention",
                    strategy=RecoveryStrategy.USER_INTERVENTION,
                    description="Request user intervention for resolution",
                    timeout=300,
                ),
            }
        )

    def register_error_handler(
        self,
        error_type: Type[Exception],
        handler: Callable[[Exception, ErrorContext], Any],
    ) -> None:
        """Register custom error handler."""
        self.error_handlers[error_type.__name__] = handler

    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        component: str = "unknown",
        operation: str = "unknown",
    ) -> ErrorContext:
        """Handle an error with appropriate recovery strategy."""
        # Create error context
        error_context = ErrorContext(
            severity=self._classify_severity(error),
            category=self._classify_category(error, context),
            component=component,
            operation=operation,
            error_type=type(error).__name__,
            message=str(error),
            details=context,
            stack_trace=traceback.format_exc(),
        )

        # Store error in memory
        await self._persist_error(error_context)

        # Determine recovery strategy
        recovery_strategy = self._determine_recovery_strategy(error_context)
        error_context.recovery_strategy = recovery_strategy

        # Log error
        self.logger.error(
            f"Error in {component}.{operation}: {error_context.message}",
            extra={"error_context": error_context.model_dump()},
        )

        # Execute recovery strategy
        await self._execute_recovery(error_context)

        return error_context

    def _classify_severity(self, error: Exception) -> ErrorSeverity:
        """Classify error severity."""
        # Critical errors that can crash the system
        critical_errors = (
            SystemExit,
            KeyboardInterrupt,
            MemoryError,
            OSError,
        )

        # High severity errors
        high_errors = (
            ConnectionError,
            TimeoutError,
            ValueError,
            TypeError,
        )

        # Medium severity errors
        medium_errors = (
            FileNotFoundError,
            PermissionError,
            AttributeError,
        )

        if isinstance(error, critical_errors):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, high_errors):
            return ErrorSeverity.HIGH
        elif isinstance(error, medium_errors):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _classify_category(
        self, error: Exception, context: Dict[str, Any]
    ) -> ErrorCategory:
        """Classify error category."""
        error_msg = str(error).lower()

        if any(
            term in error_msg
            for term in ["connection", "network", "timeout", "unreachable"]
        ):
            return ErrorCategory.NETWORK
        elif any(
            term in error_msg for term in ["database", "lmdb", "transaction", "cursor"]
        ):
            return ErrorCategory.DATABASE
        elif any(
            term in error_msg for term in ["validation", "schema", "format", "invalid"]
        ):
            return ErrorCategory.VALIDATION
        elif any(
            term in error_msg
            for term in ["orchestration", "task", "agent", "supervisor"]
        ):
            return ErrorCategory.ORCHESTRATION
        elif any(term in error_msg for term in ["agent", "worker", "process"]):
            return ErrorCategory.AGENT
        elif any(term in error_msg for term in ["user", "input", "command"]):
            return ErrorCategory.USER
        else:
            return ErrorCategory.SYSTEM

    def _determine_recovery_strategy(
        self, error_context: ErrorContext
    ) -> RecoveryStrategy:
        """Determine appropriate recovery strategy."""
        severity = error_context.severity
        category = error_context.category

        # Critical errors require immediate abort
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.ABORT

        # Network errors are often transient, retry with backoff
        if category == ErrorCategory.NETWORK:
            return RecoveryStrategy.RETRY

        # Database errors might be recoverable with retry
        if category == ErrorCategory.DATABASE:
            return RecoveryStrategy.RETRY

        # Validation errors need user intervention
        if category == ErrorCategory.VALIDATION:
            return RecoveryStrategy.USER_INTERVENTION

        # Orchestration errors can often be skipped
        if category == ErrorCategory.ORCHESTRATION:
            return (
                RecoveryStrategy.SKIP
                if severity == ErrorSeverity.LOW
                else RecoveryStrategy.FALLBACK
            )

        # Agent errors might need fallback
        if category == ErrorCategory.AGENT:
            return RecoveryStrategy.FALLBACK

        # Default to retry for unknown cases
        return RecoveryStrategy.RETRY

    async def _execute_recovery(self, error_context: ErrorContext) -> None:
        """Execute recovery strategy."""
        if not error_context.recovery_strategy:
            return

        strategy = error_context.recovery_strategy

        if strategy == RecoveryStrategy.RETRY:
            await self._handle_retry_recovery(error_context)
        elif strategy == RecoveryStrategy.FALLBACK:
            await self._handle_fallback_recovery(error_context)
        elif strategy == RecoveryStrategy.SKIP:
            await self._handle_skip_recovery(error_context)
        elif strategy == RecoveryStrategy.ABORT:
            await self._handle_abort_recovery(error_context)
        elif strategy == RecoveryStrategy.USER_INTERVENTION:
            await self._handle_user_intervention_recovery(error_context)

    async def _handle_retry_recovery(self, error_context: ErrorContext) -> None:
        """Handle retry recovery strategy."""
        self.logger.info(f"Scheduling retry for error {error_context.error_id}")

        # Store retry information
        retry_key = f"/errors/{error_context.error_id}/retry"
        retry_data = {
            "error_id": error_context.error_id,
            "retry_count": error_context.retry_count + 1,
            "scheduled_at": datetime.now().isoformat(),
            "backoff_seconds": min(2**error_context.retry_count, 60),
        }
        await self.memory.mcp.write(retry_key, json.dumps(retry_data))

    async def _handle_fallback_recovery(self, error_context: ErrorContext) -> None:
        """Handle fallback recovery strategy."""
        self.logger.info(f"Activating fallback mode for error {error_context.error_id}")

        # Store fallback state
        fallback_key = f"/errors/{error_context.error_id}/fallback"
        fallback_data = {
            "error_id": error_context.error_id,
            "fallback_mode": True,
            "activated_at": datetime.now().isoformat(),
            "original_operation": error_context.operation,
        }
        await self.memory.mcp.write(fallback_key, json.dumps(fallback_data))

    async def _handle_skip_recovery(self, error_context: ErrorContext) -> None:
        """Handle skip recovery strategy."""
        self.logger.info(
            f"Skipping failed operation for error {error_context.error_id}"
        )

        # Mark as resolved by skipping
        error_context.resolved = True
        error_context.resolution_notes = "Operation skipped due to non-critical error"
        await self._persist_error(error_context)

    async def _handle_abort_recovery(self, error_context: ErrorContext) -> None:
        """Handle abort recovery strategy."""
        self.logger.critical(f"Aborting due to critical error {error_context.error_id}")

        # Store abort information
        abort_key = f"/errors/{error_context.error_id}/abort"
        abort_data = {
            "error_id": error_context.error_id,
            "aborted": True,
            "abort_reason": error_context.message,
            "aborted_at": datetime.now().isoformat(),
        }
        await self.memory.mcp.write(abort_key, json.dumps(abort_data))

    async def _handle_user_intervention_recovery(
        self, error_context: ErrorContext
    ) -> None:
        """Handle user intervention recovery strategy."""
        self.logger.warning(
            f"User intervention required for error {error_context.error_id}"
        )

        # Store user intervention request
        intervention_key = f"/errors/{error_context.error_id}/intervention"
        intervention_data = {
            "error_id": error_context.error_id,
            "intervention_required": True,
            "requested_at": datetime.now().isoformat(),
            "component": error_context.component,
            "operation": error_context.operation,
            "suggested_actions": self._suggest_user_actions(error_context),
        }
        await self.memory.mcp.write(intervention_key, json.dumps(intervention_data))

    def _suggest_user_actions(self, error_context: ErrorContext) -> List[str]:
        """Suggest user actions based on error context."""
        suggestions = []

        if error_context.category == ErrorCategory.VALIDATION:
            suggestions.extend(
                [
                    "Check input parameters for correct format",
                    "Verify configuration file syntax",
                    "Review error details for specific validation failures",
                ]
            )
        elif error_context.category == ErrorCategory.NETWORK:
            suggestions.extend(
                [
                    "Check network connectivity",
                    "Verify service endpoints are accessible",
                    "Review firewall and proxy settings",
                ]
            )
        elif error_context.category == ErrorCategory.DATABASE:
            suggestions.extend(
                [
                    "Check database connectivity",
                    "Verify database permissions",
                    "Review disk space availability",
                ]
            )
        else:
            suggestions.extend(
                [
                    "Review error details and stack trace",
                    "Check system logs for additional context",
                    "Consider restarting the affected component",
                ]
            )

        return suggestions

    async def _persist_error(self, error_context: ErrorContext) -> None:
        """Persist error context to memory."""
        error_key = f"/errors/{error_context.error_id}/context"
        await self.memory.mcp.write(error_key, error_context.model_dump_json())

        # Update active errors tracking
        self.active_errors[error_context.error_id] = error_context

    async def get_error_summary(
        self, project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get error summary for monitoring."""
        try:
            prefix = f"/projects/{project_id}/errors/" if project_id else "/errors/"
            error_keys = await self.memory.mcp.list_keys(prefix)

            summary = {
                "total_errors": len(error_keys),
                "by_severity": {s.value: 0 for s in ErrorSeverity},
                "by_category": {c.value: 0 for c in ErrorCategory},
                "by_strategy": {s.value: 0 for s in RecoveryStrategy},
                "resolved_count": 0,
                "pending_count": 0,
            }

            for key in error_keys:
                if key.endswith("/context"):
                    try:
                        error_json = await self.memory.mcp.read(key)
                        if error_json:
                            error_data = json.loads(error_json)
                            summary["by_severity"][
                                error_data.get("severity", "low")
                            ] += 1
                            summary["by_category"][
                                error_data.get("category", "system")
                            ] += 1

                            if error_data.get("recovery_strategy"):
                                summary["by_strategy"][
                                    error_data["recovery_strategy"]
                                ] += 1

                            if error_data.get("resolved", False):
                                summary["resolved_count"] += 1
                            else:
                                summary["pending_count"] += 1
                    except Exception:
                        continue

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get error summary: {e}")
            return {"error": str(e)}

    async def resolve_error(self, error_id: str, resolution_notes: str) -> bool:
        """Mark an error as resolved."""
        try:
            error_key = f"/errors/{error_id}/context"
            error_json = await self.memory.mcp.read(error_key)

            if not error_json:
                return False

            error_data = json.loads(error_json)
            error_data["resolved"] = True
            error_data["resolution_notes"] = resolution_notes
            error_data["resolved_at"] = datetime.now().isoformat()

            await self.memory.mcp.write(error_key, json.dumps(error_data))

            # Remove from active errors
            if error_id in self.active_errors:
                del self.active_errors[error_id]

            self.logger.info(f"Error {error_id} marked as resolved: {resolution_notes}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to resolve error {error_id}: {e}")
            return False


@asynccontextmanager
async def error_handler(
    memory: MemoryPatterns,
    component: str,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
):
    """Context manager for error handling."""
    error_manager = ErrorRecoveryManager(memory)

    try:
        yield error_manager
    except Exception as e:
        await error_manager.handle_error(
            error=e,
            context=context or {},
            component=component,
            operation=operation,
        )
        raise  # Re-raise the exception after handling


class RetryableOperation:
    """Decorator for retryable operations."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,),
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except self.exceptions as e:
                    last_exception = e

                    if attempt < self.max_retries:
                        backoff_time = self.backoff_factor**attempt
                        await asyncio.sleep(backoff_time)
                        continue
                    else:
                        break

            if last_exception:
                raise last_exception

        return wrapper


def with_error_recovery(
    component: str,
    operation: str,
    memory: MemoryPatterns,
    context: Optional[Dict[str, Any]] = None,
):
    """Decorator for automatic error recovery."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args, **kwargs) -> T:
            async with error_handler(
                memory, component, operation, context
            ) as error_mgr:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
