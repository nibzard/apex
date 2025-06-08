"""Persistent state storage using LMDB."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

import lmdb
import msgpack


class StateStore:
    """Simple LMDB-backed key-value store."""

    def __init__(self, path: Path, map_size: int = 2 * 1024 * 1024):
        self.path = path
        self.env = lmdb.open(str(self.path), map_size=map_size)

    def _pack(self, value: Any) -> bytes:
        return msgpack.packb(value, use_bin_type=True)

    def _unpack(self, data: Optional[bytes]) -> Any:
        if data is None:
            return None
        return msgpack.unpackb(data, raw=False)

    def set(self, key: str, value: Any) -> None:
        with self.env.begin(write=True) as txn:
            txn.put(key.encode(), self._pack(value))

    def get(self, key: str) -> Any:
        with self.env.begin() as txn:
            return self._unpack(txn.get(key.encode()))

    def delete(self, key: str) -> bool:
        with self.env.begin(write=True) as txn:
            return txn.delete(key.encode())

    def keys(self) -> Iterable[str]:
        with self.env.begin() as txn:
            cursor = txn.cursor()
            for key, _ in cursor:
                yield key.decode()
