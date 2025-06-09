"""Tests for ProcessManager."""

import sys
import time

from apex.core import ProcessManager


def test_process_lifecycle():
    """Test basic process lifecycle operations."""
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


def test_monitor_restart_on_failure():
    """Test process monitoring and restart on failure."""
    manager = ProcessManager()
    cmd = [sys.executable, "-c", "import time; time.sleep(5)"]
    manager.spawn("mon", cmd)
    manager.monitor(start=True, interval=0.05)
    time.sleep(0.1)

    proc = manager.processes["mon"].process
    proc.kill()
    proc.wait()

    time.sleep(0.2)
    manager.monitor(start=False)

    assert manager.restart_events.get("mon", 0) >= 1
    assert manager.health_check("mon") is True
    manager.shutdown()
