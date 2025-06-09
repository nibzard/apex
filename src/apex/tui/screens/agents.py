"""Agent management screen for TUI."""

from typing import Optional, Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from ..widgets import AgentStatusWidget, LogViewerWidget


class AgentsScreen(Screen):
    """Screen for agent management and monitoring."""

    BINDINGS = [
        ("q", "app.pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
        ("s", "start_agent", "Start"),
        ("x", "stop_agent", "Stop"),
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
        """Compose the agents screen layout."""
        yield Header(show_clock=True)

        with Container(id="agents-container"):
            with Vertical():
                yield Static("[bold]Agent Management[/bold]", id="agents-title")

                # Agent status section
                yield AgentStatusWidget(
                    agent_runner=self.agent_runner, id="agent-status"
                )

                # Control buttons
                with Horizontal(id="agent-controls"):
                    yield Button(
                        "Start Supervisor", id="start-supervisor", variant="primary"
                    )
                    yield Button("Start Coder", id="start-coder", variant="primary")
                    yield Button(
                        "Start Adversary", id="start-adversary", variant="primary"
                    )
                    yield Button("Stop All", id="stop-all", variant="error")

                # Log viewer with filters
                yield Static("\n[bold]Agent Logs[/bold]", id="logs-title")

                with Horizontal(id="log-filters"):
                    yield Label("Filter: ")
                    yield Input(placeholder="Agent name", id="filter-agent")
                    yield Input(placeholder="Log level", id="filter-level")
                    yield Input(placeholder="Search pattern", id="filter-pattern")
                    yield Button("Apply", id="apply-filters", variant="success")

                yield LogViewerWidget(lmdb_client=self.lmdb_client, id="log-viewer")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if not self.agent_runner:
            return

        button_id = event.button.id

        try:
            if button_id == "start-supervisor":
                from apex.types import AgentType

                await self.agent_runner.start_agent(AgentType.SUPERVISOR)
                self.notify("Started Supervisor agent")

            elif button_id == "start-coder":
                from apex.types import AgentType

                await self.agent_runner.start_agent(AgentType.CODER)
                self.notify("Started Coder agent")

            elif button_id == "start-adversary":
                from apex.types import AgentType

                await self.agent_runner.start_agent(AgentType.ADVERSARY)
                self.notify("Started Adversary agent")

            elif button_id == "stop-all":
                await self.agent_runner.stop_all_agents()
                self.notify("Stopped all agents")

            elif button_id == "apply-filters":
                # Apply log filters
                log_viewer = self.query_one("#log-viewer", LogViewerWidget)
                agent_filter = self.query_one("#filter-agent", Input).value or None
                level_filter = self.query_one("#filter-level", Input).value or None
                pattern_filter = self.query_one("#filter-pattern", Input).value or None

                log_viewer.set_filter(
                    agent=agent_filter, level=level_filter, pattern=pattern_filter
                )
                self.notify("Filters applied")

        except Exception as e:
            self.notify(f"Error: {str(e)}", severity="error")

    def action_refresh(self) -> None:
        """Refresh agent status."""
        agent_status = self.query_one("#agent-status", AgentStatusWidget)
        agent_status.update_status()
        self.notify("Refreshed agent status")

    def action_start_agent(self) -> None:
        """Show agent start dialog."""
        # In a full implementation, this would show a dialog
        self.notify("Use the Start buttons to launch agents")

    def action_stop_agent(self) -> None:
        """Show agent stop dialog."""
        # In a full implementation, this would show a dialog
        self.notify("Use the Stop All button to stop agents")
