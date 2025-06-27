"""LMDB MCP Server implementation for APEX.

This module provides APEX-specific functionality using the external lmdb-mcp package.
"""

from __future__ import annotations

import asyncio
import os

# Import from the external lmdb-mcp package
from lmdb_mcp.server import LMDBMCPServer as _LMDBMCPServer


class LMDBMCPServer(_LMDBMCPServer):
    """APEX-specific LMDB MCP server.

    This extends the base LMDB MCP server with APEX-specific configurations
    and tool prefixes.
    """

    def __init__(self, db_path: str, map_size: int = 10 * 1024 * 1024 * 1024):
        """Initialize APEX LMDB MCP server.

        Args:
            db_path: Path to LMDB database
            map_size: Maximum size of LMDB database (default: 10GB)

        """
        # Use the external server with APEX-specific tool prefix
        super().__init__(db_path, map_size, tool_prefix="lmdb_")


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
