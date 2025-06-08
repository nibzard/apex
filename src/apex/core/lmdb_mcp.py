"""LMDB MCP server implementation."""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional

import lmdb


class LMDBMCP:
    """Simple LMDB-based MCP server."""

    def __init__(self, path: Path, map_size: int = 1_048_576) -> None:
        self.env = lmdb.open(str(path), map_size=map_size, max_dbs=1)
        self.db = self.env.open_db(b"apex")

    def read(self, key: str) -> Optional[bytes]:
        """Read value for key."""
        with self.env.begin(db=self.db) as txn:
            value = txn.get(key.encode())
            return value

    def write(self, key: str, value: bytes) -> None:
        """Write value for key."""
        with self.env.begin(write=True, db=self.db) as txn:
            txn.put(key.encode(), value)

    def list_keys(self, prefix: str = "") -> List[str]:
        """List keys starting with prefix."""
        keys = []
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

    def delete(self, key: str) -> None:
        """Delete a key."""
        with self.env.begin(write=True, db=self.db) as txn:
            txn.delete(key.encode())

    def close(self) -> None:
        """Close environment."""
        self.env.close()
