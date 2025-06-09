"""Tests for StreamParser."""

import asyncio
import msgpack
import pytest

from apex.core import LMDBMCP, AssistantEvent, StreamParser, SystemEvent, ToolCallEvent


def test_parse_lines():
    """Test parsing different types of stream events."""
    lines = [
        '{"type": "system", "msg": "hello"}',
        '{"type": "assistant", "msg": "hi"}',
        '{"type": "tool_use", "name": "test_tool", "id": "t1", "input": {}}',
    ]
    parser = StreamParser(agent_id="test_agent", session_id="test_session")
    events = list(parser.parse_lines(lines))
    assert isinstance(events[0], SystemEvent)
    assert isinstance(events[1], AssistantEvent)
    assert isinstance(events[2], ToolCallEvent)


@pytest.mark.asyncio
async def test_event_persistence(tmp_path):
    """Test event persistence to LMDB storage."""
    mcp = LMDBMCP(tmp_path / "db")
    parser = StreamParser(agent_id="a1", session_id="s1", mcp=mcp)
    lines = [
        '{"type": "system", "msg": "system message"}',
        '{"type": "assistant", "message": {"text": "hi"}}',
        '{"type": "tool_use", "name": "test_tool", "id": "t1", "input": {"param": "value"}}',
    ]
    events = list(parser.parse_lines(lines))
    
    # Store events asynchronously
    for e in events:
        await parser.store_event(e)

    keys = mcp.list_keys()
    session_keys = [k for k in keys if k.startswith("/sessions/s1/events/")]
    agent_keys = [k for k in keys if k.startswith("/agents/a1/messages/")]

    assert len(session_keys) == 3  # All events stored in session
    assert len(agent_keys) == 1   # Only assistant message stored in agent messages
    assert "/tools/calls/t1" in keys  # Tool call stored

    # Validate stored message content
    data = mcp.read(agent_keys[0])
    assert data is not None
    message = msgpack.unpackb(data, raw=False)
    assert message["content"]["message"]["text"] == "hi"
