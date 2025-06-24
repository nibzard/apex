"""Agent status widget for TUI."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Static


class AgentStatusWidget(Static):
    """Widget displaying agent status with live updates."""

    agents_data: reactive[Dict[str, Dict[str, Any]]] = reactive({})
    agent_history: reactive[Dict[str, List[Dict[str, Any]]]] = reactive({})

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
        self.update_timer = self.set_interval(0.5, self.update_status)  # Faster updates
        self.update_status()

    def on_unmount(self) -> None:
        """Stop updating when unmounted."""
        if self.update_timer:
            self.update_timer.stop()

    def update_status(self) -> None:
        """Update agent status from runner and LMDB."""
        new_data = {}

        # Get process status from runner
        if self.agent_runner:
            try:
                status = self.agent_runner.get_agent_status()
                for name, info in status.items():
                    new_data[name] = info.copy()
            except Exception:
                pass

        # Enhance with LMDB memory data
        if self.lmdb_client:
            try:
                # Get all agent status keys
                keys = self.lmdb_client.list_keys("/agents/")

                for key in keys:
                    if "/status" in key:
                        try:
                            value = self.lmdb_client.read(key)
                            if value:
                                data = json.loads(
                                    value.decode()
                                    if isinstance(value, bytes)
                                    else value
                                )
                                agent_type = key.split("/")[
                                    2
                                ]  # Extract agent type from key

                                if agent_type in new_data:
                                    # Merge LMDB data with process data
                                    new_data[agent_type].update(data)
                                else:
                                    # Agent not running, but has status in LMDB
                                    new_data[agent_type] = {
                                        "running": False,
                                        "agent_type": agent_type,
                                        **data,
                                    }
                        except Exception:
                            continue

                # Check for active tasks
                task_keys = self.lmdb_client.list_keys("/tasks/pending/")
                for key in task_keys:
                    try:
                        value = self.lmdb_client.read(key)
                        if value:
                            task = json.loads(
                                value.decode() if isinstance(value, bytes) else value
                            )
                            assigned_to = task.get("assigned_to", "").lower()
                            if assigned_to in new_data:
                                new_data[assigned_to]["current_task"] = task.get(
                                    "description", "Unknown task"
                                )
                                new_data[assigned_to]["task_id"] = task.get("id", "")
                    except Exception:
                        continue

            except Exception:
                pass

        # Update history for each agent
        for agent_name, data in new_data.items():
            if agent_name not in self.agent_history:
                self.agent_history[agent_name] = []

            # Add timestamp to history entry
            history_entry = {"timestamp": datetime.now().isoformat(), **data}

            # Keep last 100 entries
            self.agent_history[agent_name].append(history_entry)
            if len(self.agent_history[agent_name]) > 100:
                self.agent_history[agent_name] = self.agent_history[agent_name][-100:]

        self.agents_data = new_data

    def watch_agents_data(self, old_data: Dict, new_data: Dict) -> None:
        """React to agent data changes."""
        self.update_display()

    def update_display(self) -> None:
        """Update the displayed content with enhanced information."""
        lines = ["[bold cyan]Agent Status Monitor[/bold cyan]\n"]

        if not self.agents_data:
            lines.append("[dim]No agents detected[/dim]")
        else:
            # Sort agents by type for consistent display
            agent_order = ["supervisor", "coder", "adversary"]
            sorted_agents = sorted(
                self.agents_data.items(),
                key=lambda x: agent_order.index(x[0]) if x[0] in agent_order else 999,
            )

            for name, info in sorted_agents:
                # Status icon with more states
                if info.get("running"):
                    if info.get("current_task"):
                        status_icon = "🟡"  # Working
                    else:
                        status_icon = "🟢"  # Idle
                else:
                    status_icon = "🔴"  # Stopped

                # Memory usage with color coding
                memory = info.get("memory", 0)
                memory_mb = memory // 1024 // 1024 if memory else 0
                memory_color = (
                    "green"
                    if memory_mb < 100
                    else "yellow"
                    if memory_mb < 200
                    else "red"
                )
                memory_str = f"[{memory_color}]{memory_mb} MB[/{memory_color}]"

                # Uptime with better formatting
                start_time = info.get("start_time")
                if start_time:
                    uptime = int(datetime.now().timestamp() - start_time)
                    hours = uptime // 3600
                    minutes = (uptime % 3600) // 60
                    seconds = uptime % 60
                    if hours > 0:
                        uptime_str = f"{hours}h {minutes}m"
                    else:
                        uptime_str = f"{minutes}m {seconds}s"
                else:
                    uptime_str = "N/A"

                # Agent type with proper casing
                agent_type = info.get("agent_type", name).title()

                # Current task with progress indicator
                current_task = info.get("current_task", "Idle")
                info.get("task_id", "")

                # Get progress from LMDB if available
                progress = info.get("progress", 0)
                if progress > 0 and progress < 100:
                    progress_bar = self._create_progress_bar(progress, 10)
                    task_display = f"{current_task[:20]}... {progress_bar} {progress}%"
                else:
                    task_display = (
                        current_task[:40] + "..."
                        if len(current_task) > 40
                        else current_task
                    )

                # CPU usage if available
                cpu_str = ""
                if "cpu_percent" in info:
                    cpu = info["cpu_percent"]
                    cpu_color = "green" if cpu < 50 else "yellow" if cpu < 80 else "red"
                    cpu_str = (
                        f" [dim]│[/dim] CPU: [{cpu_color}]{cpu:.1f}%[/{cpu_color}]"
                    )

                lines.append(
                    f"{status_icon} [bold]{agent_type}[/bold] "
                    f"[dim]│[/dim] Mem: {memory_str} "
                    f"[dim]│[/dim] Up: [green]{uptime_str}[/green]"
                    f"{cpu_str} "
                    f"[dim]│[/dim] Task: [cyan]{task_display}[/cyan]"
                )

                # Add last activity if available
                last_activity = info.get("last_activity")
                if last_activity:
                    try:
                        last_time = datetime.fromisoformat(
                            last_activity.replace("Z", "+00:00")
                        )
                        time_ago = (datetime.now() - last_time).total_seconds()
                        if time_ago < 60:
                            activity_str = f"{int(time_ago)}s ago"
                        elif time_ago < 3600:
                            activity_str = f"{int(time_ago / 60)}m ago"
                        else:
                            activity_str = f"{int(time_ago / 3600)}h ago"
                        lines.append(f"   [dim]Last activity: {activity_str}[/dim]")
                    except Exception:
                        pass

        self.update("\n".join(lines))

    def _create_progress_bar(self, progress: float, width: int = 10) -> str:
        """Create a simple progress bar."""
        filled = int((progress / 100) * width)
        empty = width - filled
        return "[blue]" + "█" * filled + "[/blue][dim]" + "░" * empty + "[/dim]"
