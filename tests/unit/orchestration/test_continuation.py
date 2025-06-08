"""Tests for ContinuationManager."""

from apex.orchestration import ContinuationManager


def test_save_and_load_checkpoint(tmp_path):
    manager = ContinuationManager(tmp_path)
    state = {"counter": 1}

    path = manager.save_checkpoint("sess", state)
    loaded = manager.load_checkpoint("sess", path)

    assert loaded == state
