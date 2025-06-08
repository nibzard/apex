"""APEX CLI commands."""

from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="apex",
    help="APEX - Adversarial Pair EXecution for AI-powered development",
    no_args_is_help=True,
)

# Sub-command groups
agent_app = typer.Typer(help="Agent management commands")
memory_app = typer.Typer(help="Memory operations")

app.add_typer(agent_app, name="agent")
app.add_typer(memory_app, name="memory")


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
def list() -> None:
    """List existing APEX projects."""
    projects_dir = Path("projects")
    if not projects_dir.exists():
        typer.echo("No projects found.")
        raise typer.Exit()

    typer.echo("PROJECT")
    for project in sorted(p for p in projects_dir.iterdir() if p.is_dir()):
        typer.echo(project.name)


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
def pause() -> None:
    """Pause running agents."""
    typer.echo("Pausing agents...")
    # TODO: Implement pause logic


@app.command()
def resume() -> None:
    """Resume paused agents."""
    typer.echo("Resuming agents...")
    # TODO: Implement resume logic


@app.command()
def stop() -> None:
    """Stop all running agents."""
    typer.echo("Stopping agents...")
    # TODO: Implement stop logic


@app.command()
def tui(
    layout: Optional[str] = typer.Option("dashboard", "--layout", help="TUI layout"),
    theme: Optional[str] = typer.Option("dark", "--theme", help="Color theme"),
):
    """Launch TUI interface."""
    from apex.tui import DashboardApp

    DashboardApp().run()


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


@agent_app.command("list")
def agent_list() -> None:
    """Show agent status."""
    for agent in ["Supervisor", "Coder", "Adversary"]:
        typer.echo(f"{agent}: inactive")


@agent_app.command("restart")
def agent_restart(agent_name: str) -> None:
    """Restart agent process."""
    typer.echo(f"Restarting {agent_name}...")
    # TODO: Implement restart logic


@memory_app.command("show")
def memory_show(key: Optional[str] = None) -> None:
    """Display memory contents."""
    if key is None:
        typer.echo("Showing memory root")
    else:
        typer.echo(f"Showing memory key: {key}")
    # TODO: Implement memory retrieval


def main():
    """Main entry point for CLI."""
    app()
