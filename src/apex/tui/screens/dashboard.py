from typing import Any, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from ..widgets import (
    AgentStatusWidget,
    LogViewerWidget,
    MetricsWidget,
)


class DashboardScreen(Screen):
    """Main dashboard screen for APEX."""

    BINDINGS = [
        ("q", "app.quit", "Quit"),
        ("a", "show_agents", "Agents"),
        ("m", "show_memory", "Memory"),
        ("r", "refresh", "Refresh"),
    ]

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

    def compose(self) -> ComposeResult:
        """Compose the dashboard screen layout."""
        yield Header(show_clock=True)

        with Container(id="dashboard-container"):
            yield Static("[bold]APEX Dashboard[/bold]", id="dashboard-title")

            # Top row: Agent Status and Metrics
            with Horizontal(id="top-row"):
                with Vertical(id="left-panel"):
                    yield AgentStatusWidget(
                        agent_runner=self.agent_runner,
                        lmdb_client=self.lmdb_client,
                        id="agent-status-widget",
                    )

                with Vertical(id="right-panel"):
                    yield MetricsWidget(
                        agent_runner=self.agent_runner,
                        lmdb_client=self.lmdb_client,
                        id="metrics-widget",
                    )

            # Middle: Log viewer
            yield Static("\n[bold]Recent Activity[/bold]", id="activity-title")
            yield LogViewerWidget(
                lmdb_client=self.lmdb_client, max_logs=50, id="activity-log"
            )

            # Bottom: Quick actions
            yield Static("\n[bold]Quick Actions[/bold]", id="actions-title")
            with Horizontal(id="quick-actions"):
                yield Button("Agents Screen", id="btn-agents", variant="primary")
                yield Button("Memory Browser", id="btn-memory", variant="primary")
                yield Button("Start All", id="btn-start-all", variant="success")
                yield Button("Stop All", id="btn-stop-all", variant="error")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "btn-agents":
            await self.action_show_agents()
        elif button_id == "btn-memory":
            await self.action_show_memory()
        elif button_id == "btn-start-all":
            await self.start_all_agents()
        elif button_id == "btn-stop-all":
            await self.stop_all_agents()

    async def action_show_agents(self) -> None:
        """Show agents screen."""
        from .agents import AgentsScreen

        await self.app.push_screen(
            AgentsScreen(agent_runner=self.agent_runner, lmdb_client=self.lmdb_client)
        )

    async def action_show_memory(self) -> None:
        """Show memory screen."""
        from .memory import MemoryScreen

        await self.app.push_screen(MemoryScreen(lmdb_client=self.lmdb_client))

    def action_refresh(self) -> None:
        """Refresh all widgets."""
        # Refresh agent status
        agent_widget = self.query_one("#agent-status-widget", AgentStatusWidget)
        agent_widget.update_status()

        # Refresh metrics
        metrics_widget = self.query_one("#metrics-widget", MetricsWidget)
        metrics_widget.update_metrics()

        self.notify("Dashboard refreshed")

    async def start_all_agents(self) -> None:
        """Start all agents."""
        if not self.agent_runner:
            self.notify("No agent runner available", severity="error")
            return

        try:
            from apex.types import AgentType

            for agent_type in [
                AgentType.SUPERVISOR,
                AgentType.CODER,
                AgentType.ADVERSARY,
            ]:
                await self.agent_runner.start_agent(agent_type)

            self.notify("Started all agents")
        except Exception as e:
            self.notify(f"Error starting agents: {str(e)}", severity="error")

    async def stop_all_agents(self) -> None:
        """Stop all agents."""
        if not self.agent_runner:
            self.notify("No agent runner available", severity="error")
            return

        try:
            await self.agent_runner.stop_all_agents()
            self.notify("Stopped all agents")
        except Exception as e:
            self.notify(f"Error stopping agents: {str(e)}", severity="error")
