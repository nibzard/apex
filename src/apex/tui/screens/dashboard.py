from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static


class DashboardScreen(Screen):
    """Main dashboard screen for APEX."""

    BINDINGS = [("q", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("APEX Dashboard", id="dashboard-title")
        yield Footer()
