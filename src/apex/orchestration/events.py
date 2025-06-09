"""Event bus implementation."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import lmdb
import msgpack


class EventBus:
    """Publish and subscribe to events."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """Initialize event bus.

        Args:
            storage_path: Optional path for persistent event storage

        """
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.env: Optional[lmdb.Environment] = None
        self.db: Optional[lmdb._Database] = None
        if storage_path is not None:
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.env = lmdb.open(str(storage_path), map_size=2 * 1024 * 1024, max_dbs=1)
            self.db = self.env.open_db(b"events")

    def subscribe(
        self, event_type: str, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle events

        """
        self.subscribers.setdefault(event_type, []).append(handler)

    def _persist(self, event: Dict[str, Any]) -> None:
        if self.env is None or self.db is None:
            return
        with self.env.begin(write=True, db=self.db) as txn:
            txn.put(uuid.uuid4().hex.encode(), msgpack.packb(event, use_bin_type=True))

    def publish(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish an event to all subscribers.

        Args:
            event_type: Type of event to publish
            data: Optional event data

        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
        }
        self._persist(event)
        for handler in self.subscribers.get(event_type, []):
            handler(event)

    def replay(self) -> List[Dict[str, Any]]:
        """Replay all persisted events.

        Returns:
            List of all persisted events

        """
        if self.env is None or self.db is None:
            return []
        events: List[Dict[str, Any]] = []
        with self.env.begin(db=self.db) as txn:
            cursor = txn.cursor()
            for _, value in cursor:
                events.append(msgpack.unpackb(value, raw=False))
        return events
