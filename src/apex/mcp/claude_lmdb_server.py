#!/usr/bin/env python3
"""LMDB MCP Server for Claude Code integration."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Optional

import lmdb
from mcp.server.fastmcp import FastMCP


class ClaudeLMDBServer:
    """LMDB MCP server designed for Claude Code integration."""

    def __init__(self, db_path: str, map_size: int = 1024 * 1024 * 1024):  # 1GB default
        """Initialize LMDB MCP server for Claude Code.

        Args:
            db_path: Path to LMDB database
            map_size: Maximum size of LMDB database (default: 1GB)

        """
        self.db_path = Path(db_path)
        self.map_size = map_size
        self.env: Optional[lmdb.Environment] = None
        self.db: Optional[Any] = None

        # Create FastMCP server with stdio transport for Claude Code
        self.app = FastMCP("APEX LMDB")
        self._register_tools()

    def _ensure_db(self) -> None:
        """Ensure database is initialized."""
        if self.env is None:
            # Create parent directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Open LMDB environment
            self.env = lmdb.open(
                str(self.db_path), map_size=self.map_size, max_dbs=10, create=True
            )
            self.db = self.env.open_db(b"apex_data", create=True)

    def _register_tools(self) -> None:
        """Register all MCP tools for APEX."""

        @self.app.tool()
        async def mcp__lmdb__read(key: str) -> str:
            """Read value from APEX LMDB by key.

            Args:
                key: The key to read from LMDB

            Returns:
                The value as a string, or null if not found

            """
            try:
                self._ensure_db()
                with self.env.begin(db=self.db) as txn:
                    value = txn.get(key.encode())
                    if value is None:
                        return "null"
                    return value.decode()
            except Exception as e:
                return json.dumps({"error": f"Failed to read key '{key}': {str(e)}"})

        @self.app.tool()
        async def mcp__lmdb__write(key: str, value: str) -> str:
            """Write value to APEX LMDB.

            Args:
                key: The key to write to
                value: The value to write

            Returns:
                Success confirmation

            """
            try:
                self._ensure_db()
                with self.env.begin(write=True, db=self.db) as txn:
                    txn.put(key.encode(), value.encode())
                return json.dumps({"success": True, "key": key})
            except Exception as e:
                return json.dumps({"error": f"Failed to write key '{key}': {str(e)}"})

        @self.app.tool()
        async def mcp__lmdb__list(prefix: str = "") -> str:
            """List keys with optional prefix from APEX LMDB.

            Args:
                prefix: Optional prefix to filter keys (default: all keys)

            Returns:
                JSON array of matching keys

            """
            try:
                self._ensure_db()
                keys = []
                with self.env.begin(db=self.db) as txn:
                    cursor = txn.cursor()
                    if prefix:
                        start_key = prefix.encode()
                        if cursor.set_range(start_key):
                            for key, _ in cursor:
                                key_str = key.decode()
                                if not key_str.startswith(prefix):
                                    break
                                keys.append(key_str)
                    else:
                        keys = [key.decode() for key, _ in cursor]
                return json.dumps(keys)
            except Exception as e:
                return json.dumps({"error": f"Failed to list keys: {str(e)}"})

        @self.app.tool()
        async def mcp__lmdb__delete(key: str) -> str:
            """Delete a key from APEX LMDB.

            Args:
                key: The key to delete

            Returns:
                Success confirmation

            """
            try:
                self._ensure_db()
                with self.env.begin(write=True, db=self.db) as txn:
                    deleted = txn.delete(key.encode())
                return json.dumps({"success": True, "deleted": deleted, "key": key})
            except Exception as e:
                return json.dumps({"error": f"Failed to delete key '{key}': {str(e)}"})

        @self.app.tool()
        async def mcp__lmdb__cursor_scan(prefix: str = "", limit: int = 100) -> str:
            """Scan APEX LMDB keys and values with optional prefix.

            Args:
                prefix: Optional prefix to filter keys
                limit: Maximum number of results to return (default: 100)

            Returns:
                JSON array of key-value pairs

            """
            try:
                self._ensure_db()
                results = []
                count = 0

                with self.env.begin(db=self.db) as txn:
                    cursor = txn.cursor()
                    if prefix:
                        start_key = prefix.encode()
                        if cursor.set_range(start_key):
                            for key, value in cursor:
                                if count >= limit:
                                    break
                                key_str = key.decode()
                                if not key_str.startswith(prefix):
                                    break
                                results.append(
                                    {"key": key_str, "value": value.decode()}
                                )
                                count += 1
                    else:
                        for key, value in cursor:
                            if count >= limit:
                                break
                            results.append(
                                {"key": key.decode(), "value": value.decode()}
                            )
                            count += 1

                return json.dumps({"results": results, "count": len(results)})
            except Exception as e:
                return json.dumps({"error": f"Failed to scan: {str(e)}"})

        @self.app.tool()
        async def mcp__lmdb__project_status(project_id: str) -> str:
            """Get APEX project status and summary.

            Args:
                project_id: The project ID to get status for

            Returns:
                JSON object with project status information

            """
            try:
                self._ensure_db()

                # Get project config
                project_key = f"/projects/{project_id}/config"
                with self.env.begin(db=self.db) as txn:
                    project_data = txn.get(project_key.encode())
                    if not project_data:
                        return json.dumps({"error": f"Project {project_id} not found"})

                project_config = json.loads(project_data.decode())

                # Get task counts
                task_counts = {"pending": 0, "in_progress": 0, "completed": 0}
                task_prefix = f"/projects/{project_id}/tasks/"

                with self.env.begin(db=self.db) as txn:
                    cursor = txn.cursor()
                    start_key = task_prefix.encode()
                    if cursor.set_range(start_key):
                        for key, value in cursor:
                            key_str = key.decode()
                            if not key_str.startswith(task_prefix):
                                break
                            try:
                                task_data = json.loads(value.decode())
                                status = task_data.get("status", "unknown")
                                if status in task_counts:
                                    task_counts[status] += 1
                            except:
                                pass

                # Get agent status
                agent_statuses = {}
                agent_prefix = f"/projects/{project_id}/agents/"

                with self.env.begin(db=self.db) as txn:
                    cursor = txn.cursor()
                    start_key = agent_prefix.encode()
                    if cursor.set_range(start_key):
                        for key, value in cursor:
                            key_str = key.decode()
                            if not key_str.startswith(agent_prefix):
                                break
                            try:
                                agent_name = key_str.split("/")[-1]
                                agent_data = json.loads(value.decode())
                                agent_statuses[agent_name] = agent_data.get(
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

        @self.app.tool()
        async def mcp__lmdb__watch(prefix: str, timeout: int = 30) -> str:
            """Watch for changes to keys with prefix (polling-based).

            Args:
                prefix: Key prefix to watch for changes
                timeout: Maximum time to wait for changes in seconds

            Returns:
                JSON object with change information or timeout message

            """
            try:
                self._ensure_db()

                # Get initial state
                initial_keys = {}
                with self.env.begin(db=self.db) as txn:
                    cursor = txn.cursor()
                    start_key = prefix.encode()
                    if cursor.set_range(start_key):
                        for key, value in cursor:
                            key_str = key.decode()
                            if not key_str.startswith(prefix):
                                break
                            initial_keys[key_str] = value.decode()

                # Poll for changes
                import time

                start_time = time.time()
                poll_interval = 0.5  # 500ms polling interval

                while time.time() - start_time < timeout:
                    await asyncio.sleep(poll_interval)

                    current_keys = {}
                    with self.env.begin(db=self.db) as txn:
                        cursor = txn.cursor()
                        start_key = prefix.encode()
                        if cursor.set_range(start_key):
                            for key, value in cursor:
                                key_str = key.decode()
                                if not key_str.startswith(prefix):
                                    break
                                current_keys[key_str] = value.decode()

                    # Check for changes
                    added = set(current_keys.keys()) - set(initial_keys.keys())
                    removed = set(initial_keys.keys()) - set(current_keys.keys())
                    modified = {
                        k
                        for k in current_keys.keys()
                        if k in initial_keys and current_keys[k] != initial_keys[k]
                    }

                    if added or removed or modified:
                        return json.dumps(
                            {
                                "change_detected": True,
                                "added": list(added),
                                "removed": list(removed),
                                "modified": list(modified),
                                "timestamp": time.time(),
                            }
                        )

                # Timeout reached
                return json.dumps(
                    {
                        "change_detected": False,
                        "message": f"No changes detected within {timeout} seconds",
                        "timeout": True,
                    }
                )

            except Exception as e:
                return json.dumps(
                    {"error": f"Failed to watch prefix '{prefix}': {str(e)}"}
                )

    async def run(self) -> None:
        """Run the MCP server with stdio transport for Claude Code."""
        # Use stdio transport for Claude Code integration
        await self.app.run(transport="stdio")

    def close(self) -> None:
        """Close the database."""
        if self.env:
            self.env.close()
            self.env = None


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
