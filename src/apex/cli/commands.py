"""APEX CLI commands."""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from apex.core.agent_runner import AgentRunner
from apex.types import AgentType, ProjectConfig

app = typer.Typer(
    name="apex",
    help="APEX - Adversarial Pair EXecution for AI-powered development",
    no_args_is_help=True,
)

# Global console for rich output
console = Console()

# Global state for CLI (simple approach for now)
_current_runner: Optional[AgentRunner] = None

# Sub-command groups

agent_app = typer.Typer(help="Agent management commands")
memory_app = typer.Typer(help="Memory operations")

# Option defaults
TEMPLATE_OPTION = typer.Option(None, "--template", "-t", help="Project template")
NO_GIT_OPTION = typer.Option(False, "--no-git", help="Skip git initialization")
TECH_STACK_OPTION = typer.Option(None, "--tech", help="Technology stack")
IMPORT_CONFIG_OPTION = typer.Option(
    None,
    "--import",
    help="Import configuration file",
)
AGENTS_OPTION = typer.Option(
    None,
    "--agents",
    help="Specific agents to start",
)
CONTINUE_SESSION_OPTION = typer.Option(
    None,
    "--continue",
    help="Continue from checkpoint",
)
TASK_OPTION = typer.Option(
    None,
    "--task",
    help="Initial task description",
)
LAYOUT_OPTION = typer.Option("dashboard", "--layout", help="TUI layout")
THEME_OPTION = typer.Option("dark", "--theme", help="Color theme")

app.add_typer(agent_app, name="agent")
app.add_typer(memory_app, name="memory")


def _load_project_config(project_path: Path = Path(".")) -> Optional[ProjectConfig]:
    """Load project configuration from current directory."""
    config_file = project_path / "apex.json"
    if not config_file.exists():
        return None

    try:
        with open(config_file) as f:
            data = json.load(f)
        return ProjectConfig(**data)
    except Exception as e:
        console.print(f"[red]Error loading project config: {e}[/red]")
        return None


def _save_project_config(config: ProjectConfig, project_path: Path = Path(".")) -> bool:
    """Save project configuration to current directory."""
    config_file = project_path / "apex.json"
    try:
        with open(config_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2, default=str)
        return True
    except Exception as e:
        console.print(f"[red]Error saving project config: {e}[/red]")
        return False


async def _get_or_create_runner() -> Optional[AgentRunner]:
    """Get existing runner or create new one from project config."""
    global _current_runner

    if _current_runner:
        return _current_runner

    # Try to load project config
    config = _load_project_config()
    if not config:
        console.print(
            (
                "[red]No APEX project found in current directory. "
                "Run 'apex init' first.[/red]"
            )
        )
        return None

    # Create new runner
    _current_runner = AgentRunner(config)
    return _current_runner


def _run_async(coro):
    """Run async functions in CLI commands."""
    try:
        return asyncio.run(coro)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None


@app.command()
def new(
    project_name: str = typer.Argument(..., help="Name of the new project"),
    template: Optional[str] = TEMPLATE_OPTION,
    no_git: bool = NO_GIT_OPTION,
    tech_stack: Optional[str] = TECH_STACK_OPTION,
):
    """Create a new APEX project."""
    console.print(f"[bold blue]Creating new APEX project: {project_name}[/bold blue]")

    # Create project directory
    project_path = Path(project_name)
    if project_path.exists():
        console.print(f"[red]Directory '{project_name}' already exists[/red]")
        raise typer.Exit(1)

    project_path.mkdir()

    # Interactive setup
    console.print("\n[bold]Project Setup[/bold]")

    description = typer.prompt(
        "Project description", default=f"A new {project_name} project"
    )

    # Technology stack
    if tech_stack:
        tech_list = [t.strip() for t in tech_stack.split(",")]
    else:
        console.print("\nSelect technologies (comma-separated):")
        console.print("Examples: Python, JavaScript, TypeScript, React, Flask, Django")
        tech_input = typer.prompt("Technologies", default="Python")
        tech_list = [t.strip() for t in tech_input.split(",")]

    # Project type
    project_types = [
        "Web Application",
        "API Service",
        "CLI Tool",
        "Library",
        "Data Pipeline",
        "Other",
    ]
    console.print(f"\nProject types: {', '.join(project_types)}")
    project_type = typer.prompt("Project type", default="CLI Tool")

    # Features
    features_input = typer.prompt(
        "Key features (comma-separated)", default="core functionality"
    )
    features = [f.strip() for f in features_input.split(",")]

    # Create configuration
    config = ProjectConfig(
        project_id=str(uuid.uuid4()),
        name=project_name,
        description=description,
        tech_stack=tech_list,
        project_type=project_type,
        features=features,
    )

    # Save configuration
    if _save_project_config(config, project_path):
        console.print("[green]✓ Created project configuration[/green]")
    else:
        console.print("[red]✗ Failed to create project configuration[/red]")
        raise typer.Exit(1)

    # Initialize git
    if not no_git:
        import subprocess

        try:
            subprocess.run(
                ["git", "init"], cwd=project_path, check=True, capture_output=True
            )
            console.print("[green]✓ Initialized git repository[/green]")
        except subprocess.CalledProcessError:
            console.print("[yellow]⚠ Failed to initialize git repository[/yellow]")

    console.print(
        f"\n[bold green]✓ Project '{project_name}' created successfully![/bold green]"
    )
    console.print("[dim]Next steps:[/dim]")
    console.print(f"[dim]  cd {project_name}[/dim]")
    console.print('[dim]  apex start --task "Your initial task here"[/dim]')


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
    import_config: Optional[Path] = IMPORT_CONFIG_OPTION,
):
    """Initialize APEX in existing project."""
    console.print("[bold blue]Initializing APEX in current directory[/bold blue]")

    # Check if already initialized
    if Path("apex.json").exists():
        console.print("[yellow]APEX already initialized in this directory[/yellow]")
        if not typer.confirm("Reinitialize?"):
            raise typer.Exit()

    if import_config and import_config.exists():
        # Import existing configuration
        try:
            with open(import_config) as f:
                data = json.load(f)
            config = ProjectConfig(**data)
            console.print(
                f"[green]✓ Imported configuration from {import_config}[/green]"
            )
        except Exception as e:
            console.print(f"[red]Error importing config: {e}[/red]")
            raise typer.Exit(1) from None
    else:
        # Interactive initialization
        project_name = typer.prompt("Project name", default=Path.cwd().name)
        description = typer.prompt(
            "Project description", default=f"APEX project: {project_name}"
        )

        console.print("\nTechnologies (comma-separated):")
        tech_input = typer.prompt("Technologies", default="Python")
        tech_list = [t.strip() for t in tech_input.split(",")]

        project_type = typer.prompt("Project type", default="CLI Tool")

        features_input = typer.prompt(
            "Key features (comma-separated)", default="core functionality"
        )
        features = [f.strip() for f in features_input.split(",")]

        config = ProjectConfig(
            project_id=str(uuid.uuid4()),
            name=project_name,
            description=description,
            tech_stack=tech_list,
            project_type=project_type,
            features=features,
        )

    # Save configuration
    if _save_project_config(config):
        console.print("[green]✓ APEX initialized successfully![/green]")
        console.print("[dim]Run 'apex start' to begin development[/dim]")
    else:
        raise typer.Exit(1)


@app.command()
def start(
    agents: Optional[str] = AGENTS_OPTION,
    continue_session: Optional[str] = CONTINUE_SESSION_OPTION,
    task: Optional[str] = TASK_OPTION,
):
    """Start APEX agents."""

    async def _start_agents():
        runner = await _get_or_create_runner()
        if not runner:
            return

        console.print("[bold blue]Starting APEX agents...[/bold blue]")

        if task:
            # Start complete workflow
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                workflow_task = progress.add_task("Creating workflow...", total=None)

                workflow_id = await runner.start_workflow(task, auto_start_agents=True)

                progress.update(workflow_task, description="Workflow created!")
                progress.stop()

            console.print(f"[green]✓ Started workflow: {workflow_id}[/green]")
            console.print(f"[dim]Task: {task}[/dim]")

            # Show initial workflow status
            workflow_status = await runner.get_workflow_status(workflow_id)
            if workflow_status:
                console.print("\n[bold]Workflow Status:[/bold]")
                console.print(f"Status: [cyan]{workflow_status['status']}[/cyan]")
                console.print(
                    f"Tasks: [cyan]{len(workflow_status.get('task_ids', []))}[/cyan]"
                )

                # Show first few tasks
                for i, task_id in enumerate(workflow_status.get("task_ids", [])[:3], 1):
                    task_status = await runner.task_workflow.get_task_status(task_id)
                    if task_status:
                        desc = task_status["description"][:50] + (
                            "..." if len(task_status["description"]) > 50 else ""
                        )
                        console.print(
                            f"  {i}. {desc} → [cyan]{task_status['assigned_to']}[/cyan]"
                        )
        else:
            # Start agents without specific task
            console.print("Starting agents in monitoring mode...")

            if agents:
                # Start specific agents
                agent_list = [a.strip().lower() for a in agents.split(",")]
                for agent_name in agent_list:
                    try:
                        agent_type = AgentType(agent_name)
                        await runner.start_agent(agent_type)
                        console.print(
                            f"[green]✓ Started {agent_type.value} agent[/green]"
                        )
                    except ValueError:
                        console.print(f"[red]✗ Unknown agent type: {agent_name}[/red]")
            else:
                # Start all agents
                await runner.start_all_agents()
                console.print("[green]✓ Started all agents[/green]")

        console.print("\n[dim]Use 'apex status' to monitor agents[/dim]")
        console.print("[dim]Use 'apex tui' for interactive monitoring[/dim]")

    _run_async(_start_agents())


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
    layout: Optional[str] = LAYOUT_OPTION,
    theme: Optional[str] = THEME_OPTION,
):
    """Launch TUI interface."""
    from apex.tui import DashboardApp

    DashboardApp().run()


@app.command()
def status():
    """Show agent status."""

    async def _show_status():
        runner = await _get_or_create_runner()
        if not runner:
            return

        console.print("[bold blue]APEX Status[/bold blue]")

        # Agent status table
        agent_table = Table(title="Agent Status")
        agent_table.add_column("Agent", style="cyan")
        agent_table.add_column("Status", style="green")
        agent_table.add_column("Memory", style="yellow")
        agent_table.add_column("Uptime", style="dim")

        agent_status = runner.get_agent_status()

        if not agent_status:
            console.print("[yellow]No agents currently running[/yellow]")
        else:
            for name, info in agent_status.items():
                status_icon = "🟢 Running" if info.get("running") else "🔴 Stopped"
                memory = (
                    f"{info.get('memory', 0) // 1024 // 1024} MB"
                    if info.get("memory")
                    else "N/A"
                )

                # Calculate uptime
                start_time = info.get("start_time")
                if start_time:
                    import time

                    uptime = time.time() - start_time
                    uptime_str = f"{int(uptime // 60)}m {int(uptime % 60)}s"
                else:
                    uptime_str = "N/A"

                agent_table.add_row(name, status_icon, memory, uptime_str)

        console.print(agent_table)

        # Task summary
        console.print("\n[bold]Task Summary[/bold]")

        task_table = Table()
        task_table.add_column("Agent", style="cyan")
        task_table.add_column("Pending Tasks", style="yellow")
        task_table.add_column("Next Task", style="dim")

        for agent_type in [AgentType.SUPERVISOR, AgentType.CODER, AgentType.ADVERSARY]:
            pending_tasks = await runner.get_pending_tasks(agent_type)
            task_count = len(pending_tasks)

            next_task = "None"
            if pending_tasks:
                next_task = pending_tasks[0]["description"][:40] + "..."

            task_table.add_row(agent_type.value.title(), str(task_count), next_task)

        console.print(task_table)

        # Resource usage
        if agent_status:
            console.print("\n[bold]Resource Usage[/bold]")
            total_memory = sum(info.get("memory", 0) for info in agent_status.values())
            console.print(
                f"Total Memory: [cyan]{total_memory // 1024 // 1024} MB[/cyan]"
            )
            console.print(f"Active Processes: [cyan]{len(agent_status)}[/cyan]")

    _run_async(_show_status())


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
    """Run the command line interface."""
    app()
