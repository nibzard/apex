"""Tests for LMDBMCP."""

from pathlib import Path

from apex.core import LMDBMCP


def test_lmdb_read_write(tmp_path):
    path = tmp_path / "db"
    mcp = LMDBMCP(path)
    mcp.write("foo", b"bar")
    assert mcp.read("foo") == b"bar"
    assert mcp.list_keys() == ["foo"]
    mcp.delete("foo")
    assert mcp.read("foo") is None
    mcp.close()
