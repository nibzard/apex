"""Entry point for APEX LMDB MCP server compatible with Claude Code."""

import sys

from .claude_lmdb_server import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error running APEX LMDB MCP server: {e}", file=sys.stderr)
        sys.exit(1)
