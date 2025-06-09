"""Memory browser screen for TUI."""

from typing import Optional, Any

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input

from ..widgets import MemoryBrowserWidget


class MemoryScreen(Screen):
    """Screen for browsing and managing memory."""

    BINDINGS = [
        ("q", "app.pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
        ("/", "search", "Search"),
    ]

    def __init__(self, lmdb_client: Optional[Any] = None, **kwargs) -> None:
        """Initialize with optional LMDB client."""
        super().__init__(**kwargs)
        self.lmdb_client = lmdb_client

    def compose(self) -> ComposeResult:
        """Compose the memory screen layout."""
        yield Header(show_clock=True)

        with Container(id="memory-container"):
            yield MemoryBrowserWidget(lmdb_client=self.lmdb_client, id="memory-browser")

        yield Footer()

    def action_refresh(self) -> None:
        """Refresh memory tree."""
        browser = self.query_one("#memory-browser", MemoryBrowserWidget)
        browser.refresh_tree()
        self.notify("Refreshed memory tree")

    def action_search(self) -> None:
        """Show search dialog."""
        # In a full implementation, this would show a search dialog
        self.notify("Search functionality coming soon")
