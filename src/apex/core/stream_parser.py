"""Streaming JSON parser for Claude CLI output."""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
)

import msgpack

from .lmdb_mcp import LMDBMCP


@dataclass
class StreamEvent:
    """Base class for all stream events."""

    event_type: str
    timestamp: datetime
    agent_id: str
    session_id: str
    content: dict


@dataclass
class SystemEvent(StreamEvent):
    """System event from Claude CLI."""

    def __post_init__(self) -> None:
        """Initialize system event."""
        self.event_type = "system"


@dataclass
class AssistantEvent(StreamEvent):
    """Assistant event from Claude CLI."""

    def __post_init__(self) -> None:
        """Initialize assistant event."""
        self.event_type = "assistant"


@dataclass
class ToolCallEvent(StreamEvent):
    """Tool call event from Claude CLI."""

    tool_name: str
    tool_id: str
    parameters: dict

    def __post_init__(self) -> None:
        """Initialize tool call event."""
        self.event_type = "tool_call"


@dataclass
class ToolResultEvent(StreamEvent):
    """Tool result event from Claude CLI."""

    tool_id: str
    result: Any
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize tool result event."""
        self.event_type = "tool_result"


class StreamParser:
    """Parse streaming JSON lines from Claude CLI."""

    def __init__(
        self, agent_id: str, session_id: str, mcp: Optional[LMDBMCP] = None
    ) -> None:
        """Initialize stream parser.

        Args:
            agent_id: ID of the agent producing the stream
            session_id: ID of the current session
            mcp: Optional LMDB MCP instance for persistence

        """
        self.agent_id = agent_id
        self.session_id = session_id
        self.buffer = ""
        self.mcp = mcp
        self.filters: List[Callable[[StreamEvent], bool]] = []

    def add_filter(self, filter_func: Callable[[StreamEvent], bool]) -> None:
        """Register an event filter."""
        self.filters.append(filter_func)

    def _apply_filters(self, event: StreamEvent) -> bool:
        """Apply all registered filters to an event."""
        for func in self.filters:
            if not func(event):
                return False
        return True

    def parse_event(self, payload: Dict[str, Any]) -> Optional[StreamEvent]:
        """Parse a single JSON payload into a StreamEvent."""
        event_type = payload.get("type")
        timestamp = datetime.now()

        # Create base event data
        base_data = {
            "timestamp": timestamp,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "content": payload,
        }

        if event_type == "system":
            return SystemEvent(event_type="system", **base_data)

        elif event_type == "assistant":
            return AssistantEvent(event_type="assistant", **base_data)

        elif event_type == "tool_use":
            # Extract tool call information
            tool_name = payload.get("name", "")
            tool_id = payload.get("id", "")
            parameters = payload.get("input", {})

            return ToolCallEvent(
                event_type="tool_call",
                tool_name=tool_name,
                tool_id=tool_id,
                parameters=parameters,
                **base_data,
            )

        elif event_type == "tool_result":
            # Extract tool result information
            tool_id = payload.get("tool_use_id", "")
            result = payload.get("content", [])
            error = payload.get("error")

            return ToolResultEvent(
                event_type="tool_result",
                tool_id=tool_id,
                result=result,
                error=error,
                **base_data,
            )

        # For unknown event types, create a generic StreamEvent
        return StreamEvent(event_type=event_type or "unknown", **base_data)

    def feed(self, data: str) -> Iterator[StreamEvent]:
        """Feed data into the parser and yield events."""
        self.buffer += data
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                event = self.parse_event(payload)
                if event and self._apply_filters(event):
                    yield event
            except json.JSONDecodeError:
                continue

    def parse_lines(self, lines: Iterable[str]) -> Iterator[StreamEvent]:
        """Parse an iterable of lines."""
        for line in lines:
            yield from self.feed(line + "\n")

    async def parse_stream_async(
        self, stream: AsyncIterator[Dict[str, Any]]
    ) -> AsyncIterator[StreamEvent]:
        """Parse events from an async stream."""
        async for payload in stream:
            event = self.parse_event(payload)
            if event and self._apply_filters(event):
                yield event

    async def store_event(self, event: StreamEvent) -> None:
        """Persist an event to LMDB if configured."""
        if self.mcp is None:
            return

        # Store in session events
        event_key = f"/sessions/{event.session_id}/events/{uuid.uuid4().hex}"
        event_data = {
            "type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "agent_id": event.agent_id,
            "content": event.content,
        }
        await self._write_to_lmdb(event_key, event_data)

        # Store agent-specific data
        if isinstance(event, AssistantEvent):
            message_key = f"/agents/{event.agent_id}/messages/{uuid.uuid4().hex}"
            message_data = {
                "timestamp": event.timestamp.isoformat(),
                "content": event.content,
            }
            await self._write_to_lmdb(message_key, message_data)

        elif isinstance(event, ToolCallEvent):
            tool_key = f"/tools/calls/{event.tool_id}"
            tool_data = {
                "agent_id": event.agent_id,
                "tool_name": event.tool_name,
                "parameters": event.parameters,
                "timestamp": event.timestamp.isoformat(),
            }
            await self._write_to_lmdb(tool_key, tool_data)

        elif isinstance(event, ToolResultEvent):
            result_key = f"/tools/results/{event.tool_id}"
            result_data = {
                "agent_id": event.agent_id,
                "result": event.result,
                "error": event.error,
                "timestamp": event.timestamp.isoformat(),
            }
            await self._write_to_lmdb(result_key, result_data)

    async def _write_to_lmdb(self, key: str, data: Dict[str, Any]) -> None:
        """Write data to LMDB (async wrapper)."""
        if self.mcp:
            # Convert to bytes for LMDB storage
            serialized_data = msgpack.packb(data, use_bin_type=True)
            # Note: Current LMDB implementation is sync, would need async version
            await asyncio.get_event_loop().run_in_executor(
                None, self.mcp.write, key, serialized_data
            )
