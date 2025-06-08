"""Tests for GitWrapper and auto_commit utilities."""

from pathlib import Path

from git import Repo

from apex.vcs import GitWrapper, auto_commit


def test_gitwrapper_commit(tmp_path: Path) -> None:
    repo = Repo.init(tmp_path)
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    repo.config_writer().set_value("user", "name", "Tester").release()

    test_file = tmp_path / "file.txt"
    test_file.write_text("example")

    wrapper = GitWrapper(tmp_path)
    wrapper.add_all()
    sha = wrapper.commit("test commit")

    log = repo.git.log("--oneline")
    assert "test commit" in log


def test_auto_commit(tmp_path: Path) -> None:
    repo = Repo.init(tmp_path)
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    repo.config_writer().set_value("user", "name", "Tester").release()

    file1 = tmp_path / "a.txt"
    file1.write_text("a")

    sha = auto_commit(tmp_path, "auto commit")
    assert sha
    log = repo.git.log("--oneline")
    assert "auto commit" in log

