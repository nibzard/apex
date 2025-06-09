"""Log viewer widget for TUI."""

import json
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Static


class LogViewerWidget(VerticalScroll):
    """Widget for viewing and filtering agent logs."""

    logs: reactive[List[Dict[str, Any]]] = reactive([])
    filter_agent: reactive[Optional[str]] = reactive(None)
    filter_level: reactive[Optional[str]] = reactive(None)
    filter_pattern: reactive[Optional[str]] = reactive(None)

    def __init__(
        self, lmdb_client: Optional[Any] = None, max_logs: int = 100, **kwargs
    ) -> None:
        """Initialize with optional LMDB client."""
        super().__init__(**kwargs)
        self.lmdb_client = lmdb_client
        self.max_logs = max_logs
        self.log_buffer: Deque[Dict[str, Any]] = deque(maxlen=max_logs)
        self.update_timer: Optional[Timer] = None
        self.seen_keys: set = set()

    def compose(self) -> ComposeResult:
        """Compose the log viewer."""
        yield Static("[bold cyan]Log Stream[/bold cyan]", id="log-header")
        yield Static("", id="log-content")

    def on_mount(self) -> None:
        """Start updating when mounted."""
        if self.lmdb_client:
            self.update_timer = self.set_interval(0.5, self.fetch_new_logs)
            self.fetch_all_logs()  # Initial load

    def on_unmount(self) -> None:
        """Stop updating when unmounted."""
        if self.update_timer:
            self.update_timer.stop()

    async def fetch_all_logs(self) -> None:
        """Fetch all existing logs."""
        if not self.lmdb_client:
            return

        try:
            # Get all log-related keys
            keys = await self.lmdb_client.list_keys("")

            log_patterns = [
                "/agents/*/messages/*",
                "/sessions/*/events/*",
                "/tools/calls/*",
            ]

            for key in keys:
                if key not in self.seen_keys and any(
                    self._matches_pattern(key, pattern) for pattern in log_patterns
                ):
                    await self._process_log_entry(key)

        except Exception:
            pass

    async def fetch_new_logs(self) -> None:
        """Fetch only new log entries."""
        if not self.lmdb_client:
            return

        try:
            # Get all log-related keys
            keys = await self.lmdb_client.list_keys("")

            log_patterns = [
                "/agents/*/messages/*",
                "/sessions/*/events/*",
                "/tools/calls/*",
            ]

            for key in keys:
                if key not in self.seen_keys and any(
                    self._matches_pattern(key, pattern) for pattern in log_patterns
                ):
                    await self._process_log_entry(key)

        except Exception:
            pass

    async def _process_log_entry(self, key: str) -> None:
        """Process a single log entry."""
        try:
            value = await self.lmdb_client.read(key)
            if not value:
                return

            self.seen_keys.add(key)

            # Try to parse as JSON
            try:
                data = json.loads(value.decode() if isinstance(value, bytes) else value)
                if isinstance(data, dict):
                    # Extract log info
                    timestamp = data.get("timestamp", data.get("created_at", ""))
                    content = data.get("content", data.get("message", str(data)))
                    level = data.get("level", "info")

                    # Extract agent from key
                    agent = "unknown"
                    if "/agents/" in key:
                        parts = key.split("/")
                        if len(parts) > 2:
                            agent = parts[2]

                    log_entry = {
                        "timestamp": timestamp,
                        "level": level.upper(),
                        "agent": agent,
                        "content": str(content),
                        "key": key,
                    }

                    self.log_buffer.append(log_entry)
                    self.update_display()

            except (json.JSONDecodeError, UnicodeDecodeError):
                # Treat as plain text
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "agent": "unknown",
                    "content": (
                        value.decode() if isinstance(value, bytes) else str(value)
                    ),
                    "key": key,
                }
                self.log_buffer.append(log_entry)
                self.update_display()

        except Exception:
            pass

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches a glob pattern."""
        import fnmatch

        return fnmatch.fnmatch(key, pattern)

    def update_display(self) -> None:
        """Update the displayed logs."""
        # Apply filters
        filtered_logs = list(self.log_buffer)

        if self.filter_agent:
            filtered_logs = [
                log
                for log in filtered_logs
                if log["agent"].lower() == self.filter_agent.lower()
            ]

        if self.filter_level:
            filtered_logs = [
                log
                for log in filtered_logs
                if log["level"] == self.filter_level.upper()
            ]

        if self.filter_pattern:
            filtered_logs = [
                log
                for log in filtered_logs
                if self.filter_pattern.lower() in log["content"].lower()
            ]

        # Format logs
        lines = []
        for log in filtered_logs[-20:]:  # Show last 20
            timestamp = log["timestamp"]
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except Exception:
                    time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
            else:
                time_str = "??:??:??"

            level = log["level"]
            level_colors = {
                "ERROR": "red",
                "WARN": "yellow",
                "WARNING": "yellow",
                "INFO": "blue",
                "DEBUG": "dim",
            }
            level_color = level_colors.get(level, "white")

            agent = log["agent"][:10]  # Truncate agent name
            content = log["content"]

            if len(content) > 80:
                content = content[:77] + "..."

            lines.append(
                f"[dim]{time_str}[/dim] [{level_color}]{level:5}[/{level_color}] "
                f"[cyan]{agent:10}[/cyan] {content}"
            )

        content_widget = self.query_one("#log-content", Static)
        content_widget.update("\n".join(lines) if lines else "[dim]No logs[/dim]")

    def set_filter(
        self,
        agent: Optional[str] = None,
        level: Optional[str] = None,
        pattern: Optional[str] = None,
    ) -> None:
        """Set log filters."""
        self.filter_agent = agent
        self.filter_level = level
        self.filter_pattern = pattern
        self.update_display()
