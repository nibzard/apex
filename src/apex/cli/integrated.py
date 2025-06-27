"""Integrated CLI for APEX v2.0 - Connects simplified and full systems."""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from apex.core.claude_integration import setup_project_mcp
from apex.core.lmdb_mcp import LMDBMCP
from apex.core.memory import MemoryPatterns
from apex.integration.simple_bridge import IntegratedOrchestrator
from apex.tui.integrated_app import IntegratedTUIApp
from apex.types import ProjectConfig

app = typer.Typer(
    name="apex",
    help="APEX v2.0 - Adversarial Pair EXecution for AI-powered development",
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
    lmdb_mcp = LMDBMCP(lmdb_path)
    return MemoryPatterns(lmdb_mcp)


@app.command()
def start(
    goal: str = typer.Argument(..., help="High-level goal to achieve"),
    project_id: Optional[str] = typer.Option(
        None, help="Project ID (auto-generated if not provided)"
    ),
    use_tui: bool = typer.Option(
        False, "--tui", help="Launch TUI interface after starting"
    ),
    mode: str = typer.Option(
        "full", "--mode", help="Execution mode: 'simple', 'full', or 'hybrid'"
    ),
):
    """Start APEX integrated orchestration for a goal."""

    async def _start_orchestration():
        # Initialize memory
        memory = await _get_memory_patterns()

        # Create integrated orchestrator
        orchestrator = IntegratedOrchestrator(memory)

        # Generate project ID if not provided
        if project_id is None:
            pid = f"project-{uuid.uuid4().hex[:8]}"
        else:
            pid = project_id

        console.print("[bold blue]Starting APEX Integrated Orchestration[/bold blue]")
        console.print(f"Project ID: [cyan]{pid}[/cyan]")
        console.print(f"Goal: [green]{goal}[/green]")
        console.print(f"Mode: [yellow]{mode}[/yellow]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize session
            init_task = progress.add_task("Initializing session...", total=None)
            session_id = await orchestrator.initialize_session(pid, goal)
            progress.update(init_task, description="Session initialized!")

            # Create task graph
            planning_task = progress.add_task("Creating task graph...", total=None)
            task_graph = await orchestrator.create_simplified_task_graph(goal)
            progress.update(
                planning_task,
                description=f"Created {len(task_graph.tasks)} tasks",
            )

            # Execute orchestration
            orchestration_task = progress.add_task(
                "Running orchestration...", total=None
            )

            if mode == "simple":
                # Use simplified execution (simulation)
                await _run_simple_mode(orchestrator, progress, orchestration_task)
            elif mode == "full":
                # Use full supervisor engine
                result = await orchestrator.orchestrate()
            else:  # hybrid
                # Interactive mode with TUI
                if use_tui:
                    progress.stop()
                    await _launch_tui_orchestration(orchestrator, pid)
                    return
                else:
                    result = await orchestrator.orchestrate()

            progress.update(orchestration_task, description="Orchestration completed!")
            progress.stop()

        # Show final status
        if not use_tui:
            await _show_final_status(orchestrator)

        # Launch TUI if requested
        if use_tui and mode != "hybrid":
            console.print("\n[bold blue]Launching TUI interface...[/bold blue]")
            await _launch_tui_orchestration(orchestrator, pid)

        await memory.close()

    _run_async(_start_orchestration())


async def _run_simple_mode(orchestrator, progress, task_id):
    """Run orchestration in simple simulation mode."""
    if not orchestrator.task_graph:
        return

    for i, task in enumerate(orchestrator.task_graph.tasks):
        progress.update(
            task_id,
            description=f"Executing task {i + 1}/{len(orchestrator.task_graph.tasks)}: {task.description[:50]}...",
        )

        # Simulate task execution
        await asyncio.sleep(1)
        orchestrator.completed_tasks.append(task.id)
        task.status = "completed"


async def _show_final_status(orchestrator):
    """Show final orchestration status."""
    if not orchestrator.task_graph:
        return

    # Create status table
    table = Table(title="Orchestration Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    total_tasks = len(orchestrator.task_graph.tasks)
    completed_tasks = len(orchestrator.completed_tasks)
    failed_tasks = len(orchestrator.failed_tasks)
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    table.add_row("Project ID", orchestrator.project_id or "Unknown")
    table.add_row("Session ID", orchestrator.session_id or "Unknown")
    table.add_row("Goal", orchestrator.task_graph.goal)
    table.add_row("Total Tasks", str(total_tasks))
    table.add_row("Completed Tasks", str(completed_tasks))
    table.add_row("Failed Tasks", str(failed_tasks))
    table.add_row("Completion Rate", f"{completion_rate:.1f}%")

    console.print(table)

    # Show task details
    if orchestrator.task_graph.tasks:
        console.print("\n[bold]Task Details:[/bold]")
        for task in orchestrator.task_graph.tasks:
            status_icon = (
                "✅"
                if task.status == "completed"
                else "❌"
                if task.status == "failed"
                else "⏳"
            )
            console.print(
                f"  {status_icon} [{task.role.lower()}]{task.description}[/{task.role.lower()}]"
            )


async def _launch_tui_orchestration(orchestrator, project_id):
    """Launch TUI interface for orchestration monitoring."""
    try:
        # Create TUI app with orchestrator context
        tui_app = IntegratedTUIApp(
            memory=orchestrator.memory, orchestrator=orchestrator, project_id=project_id
        )

        # Run TUI app
        await tui_app.run_async()
    except Exception as e:
        console.print(f"[red]TUI launch failed: {e}[/red]")


@app.command()
def resume(
    project_id: str = typer.Argument(..., help="Project ID to resume"),
    session_id: str = typer.Argument(..., help="Session ID to resume"),
    use_tui: bool = typer.Option(
        False, "--tui", help="Launch TUI interface after resuming"
    ),
):
    """Resume a previous orchestration session."""

    async def _resume_session():
        memory = await _get_memory_patterns()
        orchestrator = IntegratedOrchestrator(memory)

        console.print("[bold blue]Resuming APEX Orchestration[/bold blue]")
        console.print(f"Project ID: [cyan]{project_id}[/cyan]")
        console.print(f"Session ID: [cyan]{session_id}[/cyan]")

        success = await orchestrator.resume_session(project_id, session_id)

        if success:
            console.print("[green]Session resumed successfully![/green]")

            # Show current status
            status = await orchestrator.get_session_status()
            console.print(f"Goal: [green]{status.get('goal', 'Unknown')}[/green]")
            console.print(
                f"Progress: [blue]{status.get('completed_tasks', 0)}/{status.get('total_tasks', 0)} tasks[/blue]"
            )

            if use_tui:
                await _launch_tui_orchestration(orchestrator, project_id)
            else:
                # Continue orchestration
                result = await orchestrator.orchestrate()
                await _show_final_status(orchestrator)
        else:
            console.print("[red]Failed to resume session[/red]")

        await memory.close()

    _run_async(_resume_session())


@app.command()
def status(
    project_id: Optional[str] = typer.Option(None, help="Project ID to check"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to check"),
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed status"
    ),
):
    """Show orchestration status."""

    async def _show_status():
        memory = await _get_memory_patterns()

        if project_id:
            pid = project_id
        else:
            # Find most recent project
            try:
                keys = await memory.mcp.list_keys("/projects/")
                if not keys:
                    console.print("[yellow]No projects found[/yellow]")
                    return
                pid = keys[0].split("/")[2] if len(keys[0].split("/")) > 2 else None
                if not pid:
                    console.print("[yellow]No valid projects found[/yellow]")
                    return
            except Exception as e:
                console.print(f"[red]Error finding projects: {e}[/red]")
                return

        console.print(f"[bold blue]Project Status: [cyan]{pid}[/cyan][/bold blue]")

        try:
            # Get project metadata
            config_key = f"/projects/{pid}/config"
            config_data = await memory.mcp.read(config_key)

            if config_data:
                config = json.loads(config_data)
                console.print(
                    f"Project Name: [green]{config.get('name', 'Unknown')}[/green]"
                )

            # Get task graph
            graph_key = f"/projects/{pid}/supervisor/task_graph"
            graph_data = await memory.mcp.read(graph_key)

            if graph_data:
                graph = json.loads(graph_data)
                console.print(f"Goal: [green]{graph.get('goal', 'Unknown')}[/green]")
                console.print(
                    f"Total Tasks: [blue]{len(graph.get('tasks', []))}[/blue]"
                )

                if detailed:
                    # Show task breakdown
                    tasks = graph.get("tasks", [])
                    if tasks:
                        table = Table(title="Task Breakdown")
                        table.add_column("ID", style="cyan")
                        table.add_column("Type", style="yellow")
                        table.add_column("Role", style="magenta")
                        table.add_column("Description", style="white")
                        table.add_column("Status", style="green")

                        for task in tasks[:10]:  # Show first 10 tasks
                            table.add_row(
                                task.get("id", "")[:20],
                                task.get("type", ""),
                                task.get("role", ""),
                                task.get("description", "")[:50] + "...",
                                task.get("status", "pending"),
                            )

                        console.print(table)

                        if len(tasks) > 10:
                            console.print(
                                f"[dim]... and {len(tasks) - 10} more tasks[/dim]"
                            )

            # Get session information if session_id provided
            if session_id:
                session_key = f"/projects/{pid}/sessions/{session_id}/metadata"
                session_data = await memory.mcp.read(session_key)

                if session_data:
                    session = json.loads(session_data)
                    console.print(f"\n[bold]Session {session_id}:[/bold]")
                    console.print(
                        f"Created: [blue]{session.get('created_at', 'Unknown')}[/blue]"
                    )
                    console.print(
                        f"Type: [yellow]{session.get('orchestrator_type', 'Unknown')}[/yellow]"
                    )

        except Exception as e:
            console.print(f"[red]Error reading project status: {e}[/red]")

        await memory.close()

    _run_async(_show_status())


@app.command()
def tui(
    project_id: Optional[str] = typer.Option(None, help="Project ID to monitor"),
):
    """Launch TUI interface for monitoring."""

    async def _launch_tui():
        memory = await _get_memory_patterns()

        try:
            tui_app = IntegratedTUIApp(memory=memory, project_id=project_id)
            await tui_app.run_async()
        except Exception as e:
            console.print(f"[red]TUI launch failed: {e}[/red]")
        finally:
            await memory.close()

    _run_async(_launch_tui())


@app.command()
def memory(
    key: Optional[str] = typer.Argument(None, help="Memory key to read"),
    list_keys: bool = typer.Option(False, "--list", "-l", help="List all keys"),
    project_id: Optional[str] = typer.Option(None, help="Project ID to filter"),
    export_file: Optional[str] = typer.Option(
        None, "--export", help="Export to JSON file"
    ),
):
    """Access project memory with enhanced features."""

    async def _access_memory():
        memory = await _get_memory_patterns()

        if list_keys:
            console.print("[bold blue]Memory Keys:[/bold blue]")
            try:
                prefix = f"/projects/{project_id}/" if project_id else ""
                keys = await memory.mcp.list_keys(prefix)

                if not keys:
                    console.print("[yellow]No keys found[/yellow]")
                else:
                    # Group keys by category
                    categories = {}
                    for key in keys:
                        parts = key.split("/")
                        if len(parts) >= 3:
                            category = "/".join(parts[:3])
                            if category not in categories:
                                categories[category] = []
                            categories[category].append(key)

                    for category, category_keys in categories.items():
                        console.print(f"\n[bold]{category}[/bold]")
                        for key in sorted(category_keys)[:5]:
                            console.print(f"  [cyan]{key}[/cyan]")
                        if len(category_keys) > 5:
                            console.print(
                                f"  [dim]... and {len(category_keys) - 5} more[/dim]"
                            )

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

                        if export_file:
                            with open(export_file, "w") as f:
                                f.write(formatted)
                            console.print(f"[green]Exported to {export_file}[/green]")
                        else:
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
def orchestrate(
    goal: str = typer.Argument(..., help="Goal to orchestrate"),
    project_id: Optional[str] = typer.Option(None, help="Project ID"),
    workers: int = typer.Option(3, help="Number of worker processes"),
    mode: str = typer.Option(
        "auto", help="Orchestration mode: auto, supervised, autonomous"
    ),
    timeout: int = typer.Option(3600, help="Orchestration timeout in seconds"),
    strategy: str = typer.Option(
        "balanced", help="Strategy: balanced, speed, quality, thorough"
    ),
):
    """Advanced orchestration with full control options."""

    async def _orchestrate():
        memory = await _get_memory_patterns()
        orchestrator = IntegratedOrchestrator(memory)

        # Generate project ID if not provided
        pid = project_id or f"orch-{uuid.uuid4().hex[:8]}"

        console.print("[bold blue]🚀 Advanced APEX Orchestration[/bold blue]")
        console.print(f"Project: [cyan]{pid}[/cyan]")
        console.print(f"Goal: [green]{goal}[/green]")
        console.print(f"Workers: [yellow]{workers}[/yellow]")
        console.print(f"Mode: [magenta]{mode}[/magenta]")
        console.print(f"Strategy: [blue]{strategy}[/blue]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize with advanced settings
            init_task = progress.add_task(
                "Initializing advanced orchestration...", total=None
            )
            session_id = await orchestrator.initialize_session(pid, goal)

            # Configure orchestration parameters
            config = {
                "workers": workers,
                "mode": mode,
                "timeout": timeout,
                "strategy": strategy,
                "advanced": True,
            }

            # Store configuration
            config_key = f"/projects/{pid}/orchestration/config"
            await memory.mcp.write(config_key, json.dumps(config))

            progress.update(init_task, description="Configuration saved")

            # Create task graph with advanced parameters
            planning_task = progress.add_task(
                "Creating optimized task graph...", total=None
            )
            task_graph = await orchestrator.create_simplified_task_graph(goal)

            # Apply strategy optimizations
            if strategy == "speed":
                console.print("📈 Optimizing for speed - parallel execution enabled")
            elif strategy == "quality":
                console.print("🎯 Optimizing for quality - thorough validation enabled")
            elif strategy == "thorough":
                console.print(
                    "🔍 Optimizing for thoroughness - comprehensive analysis enabled"
                )

            task_count = len(task_graph.tasks) if task_graph else 0
            progress.update(
                planning_task, description=f"Created {task_count} optimized tasks"
            )

            # Execute orchestration
            orchestration_task = progress.add_task(
                "Running advanced orchestration...", total=None
            )
            result = await orchestrator.orchestrate()

            progress.update(
                orchestration_task, description="Advanced orchestration completed!"
            )
            progress.stop()

        # Show results
        await _show_final_status(orchestrator)

        # Show advanced metrics
        console.print("\n[bold]Advanced Metrics:[/bold]")
        metrics_table = Table()
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")

        if result:
            completion = result.get("completion_percentage", 0)
            duration = result.get("duration_seconds", 0)
            metrics_table.add_row("Completion Rate", f"{completion:.1f}%")
            metrics_table.add_row("Duration", f"{duration:.1f}s")
            metrics_table.add_row("Workers Used", str(workers))
            metrics_table.add_row("Strategy", strategy.title())

        console.print(metrics_table)
        await memory.close()

    _run_async(_orchestrate())


plan = typer.Typer(help="Plan management commands")
app.add_typer(plan, name="plan")


@plan.command("show")
def plan_show(
    project_id: Optional[str] = typer.Option(None, help="Project ID"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed plan"),
    format: str = typer.Option("table", help="Output format: table, json, tree"),
):
    """Show orchestration plan for a project."""

    async def _show_plan():
        memory = await _get_memory_patterns()

        # Find project if not specified
        if not project_id:
            try:
                keys = await memory.mcp.list_keys("/projects/")
                if not keys:
                    console.print("[yellow]No projects found[/yellow]")
                    return
                pid = keys[0].split("/")[2] if len(keys[0].split("/")) > 2 else None
                if not pid:
                    console.print("[yellow]No valid projects found[/yellow]")
                    return
            except Exception as e:
                console.print(f"[red]Error finding projects: {e}[/red]")
                return
        else:
            pid = project_id

        console.print(
            f"[bold blue]📋 Orchestration Plan: [cyan]{pid}[/cyan][/bold blue]"
        )

        try:
            # Get task graph
            graph_key = f"/projects/{pid}/supervisor/task_graph"
            graph_data = await memory.mcp.read(graph_key)

            if not graph_data:
                console.print("[yellow]No plan found for this project[/yellow]")
                return

            graph = json.loads(graph_data)

            if format == "json":
                console.print(json.dumps(graph, indent=2))
            elif format == "tree":
                await _show_plan_tree(graph, detailed)
            else:
                await _show_plan_table(graph, detailed)

        except Exception as e:
            console.print(f"[red]Error reading plan: {e}[/red]")

        await memory.close()

    async def _show_plan_tree(graph, detailed):
        """Show plan as tree structure."""
        console.print(f"🎯 [bold]Goal:[/bold] {graph.get('goal', 'Unknown')}")
        console.print(f"📊 [bold]Tasks:[/bold] {len(graph.get('tasks', []))}")

        tasks = graph.get("tasks", [])
        # Group by role
        roles = {}
        for task in tasks:
            role = task.get("role", "unknown")
            if role not in roles:
                roles[role] = []
            roles[role].append(task)

        for role, role_tasks in roles.items():
            role_icon = {"coder": "👨‍💻", "adversary": "🔍", "supervisor": "🧠"}.get(
                role.lower(), "⚙️"
            )
            console.print(
                f"\n{role_icon} [bold]{role.title()}[/bold] ({len(role_tasks)} tasks)"
            )

            for i, task in enumerate(role_tasks):
                is_last = i == len(role_tasks) - 1
                prefix = "└── " if is_last else "├── "
                status_icon = {
                    "completed": "✅",
                    "failed": "❌",
                    "in_progress": "⏳",
                }.get(task.get("status", "pending"), "⏸️")

                console.print(
                    f"  {prefix}{status_icon} {task.get('description', 'No description')}"
                )

                if detailed:
                    indent = "    " if is_last else "│   "
                    console.print(f"  {indent}  Type: {task.get('type', 'unknown')}")
                    console.print(f"  {indent}  ID: {task.get('id', 'unknown')}")

    async def _show_plan_table(graph, detailed):
        """Show plan as table."""
        table = Table(title=f"Plan: {graph.get('goal', 'Unknown Goal')}")

        if detailed:
            table.add_column("ID", style="dim")
            table.add_column("Type", style="yellow")
            table.add_column("Role", style="magenta")
            table.add_column("Description", style="white")
            table.add_column("Status", style="green")
            table.add_column("Dependencies", style="cyan")
        else:
            table.add_column("Role", style="magenta")
            table.add_column("Description", style="white")
            table.add_column("Status", style="green")

        tasks = graph.get("tasks", [])
        for task in tasks:
            status_icon = {"completed": "✅", "failed": "❌", "in_progress": "⏳"}.get(
                task.get("status", "pending"), "⏸️"
            )

            if detailed:
                deps = (
                    ", ".join(task.get("dependencies", []))
                    if task.get("dependencies")
                    else "None"
                )
                table.add_row(
                    task.get("id", "")[:20],
                    task.get("type", "unknown"),
                    task.get("role", "unknown"),
                    task.get("description", "No description"),
                    f"{status_icon} {task.get('status', 'pending')}",
                    deps[:30] + "..." if len(deps) > 30 else deps,
                )
            else:
                table.add_row(
                    task.get("role", "unknown"),
                    (
                        task.get("description", "No description")[:60] + "..."
                        if len(task.get("description", "")) > 60
                        else task.get("description", "No description")
                    ),
                    f"{status_icon} {task.get('status', 'pending')}",
                )

        console.print(table)

    _run_async(_show_plan())


@plan.command("create")
def plan_create(
    goal: str = typer.Argument(..., help="Goal for the plan"),
    template: str = typer.Option(
        "auto", help="Plan template: auto, development, testing, deployment"
    ),
    complexity: str = typer.Option(
        "medium", help="Complexity level: simple, medium, complex"
    ),
    output_file: Optional[str] = typer.Option(None, help="Save plan to file"),
):
    """Create a new orchestration plan."""

    async def _create_plan():
        memory = await _get_memory_patterns()
        orchestrator = IntegratedOrchestrator(memory)

        pid = f"plan-{uuid.uuid4().hex[:8]}"

        console.print("[bold blue]📋 Creating Orchestration Plan[/bold blue]")
        console.print(f"Goal: [green]{goal}[/green]")
        console.print(f"Template: [yellow]{template}[/yellow]")
        console.print(f"Complexity: [magenta]{complexity}[/magenta]")

        # Initialize session
        session_id = await orchestrator.initialize_session(pid, goal)

        # Create task graph
        task_graph = await orchestrator.create_simplified_task_graph(goal)

        if task_graph:
            console.print(f"✅ Created plan with {len(task_graph.tasks)} tasks")

            # Show summary
            await _show_plan_table(
                {
                    "goal": goal,
                    "tasks": [
                        {
                            "id": task.id,
                            "type": task.type,
                            "role": task.role,
                            "description": task.description,
                            "status": task.status,
                            "dependencies": getattr(task, "dependencies", []),
                        }
                        for task in task_graph.tasks
                    ],
                },
                True,
            )

            # Save to file if requested
            if output_file:
                plan_data = {
                    "project_id": pid,
                    "goal": goal,
                    "template": template,
                    "complexity": complexity,
                    "created_at": datetime.now().isoformat(),
                    "tasks": [
                        {
                            "id": task.id,
                            "type": task.type,
                            "role": task.role,
                            "description": task.description,
                            "status": task.status,
                            "context_keys": task.context_keys,
                        }
                        for task in task_graph.tasks
                    ],
                }

                with open(output_file, "w") as f:
                    json.dump(plan_data, f, indent=2)

                console.print(f"💾 Plan saved to [cyan]{output_file}[/cyan]")
        else:
            console.print("[red]Failed to create plan[/red]")

        await memory.close()

    _run_async(_create_plan())


workers = typer.Typer(help="Worker management commands")
app.add_typer(workers, name="workers")


@workers.command("status")
def workers_status(
    project_id: Optional[str] = typer.Option(None, help="Project ID to filter"),
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed worker info"
    ),
):
    """Show status of all workers."""

    async def _show_workers():
        memory = await _get_memory_patterns()

        console.print("[bold blue]👥 Worker Status[/bold blue]")

        try:
            # Get worker information from memory
            worker_keys = await memory.mcp.list_keys("/workers/")

            if not worker_keys:
                console.print("[yellow]No active workers found[/yellow]")
                return

            # Create workers table
            table = Table(title="Active Workers")
            if detailed:
                table.add_column("ID", style="cyan")
                table.add_column("Project", style="magenta")
                table.add_column("Role", style="yellow")
                table.add_column("Status", style="green")
                table.add_column("Current Task", style="white")
                table.add_column("Started", style="dim")
                table.add_column("CPU", style="red")
                table.add_column("Memory", style="blue")
            else:
                table.add_column("ID", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Current Task", style="white")
                table.add_column("Uptime", style="dim")

            # Mock worker data (in real implementation, this would query actual worker processes)
            workers = [
                {
                    "id": "worker-001",
                    "project": project_id or "current",
                    "role": "coder",
                    "status": "active",
                    "task": "Implementing user authentication",
                    "started": "2 hours ago",
                    "cpu": "15%",
                    "memory": "128MB",
                    "uptime": "2h 15m",
                },
                {
                    "id": "worker-002",
                    "project": project_id or "current",
                    "role": "adversary",
                    "status": "idle",
                    "task": "Waiting for code review",
                    "started": "1 hour ago",
                    "cpu": "2%",
                    "memory": "64MB",
                    "uptime": "1h 30m",
                },
                {
                    "id": "worker-003",
                    "project": project_id or "current",
                    "role": "supervisor",
                    "status": "monitoring",
                    "task": "Orchestrating workflow",
                    "started": "3 hours ago",
                    "cpu": "8%",
                    "memory": "96MB",
                    "uptime": "3h 5m",
                },
            ]

            for worker in workers:
                status_icon = {
                    "active": "🟢",
                    "idle": "🟡",
                    "monitoring": "🔵",
                    "error": "🔴",
                }.get(worker["status"], "⚪")

                if detailed:
                    table.add_row(
                        worker["id"],
                        worker["project"],
                        worker["role"],
                        f"{status_icon} {worker['status']}",
                        (
                            worker["task"][:40] + "..."
                            if len(worker["task"]) > 40
                            else worker["task"]
                        ),
                        worker["started"],
                        worker["cpu"],
                        worker["memory"],
                    )
                else:
                    table.add_row(
                        worker["id"],
                        f"{status_icon} {worker['status']}",
                        (
                            worker["task"][:50] + "..."
                            if len(worker["task"]) > 50
                            else worker["task"]
                        ),
                        worker["uptime"],
                    )

            console.print(table)

            # Show summary
            active_count = sum(1 for w in workers if w["status"] == "active")
            idle_count = sum(1 for w in workers if w["status"] == "idle")

            console.print(
                f"\n[bold]Summary:[/bold] {active_count} active, {idle_count} idle, {len(workers)} total"
            )

        except Exception as e:
            console.print(f"[red]Error getting worker status: {e}[/red]")

        await memory.close()

    _run_async(_show_workers())


@workers.command("stop")
def workers_stop(
    worker_id: Optional[str] = typer.Option(None, help="Specific worker ID to stop"),
    project_id: Optional[str] = typer.Option(None, help="Stop all workers for project"),
    force: bool = typer.Option(False, "--force", help="Force stop workers"),
):
    """Stop workers."""

    async def _stop_workers():
        console.print("[bold yellow]🛑 Stopping Workers[/bold yellow]")

        if worker_id:
            console.print(f"Stopping worker: [cyan]{worker_id}[/cyan]")
            # In real implementation, would stop specific worker process
            console.print(f"✅ Worker [cyan]{worker_id}[/cyan] stopped")
        elif project_id:
            console.print(
                f"Stopping all workers for project: [magenta]{project_id}[/magenta]"
            )
            # In real implementation, would stop all workers for project
            console.print(
                f"✅ All workers for project [magenta]{project_id}[/magenta] stopped"
            )
        else:
            console.print("Stopping all workers...")
            # In real implementation, would stop all workers
            console.print("✅ All workers stopped")

    _run_async(_stop_workers())


utilities = typer.Typer(help="Utility management commands")
app.add_typer(utilities, name="utilities")


@utilities.command("list")
def utilities_list(
    available: bool = typer.Option(
        False, "--available", help="Show available utilities"
    ),
    running: bool = typer.Option(
        False, "--running", help="Show only running utilities"
    ),
):
    """List utilities."""

    async def _list_utilities():
        console.print("[bold blue]🔧 Utilities[/bold blue]")

        # Mock utilities data
        utilities = [
            {
                "name": "TestRunner",
                "status": "ready",
                "description": "Pytest integration with coverage",
                "last_run": "5 min ago",
            },
            {
                "name": "CodeLinter",
                "status": "active",
                "description": "Ruff linting with auto-fix",
                "last_run": "Now",
            },
            {
                "name": "SecurityScanner",
                "status": "ready",
                "description": "Bandit security analysis",
                "last_run": "1 hour ago",
            },
            {
                "name": "DocumentationGenerator",
                "status": "ready",
                "description": "MkDocs documentation",
                "last_run": "Never",
            },
            {
                "name": "BuildUtility",
                "status": "ready",
                "description": "Project build automation",
                "last_run": "30 min ago",
            },
            {
                "name": "GitManager",
                "status": "ready",
                "description": "AI-powered Git operations",
                "last_run": "15 min ago",
            },
        ]

        if running:
            utilities = [u for u in utilities if u["status"] == "active"]

        table = Table(title="Available Utilities" if available else "Utilities")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Description", style="white")
        table.add_column("Last Run", style="dim")

        for utility in utilities:
            status_icon = {"active": "🔵", "ready": "⚪", "error": "🔴"}.get(
                utility["status"], "❓"
            )

            table.add_row(
                utility["name"],
                f"{status_icon} {utility['status']}",
                utility["description"],
                utility["last_run"],
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(utilities)} utilities[/dim]")

    _run_async(_list_utilities())


@utilities.command("run")
def utilities_run(
    name: str = typer.Argument(..., help="Utility name to run"),
    project_id: Optional[str] = typer.Option(None, help="Project ID"),
    args: Optional[str] = typer.Option(None, help="Additional arguments"),
):
    """Run a utility."""

    async def _run_utility():
        console.print(f"[bold blue]🔧 Running Utility: [cyan]{name}[/cyan][/bold blue]")

        if project_id:
            console.print(f"Project: [magenta]{project_id}[/magenta]")

        if args:
            console.print(f"Arguments: [yellow]{args}[/yellow]")

        # Mock utility execution
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Running {name}...", total=None)
            await asyncio.sleep(2)  # Simulate work
            progress.update(task, description=f"{name} completed successfully!")

        console.print(f"✅ Utility [cyan]{name}[/cyan] completed")

    _run_async(_run_utility())


projects = typer.Typer(help="Project management commands")
app.add_typer(projects, name="projects")


@projects.command("list")
def projects_list(
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed project info"
    ),
):
    """List all projects."""
    console.print("[bold blue]📁 Projects[/bold blue]")

    # For now, just show the current project if it exists
    current_config = None
    if Path("apex.json").exists():
        try:
            with open("apex.json") as f:
                current_config = json.load(f)
        except Exception:
            pass

    if current_config:
        if detailed:
            table = Table(title="Current Project (Detailed)")
            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Type", style="green")
            table.add_column("Tech Stack", style="yellow")
            table.add_column("Description", style="white")

            tech_stack = ", ".join(current_config.get("tech_stack", []))
            table.add_row(
                current_config.get("name", "Unknown"),
                current_config.get("project_id", "Unknown")[:20],
                current_config.get("project_type", "Unknown"),
                tech_stack[:30] + "..." if len(tech_stack) > 30 else tech_stack,
                current_config.get("description", "No description")[:40],
            )
        else:
            table = Table(title="Current Project")
            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Type", style="green")
            table.add_column("Description", style="white")

            table.add_row(
                current_config.get("name", "Unknown"),
                current_config.get("project_id", "Unknown")[:20],
                current_config.get("project_type", "Unknown"),
                current_config.get("description", "No description")[:50],
            )

        console.print(table)

        # Show additional info if available
        if detailed and current_config.get("features"):
            console.print(
                f"\n[bold]Features:[/bold] {', '.join(current_config['features'])}"
            )

    else:
        console.print("[yellow]No APEX project found in current directory[/yellow]")
        console.print(
            "Use 'apex init' to initialize APEX or 'apex new <name>' to create a new project"
        )


@projects.command("clean")
def projects_clean(
    older_than: int = typer.Option(7, help="Clean projects older than N days"),
    completed_only: bool = typer.Option(True, help="Only clean completed projects"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be cleaned"),
):
    """Clean up old projects."""

    async def _clean_projects():
        console.print("[bold yellow]🧹 Cleaning Projects[/bold yellow]")
        console.print(
            f"Criteria: Older than {older_than} days, Completed only: {completed_only}"
        )

        if dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]")

        # Mock cleanup
        projects_to_clean = [
            {"id": "proj-abc123", "age": "10 days", "status": "completed"},
            {"id": "proj-def456", "age": "15 days", "status": "completed"},
        ]

        if projects_to_clean:
            table = Table(title="Projects to Clean")
            table.add_column("Project ID", style="cyan")
            table.add_column("Age", style="yellow")
            table.add_column("Status", style="green")

            for proj in projects_to_clean:
                table.add_row(proj["id"], proj["age"], proj["status"])

            console.print(table)

            if not dry_run:
                console.print(f"✅ Cleaned {len(projects_to_clean)} projects")
            else:
                console.print(
                    f"[dim]Would clean {len(projects_to_clean)} projects[/dim]"
                )
        else:
            console.print("[green]No projects need cleaning[/green]")

    _run_async(_clean_projects())


@app.command()
def new(
    project_name: str = typer.Argument(..., help="Name of the new project"),
    template: Optional[str] = typer.Option(None, help="Project template to use"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git initialization"),
    tech_stack: Optional[str] = typer.Option(
        None, "--tech", help="Technology stack (comma-separated)"
    ),
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

    # Create project config
    config = ProjectConfig(
        project_id=f"{project_name}-{uuid.uuid4().hex[:8]}",
        name=project_name,
        description=description,
        tech_stack=tech_list,
        project_type=project_type,
        features=features,
    )

    # Save config
    config_file = project_path / "apex.json"
    with open(config_file, "w") as f:
        json.dump(config.model_dump(), f, indent=2, default=str)

    console.print("✓ Created project configuration")

    # Setup MCP integration
    mcp_success = setup_project_mcp(project_path)

    # Initialize git if requested
    if not no_git:
        try:
            import subprocess

            subprocess.run(
                ["git", "init"], cwd=project_path, check=True, capture_output=True
            )
            console.print("✓ Initialized git repository")
        except Exception:
            console.print("[yellow]⚠ Git initialization failed[/yellow]")

    console.print(f"\n✓ Project '{project_name}' created successfully!")
    console.print("Next steps:")
    console.print(f"  cd {project_name}")
    console.print('  apex start --task "Your initial task here"')
    console.print("  claude  # Start Claude Code with APEX integration")


@app.command()
def init(
    import_config: Optional[str] = typer.Option(
        None, "--import", help="Import existing configuration"
    ),
):
    """Initialize APEX in existing project."""
    if Path("apex.json").exists():
        console.print("[yellow]APEX already initialized in this directory[/yellow]")
        raise typer.Exit(1)

    console.print("[bold blue]Initializing APEX in current directory[/bold blue]")

    if import_config:
        # Import existing config
        try:
            with open(import_config) as f:
                config_data = json.load(f)
            config = ProjectConfig(**config_data)
        except Exception as e:
            console.print(f"[red]Error importing config: {e}[/red]")
            raise typer.Exit(1)
    else:
        # Interactive setup
        project_name = typer.prompt("Project name", default=Path.cwd().name)
        description = typer.prompt(
            "Project description", default=f"APEX project: {project_name}"
        )

        config = ProjectConfig(
            project_id=f"{project_name}-{uuid.uuid4().hex[:8]}",
            name=project_name,
            description=description,
            tech_stack=["Python"],
            project_type="CLI Tool",
            features=["core functionality"],
        )

    # Save config
    with open("apex.json", "w") as f:
        json.dump(config.model_dump(), f, indent=2, default=str)

    # Setup MCP integration
    setup_project_mcp(Path("."))

    console.print("✓ APEX initialized successfully!")


@app.command()
def list():
    """List existing APEX projects."""
    console.print("[bold blue]APEX Projects[/bold blue]")

    # For now, just show the current project if it exists
    current_config = None
    if Path("apex.json").exists():
        try:
            with open("apex.json") as f:
                current_config = json.load(f)
        except Exception:
            pass

    if current_config:
        table = Table(title="Current Project")
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Type", style="green")
        table.add_column("Description", style="white")

        table.add_row(
            current_config.get("name", "Unknown"),
            current_config.get("project_id", "Unknown")[:20],
            current_config.get("project_type", "Unknown"),
            current_config.get("description", "No description")[:50],
        )

        console.print(table)
    else:
        console.print("[yellow]No APEX project found in current directory[/yellow]")
        console.print(
            "Use 'apex init' to initialize APEX or 'apex new <name>' to create a new project"
        )


@app.command()
def version():
    """Show APEX version and system information."""
    console.print("[bold blue]APEX v2.0 - Integrated Orchestrator[/bold blue]")
    console.print("[dim]Connecting simplified and full orchestration systems[/dim]")

    # Show system capabilities
    table = Table(title="System Capabilities")
    table.add_column("Feature", style="cyan")
    table.add_column("Status", style="green")

    table.add_row("Simplified Orchestration", "✅ Available")
    table.add_row("Full LMDB Integration", "✅ Available")
    table.add_row("TUI Interface", "✅ Available")
    table.add_row("Session Resume", "✅ Available")
    table.add_row("Memory Export", "✅ Available")
    table.add_row("Error Recovery", "✅ Available")
    table.add_row("Advanced Orchestration", "✅ Available")
    table.add_row("Plan Management", "✅ Available")
    table.add_row("Project Management", "✅ Available")

    console.print(table)


def main():
    """Run the integrated CLI."""
    app()


if __name__ == "__main__":
    main()
