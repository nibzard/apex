"""Tests for CLI commands."""

from typer.testing import CliRunner

from apex.cli.commands import app

runner = CliRunner()


def test_version_command() -> None:
    """Test version command output."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "APEX v" in result.stdout


def test_list_no_projects(tmp_path, monkeypatch) -> None:
    """Test list command with no projects."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No projects" in result.stdout


def test_list_with_project(tmp_path, monkeypatch) -> None:
    """Test list command with existing projects."""
    projects = tmp_path / "projects"
    projects.mkdir()
    (projects / "demo").mkdir()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "demo" in result.stdout


def test_agent_list() -> None:
    """Test agent list command."""
    result = runner.invoke(app, ["agent", "list"])
    assert result.exit_code == 0
    assert "Supervisor" in result.stdout
