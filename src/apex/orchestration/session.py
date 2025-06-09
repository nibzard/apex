"""Session management utilities."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import lmdb
import msgpack
from pydantic import BaseModel, Field

from apex.types import ProjectConfig, SessionState


class Session(BaseModel):
    """Represents a single APEX session."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: ProjectConfig
    metadata: Dict[str, Any] = Field(default_factory=dict)
    state: SessionState = SessionState.INACTIVE
    created_at: datetime = Field(default_factory=datetime.now)


class SessionManager:
    """Manage the lifecycle of APEX sessions."""

    def __init__(self, path: Path):
        """Initialize session manager.

        Args:
            path: Directory path for session storage

        """
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        # a dedicated LMDB environment for sessions
        self.env = lmdb.open(
            str(self.path / "sessions.db"), map_size=2 * 1024 * 1024, max_dbs=1
        )
        self.db = self.env.open_db(b"sessions")

    def _serialize(self, session: Session) -> bytes:
        """Serialize a session to bytes."""
        return msgpack.packb(session.model_dump(mode="json"), use_bin_type=True)

    def _deserialize(self, data: bytes) -> Session:
        """Deserialize a session from bytes."""
        unpacked = msgpack.unpackb(data, raw=False)
        return Session.model_validate(unpacked)

    def create(
        self, config: ProjectConfig, metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create and persist a new session."""
        session = Session(config=config, metadata=metadata or {})
        with self.env.begin(write=True, db=self.db) as txn:
            txn.put(session.session_id.encode(), self._serialize(session))
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        with self.env.begin(db=self.db) as txn:
            data = txn.get(session_id.encode())
            if data is None:
                return None
            return self._deserialize(data)

    def list_sessions(self) -> List[Session]:
        """Return all stored sessions."""
        sessions: List[Session] = []
        with self.env.begin(db=self.db) as txn:
            cursor = txn.cursor()
            for _, value in cursor:
                sessions.append(self._deserialize(value))
        return sessions

    def update(self, session: Session) -> None:
        """Persist an updated session."""
        with self.env.begin(write=True, db=self.db) as txn:
            txn.put(session.session_id.encode(), self._serialize(session))

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        with self.env.begin(write=True, db=self.db) as txn:
            return txn.delete(session_id.encode())
