"""LMDB MCP Server implementation for APEX."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import lmdb
from mcp.server.fastmcp import FastMCP


class LMDBMCPServer:
    """MCP server providing LMDB operations for APEX agents."""

    def __init__(self, db_path: str, map_size: int = 10 * 1024 * 1024 * 1024):
        """Initialize LMDB MCP server.

        Args:
            db_path: Path to LMDB database
            map_size: Maximum size of LMDB database (default: 10GB)

        """
        self.db_path = Path(db_path)
        self.map_size = map_size
        self.env: Optional[lmdb.Environment] = None
        self.db: Optional[Any] = None

        # Create FastMCP server
        self.app = FastMCP("LMDB MCP Server")
        self._register_tools()

    def _register_tools(self) -> None:
        """Register MCP tools."""
        self._register_read_tool()
        self._register_write_tool()
        self._register_list_tool()
        self._register_delete_tool()
        self._register_watch_tool()
        self._register_cursor_scan_tool()
        self._register_transaction_tool()

    def _register_read_tool(self) -> None:
        """Register the read tool."""

        @self.app.tool()
        async def lmdb_read(key: str) -> str:
            """Read value from LMDB by key.

            Args:
                key: The key to read

            Returns:
                JSON string of the value, or null if not found

            """
            try:
                value = await self._read(key)
                if value is None:
                    return "null"
                return value.decode() if isinstance(value, bytes) else str(value)
            except Exception as e:
                return json.dumps({"error": str(e)})

    def _register_write_tool(self) -> None:
        """Register the write tool."""

        @self.app.tool()
        async def lmdb_write(key: str, value: str) -> str:
            """Write value to LMDB.

            Args:
                key: The key to write to
                value: The value to write (JSON string)

            Returns:
                Success confirmation

            """
            try:
                await self._write(key, value.encode())
                return json.dumps({"success": True, "key": key})
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})

    def _register_list_tool(self) -> None:
        """Register the list tool."""

        @self.app.tool()
        async def lmdb_list(prefix: str = "") -> str:
            """List keys with optional prefix.

            Args:
                prefix: Optional prefix to filter keys

            Returns:
                JSON array of matching keys

            """
            try:
                keys = await self._list_keys(prefix)
                return json.dumps(keys)
            except Exception as e:
                return json.dumps({"error": str(e)})

    def _register_delete_tool(self) -> None:
        """Register the delete tool."""

        @self.app.tool()
        async def lmdb_delete(key: str) -> str:
            """Delete a key from LMDB.

            Args:
                key: The key to delete

            Returns:
                Success confirmation

            """
            try:
                await self._delete(key)
                return json.dumps({"success": True, "key": key})
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})

    def _register_watch_tool(self) -> None:
        """Register the watch tool."""

        @self.app.tool()
        async def lmdb_watch(pattern: str, timeout: int = 30) -> str:
            """Watch for changes to keys matching pattern.

            Args:
                pattern: Pattern to match keys (simple prefix matching)
                timeout: Timeout in seconds

            Returns:
                JSON with change notification or timeout

            """
            try:
                await self._ensure_db()

                # Store initial state of matching keys
                initial_keys = await self._list_keys(pattern)
                initial_values = {}

                if self.env is not None and self.db is not None:
                    with self.env.begin(db=self.db) as txn:
                        for key in initial_keys:
                            value = txn.get(key.encode())
                            initial_values[key] = value

                # Poll for changes with exponential backoff
                poll_interval = 0.1  # Start with 100ms
                max_interval = 2.0   # Max 2 seconds
                elapsed = 0.0

                while elapsed < timeout:
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval

                    # Check for changes
                    current_keys = await self._list_keys(pattern)
                    changes = []

                    # Check for new keys
                    new_keys = set(current_keys) - set(initial_keys)
                    for key in new_keys:
                        if self.env is not None and self.db is not None:
                            with self.env.begin(db=self.db) as txn:
                                value = txn.get(key.encode())
                            changes.append({
                                "type": "created",
                                "key": key,
                                "value": value.decode() if value else None
                            })

                    # Check for deleted keys
                    deleted_keys = set(initial_keys) - set(current_keys)
                    for key in deleted_keys:
                        changes.append({
                            "type": "deleted",
                            "key": key,
                            "old_value": (
                                initial_values[key].decode()
                                if initial_values[key]
                                else None
                            )
                        })

                    # Check for modified keys
                    for key in set(current_keys) & set(initial_keys):
                        if self.env is not None and self.db is not None:
                            with self.env.begin(db=self.db) as txn:
                                current_value = txn.get(key.encode())

                            if current_value != initial_values[key]:
                                changes.append({
                                    "type": "modified",
                                    "key": key,
                                    "old_value": (
                                        initial_values[key].decode()
                                        if initial_values[key]
                                        else None
                                    ),
                                    "new_value": (
                                        current_value.decode()
                                        if current_value
                                        else None
                                    )
                                })

                    if changes:
                        return json.dumps({
                            "pattern": pattern,
                            "elapsed": elapsed,
                            "changes": changes
                        })

                    # Exponential backoff to reduce CPU usage
                    poll_interval = min(poll_interval * 1.2, max_interval)

                # Timeout reached
                return json.dumps({
                    "pattern": pattern,
                    "timeout": True,
                    "elapsed": elapsed,
                    "changes": []
                })

            except Exception as e:
                return json.dumps({"error": str(e)})

    def _register_cursor_scan_tool(self) -> None:
        """Register the cursor scan tool."""

        @self.app.tool()
        async def lmdb_cursor_scan(start: str, end: str, limit: int = 100) -> str:
            """Scan a range of keys using cursor.

            Args:
                start: Start key for range
                end: End key for range
                limit: Maximum number of keys to return

            Returns:
                JSON array of key-value pairs in range

            """
            try:
                results = await self._cursor_scan(start, end, limit)
                return json.dumps(results)
            except Exception as e:
                return json.dumps({"error": str(e)})

    def _register_transaction_tool(self) -> None:
        """Register the transaction tool."""

        @self.app.tool()
        async def lmdb_transaction(operations: str) -> str:
            """Execute multiple operations in a transaction.

            Args:
                operations: JSON array of operations

            Returns:
                Transaction result

            """
            try:
                ops = json.loads(operations)
                result = await self._transaction(ops)
                return json.dumps(result)
            except Exception as e:
                return json.dumps({"error": str(e)})

    async def _ensure_db(self) -> None:
        """Ensure database is initialized."""
        if self.env is None:
            # Create parent directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Open LMDB environment
            self.env = lmdb.open(
                str(self.db_path), map_size=self.map_size, max_dbs=1, create=True
            )
            self.db = self.env.open_db(b"apex", create=True)

    async def _read(self, key: str) -> Optional[bytes]:
        """Read value for key."""
        await self._ensure_db()
        if self.env is not None and self.db is not None:
            with self.env.begin(db=self.db) as txn:
                return txn.get(key.encode())
        return None

    async def _write(self, key: str, value: bytes) -> None:
        """Write value for key."""
        await self._ensure_db()
        if self.env is not None and self.db is not None:
            with self.env.begin(write=True, db=self.db) as txn:
                txn.put(key.encode(), value)

    async def _list_keys(self, prefix: str = "") -> List[str]:
        """List keys starting with prefix."""
        await self._ensure_db()
        keys = []
        if self.env is not None and self.db is not None:
            with self.env.begin(db=self.db) as txn:
                cursor = txn.cursor()
                if prefix:
                    start = prefix.encode()
                    if cursor.set_range(start):
                        for k in cursor.iternext(keys=True, values=False):
                            if not k.startswith(start):
                                break
                            keys.append(k.decode())
                else:
                    keys = [k.decode() for k, _ in cursor]
        return keys

    async def _delete(self, key: str) -> None:
        """Delete a key."""
        await self._ensure_db()
        if self.env is not None and self.db is not None:
            with self.env.begin(write=True, db=self.db) as txn:
                txn.delete(key.encode())

    async def _cursor_scan(
        self, start: str, end: str, limit: int
    ) -> List[Dict[str, str]]:
        """Scan range with cursor."""
        await self._ensure_db()
        results = []
        count = 0

        if self.env is not None and self.db is not None:
            with self.env.begin(db=self.db) as txn:
                cursor = txn.cursor()
                start_bytes = start.encode()
                end_bytes = end.encode()

                if cursor.set_range(start_bytes):
                    for key, value in cursor:
                        if key > end_bytes or count >= limit:
                            break

                        results.append(
                            {"key": key.decode(), "value": value.decode() if value else ""}
                        )
                        count += 1

        return results

    async def _transaction(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute operations in transaction."""
        await self._ensure_db()

        results = []
        if self.env is not None and self.db is not None:
            with self.env.begin(write=True, db=self.db) as txn:
                for op in operations:
                    op_type = op.get("type")
                    key = op.get("key", "").encode()

                    try:
                        if op_type == "read":
                            value = txn.get(key)
                            results.append(
                                {
                                    "type": "read",
                                    "key": op.get("key"),
                                    "value": value.decode() if value else None,
                                }
                            )
                        elif op_type == "write":
                            value = op.get("value", "").encode()
                            txn.put(key, value)
                            results.append(
                                {"type": "write", "key": op.get("key"), "success": True}
                            )
                        elif op_type == "delete":
                            txn.delete(key)
                            results.append(
                                {"type": "delete", "key": op.get("key"), "success": True}
                            )
                        else:
                            results.append(
                                {
                                    "type": op_type,
                                    "error": f"Unknown operation type: {op_type}",
                                }
                            )
                    except Exception as e:
                        results.append(
                            {"type": op_type, "key": op.get("key"), "error": str(e)}
                        )

        return {"results": results}

    async def run(self) -> None:
        """Run the MCP server."""
        await self.app.run()  # type: ignore[func-returns-value]

    def close(self) -> None:
        """Close the database."""
        if self.env:
            self.env.close()
            self.env = None


async def main() -> None:
    """Run the MCP server."""
    # Get configuration from environment
    db_path = os.getenv("LMDB_PATH", "./apex.db")
    map_size = int(os.getenv("LMDB_MAP_SIZE", "10737418240"))  # 10GB default

    # Create and run server
    server = LMDBMCPServer(db_path, map_size)

    try:
        await server.run()
    finally:
        server.close()


if __name__ == "__main__":
    asyncio.run(main())
