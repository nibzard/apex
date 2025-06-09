"""TUI interface for APEX."""

from typing import Optional, Any

from textual.app import App
from textual.css.query import NoMatches

from .screens.dashboard import DashboardScreen


class DashboardApp(App):
    """Enhanced dashboard TUI application."""

    TITLE = "APEX Dashboard"
    CSS = """
    #dashboard-container {
        padding: 1;
    }
    
    #top-row {
        height: 12;
        margin-bottom: 1;
    }
    
    #left-panel {
        width: 60%;
        padding-right: 1;
    }
    
    #right-panel {
        width: 40%;
    }
    
    #activity-log {
        height: 15;
        border: solid cyan;
        padding: 1;
    }
    
    #quick-actions {
        margin-top: 1;
    }
    
    #agents-container {
        padding: 1;
    }
    
    #agent-controls {
        margin: 1 0;
    }
    
    #log-filters {
        margin: 1 0;
    }
    
    #log-viewer {
        height: 20;
        border: solid blue;
        padding: 1;
    }
    
    #memory-container {
        padding: 1;
    }
    
    #memory-tree-container {
        width: 40%;
        border: solid cyan;
        padding: 1;
    }
    
    #memory-content-container {
        width: 60%;
        border: solid green;
        padding: 1;
        margin-left: 1;
    }
    
    #memory-tree {
        height: 100%;
    }
    
    #memory-content {
        height: 100%;
        overflow-y: auto;
    }
    
    Button {
        margin-right: 1;
    }
    """

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

    def on_mount(self) -> None:
        """Handle mount event by pushing dashboard screen."""
        self.push_screen(
            DashboardScreen(
                agent_runner=self.agent_runner, lmdb_client=self.lmdb_client
            )
        )


__all__ = ["DashboardApp"]
