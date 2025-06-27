#!/usr/bin/env python3
"""LMDB MCP Server for Claude Code integration.

This module provides APEX-specific functionality using the external lmdb-mcp package,
including APEX-specific tools like project_status.
"""

from __future__ import annotations

import asyncio
import json
import os

# Import from the external lmdb-mcp package
from lmdb_mcp.server import LMDBMCPServer


class ClaudeLMDBServer(LMDBMCPServer):
    """LMDB MCP server designed for Claude Code integration with APEX features."""

    def __init__(self, db_path: str, map_size: int = 1024 * 1024 * 1024):  # 1GB default
        """Initialize LMDB MCP server for Claude Code.

        Args:
            db_path: Path to LMDB database
            map_size: Maximum size of LMDB database (default: 1GB)

        """
        # Initialize with Claude Code-compatible settings
        super().__init__(db_path, map_size, tool_prefix="mcp__lmdb__")
        self._register_apex_tools()

    def _register_apex_tools(self) -> None:
        """Register APEX-specific MCP tools."""

        @self.app.tool(name="mcp__lmdb__project_status")
        async def project_status(project_id: str) -> str:
            """Get APEX project status and summary.

            Args:
                project_id: The project ID to get status for

            Returns:
                JSON object with project status information

            """
            try:
                await self._ensure_db()

                # Get project config
                project_key = f"/projects/{project_id}/config"
                project_data = await self._read(project_key)
                if not project_data:
                    return json.dumps({"error": f"Project {project_id} not found"})

                project_config = json.loads(project_data.decode())

                # Get task counts
                task_counts = {"pending": 0, "in_progress": 0, "completed": 0}
                task_prefix = f"/projects/{project_id}/tasks/"
                task_keys = await self._list_keys(task_prefix)

                for task_key in task_keys:
                    task_data = await self._read(task_key)
                    if task_data:
                        try:
                            task_info = json.loads(task_data.decode())
                            status = task_info.get("status", "unknown")
                            if status in task_counts:
                                task_counts[status] += 1
                        except:
                            pass

                # Get agent status
                agent_statuses = {}
                agent_prefix = f"/projects/{project_id}/agents/"
                agent_keys = await self._list_keys(agent_prefix)

                for agent_key in agent_keys:
                    agent_data = await self._read(agent_key)
                    if agent_data:
                        try:
                            agent_name = agent_key.split("/")[-1]
                            agent_info = json.loads(agent_data.decode())
                            agent_statuses[agent_name] = agent_info.get(
                                "status", "unknown"
                            )
                        except:
                            pass

                status_summary = {
                    "project_id": project_id,
                    "project_name": project_config.get("name", "Unknown"),
                    "task_counts": task_counts,
                    "agent_statuses": agent_statuses,
                    "total_tasks": sum(task_counts.values()),
                }

                return json.dumps(status_summary)
            except Exception as e:
                return json.dumps({"error": f"Failed to get project status: {str(e)}"})

    async def run(self) -> None:
        """Run the MCP server with stdio transport for Claude Code."""
        # Use stdio transport for Claude Code integration
        await super().run(transport="stdio")


def main() -> None:
    """Main entry point for Claude Code MCP server."""
    # Get configuration from environment variables
    db_path = os.getenv("APEX_LMDB_PATH", "./apex_shared.db")
    map_size_str = os.getenv("APEX_LMDB_MAP_SIZE", "1073741824")  # 1GB default

    try:
        map_size = int(map_size_str)
    except ValueError:
        map_size = 1073741824  # Fallback to 1GB

    # Create and run the server
    server = ClaudeLMDBServer(db_path, map_size)

    try:
        # Run with FastMCP's built-in event loop handling
        asyncio.get_event_loop().run_until_complete(server.run())
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        if "already running" in str(e):
            # Handle case where event loop is already running
            import nest_asyncio

            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(server.run())
        else:
            raise
    finally:
        server.close()


if __name__ == "__main__":
    # Run the server
    main()
