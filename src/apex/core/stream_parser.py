"""Streaming JSON parser for Claude CLI output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, List, Optional

import msgpack
import uuid

from .lmdb_mcp import LMDBMCP


@dataclass
class SystemEvent:
    """System event from Claude CLI."""

    content: dict


@dataclass
class AssistantEvent:
    """Assistant event from Claude CLI."""

    content: dict


@dataclass
class ToolCallEvent:
    """Tool call event from Claude CLI."""

    content: dict


class StreamParser:
    """Parse streaming JSON lines from Claude CLI."""

    def __init__(self, mcp: Optional[LMDBMCP] = None) -> None:
        self.buffer = ""
        self.mcp = mcp
        self.filters: List[Callable[[object], bool]] = []

    def add_filter(self, filter_func: Callable[[object], bool]) -> None:
        """Register an event filter."""
        self.filters.append(filter_func)

    def _apply_filters(self, event: object) -> bool:
        for func in self.filters:
            if not func(event):
                return False
        return True

    def feed(self, data: str) -> Iterator[object]:
        """Feed data into the parser and yield events."""
        self.buffer += data
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = payload.get("type")
            if event_type == "system":
                event = SystemEvent(payload)
            elif event_type == "assistant":
                event = AssistantEvent(payload)
            elif event_type == "tool":
                event = ToolCallEvent(payload)
            else:
                event = payload
            if self._apply_filters(event):
                yield event

    def parse_lines(self, lines: Iterable[str]) -> Iterator[object]:
        """Convenience method to parse an iterable of lines."""
        for line in lines:
            yield from self.feed(line + "\n")

    def store_event(self, event: object) -> None:
        """Persist an event to LMDB if configured."""
        if self.mcp is None:
            return

        if isinstance(event, (SystemEvent, AssistantEvent, ToolCallEvent)):
            payload = event.content
        else:
            payload = event  # type: ignore[assignment]

        session_id = payload.get("session_id")
        if session_id is not None:
            key = f"/sessions/{session_id}/events/{uuid.uuid4().hex}"
            self.mcp.write(key, msgpack.packb(payload, use_bin_type=True))

        agent_id = payload.get("agent_id")
        if isinstance(event, AssistantEvent) and agent_id is not None:
            message = payload.get("message", payload)
            key = f"/agents/{agent_id}/messages/{uuid.uuid4().hex}"
            self.mcp.write(key, msgpack.packb(message, use_bin_type=True))

        if isinstance(event, ToolCallEvent):
            tool_id = payload.get("tool_id")
            if tool_id is not None:
                key = f"/tools/calls/{tool_id}"
                self.mcp.write(key, msgpack.packb(payload, use_bin_type=True))
