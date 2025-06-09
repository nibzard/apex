"""Agent status widget for TUI."""

from typing import Dict, Any, Optional
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static
from textual.timer import Timer


class AgentStatusWidget(Static):
    """Widget displaying agent status with live updates."""

    agents_data: reactive[Dict[str, Dict[str, Any]]] = reactive({})

    def __init__(self, agent_runner: Optional[Any] = None, **kwargs) -> None:
        """Initialize with optional agent runner."""
        super().__init__(**kwargs)
        self.agent_runner = agent_runner
        self.update_timer: Optional[Timer] = None

    def on_mount(self) -> None:
        """Start updating when mounted."""
        if self.agent_runner:
            self.update_timer = self.set_interval(1.0, self.update_status)
            self.update_status()

    def on_unmount(self) -> None:
        """Stop updating when unmounted."""
        if self.update_timer:
            self.update_timer.stop()

    def update_status(self) -> None:
        """Update agent status from runner."""
        if not self.agent_runner:
            return

        try:
            status = self.agent_runner.get_agent_status()
            self.agents_data = status
        except Exception:
            pass

    def watch_agents_data(self, old_data: Dict, new_data: Dict) -> None:
        """React to agent data changes."""
        self.update_display()

    def update_display(self) -> None:
        """Update the displayed content."""
        lines = ["[bold cyan]Agent Status[/bold cyan]\n"]

        if not self.agents_data:
            lines.append("[dim]No agents running[/dim]")
        else:
            for name, info in self.agents_data.items():
                # Status icon
                status_icon = "🟢" if info.get("running") else "🔴"

                # Memory usage
                memory = info.get("memory", 0)
                memory_str = f"{memory // 1024 // 1024} MB" if memory else "N/A"

                # Uptime
                start_time = info.get("start_time")
                if start_time:
                    uptime = int(datetime.now().timestamp() - start_time)
                    uptime_str = f"{uptime // 60}m {uptime % 60}s"
                else:
                    uptime_str = "N/A"

                # Agent type
                agent_type = info.get("agent_type", "unknown").title()

                # Current task
                current_task = info.get("current_task", "Idle")
                if len(current_task) > 30:
                    current_task = current_task[:27] + "..."

                lines.append(
                    f"{status_icon} [bold]{agent_type}[/bold] "
                    f"[dim]│[/dim] Mem: [yellow]{memory_str}[/yellow] "
                    f"[dim]│[/dim] Up: [green]{uptime_str}[/green] "
                    f"[dim]│[/dim] Task: [cyan]{current_task}[/cyan]"
                )

        self.update("\n".join(lines))
