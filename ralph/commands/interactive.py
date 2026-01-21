"""Interactive menu mode for Research-Ralph."""

import os
import time
from pathlib import Path
from typing import Optional

import questionary
from questionary import Style
from rich.panel import Panel

from ralph import __version__
from ralph.config import (
    Agent,
    load_config,
    save_config,
    list_research_projects,
)
from ralph.commands.create import create_project_interactive
from ralph.commands.list_cmd import list_projects
from ralph.commands.reset import reset_project
from ralph.commands.run import run_research
from ralph.commands.status import show_status
from ralph.ui.console import console, print_info, SimpsonsColors


# Custom questionary style using Simpsons colors
MENU_STYLE = Style(
    [
        ("question", "bold"),
        ("answer", f"fg:{SimpsonsColors.BLUE} bold"),
        ("pointer", f"fg:{SimpsonsColors.YELLOW} bold"),
        ("highlighted", f"fg:{SimpsonsColors.YELLOW} bold"),
        ("selected", f"fg:{SimpsonsColors.PINK}"),
    ]
)


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
    projects = list_research_projects()

    if not projects:
        console.print()
        print_info("No research projects found. Create one first!")
        return

    # Build choices
    choices = []
    for p in projects:
        # Try to get project info
        rrd_path = p / "rrd.json"
        try:
            import json

            with open(rrd_path) as f:
                rrd = json.load(f)
            phase = rrd.get("phase", "?")
            analyzed = rrd.get("statistics", {}).get("total_analyzed", 0)
            target = rrd.get("requirements", {}).get("target_papers", "?")
            label = f"{p.name} [{phase}] ({analyzed}/{target} papers)"
        except Exception:
            label = p.name

        choices.append(questionary.Choice(label, value=p))

    choices.append(questionary.Separator())
    choices.append(questionary.Choice("Back to main menu", value=None))

    console.print()
    project = questionary.select(
        "Select a research project to run:",
        choices=choices,
        style=MENU_STYLE,
    ).ask()

    if project is None:
        return

    # Ask for options
    console.print()
    use_defaults = questionary.confirm(
        "Use default settings?",
        default=True,
        style=MENU_STYLE,
    ).ask()

    if use_defaults:
        run_research(str(project))
    else:
        # Get custom options
        papers = questionary.text(
            "Target papers (leave empty to use existing):",
            style=MENU_STYLE,
        ).ask()

        iterations = questionary.text(
            "Max iterations (leave empty for auto):",
            style=MENU_STYLE,
        ).ask()

        config = load_config()
        agent = questionary.select(
            "Agent to use:",
            choices=[
                questionary.Choice("Claude", value="claude"),
                questionary.Choice("Amp", value="amp"),
                questionary.Choice("Codex", value="codex"),
            ],
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
    projects = list_research_projects()

    if not projects:
        console.print()
        print_info("No research projects found. Create one first!")
        return

    # Build choices
    choices = []
    for p in projects:
        choices.append(questionary.Choice(p.name, value=p))

    choices.append(questionary.Separator())
    choices.append(questionary.Choice("Back to main menu", value=None))

    console.print()
    project = questionary.select(
        "Select a research project:",
        choices=choices,
        style=MENU_STYLE,
    ).ask()

    if project is None:
        return

    show_status(str(project))

    # Offer actions
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


def config_menu() -> None:
    """Show menu for configuring settings."""
    config = load_config()

    console.print()
    console.print("[bold]Current Settings[/bold]")
    console.print(f"  Research directory: {config.research_dir}")
    console.print(f"  Default agent: {config.default_agent.value}")
    console.print(f"  Default papers: {config.default_papers}")
    console.print(f"  Live output: {config.live_output}")
    console.print()

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
        elif choice == "research_dir":
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
                choices=[
                    questionary.Choice("Claude", value="claude"),
                    questionary.Choice("Amp", value="amp"),
                    questionary.Choice("Codex", value="codex"),
                ],
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

        # Show updated settings
        console.print()
        console.print("[dim]Updated settings:[/dim]")
        console.print(f"  Research directory: {config.research_dir}")
        console.print(f"  Default agent: {config.default_agent.value}")
        console.print(f"  Default papers: {config.default_papers}")
        console.print(f"  Live output: {config.live_output}")
        console.print()
