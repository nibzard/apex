"""Main TUI application for APEX."""

from pathlib import Path
from typing import Optional

from textual.app import App

from apex.core.agent_runner import AgentRunner
from apex.core.lmdb_mcp import LMDBMCP

from .screens.dashboard import DashboardScreen


class ApexTUI(App):
    """Main TUI application."""

    TITLE = "APEX - Adversarial Pair EXecution"

    def __init__(
        self,
        agent_runner: Optional[AgentRunner] = None,
        lmdb_path: Optional[Path] = None,
        **kwargs,
    ):
        """Initialize the TUI application."""
        super().__init__(**kwargs)
        self.agent_runner = agent_runner
        self.lmdb_client = None

        # Initialize LMDB client if path provided
        if lmdb_path:
            try:
                self.lmdb_client = LMDBMCP(str(lmdb_path))
                self.lmdb_client.connect()
            except Exception as e:
                self.notify(f"Failed to connect to LMDB: {e}", severity="error")

    def on_mount(self) -> None:
        """Mount the initial screen."""
        self.push_screen(
            DashboardScreen(
                agent_runner=self.agent_runner, lmdb_client=self.lmdb_client
            )
        )

    def on_unmount(self) -> None:
        """Clean up resources."""
        if self.lmdb_client:
            try:
                self.lmdb_client.close()
            except Exception:
                pass


def run_tui(
    agent_runner: Optional[AgentRunner] = None, lmdb_path: Optional[Path] = None
):
    """Run the TUI application."""
    app = ApexTUI(agent_runner=agent_runner, lmdb_path=lmdb_path)
    app.run()


if __name__ == "__main__":
    # For testing
    run_tui()
