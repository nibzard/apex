"""Tests for TUI dashboard."""

import pytest
from textual.testing import AppTest

from apex.tui import DashboardApp
from apex.tui.screens import DashboardScreen


@pytest.mark.asyncio
async def test_dashboard_app_runs():
    """Test that dashboard app can be created and run."""
    app = DashboardApp()
    async with AppTest(app) as pilot:
        # Verify app loaded
        assert pilot.app.title == "APEX Dashboard"
        
        # Verify dashboard screen is pushed
        assert len(pilot.app.screen_stack) > 0
        assert isinstance(pilot.app.screen, DashboardScreen)


@pytest.mark.asyncio  
async def test_dashboard_widgets_load():
    """Test that dashboard widgets are loaded."""
    app = DashboardApp()
    async with AppTest(app) as pilot:
        # Check for key widgets
        assert pilot.app.query_one("#dashboard-title")
        assert pilot.app.query_one("#agent-status-widget")
        assert pilot.app.query_one("#metrics-widget")
        assert pilot.app.query_one("#activity-log")
        

@pytest.mark.asyncio
async def test_dashboard_navigation():
    """Test dashboard navigation."""
    app = DashboardApp()
    async with AppTest(app) as pilot:
        # Test pressing 'a' for agents screen
        await pilot.press("a")
        # In a full test, we'd verify the agents screen is pushed
        
        # Test pressing 'q' to quit
        await pilot.press("q")
        # App should exit