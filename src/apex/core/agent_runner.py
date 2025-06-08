"""Agent runner that integrates ProcessManager with StreamParser."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from apex.agents.prompts import AgentPrompts
from apex.core.lmdb_mcp import LMDBMCP
from apex.core.process_manager import ProcessManager
from apex.core.stream_parser import StreamEvent, StreamParser
from apex.core.task_workflow import TaskWorkflow, WorkflowManager
from apex.types import AgentType, ProjectConfig


class AgentRunner:
    """Manages agents with integrated stream parsing and event storage."""

    def __init__(
        self,
        project_config: ProjectConfig,
        mcp_config: Optional[Path] = None,
        lmdb_path: Optional[Path] = None,
    ) -> None:
        """Initialize the runner with configuration and storage paths."""
        self.project_config = project_config
        self.session_id = str(uuid.uuid4())

        # Initialize LMDB
        self.lmdb_path = lmdb_path or Path("apex.db")
        self.lmdb = LMDBMCP(self.lmdb_path)

        # Initialize process manager
        self.process_manager = ProcessManager(mcp_config)

        # Track parsers and running tasks
        self.parsers: Dict[str, StreamParser] = {}
        self.stream_tasks: Dict[str, asyncio.Task] = {}

        # Initialize workflow management
        self.task_workflow = TaskWorkflow(self.lmdb)
        self.workflow_manager = WorkflowManager(self.task_workflow)

        # Agent prompts are class methods, no instance needed

    async def start_agent(
        self, agent_type: AgentType, initial_task: Optional[str] = None
    ) -> str:
        """Start an agent with stream parsing.

        Args:
            agent_type: Type of agent to start
            initial_task: Optional initial task for the agent

        Returns:
            Process name for the started agent

        """
        # Generate agent prompt
        prompt = AgentPrompts.generate_prompt(
            agent_type=agent_type,
            config=self.project_config,
            user_request=initial_task
            or f"You are a {agent_type.value} agent. Wait for tasks.",
        )

        # Start Claude process
        process_name = await self.process_manager.spawn_claude_agent(
            agent_type=agent_type, prompt=prompt
        )

        # Create stream parser for this agent
        parser = StreamParser(
            agent_id=process_name, session_id=self.session_id, mcp=self.lmdb
        )
        self.parsers[process_name] = parser

        # Start stream processing task
        stream_task = asyncio.create_task(self._process_agent_stream(process_name))
        self.stream_tasks[process_name] = stream_task

        # Store agent startup in LMDB
        await self._store_agent_status(process_name, agent_type, "started")

        return process_name

    async def start_all_agents(
        self, supervisor_task: Optional[str] = None
    ) -> Dict[str, str]:
        """Start all three agent types.

        Args:
            supervisor_task: Initial task for supervisor agent

        Returns:
            Mapping of agent type to process name

        """
        agent_names = {}

        # Start supervisor first
        supervisor_name = await self.start_agent(AgentType.SUPERVISOR, supervisor_task)
        agent_names["supervisor"] = supervisor_name

        # Start coder
        coder_name = await self.start_agent(AgentType.CODER)
        agent_names["coder"] = coder_name

        # Start adversary
        adversary_name = await self.start_agent(AgentType.ADVERSARY)
        agent_names["adversary"] = adversary_name

        return agent_names

    async def stop_agent(self, process_name: str) -> None:
        """Stop an agent and its stream processing."""
        # Cancel stream processing task
        if process_name in self.stream_tasks:
            self.stream_tasks[process_name].cancel()
            del self.stream_tasks[process_name]

        # Stop the process
        self.process_manager.stop(process_name)

        # Clean up parser
        if process_name in self.parsers:
            del self.parsers[process_name]

        # Store agent shutdown in LMDB
        await self._store_agent_status(process_name, None, "stopped")

    async def stop_all_agents(self) -> None:
        """Stop all running agents."""
        # Cancel all stream tasks
        for task in self.stream_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self.stream_tasks:
            await asyncio.gather(*self.stream_tasks.values(), return_exceptions=True)

        # Shutdown process manager
        self.process_manager.shutdown()

        # Clear tracking
        self.parsers.clear()
        self.stream_tasks.clear()

    async def get_agent_events(
        self, process_name: str, limit: int = 100
    ) -> List[StreamEvent]:
        """Get recent events from an agent."""
        parser = self.parsers.get(process_name)
        if not parser:
            return []

        # Placeholder for reading events from LMDB
        events = []

        # Actual LMDB retrieval would need to be implemented
        # For now, return empty list
        return events

    def get_agent_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all agents."""
        return self.process_manager.list_processes()

    def is_agent_healthy(self, process_name: str) -> bool:
        """Check if an agent is running and healthy."""
        return self.process_manager.health_check(process_name)

    async def send_message_to_agent(self, process_name: str, message: str) -> bool:
        """Send a message to an agent via stdin.

        Args:
            process_name: Name of the agent process
            message: Message to send

        Returns:
            True if message was sent successfully

        """
        claude_process = self.process_manager.get_claude_process(process_name)
        if not claude_process or not claude_process.process:
            return False

        try:
            if claude_process.process.stdin:
                claude_process.process.stdin.write(message + "\n")
                claude_process.process.stdin.flush()
                return True
        except Exception:
            pass

        return False

    async def _process_agent_stream(self, process_name: str) -> None:
        """Process streaming events from an agent."""
        parser = self.parsers.get(process_name)
        if not parser:
            return

        try:
            # Get stream from process manager
            async for event_data in self.process_manager.get_claude_stream(
                process_name
            ):
                # Parse the event
                event = parser.parse_event(event_data)
                if event:
                    # Store the event
                    await parser.store_event(event)

                    # Handle specific event types
                    await self._handle_event(process_name, event)

        except asyncio.CancelledError:
            # Task was cancelled, clean shutdown
            pass
        except Exception as e:
            # Log error and continue
            print(f"Error processing stream for {process_name}: {e}")

    async def _handle_event(self, process_name: str, event: StreamEvent) -> None:
        """Handle specific event types for routing and responses."""
        # This is where we'd implement event-driven workflows
        # For now, just basic logging

        if event.event_type == "tool_call":
            # Handle tool calls - could trigger cross-agent communication
            pass
        elif event.event_type == "assistant":
            # Handle assistant messages - could trigger task updates
            pass

    async def _store_agent_status(
        self, process_name: str, agent_type: Optional[AgentType], status: str
    ) -> None:
        """Store agent status change in LMDB."""
        from datetime import datetime

        status_data = {
            "agent_type": agent_type.value if agent_type else None,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
        }

        status_key = f"/agents/{process_name}/status"
        await asyncio.get_event_loop().run_in_executor(
            None, self.lmdb.write, status_key, str(status_data).encode()
        )

    async def start_workflow(
        self, user_request: str, auto_start_agents: bool = True
    ) -> str:
        """Start a complete workflow for a user request.

        Args:
            user_request: The user's request
            auto_start_agents: Whether to automatically start required agents

        Returns:
            Workflow ID

        """
        # Start workflow
        workflow_id = await self.workflow_manager.start_project_workflow(
            user_request, self.project_config.model_dump()
        )

        if auto_start_agents:
            # Start supervisor with the user request
            await self.start_agent(AgentType.SUPERVISOR, user_request)

            # Start coder to handle implementation tasks
            await self.start_agent(AgentType.CODER)

            # Start adversary for testing
            await self.start_agent(AgentType.ADVERSARY)

        return workflow_id

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, any]]:
        """Get status of a workflow."""
        return await self.workflow_manager.get_workflow_status(workflow_id)

    async def get_pending_tasks(self, agent_type: AgentType) -> List[Dict[str, any]]:
        """Get pending tasks for an agent."""
        return await self.task_workflow.get_pending_tasks(agent_type)

    async def complete_task(
        self, task_id: str, result: Dict[str, any], completed_by: str
    ) -> bool:
        """Mark a task as completed."""
        return await self.task_workflow.complete_task(task_id, result, completed_by)

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.lmdb:
            self.lmdb.close()


# Example usage and integration test
async def test_agent_runner():
    """Test the agent runner integration."""
    from apex.types import ProjectConfig

    # Create a test project config
    config = ProjectConfig(
        name="test-project",
        description="Test project for agent runner",
        tech_stack=["Python"],
        project_type="CLI Tool",
    )

    # Create agent runner
    runner = AgentRunner(config)

    try:
        # Start supervisor agent
        supervisor_name = await runner.start_agent(
            AgentType.SUPERVISOR, "Coordinate the development of a simple calculator"
        )
        print(f"Started supervisor: {supervisor_name}")

        # Wait a bit to see some activity
        await asyncio.sleep(2)

        # Check status
        status = runner.get_agent_status()
        print(f"Agent status: {status}")

        # Stop agents
        await runner.stop_agent(supervisor_name)
        print("Stopped supervisor")

    finally:
        await runner.stop_all_agents()
        runner.cleanup()


if __name__ == "__main__":
    asyncio.run(test_agent_runner())
