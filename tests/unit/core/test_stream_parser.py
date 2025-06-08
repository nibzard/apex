"""Tests for StreamParser."""

import msgpack

from apex.core import LMDBMCP, StreamParser, SystemEvent, AssistantEvent, ToolCallEvent


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


def test_event_persistence(tmp_path):
    mcp = LMDBMCP(tmp_path / "db")
    parser = StreamParser(mcp)
    lines = [
        '{"type": "system", "session_id": "s1", "agent_id": "a1"}',
        '{"type": "assistant", "session_id": "s1", "agent_id": "a1", "message": {"text": "hi"}}',
        '{"type": "tool", "session_id": "s1", "agent_id": "a1", "tool_id": "t1"}',
    ]
    events = list(parser.parse_lines(lines))
    for e in events:
        parser.store_event(e)

    keys = mcp.list_keys()
    session_keys = [k for k in keys if k.startswith("/sessions/s1/events/")]
    agent_keys = [k for k in keys if k.startswith("/agents/a1/messages/")]

    assert len(session_keys) == 3
    assert len(agent_keys) == 1
    assert "/tools/calls/t1" in keys

    # Validate stored message content
    data = mcp.read(agent_keys[0])
    assert data is not None
    message = msgpack.unpackb(data, raw=False)
    assert message["text"] == "hi"
