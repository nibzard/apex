"""Checkpoint and continuation utilities."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional

import msgpack


class ContinuationManager:
    """Manage checkpoints for pause/resume functionality."""

    def __init__(self, base_path: Path):
        """Initialize continuation manager.

        Args:
            base_path: Base directory for storing checkpoints

        """
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        path = self.base_path / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_checkpoint(self, session_id: str, state: Dict[str, Any]) -> Path:
        """Persist a checkpoint for the given session."""
        session_dir = self._session_dir(session_id)
        file_path = session_dir / f"{int(time.time())}.msgpack"
        with open(file_path, "wb") as f:
            msgpack.pack(state, f)
        return file_path

    def load_checkpoint(
        self, session_id: str, checkpoint_file: Optional[Path] = None
    ) -> Optional[Dict[str, Any]]:
        """Load the latest or specified checkpoint."""
        session_dir = self._session_dir(session_id)
        if checkpoint_file is None:
            checkpoints = sorted(session_dir.glob("*.msgpack"))
            if not checkpoints:
                return None
            checkpoint_file = checkpoints[-1]
        if not checkpoint_file.exists():
            return None
        with open(checkpoint_file, "rb") as f:
            return msgpack.unpack(f, raw=False)
