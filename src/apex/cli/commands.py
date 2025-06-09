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
from apex.core.claude_integration import setup_project_mcp
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

    # Set up MCP configuration for Claude Code integration
    try:
        setup_project_mcp(project_path, config)
        console.print("[green]✓ Configured Claude Code MCP integration[/green]")
    except Exception as e:
        console.print(f"[yellow]⚠ Failed to set up MCP configuration: {e}[/yellow]")

    console.print(
        f"\n[bold green]✓ Project '{project_name}' created successfully![/bold green]"
    )
    console.print("[dim]Next steps:[/dim]")
    console.print(f"[dim]  cd {project_name}[/dim]")
    console.print('[dim]  apex start --task "Your initial task here"[/dim]')
    console.print("[dim]  claude  # Start Claude Code with APEX integration[/dim]")


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

    async def _pause_agents():
        runner = await _get_or_create_runner()
        if not runner:
            return

        console.print("[yellow]Pausing agents...[/yellow]")

        # Get all running processes
        processes = runner.get_agent_status()
        paused_count = 0

        for name, info in processes.items():
            if info.get("running"):
                # Send SIGSTOP to pause the process
                claude_process = runner.process_manager.get_claude_process(name)
                if claude_process and claude_process.process:
                    try:
                        import os
                        import signal

                        os.kill(claude_process.process.pid, signal.SIGSTOP)
                        console.print(f"[green]✓ Paused {name}[/green]")
                        paused_count += 1
                    except (OSError, AttributeError) as e:
                        console.print(f"[red]✗ Failed to pause {name}: {e}[/red]")

        if paused_count > 0:
            console.print(f"[green]✓ Paused {paused_count} agent(s)[/green]")
            console.print("[dim]Use 'apex resume' to continue[/dim]")
        else:
            console.print("[yellow]No running agents to pause[/yellow]")

    _run_async(_pause_agents())


@app.command()
def resume() -> None:
    """Resume paused agents."""

    async def _resume_agents():
        runner = await _get_or_create_runner()
        if not runner:
            return

        console.print("[yellow]Resuming agents...[/yellow]")

        # Get all processes
        processes = runner.get_agent_status()
        resumed_count = 0

        for name, _info in processes.items():
            # Try to resume paused processes
            claude_process = runner.process_manager.get_claude_process(name)
            if claude_process and claude_process.process:
                try:
                    import os
                    import signal

                    # Send SIGCONT to resume the process
                    os.kill(claude_process.process.pid, signal.SIGCONT)
                    console.print(f"[green]✓ Resumed {name}[/green]")
                    resumed_count += 1
                except (OSError, AttributeError) as e:
                    console.print(f"[red]✗ Failed to resume {name}: {e}[/red]")

        if resumed_count > 0:
            console.print(f"[green]✓ Resumed {resumed_count} agent(s)[/green]")
        else:
            console.print("[yellow]No agents to resume[/yellow]")

    _run_async(_resume_agents())


@app.command()
def stop() -> None:
    """Stop all running agents."""

    async def _stop_agents():
        global _current_runner
        runner = await _get_or_create_runner()
        if not runner:
            return

        console.print("[yellow]Stopping agents...[/yellow]")

        # Get all running processes before stopping
        processes = runner.get_agent_status()
        running_processes = [
            name for name, info in processes.items() if info.get("running")
        ]

        if not running_processes:
            console.print("[yellow]No running agents to stop[/yellow]")
            return

        # Stop all agents
        await runner.stop_all_agents()

        # Clear the global runner reference
        _current_runner = None

        console.print(f"[green]✓ Stopped {len(running_processes)} agent(s)[/green]")
        for name in running_processes:
            console.print(f"  [dim]• {name}[/dim]")

    _run_async(_stop_agents())


@app.command()
def tui(
    layout: Optional[str] = LAYOUT_OPTION,
    theme: Optional[str] = THEME_OPTION,
):
    """Launch TUI interface."""

    async def _launch_tui():
        from apex.tui import DashboardApp

        # Get or create runner for TUI
        runner = await _get_or_create_runner()
        lmdb_client = runner.lmdb if runner else None

        # Create and run TUI app
        app = DashboardApp(agent_runner=runner, lmdb_client=lmdb_client)
        await app.run_async()

    _run_async(_launch_tui())


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

    async def _restart_agent():
        runner = await _get_or_create_runner()
        if not runner:
            return

        console.print(f"[yellow]Restarting {agent_name}...[/yellow]")

        # Check if agent is running
        processes = runner.get_agent_status()
        if agent_name not in processes:
            console.print(f"[red]✗ Agent '{agent_name}' not found[/red]")

            # Show available agents
            if processes:
                console.print("[dim]Available agents:[/dim]")
                for name in processes.keys():
                    console.print(f"  [dim]• {name}[/dim]")
            return

        try:
            # Stop the specific agent
            await runner.stop_agent(agent_name)
            console.print(f"[green]✓ Stopped {agent_name}[/green]")

            # Get the agent type from process info
            agent_info = processes[agent_name]
            agent_type_str = agent_info.get("agent_type")

            if agent_type_str:
                from apex.types import AgentType

                try:
                    agent_type = AgentType(agent_type_str)
                    # Restart the agent
                    new_name = await runner.start_agent(agent_type)
                    console.print(f"[green]✓ Restarted as {new_name}[/green]")
                except ValueError:
                    console.print(f"[red]✗ Unknown agent type: {agent_type_str}[/red]")
            else:
                console.print("[red]✗ Could not determine agent type for restart[/red]")

        except Exception as e:
            console.print(f"[red]✗ Failed to restart {agent_name}: {e}[/red]")

    _run_async(_restart_agent())


@memory_app.command("show")
def memory_show(key: Optional[str] = None) -> None:
    """Display memory contents."""

    async def _show_memory():
        runner = await _get_or_create_runner()
        if not runner:
            return

        console.print("[bold blue]APEX Memory[/bold blue]")

        try:
            if key is None:
                # Show memory root - list all keys
                console.print("\n[bold]Memory Keys:[/bold]")

                # List all keys in LMDB
                keys = await runner.lmdb.list_keys("")

                if not keys:
                    console.print("[dim]No data in memory[/dim]")
                    return

                # Group keys by top-level namespace
                namespaces = {}
                for k in keys:
                    parts = k.split("/")
                    if len(parts) > 1:
                        namespace = parts[1]  # Skip empty first part from leading /
                        if namespace not in namespaces:
                            namespaces[namespace] = []
                        namespaces[namespace].append(k)
                    else:
                        # Root level key
                        if "root" not in namespaces:
                            namespaces["root"] = []
                        namespaces["root"].append(k)

                # Display organized by namespace
                for namespace, namespace_keys in sorted(namespaces.items()):
                    console.print(
                        f"\n[cyan]{namespace}/[/cyan] ({len(namespace_keys)} keys)"
                    )
                    for k in sorted(namespace_keys)[:10]:  # Show first 10
                        console.print(f"  [dim]{k}[/dim]")
                    if len(namespace_keys) > 10:
                        console.print(
                            f"  [dim]... and {len(namespace_keys) - 10} more[/dim]"
                        )

                console.print(f"\n[dim]Total keys: {len(keys)}[/dim]")
                console.print(
                    "[dim]Use 'apex memory show <key>' to view specific content[/dim]"
                )

            else:
                # Show specific key
                console.print(f"\n[bold]Key: [cyan]{key}[/cyan][/bold]")

                value = await runner.lmdb.read(key)
                if value is None:
                    console.print("[red]Key not found[/red]")

                    # Suggest similar keys
                    all_keys = await runner.lmdb.list_keys("")
                    similar = [k for k in all_keys if key.lower() in k.lower()]
                    if similar:
                        console.print("\n[dim]Similar keys:[/dim]")
                        for k in similar[:5]:
                            console.print(f"  [dim]{k}[/dim]")
                else:
                    # Try to format as JSON for better display
                    try:
                        import json

                        data = json.loads(
                            value.decode() if isinstance(value, bytes) else value
                        )
                        formatted = json.dumps(data, indent=2)
                        console.print(f"[green]{formatted}[/green]")
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Display as raw text
                        display_value = (
                            value.decode() if isinstance(value, bytes) else str(value)
                        )
                        console.print(f"[yellow]{display_value}[/yellow]")

        except Exception as e:
            console.print(f"[red]Error accessing memory: {e}[/red]")

    _run_async(_show_memory())


@memory_app.command("query")
def memory_query(
    pattern: str = typer.Argument(..., help="Search pattern (supports glob and regex)"),
    regex: bool = typer.Option(
        False, "--regex", "-r", help="Use regex instead of glob"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum results to show"),
    content: bool = typer.Option(
        False, "--content", "-c", help="Search in content not just keys"
    ),
) -> None:
    """Query memory with pattern matching."""

    async def _query_memory():
        runner = await _get_or_create_runner()
        if not runner:
            return

        console.print(
            f"[bold blue]Querying memory with pattern: [cyan]{pattern}[/cyan][/bold blue]"
        )

        try:
            import fnmatch
            import re

            # Get all keys
            all_keys = await runner.lmdb.list_keys("")

            # Filter keys based on pattern

            if regex:
                try:
                    pattern_re = re.compile(pattern, re.IGNORECASE)
                    matching_keys = [k for k in all_keys if pattern_re.search(k)]
                except re.error as e:
                    console.print(f"[red]Invalid regex pattern: {e}[/red]")
                    return
            else:
                # Use glob pattern matching
                matching_keys = [
                    k for k in all_keys if fnmatch.fnmatch(k.lower(), pattern.lower())
                ]

            if content:
                # Search in content as well
                console.print("[dim]Searching in content...[/dim]")
                for key in all_keys:
                    if key in matching_keys:
                        continue  # Already matched by key

                    try:
                        value = await runner.lmdb.read(key)
                        if value:
                            content_str = (
                                value.decode()
                                if isinstance(value, bytes)
                                else str(value)
                            )
                            if regex:
                                if pattern_re.search(content_str):
                                    matching_keys.append(key)
                            else:
                                if fnmatch.fnmatch(
                                    content_str.lower(), pattern.lower()
                                ):
                                    matching_keys.append(key)
                    except Exception:
                        continue

            # Sort and limit results
            matching_keys = sorted(matching_keys)[:limit]

            if not matching_keys:
                console.print("[yellow]No matches found[/yellow]")
                return

            # Display results
            console.print(f"\n[bold]Found {len(matching_keys)} matches:[/bold]")

            for key in matching_keys:
                try:
                    value = await runner.lmdb.read(key)
                    if value:
                        # Try to format as JSON preview
                        try:
                            data = json.loads(
                                value.decode() if isinstance(value, bytes) else value
                            )
                            if isinstance(data, dict):
                                preview = f"{{...}} ({len(data)} keys)"
                            elif isinstance(data, list):
                                preview = f"[...] ({len(data)} items)"
                            else:
                                preview = (
                                    str(data)[:50] + "..."
                                    if len(str(data)) > 50
                                    else str(data)
                                )
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            content_str = (
                                value.decode()
                                if isinstance(value, bytes)
                                else str(value)
                            )
                            preview = (
                                content_str[:50] + "..."
                                if len(content_str) > 50
                                else content_str
                            )

                        console.print(
                            f"  [cyan]{key}[/cyan] [dim]→[/dim] [green]{preview}[/green]"
                        )
                    else:
                        console.print(
                            f"  [cyan]{key}[/cyan] [dim]→[/dim] [red](empty)[/red]"
                        )
                except Exception as e:
                    console.print(
                        f"  [cyan]{key}[/cyan] [dim]→[/dim] [red]Error: {e}[/red]"
                    )

            if len(matching_keys) == limit:
                console.print(
                    f"\n[dim]Showing first {limit} results. Use --limit to see more.[/dim]"
                )

        except Exception as e:
            console.print(f"[red]Error querying memory: {e}[/red]")

    _run_async(_query_memory())


@memory_app.command("watch")
def memory_watch(
    pattern: str = typer.Argument("*", help="Watch pattern (glob)"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Watch timeout in seconds"),
    interval: float = typer.Option(
        1.0, "--interval", "-i", help="Polling interval in seconds"
    ),
) -> None:
    """Watch memory changes in real-time."""

    async def _watch_memory():
        runner = await _get_or_create_runner()
        if not runner:
            return

        console.print(
            f"[bold blue]Watching memory pattern: [cyan]{pattern}[/cyan][/bold blue]"
        )
        console.print("[dim]Press Ctrl+C to stop watching[/dim]\n")

        try:
            import fnmatch
            import time

            # Store initial state
            initial_keys = await runner.lmdb.list_keys("")
            initial_state = {}

            # Filter keys by pattern
            matching_keys = [
                k for k in initial_keys if fnmatch.fnmatch(k.lower(), pattern.lower())
            ]

            # Get initial values for matching keys
            for key in matching_keys:
                try:
                    value = await runner.lmdb.read(key)
                    initial_state[key] = value
                except Exception:
                    initial_state[key] = None

            console.print(
                f"[dim]Monitoring {len(matching_keys)} keys matching pattern...[/dim]\n"
            )

            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    # Check for changes
                    current_keys = await runner.lmdb.list_keys("")
                    current_matching = [
                        k
                        for k in current_keys
                        if fnmatch.fnmatch(k.lower(), pattern.lower())
                    ]

                    # Check for new keys
                    new_keys = set(current_matching) - set(initial_state.keys())
                    if new_keys:
                        for key in sorted(new_keys):
                            try:
                                value = await runner.lmdb.read(key)
                                console.print(
                                    f"[green]+ CREATED[/green] [cyan]{key}[/cyan]"
                                )
                                initial_state[key] = value
                            except Exception:
                                initial_state[key] = None

                    # Check for deleted keys
                    deleted_keys = set(initial_state.keys()) - set(current_matching)
                    if deleted_keys:
                        for key in sorted(deleted_keys):
                            console.print(f"[red]- DELETED[/red] [cyan]{key}[/cyan]")
                            del initial_state[key]

                    # Check for modified keys
                    for key in current_matching:
                        if key in initial_state:
                            try:
                                current_value = await runner.lmdb.read(key)
                                if current_value != initial_state[key]:
                                    console.print(
                                        f"[yellow]~ MODIFIED[/yellow] [cyan]{key}[/cyan]"
                                    )
                                    initial_state[key] = current_value
                            except Exception:
                                pass

                    await asyncio.sleep(interval)

                except KeyboardInterrupt:
                    console.print("\n[dim]Stopping watch...[/dim]")
                    break

            if time.time() - start_time >= timeout:
                console.print(f"\n[dim]Watch timeout ({timeout}s) reached[/dim]")

        except Exception as e:
            console.print(f"[red]Error watching memory: {e}[/red]")

    _run_async(_watch_memory())


@agent_app.command("logs")
def agent_logs(
    agent_name: str = typer.Argument(
        ..., help="Agent name (supervisor, coder, adversary)"
    ),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    level: Optional[str] = typer.Option(
        None, "--level", "-l", help="Filter by log level"
    ),
    grep: Optional[str] = typer.Option(None, "--grep", "-g", help="Filter by pattern"),
) -> None:
    """Stream agent logs with filtering."""

    async def _show_logs():
        runner = await _get_or_create_runner()
        if not runner:
            return

        # Validate agent name
        valid_agents = ["supervisor", "coder", "adversary"]
        if agent_name.lower() not in valid_agents:
            console.print(
                f"[red]Invalid agent name. Valid options: {', '.join(valid_agents)}[/red]"
            )
            return

        console.print(
            f"[bold blue]Logs for agent: [cyan]{agent_name}[/cyan][/bold blue]"
        )

        if follow:
            console.print("[dim]Following logs... Press Ctrl+C to stop[/dim]\n")
        else:
            console.print(f"[dim]Showing last {lines} lines[/dim]\n")

        try:
            import fnmatch
            import re

            # Define log key patterns for different sources
            log_patterns = [
                f"/agents/{agent_name}/messages/*",
                "/sessions/*/events/*",
                "/tools/calls/*",
            ]

            # Get all log entries
            all_logs = []

            for pattern in log_patterns:
                keys = await runner.lmdb.list_keys("")
                matching_keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]

                for key in matching_keys:
                    try:
                        value = await runner.lmdb.read(key)
                        if value:
                            # Try to parse as JSON
                            try:
                                data = json.loads(
                                    value.decode()
                                    if isinstance(value, bytes)
                                    else value
                                )
                                if isinstance(data, dict):
                                    # Extract timestamp and content
                                    timestamp = data.get(
                                        "timestamp", data.get("created_at", "unknown")
                                    )
                                    content = data.get(
                                        "content", data.get("message", str(data))
                                    )
                                    log_level = data.get("level", "info")

                                    all_logs.append(
                                        {
                                            "timestamp": timestamp,
                                            "level": log_level,
                                            "content": content,
                                            "key": key,
                                        }
                                    )
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                # Treat as plain text log
                                content = (
                                    value.decode()
                                    if isinstance(value, bytes)
                                    else str(value)
                                )
                                all_logs.append(
                                    {
                                        "timestamp": "unknown",
                                        "level": "info",
                                        "content": content,
                                        "key": key,
                                    }
                                )
                    except Exception:
                        continue

            # Sort by timestamp
            all_logs.sort(key=lambda x: x["timestamp"])

            # Apply filters
            filtered_logs = all_logs

            if level:
                filtered_logs = [
                    log
                    for log in filtered_logs
                    if log["level"].lower() == level.lower()
                ]

            if grep:
                try:
                    pattern_re = re.compile(grep, re.IGNORECASE)
                    filtered_logs = [
                        log
                        for log in filtered_logs
                        if pattern_re.search(str(log["content"]))
                    ]
                except re.error:
                    # Fallback to simple string matching
                    filtered_logs = [
                        log
                        for log in filtered_logs
                        if grep.lower() in str(log["content"]).lower()
                    ]

            # Show logs
            if not follow:
                # Show last N lines
                recent_logs = filtered_logs[-lines:] if filtered_logs else []

                if not recent_logs:
                    console.print("[yellow]No logs found for this agent[/yellow]")
                    return

                for log in recent_logs:
                    _format_log_entry(log)
            else:
                # Follow mode - show existing logs then watch for new ones
                if filtered_logs:
                    recent_logs = filtered_logs[-lines:]
                    for log in recent_logs:
                        _format_log_entry(log)

                # Start watching for new logs
                console.print("[dim]Waiting for new logs...[/dim]")

                # This is a simplified follow mode - in a real implementation,
                # we'd use the lmdb_watch tool or set up proper streaming
                seen_keys = set(log["key"] for log in filtered_logs)

                try:
                    while True:
                        await asyncio.sleep(1)  # Poll every second

                        # Check for new log entries
                        for pattern in log_patterns:
                            keys = await runner.lmdb.list_keys("")
                            matching_keys = [
                                k for k in keys if fnmatch.fnmatch(k, pattern)
                            ]

                            for key in matching_keys:
                                if key not in seen_keys:
                                    try:
                                        value = await runner.lmdb.read(key)
                                        if value:
                                            try:
                                                data = json.loads(
                                                    value.decode()
                                                    if isinstance(value, bytes)
                                                    else value
                                                )
                                                if isinstance(data, dict):
                                                    timestamp = data.get(
                                                        "timestamp",
                                                        data.get(
                                                            "created_at", "unknown"
                                                        ),
                                                    )
                                                    content = data.get(
                                                        "content",
                                                        data.get("message", str(data)),
                                                    )
                                                    log_level = data.get(
                                                        "level", "info"
                                                    )

                                                    log_entry = {
                                                        "timestamp": timestamp,
                                                        "level": log_level,
                                                        "content": content,
                                                        "key": key,
                                                    }

                                                    # Apply filters
                                                    if (
                                                        level
                                                        and log_level.lower()
                                                        != level.lower()
                                                    ):
                                                        continue
                                                    if grep:
                                                        try:
                                                            pattern_re = re.compile(
                                                                grep, re.IGNORECASE
                                                            )
                                                            if not pattern_re.search(
                                                                str(content)
                                                            ):
                                                                continue
                                                        except re.error:
                                                            if (
                                                                grep.lower()
                                                                not in str(
                                                                    content
                                                                ).lower()
                                                            ):
                                                                continue

                                                    _format_log_entry(log_entry)
                                                    seen_keys.add(key)
                                            except (
                                                json.JSONDecodeError,
                                                UnicodeDecodeError,
                                            ):
                                                pass
                                    except Exception:
                                        pass

                except KeyboardInterrupt:
                    console.print("\n[dim]Stopping log follow...[/dim]")

        except Exception as e:
            console.print(f"[red]Error reading logs: {e}[/red]")

    def _format_log_entry(log_entry):
        """Format a single log entry for display."""
        timestamp = log_entry["timestamp"]
        level = log_entry["level"].upper()
        content = log_entry["content"]

        # Color code by level
        level_colors = {
            "ERROR": "red",
            "WARN": "yellow",
            "WARNING": "yellow",
            "INFO": "blue",
            "DEBUG": "dim",
        }

        level_color = level_colors.get(level, "white")

        # Format timestamp
        if timestamp != "unknown":
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
        else:
            time_str = "??:??:??"

        console.print(
            f"[dim]{time_str}[/dim] [{level_color}]{level:5}[/{level_color}] {content}"
        )

    _run_async(_show_logs())


def main():
    """Run the command line interface."""
    app()
