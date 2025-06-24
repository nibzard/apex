"""Agent interaction widget for direct communication with agents."""

import json
from datetime import datetime
from typing import Any, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Select, Static, TextArea


class AgentInteractionWidget(Vertical):
    """Widget for interacting directly with agents."""

    selected_agent: reactive[Optional[str]] = reactive(None)

    def __init__(self, lmdb_client: Optional[Any] = None, **kwargs) -> None:
        """Initialize with optional LMDB client."""
        super().__init__(**kwargs)
        self.lmdb_client = lmdb_client

    def compose(self) -> ComposeResult:
        """Compose the interaction panel."""
        yield Static(
            "[bold cyan]Agent Interaction Panel[/bold cyan]", id="interaction-header"
        )

        # Agent selector
        with Horizontal(id="agent-selector"):
            yield Static("Agent: ")
            yield Select(
                options=[
                    ("Supervisor", "supervisor"),
                    ("Coder", "coder"),
                    ("Adversary", "adversary"),
                ],
                id="agent-select",
                value="supervisor",
            )

        # Command type selector
        with Horizontal(id="command-selector"):
            yield Static("Type: ")
            yield Select(
                options=[
                    ("Assign Task", "task"),
                    ("Send Message", "message"),
                    ("Update Status", "status"),
                    ("Query Agent", "query"),
                ],
                id="command-select",
                value="task",
            )

        # Input area
        yield TextArea(
            "",
            id="command-input",
            language="json",
            theme="monokai",
            show_line_numbers=True,
        )

        # Action buttons
        with Horizontal(id="action-buttons"):
            yield Button("Send", id="send-command", variant="primary")
            yield Button("Clear", id="clear-command", variant="default")
            yield Button("Templates", id="show-templates", variant="default")

        # Response area
        yield Static("\n[bold]Response[/bold]", id="response-header")
        yield Static("", id="response-content")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "send-command":
            await self.send_command()
        elif button_id == "clear-command":
            self.clear_input()
        elif button_id == "show-templates":
            self.show_templates()

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        if event.select.id == "agent-select":
            self.selected_agent = event.value
            self.update_template()
        elif event.select.id == "command-select":
            self.update_template()

    def update_template(self) -> None:
        """Update input with a template based on selections."""
        agent_select = self.query_one("#agent-select", Select)
        command_select = self.query_one("#command-select", Select)
        input_area = self.query_one("#command-input", TextArea)

        agent = agent_select.value
        command_type = command_select.value

        templates = {
            "task": {
                "supervisor": {
                    "description": "Break down user requirements into subtasks",
                    "priority": "high",
                    "metadata": {"user_request": "Implement feature X with tests"},
                },
                "coder": {
                    "description": "Implement authentication module",
                    "priority": "medium",
                    "depends_on": [],
                    "metadata": {"files": ["auth.py", "test_auth.py"]},
                },
                "adversary": {
                    "description": "Review and test authentication module",
                    "priority": "high",
                    "metadata": {"focus": ["security", "edge_cases"]},
                },
            },
            "message": {
                "supervisor": {
                    "type": "status_update",
                    "content": "Project status update",
                    "metadata": {},
                },
                "coder": {
                    "type": "question",
                    "content": "Need clarification on requirement X",
                    "metadata": {},
                },
                "adversary": {
                    "type": "report",
                    "content": "Found potential security issue",
                    "metadata": {},
                },
            },
            "status": {
                "supervisor": {
                    "status": "coordinating",
                    "current_task": "Breaking down requirements",
                    "metadata": {},
                },
                "coder": {
                    "status": "coding",
                    "current_task": "Implementing feature X",
                    "progress": 45,
                    "metadata": {},
                },
                "adversary": {
                    "status": "testing",
                    "current_task": "Security audit",
                    "metadata": {},
                },
            },
            "query": {
                "supervisor": {
                    "query": "What is the current project status?",
                    "context": {},
                },
                "coder": {"query": "What files have you modified?", "context": {}},
                "adversary": {"query": "What issues have you found?", "context": {}},
            },
        }

        template = templates.get(command_type, {}).get(agent, {})
        input_area.text = json.dumps(template, indent=2)

    async def send_command(self) -> None:
        """Send command to the selected agent."""
        if not self.lmdb_client:
            self.show_response("Error: No LMDB client available", error=True)
            return

        agent_select = self.query_one("#agent-select", Select)
        command_select = self.query_one("#command-select", Select)
        input_area = self.query_one("#command-input", TextArea)

        agent = agent_select.value
        command_type = command_select.value

        try:
            # Parse input as JSON
            data = json.loads(input_area.text)

            # Add metadata
            data["_meta"] = {
                "timestamp": datetime.now().isoformat(),
                "source": "tui_interaction",
                "command_type": command_type,
            }

            # Determine key based on command type
            if command_type == "task":
                from apex.core.memory import MemoryPatterns

                patterns = MemoryPatterns(self.lmdb_client)

                # Assuming we have a project_id
                project_id = "current"  # In real implementation, get from context
                task_id = await patterns.create_task(
                    project_id, data, assigned_to=agent
                )
                self.show_response(f"Task created: {task_id}")

            elif command_type == "message":
                key = f"/agents/{agent}/messages/{datetime.now().timestamp()}"
                self.lmdb_client.write(key, json.dumps(data).encode())
                self.show_response(f"Message sent to {agent}")

            elif command_type == "status":
                key = f"/agents/{agent}/status"
                self.lmdb_client.write(key, json.dumps(data).encode())
                self.show_response(f"Status updated for {agent}")

            elif command_type == "query":
                # For queries, we might want to read relevant data
                response_data = {
                    "agent": agent,
                    "query": data.get("query", ""),
                    "response": "Query processing not yet implemented",
                }
                self.show_response(json.dumps(response_data, indent=2))

        except json.JSONDecodeError as e:
            self.show_response(f"JSON Error: {str(e)}", error=True)
        except Exception as e:
            self.show_response(f"Error: {str(e)}", error=True)

    def clear_input(self) -> None:
        """Clear the input area."""
        input_area = self.query_one("#command-input", TextArea)
        input_area.text = ""

        response = self.query_one("#response-content", Static)
        response.update("")

    def show_templates(self) -> None:
        """Show available templates."""
        self.update_template()
        self.show_response("Template loaded based on current selections")

    def show_response(self, message: str, error: bool = False) -> None:
        """Show response message."""
        response = self.query_one("#response-content", Static)

        if error:
            response.update(f"[red]{message}[/red]")
        else:
            response.update(f"[green]{message}[/green]")
