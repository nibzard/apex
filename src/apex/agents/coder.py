#!/usr/bin/env python3
"""Coder agent entry point."""

import os

from apex.agents.runner import main
from apex.types import AgentType

if __name__ == "__main__":
    # Set agent type for this module
    os.environ["APEX_AGENT_TYPE"] = AgentType.CODER.value

    # Import and run using the shared event loop
    import asyncio

    asyncio.run(main())
