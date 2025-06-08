"""Tests for StateStore."""

from apex.orchestration import StateStore


def test_set_get_delete(tmp_path):
    store = StateStore(tmp_path / "state.db")

    store.set("foo", {"bar": 1})
    assert store.get("foo") == {"bar": 1}

    assert store.delete("foo") is True
    assert store.get("foo") is None
