"""Metrics widget for TUI."""

from typing import Any, Dict, Optional

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Static
from textual.timer import Timer


class MetricsWidget(Static):
    """Widget displaying system and agent metrics."""

    metrics_data: reactive[Dict[str, Any]] = reactive({})

    def __init__(
        self,
        agent_runner: Optional[Any] = None,
        lmdb_client: Optional[Any] = None,
        **kwargs,
    ) -> None:
        """Initialize with optional agent runner and LMDB client."""
        super().__init__(**kwargs)
        self.agent_runner = agent_runner
        self.lmdb_client = lmdb_client
        self.update_timer: Optional[Timer] = None

    def on_mount(self) -> None:
        """Start updating when mounted."""
        self.update_timer = self.set_interval(2.0, self.update_metrics)
        self.update_metrics()

    def on_unmount(self) -> None:
        """Stop updating when unmounted."""
        if self.update_timer:
            self.update_timer.stop()

    def update_metrics(self) -> None:
        """Update metrics from various sources."""
        metrics = {
            "agents": {"total": 0, "running": 0, "stopped": 0},
            "tasks": {"pending": 0, "completed": 0, "failed": 0},
            "memory": {"keys": 0, "size": "N/A"},
            "performance": {"cpu": "N/A", "memory": "N/A"},
        }

        # Agent metrics
        if self.agent_runner:
            try:
                status = self.agent_runner.get_agent_status()
                metrics["agents"]["total"] = len(status)
                metrics["agents"]["running"] = sum(
                    1 for s in status.values() if s.get("running")
                )
                metrics["agents"]["stopped"] = (
                    metrics["agents"]["total"] - metrics["agents"]["running"]
                )
            except Exception:
                pass

        # Memory metrics
        if self.lmdb_client:
            try:
                keys = self.lmdb_client.list_keys("")
                metrics["memory"]["keys"] = len(keys)

                # Count tasks
                pending_tasks = [k for k in keys if "/tasks/pending/" in k]
                completed_tasks = [k for k in keys if "/tasks/completed/" in k]
                metrics["tasks"]["pending"] = len(pending_tasks)
                metrics["tasks"]["completed"] = len(completed_tasks)
            except Exception:
                pass

        self.metrics_data = metrics

    def watch_metrics_data(self, old_data: Dict, new_data: Dict) -> None:
        """React to metrics data changes."""
        self.update_display()

    def update_display(self) -> None:
        """Update the displayed metrics."""
        m = self.metrics_data

        lines = [
            "[bold cyan]System Metrics[/bold cyan]",
            "",
            "[bold]Agents[/bold]",
            f"  Running: [green]{m['agents']['running']}[/green] / {m['agents']['total']}",
            f"  Stopped: [red]{m['agents']['stopped']}[/red]",
            "",
            "[bold]Tasks[/bold]",
            f"  Pending: [yellow]{m['tasks']['pending']}[/yellow]",
            f"  Completed: [green]{m['tasks']['completed']}[/green]",
            "",
            "[bold]Memory[/bold]",
            f"  Keys: [blue]{m['memory']['keys']}[/blue]",
            f"  Size: {m['memory']['size']}",
            "",
            "[bold]Performance[/bold]",
            f"  CPU: {m['performance']['cpu']}",
            f"  Memory: {m['performance']['memory']}",
        ]

        self.update("\n".join(lines))
