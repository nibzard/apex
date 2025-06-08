"""Tests for StreamParser."""

from apex.core import StreamParser, SystemEvent, AssistantEvent, ToolCallEvent


def test_parse_lines():
    lines = [
        '{"type": "system", "msg": "hello"}',
        '{"type": "assistant", "msg": "hi"}',
        '{"type": "tool", "tool": "t"}',
    ]
    parser = StreamParser()
    events = list(parser.parse_lines(lines))
    assert isinstance(events[0], SystemEvent)
    assert isinstance(events[1], AssistantEvent)
    assert isinstance(events[2], ToolCallEvent)
