"""Interactive menu mode for Research-Ralph."""

import json
import os
import time
from pathlib import Path
from typing import Optional

import questionary
from questionary import Style

from ralph import __version__
from ralph.config import (
    Agent,
    load_config,
    save_config,
    list_research_projects,
    check_initialization_status,
    ensure_current_dir_initialized,
)
from ralph.commands.create import create_project_interactive
from ralph.commands.list_cmd import list_projects
from ralph.commands.reset import reset_project
from ralph.commands.run import run_research
from ralph.commands.status import show_status
from ralph.ui.console import console, print_info, print_success, SimpsonsColors


MENU_STYLE = Style(
    [
        ("question", "bold"),
        ("answer", f"fg:{SimpsonsColors.BLUE} bold"),
        ("pointer", f"fg:{SimpsonsColors.YELLOW} bold"),
        ("highlighted", f"fg:{SimpsonsColors.YELLOW} bold"),
        ("selected", f"fg:{SimpsonsColors.PINK}"),
    ]
)

AGENT_CHOICES = [
    questionary.Choice("Claude", value="claude"),
    questionary.Choice("Amp", value="amp"),
    questionary.Choice("Codex", value="codex"),
]


def check_and_prompt_init() -> bool:
    """
    Check initialization status and prompt user if anything is missing.

    Returns True if initialization was performed, False otherwise.
    """
    status = check_initialization_status()

    if not status["config_missing"] and not status["git_missing"] and not status["files_missing"]:
        return False

    # Show what's missing
    console.print()
    console.print("[bold]Research-Ralph needs initialization:[/bold]")
    console.print()

    if status["config_missing"]:
        console.print("  [red]✗[/red] Config file missing (~/.research-ralph/config.yaml)")
    if status["git_missing"]:
        console.print("  [red]✗[/red] Git not initialized")
    if status["files_missing"]:
        console.print(f"  [red]✗[/red] Template files missing: {', '.join(status['files_missing'])}")

    console.print()

    proceed = questionary.confirm(
        "Initialize Research-Ralph?",
        default=True,
        style=MENU_STYLE,
    ).ask()

    if not proceed:
        return False

    result = ensure_current_dir_initialized()

    console.print()
    if result["config_created"]:
        print_success("Created ~/.research-ralph/config.yaml")
    if result["git_initialized"]:
        print_success("Initialized git repository")
    if result["files_created"]:
        print_success(f"Created template files: {', '.join(result['files_created'])}")
    console.print()

    return True


def _get_project_label(project_path: Path) -> str:
    """Get a display label for a project with status info."""
    try:
        with open(project_path / "rrd.json") as f:
            rrd = json.load(f)
        phase = rrd.get("phase", "?")
        analyzed = rrd.get("statistics", {}).get("total_analyzed", 0)
        target = rrd.get("requirements", {}).get("target_papers", "?")
        return f"{project_path.name} [{phase}] ({analyzed}/{target} papers)"
    except json.JSONDecodeError:
        return f"{project_path.name} [INVALID JSON]"
    except PermissionError:
        return f"{project_path.name} [NO ACCESS]"
    except FileNotFoundError:
        return f"{project_path.name} [NO RRD]"
    except Exception as e:
        detail = str(e)[:20] if str(e) else type(e).__name__
        return f"{project_path.name} [ERR: {detail}]"


def _select_project(prompt: str, include_status: bool = False) -> Optional[Path]:
    """Show project selection menu, returning selected path or None."""
    projects = list_research_projects()

    if not projects:
        console.print()
        print_info("No research projects found. Create one first!")
        return None

    choices = []
    for p in projects:
        label = _get_project_label(p) if include_status else p.name
        choices.append(questionary.Choice(label, value=p))

    choices.append(questionary.Separator())
    choices.append(questionary.Choice("Back to main menu", value=None))

    console.print()
    return questionary.select(prompt, choices=choices, style=MENU_STYLE).ask()


ASCII_BANNER = """
██████╗ ███████╗███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗      ██████╗  █████╗ ██╗     ██████╗ ██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║      ██╔══██╗██╔══██╗██║     ██╔══██╗██║  ██║
██████╔╝█████╗  ███████╗█████╗  ███████║██████╔╝██║     ███████║█████╗██████╔╝███████║██║     ██████╔╝███████║
██╔══██╗██╔══╝  ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║╚════╝██╔══██╗██╔══██║██║     ██╔═══╝ ██╔══██║
██║  ██║███████╗███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║      ██║  ██║██║  ██║███████╗██║     ██║  ██║
╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝      ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝
"""


def show_banner() -> None:
    """Show the Research-Ralph ASCII banner with fullscreen animation."""
    # Clear console for fullscreen experience
    console.clear()

    # Add top padding for vertical centering
    try:
        terminal_height = os.get_terminal_size().lines
    except OSError:
        terminal_height = 24  # Default fallback

    banner_lines = ASCII_BANNER.strip().split('\n')
    top_padding = max(0, (terminal_height - len(banner_lines) - 4) // 2)

    for _ in range(top_padding):
        console.print()

    # Animate banner with fast timing (0.1s)
    for line in banner_lines:
        console.print(f"[{SimpsonsColors.YELLOW}]{line}[/]")  # Simpson yellow
        time.sleep(0.1)

    console.print()
    console.print(f"[dim]v{__version__} - Autonomous research scouting agent[/dim]")
    console.print()


def main_menu() -> None:
    """Show the main interactive menu."""
    # Check for missing initialization before showing menu
    check_and_prompt_init()

    show_banner()

    while True:
        console.print()
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                questionary.Choice("Create new research project", value="create"),
                questionary.Choice("Run existing research", value="run"),
                questionary.Choice("View project status", value="status"),
                questionary.Choice("List all projects", value="list"),
                questionary.Choice("Configure settings", value="config"),
                questionary.Separator(),
                questionary.Choice("Exit", value="exit"),
            ],
            style=MENU_STYLE,
        ).ask()

        if choice is None or choice == "exit":
            console.print()
            print_info("Goodbye!")
            break
        elif choice == "create":
            create_project_interactive()
        elif choice == "run":
            run_menu()
        elif choice == "status":
            status_menu()
        elif choice == "list":
            console.print()
            list_projects()
        elif choice == "config":
            config_menu()


def run_menu() -> None:
    """Show menu for running a research project."""
    project = _select_project("Select a research project to run:", include_status=True)
    if project is None:
        return

    console.print()
    use_defaults = questionary.confirm(
        "Use default settings?", default=True, style=MENU_STYLE
    ).ask()

    if use_defaults:
        run_research(str(project))
        return

    papers = questionary.text(
        "Target papers (leave empty to use existing):",
        validate=lambda x: x == "" or x.isdigit() or "Enter a number",
        style=MENU_STYLE,
    ).ask()

    iterations = questionary.text(
        "Max iterations (leave empty for auto):",
        validate=lambda x: x == "" or x.isdigit() or "Enter a number",
        style=MENU_STYLE,
    ).ask()

    config = load_config()
    agent = questionary.select(
        "Agent to use:",
        choices=AGENT_CHOICES,
        default=config.default_agent.value,
        style=MENU_STYLE,
    ).ask()

    run_research(
        str(project),
        papers=int(papers) if papers else None,
        iterations=int(iterations) if iterations else None,
        agent=agent,
    )


def status_menu() -> None:
    """Show menu for viewing project status."""
    project = _select_project("Select a research project:")
    if project is None:
        return

    show_status(str(project))

    console.print()
    action = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("Run this research", value="run"),
            questionary.Choice("Reset this research", value="reset"),
            questionary.Choice("Back to main menu", value=None),
        ],
        style=MENU_STYLE,
    ).ask()

    if action == "run":
        run_research(str(project))
    elif action == "reset":
        reset_project(str(project))


def _print_config(config, title: str = "Current Settings") -> None:
    """Print configuration values."""
    console.print()
    console.print(f"[bold]{title}[/bold]")
    console.print(f"  Research directory: {config.research_dir}")
    console.print(f"  Default agent: {config.default_agent.value}")
    console.print(f"  Default papers: {config.default_papers}")
    console.print(f"  Live output: {config.live_output}")
    console.print()


def config_menu() -> None:
    """Show menu for configuring settings."""
    config = load_config()
    _print_config(config)

    while True:
        choice = questionary.select(
            "What would you like to change?",
            choices=[
                questionary.Choice("Research directory", value="research_dir"),
                questionary.Choice("Default agent", value="default_agent"),
                questionary.Choice("Default papers count", value="default_papers"),
                questionary.Choice("Live output", value="live_output"),
                questionary.Separator(),
                questionary.Choice("Save and go back", value=None),
            ],
            style=MENU_STYLE,
        ).ask()

        if choice is None:
            save_config(config)
            print_info("Settings saved!")
            break

        if choice == "research_dir":
            new_dir = questionary.path(
                "Research directory:",
                default=str(config.research_dir),
                only_directories=True,
                style=MENU_STYLE,
            ).ask()
            if new_dir:
                config.research_dir = Path(new_dir).expanduser()
        elif choice == "default_agent":
            new_agent = questionary.select(
                "Default agent:",
                choices=AGENT_CHOICES,
                default=config.default_agent.value,
                style=MENU_STYLE,
            ).ask()
            if new_agent:
                config.default_agent = Agent(new_agent)
        elif choice == "default_papers":
            new_papers = questionary.text(
                "Default papers count:",
                default=str(config.default_papers),
                validate=lambda x: x.isdigit() and int(x) > 0 or "Enter a positive number",
                style=MENU_STYLE,
            ).ask()
            if new_papers:
                config.default_papers = int(new_papers)
        elif choice == "live_output":
            config.live_output = questionary.confirm(
                "Enable live output during research?",
                default=config.live_output,
                style=MENU_STYLE,
            ).ask()

        _print_config(config, "[dim]Updated settings[/dim]")
