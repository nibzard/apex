"""APEX CLI commands."""

from pathlib import Path
from typing import Optional

from apex.vcs import GitHubClient, GitWrapper, auto_commit

import typer

app = typer.Typer(
    name="apex",
    help="APEX - Adversarial Pair EXecution for AI-powered development",
    no_args_is_help=True,
)

git_app = typer.Typer(help="Git operations")
github_app = typer.Typer(help="GitHub integration")


@app.command()
def new(
    project_name: str = typer.Argument(..., help="Name of the new project"),
    template: Optional[str] = typer.Option(
        None, "--template", "-t", help="Project template"
    ),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git initialization"),
    tech_stack: Optional[str] = typer.Option(None, "--tech", help="Technology stack"),
):
    """Create a new APEX project."""
    typer.echo(f"Creating new project: {project_name}")
    # TODO: Implement project creation


@app.command()
def init(
    import_config: Optional[Path] = typer.Option(
        None, "--import", help="Import configuration file"
    ),
):
    """Initialize APEX in existing project."""
    typer.echo("Initializing APEX...")
    # TODO: Implement initialization


@app.command()
def start(
    agents: Optional[str] = typer.Option(
        None, "--agents", help="Specific agents to start"
    ),
    continue_session: Optional[str] = typer.Option(
        None, "--continue", help="Continue from checkpoint"
    ),
    task: Optional[str] = typer.Option(None, "--task", help="Initial task description"),
):
    """Start APEX agents."""
    typer.echo("Starting agents...")
    # TODO: Implement agent startup


@app.command()
def tui(
    layout: Optional[str] = typer.Option("dashboard", "--layout", help="TUI layout"),
    theme: Optional[str] = typer.Option("dark", "--theme", help="Color theme"),
):
    """Launch TUI interface."""
    typer.echo("Launching TUI...")
    # TODO: Implement TUI


@app.command()
def status():
    """Show agent status."""
    typer.echo("Agent Status:")
    typer.echo("  Supervisor: ✓ Active")
    typer.echo("  Coder: ✓ Active")
    typer.echo("  Adversary: ✓ Active")
    # TODO: Implement real status


@app.command()
def version():
    """Show version information."""
    from apex import __version__

    typer.echo(f"APEX v{__version__}")




@git_app.command("status")
def git_status():
    """Show git status."""
    wrapper = GitWrapper(Path("."))
    typer.echo(wrapper.status())


@git_app.command("auto-commit")
def git_auto_commit(
    message: Optional[str] = typer.Option(None, "--message", "-m"),
    no_tests: bool = typer.Option(False, "--no-tests", help="Skip test requirement"),
):
    """Stage changes, optionally run tests, and commit."""
    if not no_tests:
        typer.echo("Running tests...")
        # Placeholder for running project tests
    sha = auto_commit(Path("."), message)
    typer.echo(f"Committed {sha}")


@github_app.command("pr-create")
def github_pr_create(
    repo: str = typer.Option(..., "--repo", help="Repository name"),
    title: str = typer.Option(..., "--title", help="PR title"),
    body: str = typer.Option("", "--body", help="PR description"),
    head: str = typer.Option("main", "--head", help="Head branch"),
    base: str = typer.Option("main", "--base", help="Base branch"),
    draft: bool = typer.Option(False, "--draft", help="Create draft PR"),
):
    """Create a pull request on GitHub."""
    client = GitHubClient()
    url = client.create_pull_request(repo, title, body, head, base, draft)
    typer.echo(url)


# Register subcommands
app.add_typer(git_app, name="git")
app.add_typer(github_app, name="github")


def main():
    """Main entry point for CLI."""
    app()
