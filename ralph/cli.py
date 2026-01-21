"""Main CLI application for Research-Ralph using Typer."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from ralph import __version__, __app_name__
from ralph.config import get_config_value, set_config_value, load_config
from ralph.ui.console import console, print_error, print_success, print_info, SimpsonsColors

# Create Typer app
app = typer.Typer(
    name=__app_name__,
    help="Research-Ralph - Autonomous research scouting agent",
    add_completion=True,
    no_args_is_help=False,  # We handle no args ourselves (interactive mode)
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold {SimpsonsColors.BLUE}]Research-Ralph[/] v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    # CI/CD flags for non-interactive mode
    new: Annotated[
        Optional[str],
        typer.Option(
            "--new",
            "-n",
            help="Create a new research project with the given topic",
        ),
    ] = None,
    run: Annotated[
        Optional[str],
        typer.Option(
            "--run",
            "-r",
            help="Run research on the given project",
        ),
    ] = None,
    status: Annotated[
        Optional[str],
        typer.Option(
            "--status",
            "-s",
            help="Show status of the given project",
        ),
    ] = None,
    list_projects: Annotated[
        bool,
        typer.Option(
            "--list",
            "-l",
            help="List all research projects",
        ),
    ] = False,
    reset: Annotated[
        Optional[str],
        typer.Option(
            "--reset",
            help="Reset the given project to DISCOVERY phase",
        ),
    ] = None,
    config: Annotated[
        Optional[str],
        typer.Option(
            "--config",
            "-c",
            help="Set config value (key=value) or show all config (no value)",
        ),
    ] = None,
    # Options for --new and --run
    papers: Annotated[
        Optional[int],
        typer.Option(
            "--papers",
            "-p",
            help="Target number of papers",
        ),
    ] = None,
    iterations: Annotated[
        Optional[int],
        typer.Option(
            "--iterations",
            "-i",
            help="Maximum iterations for research loop",
        ),
    ] = None,
    agent: Annotated[
        Optional[str],
        typer.Option(
            "--agent",
            "-a",
            help="Agent to use: claude, amp, or codex",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force operations (e.g., override target_papers on in-progress research)",
        ),
    ] = False,
    # Global options
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """
    Research-Ralph - Autonomous research scouting agent.

    Run without arguments for interactive menu mode.

    [bold]Examples:[/bold]

        research-ralph                          # Interactive menu
        research-ralph --new "AI in robotics"   # Create new project
        research-ralph --list                   # List all projects
        research-ralph --run my-project         # Run research
        research-ralph --status my-project      # Show status
    """
    # Check if any flag was provided (non-interactive mode)
    # Note: config can be empty string (show all), so check `is not None`
    has_flag = any([new, run, status, list_projects, reset, config is not None])

    # If a subcommand was invoked, let it handle things
    if ctx.invoked_subcommand is not None:
        return

    if not has_flag:
        # Interactive mode
        from ralph.commands.interactive import main_menu

        main_menu()
        return

    # Handle flags in order of precedence

    # --config
    if config is not None:
        handle_config(config)
        return

    # --list
    if list_projects:
        from ralph.commands.list_cmd import list_projects as cmd_list

        cmd_list()
        return

    # --new
    if new is not None:
        from ralph.commands.create import create_project

        result = create_project(new, papers=papers, agent=agent)
        raise typer.Exit(0 if result else 1)

    # --status
    if status is not None:
        from ralph.commands.status import show_status

        result = show_status(status)
        raise typer.Exit(0 if result else 1)

    # --reset
    if reset is not None:
        from ralph.commands.reset import reset_project

        # In CLI mode, skip confirmation
        result = reset_project(reset, confirm=False)
        raise typer.Exit(0 if result else 1)

    # --run
    if run is not None:
        from ralph.commands.run import run_research

        result = run_research(
            run,
            papers=papers,
            iterations=iterations,
            agent=agent,
            force=force,
        )
        raise typer.Exit(0 if result else 1)


def handle_config(config_arg: str) -> None:
    """Handle --config flag."""
    if "=" in config_arg:
        # Set config value
        key, value = config_arg.split("=", 1)
        if set_config_value(key.strip(), value.strip()):
            print_success(f"Set {key} = {value}")
        else:
            print_error(f"Unknown config key: {key}")
            console.print()
            console.print("Available keys:")
            cfg = load_config()
            for field in cfg.model_fields:
                console.print(f"  - {field}")
            raise typer.Exit(1)
    else:
        # Show config value or all config
        if config_arg.strip():
            value = get_config_value(config_arg.strip())
            if value is not None:
                console.print(f"{config_arg} = {value}")
            else:
                print_error(f"Unknown config key: {config_arg}")
                raise typer.Exit(1)
        else:
            # Show all config
            cfg = load_config()
            console.print()
            console.print("[bold]Current Configuration[/bold]")
            console.print()
            for field, value in cfg.model_dump().items():
                console.print(f"  {field}: {value}")
            console.print()


# Subcommands for those who prefer them
@app.command("create")
def cmd_create(
    topic: Annotated[str, typer.Argument(help="Research topic description")],
    papers: Annotated[
        Optional[int],
        typer.Option("--papers", "-p", help="Target number of papers"),
    ] = None,
    agent: Annotated[
        Optional[str],
        typer.Option("--agent", "-a", help="Agent: claude, amp, or codex"),
    ] = None,
) -> None:
    """Create a new research project."""
    from ralph.commands.create import create_project

    result = create_project(topic, papers=papers, agent=agent)
    raise typer.Exit(0 if result else 1)


@app.command("run")
def cmd_run(
    project: Annotated[str, typer.Argument(help="Project name or path")],
    papers: Annotated[
        Optional[int],
        typer.Option("--papers", "-p", help="Target number of papers"),
    ] = None,
    iterations: Annotated[
        Optional[int],
        typer.Option("--iterations", "-i", help="Maximum iterations"),
    ] = None,
    agent: Annotated[
        Optional[str],
        typer.Option("--agent", "-a", help="Agent: claude, amp, or codex"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force override target_papers"),
    ] = False,
) -> None:
    """Run research on a project."""
    from ralph.commands.run import run_research

    result = run_research(
        project,
        papers=papers,
        iterations=iterations,
        agent=agent,
        force=force,
    )
    raise typer.Exit(0 if result else 1)


@app.command("status")
def cmd_status(
    project: Annotated[str, typer.Argument(help="Project name or path")],
) -> None:
    """Show detailed status of a research project."""
    from ralph.commands.status import show_status

    result = show_status(project)
    raise typer.Exit(0 if result else 1)


@app.command("list")
def cmd_list() -> None:
    """List all research projects."""
    from ralph.commands.list_cmd import list_projects

    list_projects()


@app.command("reset")
def cmd_reset(
    project: Annotated[str, typer.Argument(help="Project name or path")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Reset a research project to DISCOVERY phase."""
    from ralph.commands.reset import reset_project

    result = reset_project(project, confirm=not yes)
    raise typer.Exit(0 if result else 1)


@app.command("config")
def cmd_config(
    key: Annotated[
        Optional[str],
        typer.Argument(help="Config key (or key=value to set)"),
    ] = None,
) -> None:
    """View or set configuration values."""
    if key is None:
        # Show all
        handle_config("")
    else:
        handle_config(key)


@app.command("init")
def cmd_init() -> None:
    """Initialize current directory for Research-Ralph.

    Creates AGENTS.md, CLAUDE.md, prompt.md, MISSION.md if missing.
    These files are copied from the package templates.
    """
    from ralph.config import ensure_current_dir_initialized

    created, files = ensure_current_dir_initialized()
    if created:
        console.print()
        print_success("Initialized current directory for Research-Ralph")
        console.print()
        console.print("[dim]Created files:[/dim]")
        for f in files:
            console.print(f"  - {f}")
        console.print()
    else:
        print_info("Directory already initialized (all files present)")


if __name__ == "__main__":
    app()
