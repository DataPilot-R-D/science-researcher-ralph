"""Reset command - reset a research project to DISCOVERY phase."""

import json
from pathlib import Path

from ralph.config import resolve_research_path
from ralph.core.rrd_manager import RRDManager
from ralph.ui.console import console, print_error, print_success, print_info, SimpsonsColors


def reset_project(project: str, confirm: bool = True) -> bool:
    """
    Reset a research project to DISCOVERY phase.

    Creates a backup of current state before resetting.

    Args:
        project: Project name or path
        confirm: If True, ask for confirmation

    Returns:
        True if successful, False otherwise
    """
    # Resolve project path
    project_path = resolve_research_path(project)

    if project_path is None:
        print_error(f"Research project not found: {project}")
        console.print()
        console.print("Use [bold]research-ralph --list[/bold] to see available projects")
        return False

    # Load RRD to check validity
    manager = RRDManager(project_path)

    if not manager.exists:
        print_error(f"rrd.json not found in {project_path}")
        return False

    errors = manager.validate()
    if errors:
        console.print(f"[{SimpsonsColors.YELLOW}]Warning: RRD file has issues, but will proceed with reset[/]")
        for error in errors:
            console.print(f"  - {error}")
        console.print()

    # Show current state
    try:
        summary = manager.get_summary()
        console.print()
        console.print("[bold]Current state:[/bold]")
        console.print(f"  Phase: {summary['phase']}")
        console.print(f"  Papers analyzed: {summary['analyzed']}")
        console.print(f"  Papers in pool: {summary['pool_size']}")
        console.print(f"  Insights: {summary['insights']}")
        console.print()
    except (ValueError, KeyError, FileNotFoundError, PermissionError) as e:
        console.print()
        console.print(f"[dim]Current state: Could not load rrd.json ({type(e).__name__})[/dim]")
        console.print()

    # Confirm
    if confirm:
        console.print(f"[{SimpsonsColors.YELLOW}]This will:[/]")
        console.print("  - Reset phase to DISCOVERY")
        console.print("  - Clear all papers from the pool")
        console.print("  - Clear all insights")
        console.print("  - Reset progress.txt")
        console.print()
        console.print("[dim]A backup will be created before reset.[/dim]")
        console.print()

        import questionary

        proceed = questionary.confirm("Proceed with reset?", default=False).ask()
        if not proceed:
            print_info("Reset cancelled")
            return False

    # Perform reset
    try:
        backup_path = manager.reset()
    except PermissionError as e:
        print_error(f"Permission denied: {e}")
        return False
    except OSError as e:
        print_error(f"Filesystem error: {e}")
        return False
    except json.JSONDecodeError as e:
        print_error(f"RRD file corrupted: {e}")
        return False

    print_success(f"Backup created: {backup_path}")
    print_success("Research reset to DISCOVERY phase")
    console.print()
    console.print(f"Run again with: [bold]research-ralph --run {project_path.name}[/bold]")
    console.print()
    return True
