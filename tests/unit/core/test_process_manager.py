"""Tests for ProcessManager."""

import sys
import time

from apex.core import ProcessManager


def test_process_lifecycle():
    manager = ProcessManager()
    cmd = [sys.executable, "-c", "import time; time.sleep(0.5)"]
    manager.spawn("test", cmd)
    assert manager.health_check("test") is True

    usage = manager.monitor_resources()
    assert "test" in usage

    manager.stop("test")
    time.sleep(0.1)
    assert manager.health_check("test") is False
    manager.shutdown()
