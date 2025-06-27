"""Memory management patterns and utilities for APEX.

This module now provides plugin-based memory management while maintaining
backward compatibility with existing APEX code.
"""

from __future__ import annotations

from .lmdb_mcp import LMDBMCP, AgentDatabase, APEXDatabase, LMDBWithPlugins
from .memory_compat import (
    AsyncMCPAdapter,
    MemoryNamespace,
    MemoryPatterns,
)

# For compatibility, export the classes that other modules expect
__all__ = [
    "MemoryNamespace",
    "MemoryPatterns",
    "AsyncMCPAdapter",
    "APEXDatabase",
    "LMDBMCP",
    "AgentDatabase",
    "LMDBWithPlugins",
]

# Legacy classes that are now deprecated but kept for compatibility
MemorySchema = None
MemoryQuery = None
MemorySnapshot = None
MemoryCleanup = None
ContextAsAService = None
