"""Streaming JSON parser for Claude CLI output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional


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

    def __init__(self) -> None:
        self.buffer = ""

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
                yield SystemEvent(payload)
            elif event_type == "assistant":
                yield AssistantEvent(payload)
            elif event_type == "tool":
                yield ToolCallEvent(payload)
            else:
                yield payload

    def parse_lines(self, lines: Iterable[str]) -> Iterator[object]:
        """Convenience method to parse an iterable of lines."""
        for line in lines:
            yield from self.feed(line + "\n")
