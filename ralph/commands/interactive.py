"""Interactive menu mode for Research-Ralph."""

import json
import os
import time
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

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
from rich.markdown import Markdown
from rich.panel import Panel

from ralph.ui.console import console, print_info, print_success, print_warning, SimpsonsColors


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


def _prompt_open_question(oq) -> Optional[str]:
    """Prompt user for a single open question. Returns answer or None if cancelled."""
    choices = [questionary.Choice(opt, value=opt) for opt in oq.options]
    choices.append(questionary.Choice("Other (custom answer)", value="__other__"))

    default = oq.current_default if oq.current_default in oq.options else None
    answer = questionary.select(oq.question, choices=choices, default=default, style=MENU_STYLE).ask()

    if answer is None:
        return None

    if answer == "__other__":
        return questionary.text("Enter your custom answer:", style=MENU_STYLE).ask()

    return answer


def _handle_open_questions(project_path: Path) -> bool:
    """
    Check for open questions and prompt user to answer them.

    Returns:
        True if should continue with research, False if cancelled
    """
    from ralph.core.rrd_manager import RRDManager

    manager = RRDManager(project_path)
    if not manager.exists:
        return True

    try:
        rrd = manager.load()
    except FileNotFoundError:
        return True  # Let run_research handle missing file
    except (json.JSONDecodeError, ValidationError) as e:
        import sys
        print(f"Warning: Could not parse rrd.json: {type(e).__name__}", file=sys.stderr)
        return True
    except (PermissionError, OSError) as e:
        import sys
        print(f"Warning: Could not read rrd.json: {type(e).__name__}", file=sys.stderr)
        return True

    if not rrd.open_questions:
        return True

    console.print()
    console.print(f"[bold]This research has {len(rrd.open_questions)} open question(s):[/bold]")
    console.print()

    for i, oq in enumerate(rrd.open_questions, 1):
        console.print(f"[dim]{i}. {oq.field}[/dim]")

        answer = _prompt_open_question(oq)
        if answer is None:
            return False

        oq.current_default = answer
        console.print(f"  → {answer}")
        console.print()

    rrd.open_questions = []
    manager.save()

    print_success("Open questions resolved!")
    console.print()
    return True


def run_menu() -> None:
    """Show menu for running a research project."""
    project = _select_project("Select a research project to run:", include_status=True)
    if project is None:
        return

    # Handle open questions before running
    if not _handle_open_questions(project):
        print_info("Research cancelled")
        return

    # Load current settings from project and config
    config = load_config()
    try:
        from ralph.core.rrd_manager import RRDManager

        manager = RRDManager(project)
        rrd = manager.load()
        current_papers = rrd.requirements.target_papers
    except Exception:
        current_papers = config.default_papers

    current_agent = config.default_agent  # Already a string (use_enum_values=True)
    auto_iterations = current_papers + 6

    # Show current settings
    console.print()
    console.print("[bold]Current settings:[/bold]")
    console.print(f"  Papers:     {current_papers}")
    console.print(f"  Iterations: auto ({auto_iterations})")
    console.print(f"  Agent:      {current_agent}")
    console.print()

    modify = questionary.confirm(
        "Modify settings before running?", default=False, style=MENU_STYLE
    ).ask()

    if not modify:
        run_research(str(project))
        return

    # Allow modifications with current values as defaults
    papers = questionary.text(
        f"Target papers [{current_papers}]:",
        default=str(current_papers),
        validate=lambda x: x.isdigit() or "Enter a number",
        style=MENU_STYLE,
    ).ask()

    iterations = questionary.text(
        "Max iterations [auto]:",
        default="",
        validate=lambda x: x == "" or x.isdigit() or "Enter a number",
        style=MENU_STYLE,
    ).ask()

    agent = questionary.select(
        "Agent to use:",
        choices=AGENT_CHOICES,
        default=current_agent,
        style=MENU_STYLE,
    ).ask()

    run_research(
        str(project),
        papers=int(papers) if papers else None,
        iterations=int(iterations) if iterations else None,
        agent=agent,
    )


def view_research_report(project: Path) -> None:
    """Display the research report as rendered Markdown."""
    report_path = project / "research-report.md"
    if not report_path.exists():
        print_warning("Research report not yet generated (complete ANALYSIS phase first)")
        return

    try:
        content = report_path.read_text(encoding="utf-8")
    except PermissionError:
        print_warning(f"Cannot read {report_path.name}: permission denied")
        return
    except (UnicodeDecodeError, OSError) as e:
        print_warning(f"Cannot read {report_path.name}: {e}")
        return

    console.print()
    console.print(Markdown(content))
    console.print()
    questionary.press_any_key_to_continue("Press any key to continue...").ask()


def view_product_ideas(project: Path) -> None:
    """Display product ideas in an interactive selection menu."""
    ideas_path = project / "product-ideas.json"
    if not ideas_path.exists():
        print_warning("Product ideas not yet generated (complete IDEATION phase first)")
        return

    try:
        content = ideas_path.read_text(encoding="utf-8")
    except PermissionError:
        print_warning(f"Cannot read {ideas_path.name}: permission denied")
        return
    except (UnicodeDecodeError, OSError) as e:
        print_warning(f"Cannot read {ideas_path.name}: {e}")
        return

    try:
        ideas = json.loads(content).get("ideas", [])
    except json.JSONDecodeError as e:
        print_warning(f"Cannot parse {ideas_path.name}: invalid JSON at line {e.lineno}")
        return

    if not ideas:
        print_info("No product ideas found")
        return

    while True:
        choices = [
            questionary.Choice(
                f"{idea.get('name', 'Unnamed')} (Score: {idea.get('scores', {}).get('combined_0_50', 'N/A')}/50)",
                value=idea,
            )
            for idea in ideas
            if isinstance(idea, dict)
        ]
        choices.append(questionary.Choice("Back", value=None))

        selected = questionary.select(
            "Select an idea to view details:",
            choices=choices,
            style=MENU_STYLE,
        ).ask()

        if selected is None:
            break

        _display_idea_details(selected)


def _get_score_color(combined: int) -> str:
    """Return color based on MISSION.md decision thresholds."""
    try:
        score = int(combined) if combined is not None else 0
    except (TypeError, ValueError):
        score = 0

    if score >= 35:  # PRESENT (Priority)
        return "green"
    if score >= 18:  # PRESENT or EXTRACT_INSIGHTS
        return "yellow"
    return "red"  # REJECT


def _display_idea_details(idea: dict) -> None:
    """Display detailed view of a product idea."""
    console.print()

    # Header
    console.print(
        Panel(
            f"[bold]{idea.get('name', 'Unnamed')}[/bold]\n\n{idea.get('one_liner', '')}",
            title="Product Idea",
            border_style=SimpsonsColors.BLUE,
        )
    )

    # Problem
    problem = idea.get("problem", {})
    console.print(
        Panel(
            f"[bold]Who:[/bold] {problem.get('who', 'N/A')}\n"
            f"[bold]Pain:[/bold] {problem.get('pain', 'N/A')}\n"
            f"[bold]Why Now:[/bold] {problem.get('why_now', 'N/A')}",
            title="Problem",
        )
    )

    # Solution
    solution = idea.get("solution", {})
    features = solution.get("key_features", [])
    features_str = "\n".join(f"  - {f}" for f in features) if features else "N/A"
    console.print(
        Panel(
            f"[bold]What:[/bold] {solution.get('what', 'N/A')}\n\n"
            f"[bold]Key Features:[/bold]\n{features_str}\n\n"
            f"[bold]MVP Scope:[/bold] {solution.get('mvp_scope', 'N/A')}",
            title="Solution",
        )
    )

    # Scores
    scores = idea.get("scores", {})
    combined = scores.get("combined_0_50", 0)
    color = _get_score_color(combined)
    console.print(
        Panel(
            f"[bold]Execution:[/bold] {scores.get('execution_0_30', 'N/A')}/30\n"
            f"[bold]Blue Ocean:[/bold] {scores.get('blue_ocean_0_20', 'N/A')}/20\n"
            f"[{color}][bold]Combined:[/bold] {combined}/50[/{color}]\n"
            f"[bold]Confidence:[/bold] {scores.get('confidence_0_1', 'N/A')}",
            title="Scores",
        )
    )

    # Evidence
    paper_ids = idea.get("evidence", {}).get("paper_ids", [])
    if paper_ids:
        console.print(f"\n[dim]Based on papers: {', '.join(paper_ids)}[/dim]")

    # Risks (show top 3)
    risks = idea.get("risks", [])[:3]
    if risks:
        risks_str = "\n".join(f"  - [{r.get('type', 'N/A')}] {r.get('risk', 'N/A')}" for r in risks)
        console.print(f"\n[bold]Key Risks:[/bold]\n{risks_str}")

    console.print()
    questionary.press_any_key_to_continue("Press any key to continue...").ask()


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
            questionary.Choice("View research report", value="view_report"),
            questionary.Choice("View product ideas", value="view_ideas"),
            questionary.Separator(),
            questionary.Choice("Run this research", value="run"),
            questionary.Choice("Reset this research", value="reset"),
            questionary.Choice("Back to main menu", value=None),
        ],
        style=MENU_STYLE,
    ).ask()

    actions = {
        "view_report": lambda: view_research_report(project),
        "view_ideas": lambda: view_product_ideas(project),
        "run": lambda: run_research(str(project)),
        "reset": lambda: reset_project(str(project)),
    }

    if action in actions:
        actions[action]()


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
