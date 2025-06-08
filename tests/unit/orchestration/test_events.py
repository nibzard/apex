"""Tests for EventBus."""

from apex.orchestration import EventBus


def test_publish_and_replay(tmp_path):
    bus = EventBus(tmp_path / "events.db")
    bus.publish("test", {"foo": "bar"})

    events = bus.replay()
    assert len(events) == 1
    assert events[0]["type"] == "test"
    assert events[0]["data"]["foo"] == "bar"
