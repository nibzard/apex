"""Simple CLI for APEX v2.0 - Orchestrator-Worker Architecture."""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from apex.core.memory import MemoryPatterns
from apex.supervisor.engine import SupervisorEngine

app = typer.Typer(
    name="apex",
    help="APEX v2.0 - Simple Orchestrator-Worker Architecture for AI Development",
    no_args_is_help=True,
)

console = Console()


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


async def _get_memory_patterns() -> MemoryPatterns:
    """Initialize memory patterns for the current project."""
    project_dir = Path.cwd()
    memory_dir = project_dir / ".apex"
    memory_dir.mkdir(exist_ok=True)

    lmdb_path = memory_dir / "memory.db"
    return MemoryPatterns(str(lmdb_path))


@app.command()
def start(
    goal: str = typer.Argument(..., help="High-level goal to achieve"),
    project_id: Optional[str] = typer.Option(
        None, help="Project ID (auto-generated if not provided)"
    ),
):
    """Start APEX orchestration for a goal."""

    async def _start_orchestration():
        # Initialize memory
        memory = await _get_memory_patterns()

        # Create supervisor engine
        engine = SupervisorEngine(memory)

        # Generate project ID if not provided
        if project_id is None:
            pid = f"project-{uuid.uuid4().hex[:8]}"
        else:
            pid = project_id

        console.print("[bold blue]Starting APEX Orchestration[/bold blue]")
        console.print(f"Project ID: [cyan]{pid}[/cyan]")
        console.print(f"Goal: [green]{goal}[/green]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize session
            init_task = progress.add_task("Initializing session...", total=None)
            session_id = await engine.initialize_session(pid, goal)
            progress.update(init_task, description="Session initialized!")

            # Run orchestration cycles
            orchestration_task = progress.add_task(
                "Running orchestration...", total=None
            )

            cycle_count = 0
            max_cycles = 20  # Safety limit

            while cycle_count < max_cycles:
                progress.update(
                    orchestration_task,
                    description=f"Orchestration cycle {cycle_count + 1}...",
                )

                success = await engine.execute_orchestration_cycle()

                if not success:
                    progress.update(
                        orchestration_task, description="Orchestration stopped"
                    )
                    break

                # Check if goal is achieved
                if engine.state.current_stage.value == "idle":
                    progress.update(orchestration_task, description="Goal achieved!")
                    break

                cycle_count += 1

                # Brief pause between cycles
                await asyncio.sleep(2)

            progress.stop()

        # Show final status
        if engine.state:
            console.print("\n[bold]Final Status:[/bold]")
            console.print(f"Session ID: [cyan]{session_id}[/cyan]")
            console.print(
                f"Completed Tasks: [green]{len(engine.state.completed_tasks)}[/green]"
            )
            console.print(f"Failed Tasks: [red]{len(engine.state.failed_tasks)}[/red]")
            console.print(f"Cycles Completed: [blue]{cycle_count}[/blue]")

            if engine.state.completed_tasks:
                console.print("\n[bold]Completed Tasks:[/bold]")
                for task_id in engine.state.completed_tasks:
                    console.print(f"  • [green]{task_id}[/green]")

            if engine.state.failed_tasks:
                console.print("\n[bold]Failed Tasks:[/bold]")
                for task_id in engine.state.failed_tasks:
                    console.print(f"  • [red]{task_id}[/red]")

        await memory.close()

    _run_async(_start_orchestration())


@app.command()
def status(
    project_id: Optional[str] = typer.Option(None, help="Project ID to check"),
):
    """Show current orchestration status."""

    async def _show_status():
        memory = await _get_memory_patterns()

        if project_id:
            pid = project_id
        else:
            # Try to find the most recent project
            projects_pattern = "/projects/*/supervisor/sessions/*"
            try:
                keys = await memory.mcp.list_keys("/projects/")
                if not keys:
                    console.print("[yellow]No projects found[/yellow]")
                    return

                # Get the first project for simplicity
                pid = keys[0].split("/")[2] if len(keys[0].split("/")) > 2 else None
                if not pid:
                    console.print("[yellow]No valid projects found[/yellow]")
                    return
            except Exception as e:
                console.print(f"[red]Error finding projects: {e}[/red]")
                return

        console.print(f"[bold blue]Project Status: [cyan]{pid}[/cyan][/bold blue]")

        try:
            # Get task graph
            graph_key = f"/projects/{pid}/supervisor/task_graph"
            graph_data = await memory.mcp.read(graph_key)

            if graph_data:
                graph = json.loads(graph_data)
                console.print(f"Goal: [green]{graph.get('goal', 'Unknown')}[/green]")
                console.print(f"Tasks: [blue]{len(graph.get('tasks', []))}[/blue]")

                # Show task breakdown
                for i, task in enumerate(graph.get("tasks", [])[:5], 1):
                    role = task.get("role", "unknown")
                    desc = task.get("description", "No description")[:50] + "..."
                    console.print(f"  {i}. [{role.lower()}]{desc}[/{role.lower()}]")

                if len(graph.get("tasks", [])) > 5:
                    console.print(f"  ... and {len(graph.get('tasks', [])) - 5} more")
            else:
                console.print("[yellow]No task graph found for project[/yellow]")

        except Exception as e:
            console.print(f"[red]Error reading project status: {e}[/red]")

        await memory.close()

    _run_async(_show_status())


@app.command()
def memory(
    key: Optional[str] = typer.Argument(None, help="Memory key to read"),
    list_keys: bool = typer.Option(False, "--list", "-l", help="List all keys"),
):
    """Access project memory."""

    async def _access_memory():
        memory = await _get_memory_patterns()

        if list_keys:
            console.print("[bold blue]Memory Keys:[/bold blue]")
            try:
                keys = await memory.mcp.list_keys("")
                if not keys:
                    console.print("[yellow]No keys found[/yellow]")
                else:
                    for key in sorted(keys)[:20]:  # Show first 20
                        console.print(f"  [cyan]{key}[/cyan]")
                    if len(keys) > 20:
                        console.print(f"  [dim]... and {len(keys) - 20} more[/dim]")
            except Exception as e:
                console.print(f"[red]Error listing keys: {e}[/red]")

        elif key:
            console.print(f"[bold blue]Memory Key: [cyan]{key}[/cyan][/bold blue]")
            try:
                value = await memory.mcp.read(key)
                if value:
                    # Try to format as JSON
                    try:
                        data = json.loads(value)
                        formatted = json.dumps(data, indent=2)
                        console.print(f"[green]{formatted}[/green]")
                    except json.JSONDecodeError:
                        console.print(f"[yellow]{value}[/yellow]")
                else:
                    console.print("[red]Key not found[/red]")
            except Exception as e:
                console.print(f"[red]Error reading key: {e}[/red]")

        else:
            console.print(
                "[yellow]Use --list to see all keys or provide a key to read[/yellow]"
            )

        await memory.close()

    _run_async(_access_memory())


@app.command()
def version():
    """Show APEX version."""
    console.print("[bold blue]APEX v2.0 - Orchestrator-Worker Architecture[/bold blue]")
    console.print("[dim]Simple AI development orchestration[/dim]")


def main():
    """Run the simplified CLI."""
    app()


if __name__ == "__main__":
    main()
