"""Entry point for LMDB MCP server."""

import asyncio

from .lmdb_server import main

if __name__ == "__main__":
    asyncio.run(main())
