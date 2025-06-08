"""TUI interface for APEX."""

from textual.app import App
from .screens.dashboard import DashboardScreen


class DashboardApp(App):
    """Simple dashboard TUI application."""

    TITLE = "APEX Dashboard"

    def on_mount(self) -> None:  # pragma: no cover - trivial
        self.push_screen(DashboardScreen())


__all__ = ["DashboardApp"]
