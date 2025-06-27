"""Enhanced TUI application for integrated APEX orchestration."""

import asyncio
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)

from apex.core.memory import MemoryPatterns
from apex.integration.simple_bridge import IntegratedOrchestrator


class OrchestrationStatus(Widget):
    """Widget showing orchestration status."""

    def __init__(self, orchestrator: Optional[IntegratedOrchestrator] = None):
        super().__init__()
        self.orchestrator = orchestrator
        self.update_timer = None

    def compose(self) -> ComposeResult:
        """Compose the status widget."""
        with Vertical():
            yield Label("Orchestration Status", classes="header")
            yield Static("No active session", id="status-text")
            yield ProgressBar(total=100, show_eta=False, id="progress-bar")
            with Horizontal():
                yield Button("Start", id="start-btn", variant="success")
                yield Button("Pause", id="pause-btn", variant="warning", disabled=True)
                yield Button("Stop", id="stop-btn", variant="error", disabled=True)

    async def on_mount(self) -> None:
        """Set up periodic updates."""
        self.update_timer = self.set_interval(2.0, self.update_status)

    async def update_status(self) -> None:
        """Update orchestration status."""
        if not self.orchestrator:
            return

        try:
            status = await self.orchestrator.get_session_status()

            if status.get("error"):
                self.query_one("#status-text", Static).update("No active session")
                self.query_one("#progress-bar", ProgressBar).update(progress=0)
                return

            # Update status text
            goal = status.get("goal", "Unknown")
            completed = status.get("completed_tasks", 0)
            total = status.get("total_tasks", 0)

            status_text = f"Goal: {goal}\nProgress: {completed}/{total} tasks"
            self.query_one("#status-text", Static).update(status_text)

            # Update progress bar
            if total > 0:
                progress = (completed / total) * 100
                self.query_one("#progress-bar", ProgressBar).update(progress=progress)

            # Update buttons
            self.query_one("#start-btn", Button).disabled = status.get("active", False)
            self.query_one("#pause-btn", Button).disabled = not status.get(
                "active", False
            )
            self.query_one("#stop-btn", Button).disabled = not status.get(
                "active", False
            )

        except Exception as e:
            self.query_one("#status-text", Static).update(f"Error: {e}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "start-btn":
            await self.start_orchestration()
        elif event.button.id == "pause-btn":
            await self.pause_orchestration()
        elif event.button.id == "stop-btn":
            await self.stop_orchestration()

    async def start_orchestration(self) -> None:
        """Start orchestration."""
        if self.orchestrator and self.orchestrator.task_graph:
            self.app.notify("Starting orchestration...")
            # Start background orchestration
            asyncio.create_task(self.run_orchestration())

    async def pause_orchestration(self) -> None:
        """Pause orchestration."""
        self.app.notify("Orchestration paused")

    async def stop_orchestration(self) -> None:
        """Stop orchestration."""
        self.app.notify("Orchestration stopped")

    async def run_orchestration(self) -> None:
        """Run orchestration in background."""
        try:
            if self.orchestrator:
                result = await self.orchestrator.orchestrate()
                completion = result.get("completion_percentage", 0)
                self.app.notify(f"Orchestration completed: {completion:.1f}%")
        except Exception as e:
            self.app.notify(f"Orchestration failed: {e}", severity="error")


class TasksView(Widget):
    """Widget showing task details."""

    def __init__(self, orchestrator: Optional[IntegratedOrchestrator] = None):
        super().__init__()
        self.orchestrator = orchestrator

    def compose(self) -> ComposeResult:
        """Compose the tasks view."""
        with Vertical():
            yield Label("Tasks", classes="header")
            yield DataTable(id="tasks-table")

    async def on_mount(self) -> None:
        """Set up the tasks table."""
        table = self.query_one("#tasks-table", DataTable)
        table.add_columns("ID", "Type", "Role", "Description", "Status")

        # Set up periodic updates
        self.set_interval(3.0, self.update_tasks)
        await self.update_tasks()

    async def update_tasks(self) -> None:
        """Update tasks table."""
        if not self.orchestrator or not self.orchestrator.task_graph:
            return

        table = self.query_one("#tasks-table", DataTable)
        table.clear()

        for task in self.orchestrator.task_graph.tasks:
            status_icon = {
                "completed": "✅",
                "failed": "❌",
                "in_progress": "⏳",
                "pending": "⏸️",
            }.get(task.status, "❓")

            table.add_row(
                task.id[:20],
                task.type,
                task.role,
                (
                    task.description[:50] + "..."
                    if len(task.description) > 50
                    else task.description
                ),
                f"{status_icon} {task.status}",
            )


class MemoryBrowser(Widget):
    """Widget for browsing LMDB memory."""

    def __init__(self, memory: Optional[MemoryPatterns] = None):
        super().__init__()
        self.memory = memory

    def compose(self) -> ComposeResult:
        """Compose the memory browser."""
        with Vertical():
            yield Label("Memory Browser", classes="header")
            yield DataTable(id="memory-table")
            yield Button("Refresh", id="refresh-btn", variant="primary")

    async def on_mount(self) -> None:
        """Set up the memory browser."""
        table = self.query_one("#memory-table", DataTable)
        table.add_columns("Key", "Size", "Modified")
        await self.refresh_memory()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "refresh-btn":
            await self.refresh_memory()

    async def refresh_memory(self) -> None:
        """Refresh memory contents."""
        if not self.memory:
            return

        try:
            table = self.query_one("#memory-table", DataTable)
            table.clear()

            keys = await self.memory.mcp.list_keys("")
            for key in sorted(keys)[:50]:  # Show first 50 keys
                try:
                    value = await self.memory.mcp.read(key)
                    size = len(value) if value else 0
                    table.add_row(
                        key[:60] + "..." if len(key) > 60 else key,
                        f"{size} bytes",
                        "Recent",
                    )
                except Exception:
                    table.add_row(key, "Error", "Unknown")

        except Exception as e:
            self.app.notify(f"Failed to refresh memory: {e}", severity="error")


class TaskGraphVisualization(Widget):
    """Widget for live task graph visualization."""

    def __init__(self, orchestrator: Optional[IntegratedOrchestrator] = None):
        super().__init__()
        self.orchestrator = orchestrator

    def compose(self) -> ComposeResult:
        """Compose the task graph view."""
        with Vertical():
            yield Label("Live Task Graph", classes="header")
            yield Tree("Project Tasks", id="task-tree")
            yield Static("Select a task to see details", id="task-details")

    async def on_mount(self) -> None:
        """Set up the task graph."""
        self.set_interval(2.0, self.update_graph)
        await self.update_graph()

    async def update_graph(self) -> None:
        """Update task graph visualization."""
        if not self.orchestrator or not self.orchestrator.task_graph:
            return

        tree = self.query_one("#task-tree", Tree)
        tree.clear()

        # Group tasks by type and status
        task_groups = {"pending": [], "in_progress": [], "completed": [], "failed": []}

        for task in self.orchestrator.task_graph.tasks:
            status = task.status.lower()
            if status in task_groups:
                task_groups[status].append(task)

        # Add tasks to tree by status
        for status, tasks in task_groups.items():
            if tasks:
                status_icon = {
                    "pending": "⏸️",
                    "in_progress": "⏳",
                    "completed": "✅",
                    "failed": "❌",
                }.get(status, "❓")

                status_node = tree.root.add(
                    f"{status_icon} {status.title()} ({len(tasks)})"
                )

                for task in tasks:
                    role_icon = {
                        "coder": "👨‍💻",
                        "adversary": "🔍",
                        "supervisor": "🧠",
                    }.get(task.role.lower(), "⚙️")

                    task_label = f"{role_icon} {task.description[:40]}..."
                    task_node = status_node.add(task_label)
                    task_node.data = task  # Store task data for selection

    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle task selection."""
        if hasattr(event.node, "data") and event.node.data:
            task = event.node.data
            details = (
                f"Task ID: {task.id}\n"
                f"Type: {task.type}\n"
                f"Role: {task.role}\n"
                f"Status: {task.status}\n"
                f"Description: {task.description}\n"
                f"Context Keys: {', '.join(task.context_keys) if task.context_keys else 'None'}"
            )
            self.query_one("#task-details", Static).update(details)


class ResourceMonitor(Widget):
    """Widget for monitoring worker and utility resources."""

    def __init__(self, orchestrator: Optional[IntegratedOrchestrator] = None):
        super().__init__()
        self.orchestrator = orchestrator

    def compose(self) -> ComposeResult:
        """Compose the resource monitor."""
        with Vertical():
            yield Label("Resource Monitor", classes="header")
            with Horizontal():
                with Vertical(classes="resource-panel"):
                    yield Label("Workers", classes="sub-header")
                    yield DataTable(id="workers-table")
                with Vertical(classes="resource-panel"):
                    yield Label("Utilities", classes="sub-header")
                    yield DataTable(id="utilities-table")
            yield Label("System Metrics", classes="sub-header")
            yield DataTable(id="metrics-table")

    async def on_mount(self) -> None:
        """Set up resource monitor."""
        # Set up workers table
        workers_table = self.query_one("#workers-table", DataTable)
        workers_table.add_columns("ID", "Status", "Task", "CPU", "Memory")

        # Set up utilities table
        utilities_table = self.query_one("#utilities-table", DataTable)
        utilities_table.add_columns("Name", "Status", "Running", "Last Used")

        # Set up metrics table
        metrics_table = self.query_one("#metrics-table", DataTable)
        metrics_table.add_columns("Metric", "Value", "Trend")

        # Start periodic updates
        self.set_interval(3.0, self.update_resources)
        await self.update_resources()

    async def update_resources(self) -> None:
        """Update resource information."""
        await self.update_workers()
        await self.update_utilities()
        await self.update_metrics()

    async def update_workers(self) -> None:
        """Update workers table."""
        workers_table = self.query_one("#workers-table", DataTable)
        workers_table.clear()

        # Mock worker data - in real implementation would query actual workers
        if self.orchestrator:
            workers = [
                {
                    "id": "worker-1",
                    "status": "active",
                    "task": "Code Review",
                    "cpu": "12%",
                    "memory": "128MB",
                },
                {
                    "id": "worker-2",
                    "status": "idle",
                    "task": "None",
                    "cpu": "2%",
                    "memory": "64MB",
                },
            ]

            for worker in workers:
                status_icon = "🟢" if worker["status"] == "active" else "🟡"
                workers_table.add_row(
                    worker["id"],
                    f"{status_icon} {worker['status']}",
                    worker["task"],
                    worker["cpu"],
                    worker["memory"],
                )

    async def update_utilities(self) -> None:
        """Update utilities table."""
        utilities_table = self.query_one("#utilities-table", DataTable)
        utilities_table.clear()

        # Mock utility data
        utilities = [
            {
                "name": "TestRunner",
                "status": "ready",
                "running": "No",
                "last_used": "2 min ago",
            },
            {
                "name": "CodeLinter",
                "status": "active",
                "running": "Yes",
                "last_used": "Now",
            },
            {
                "name": "SecurityScanner",
                "status": "ready",
                "running": "No",
                "last_used": "5 min ago",
            },
        ]

        for utility in utilities:
            status_icon = "🔵" if utility["status"] == "active" else "⚪"
            utilities_table.add_row(
                utility["name"],
                f"{status_icon} {utility['status']}",
                utility["running"],
                utility["last_used"],
            )

    async def update_metrics(self) -> None:
        """Update system metrics."""
        metrics_table = self.query_one("#metrics-table", DataTable)
        metrics_table.clear()

        metrics = [
            {"metric": "Tasks Completed", "value": "12/20", "trend": "📈"},
            {"metric": "Success Rate", "value": "95%", "trend": "📈"},
            {"metric": "Avg Task Time", "value": "2.3 min", "trend": "📉"},
            {"metric": "Memory Usage", "value": "256MB", "trend": "📊"},
        ]

        for metric in metrics:
            metrics_table.add_row(metric["metric"], metric["value"], metric["trend"])


class ChatInterface(Widget):
    """Widget for direct Supervisor communication."""

    def __init__(self, orchestrator: Optional[IntegratedOrchestrator] = None):
        super().__init__()
        self.orchestrator = orchestrator

    def compose(self) -> ComposeResult:
        """Compose the chat interface."""
        with Vertical():
            yield Label("Supervisor Chat", classes="header")
            yield RichLog(id="chat-log", markup=True)
            with Horizontal():
                yield Input(
                    placeholder="Type your message to the Supervisor...",
                    id="chat-input",
                )
                yield Button("Send", id="send-btn", variant="primary")

    async def on_mount(self) -> None:
        """Set up chat interface."""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(
            "💡 [bold cyan]Supervisor:[/bold cyan] Hello! I'm here to help with orchestration. You can ask me about tasks, progress, or make requests."
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle send button."""
        if event.button.id == "send-btn":
            await self.send_message()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "chat-input":
            await self.send_message()

    async def send_message(self) -> None:
        """Send message to supervisor."""
        chat_input = self.query_one("#chat-input", Input)
        chat_log = self.query_one("#chat-log", RichLog)

        message = chat_input.value.strip()
        if not message:
            return

        # Clear input
        chat_input.value = ""

        # Add user message
        chat_log.write(f"👤 [bold green]You:[/bold green] {message}")

        # Process message and get supervisor response
        response = await self.process_supervisor_message(message)
        chat_log.write(f"🧠 [bold cyan]Supervisor:[/bold cyan] {response}")

    async def process_supervisor_message(self, message: str) -> str:
        """Process message and generate supervisor response."""
        message_lower = message.lower()

        # Simple command processing
        if "status" in message_lower:
            if self.orchestrator and self.orchestrator.task_graph:
                total = len(self.orchestrator.task_graph.tasks)
                completed = len(self.orchestrator.completed_tasks)
                return f"Current status: {completed}/{total} tasks completed. Goal: {self.orchestrator.task_graph.goal}"
            return "No active orchestration session."

        elif "help" in message_lower:
            return "I can help with: 'status' (show progress), 'pause' (pause orchestration), 'resume' (resume orchestration), 'tasks' (list tasks), or just ask me questions!"

        elif "pause" in message_lower:
            return "Orchestration paused. Use 'resume' to continue."

        elif "resume" in message_lower:
            return "Orchestration resumed."

        elif "tasks" in message_lower:
            if self.orchestrator and self.orchestrator.task_graph:
                tasks = [
                    f"- {task.description}"
                    for task in self.orchestrator.task_graph.tasks[:5]
                ]
                task_list = "\n".join(tasks)
                more = (
                    f"\n... and {len(self.orchestrator.task_graph.tasks) - 5} more"
                    if len(self.orchestrator.task_graph.tasks) > 5
                    else ""
                )
                return f"Current tasks:\n{task_list}{more}"
            return "No tasks in current session."

        else:
            return f"I understand you said: '{message}'. I'm working on more advanced responses! For now, try 'status', 'tasks', 'help', 'pause', or 'resume'."


class LogViewer(Widget):
    """Widget for viewing orchestration logs."""

    def compose(self) -> ComposeResult:
        """Compose the log viewer."""
        with Vertical():
            yield Label("Orchestration Logs", classes="header")
            yield RichLog(id="log-display", markup=True)

    async def on_mount(self) -> None:
        """Set up log viewer."""
        self.set_interval(1.0, self.update_logs)

    async def update_logs(self) -> None:
        """Update logs."""
        # This would connect to actual logging system
        pass

    def add_log_entry(self, message: str, level: str = "INFO") -> None:
        """Add a log entry."""
        log = self.query_one("#log-display", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")

        level_colors = {
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "SUCCESS": "green",
        }
        color = level_colors.get(level, "white")

        log.write(f"[{timestamp}] [{color}]{level}[/{color}]: {message}")


class IntegratedTUIApp(App):
    """Enhanced TUI application for integrated orchestration."""

    CSS = """
    .header {
        text-style: bold;
        color: cyan;
        margin-bottom: 1;
    }

    .sub-header {
        text-style: bold;
        color: yellow;
        margin: 1 0;
    }

    .resource-panel {
        width: 50%;
        margin: 0 1;
    }

    #tasks-table {
        height: 20;
    }

    #memory-table {
        height: 15;
    }

    #log-display {
        height: 10;
    }

    #chat-log {
        height: 15;
        border: solid green;
        margin: 1;
    }

    #chat-input {
        width: 80%;
    }

    #send-btn {
        width: 20%;
        margin-left: 1;
    }

    #task-tree {
        height: 20;
        border: solid cyan;
        margin: 1;
    }

    #task-details {
        height: 8;
        border: solid yellow;
        margin: 1;
        padding: 1;
    }

    #workers-table, #utilities-table {
        height: 8;
        margin: 1;
    }

    #metrics-table {
        height: 6;
        margin: 1;
    }

    #status-text {
        margin: 1;
        padding: 1;
        border: solid cyan;
    }

    #progress-bar {
        margin: 1;
    }
    """

    TITLE = "APEX - Integrated Orchestration TUI"

    def __init__(
        self,
        memory: Optional[MemoryPatterns] = None,
        orchestrator: Optional[IntegratedOrchestrator] = None,
        project_id: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the TUI application."""
        super().__init__(**kwargs)
        self.memory = memory
        self.orchestrator = orchestrator
        self.project_id = project_id

    def compose(self) -> ComposeResult:
        """Compose the main interface."""
        yield Header()

        with TabbedContent():
            with TabPane("Status", id="status-tab"):
                yield OrchestrationStatus(self.orchestrator)

            with TabPane("Graph", id="graph-tab"):
                yield TaskGraphVisualization(self.orchestrator)

            with TabPane("Tasks", id="tasks-tab"):
                yield TasksView(self.orchestrator)

            with TabPane("Resources", id="resources-tab"):
                yield ResourceMonitor(self.orchestrator)

            with TabPane("Chat", id="chat-tab"):
                yield ChatInterface(self.orchestrator)

            with TabPane("Memory", id="memory-tab"):
                yield MemoryBrowser(self.memory)

            with TabPane("Logs", id="logs-tab"):
                yield LogViewer()

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the application."""
        if self.project_id:
            self.title = f"APEX - Project {self.project_id}"

        # Add welcome message
        self.notify("APEX Integrated TUI started", severity="information")

    def action_quit(self) -> None:
        """Handle quit action."""
        self.notify("Shutting down TUI...")
        super().action_quit()

    async def on_unmount(self) -> None:
        """Clean up resources."""
        if self.memory:
            await self.memory.close()


class ApexTUIApp(IntegratedTUIApp):
    """Alias for backward compatibility."""

    def __init__(self, memory: Optional[MemoryPatterns] = None, **kwargs):
        super().__init__(memory=memory, **kwargs)
