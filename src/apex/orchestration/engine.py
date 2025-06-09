"""Main orchestration engine."""

from __future__ import annotations

from typing import Callable, Iterable, Optional

from apex.types import SessionState

from .events import EventBus
from .session import SessionManager


class OrchestrationEngine:
    """Execute workflows across agents."""

    def __init__(
        self, session_manager: SessionManager, event_bus: Optional[EventBus] = None
    ):
        """Initialize orchestration engine.

        Args:
            session_manager: Session manager instance
            event_bus: Optional event bus for communication

        """
        self.session_manager = session_manager
        self.event_bus = event_bus or EventBus()

    def run_workflow(
        self, session_id: str, steps: Iterable[Callable[[], None]]
    ) -> None:
        """Execute a series of tasks for the given session."""
        session = self.session_manager.get(session_id)
        if session is None:
            raise ValueError("Session not found")

        session.state = SessionState.ACTIVE
        self.session_manager.update(session)
        self.event_bus.publish("session_started", {"session_id": session_id})

        for step in steps:
            step_name = getattr(step, "__name__", "step")
            self.event_bus.publish(
                "task_started", {"session_id": session_id, "task": step_name}
            )
            try:
                step()
                self.event_bus.publish(
                    "task_completed", {"session_id": session_id, "task": step_name}
                )
            except Exception as exc:  # pylint: disable=broad-except
                session.state = SessionState.FAILED
                self.session_manager.update(session)
                self.event_bus.publish(
                    "task_failed",
                    {"session_id": session_id, "task": step_name, "error": str(exc)},
                )
                raise

        session.state = SessionState.INACTIVE
        self.session_manager.update(session)
        self.event_bus.publish("session_finished", {"session_id": session_id})
