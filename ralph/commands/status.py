"""Status command - show detailed status of a research project."""

from pathlib import Path

from ralph.config import resolve_research_path
from ralph.core.rrd_manager import RRDManager
from ralph.ui.console import console, print_error, get_phase_style, SimpsonsColors
from ralph.ui.tables import create_status_panel, create_completion_summary, create_timing_table, format_duration


def show_status(project: str) -> bool:
    """
    Show detailed status of a research project.

    Args:
        project: Project name or path

    Returns:
        True if successful, False if project not found
    """
    # Resolve project path
    project_path = resolve_research_path(project)

    if project_path is None:
        print_error(f"Research project not found: {project}")
        console.print()
        console.print("Use [bold]research-ralph --list[/bold] to see available projects")
        return False

    # Load RRD
    manager = RRDManager(project_path)

    errors = manager.validate()
    if errors:
        print_error("Invalid RRD file:")
        for error in errors:
            console.print(f"  - {error}")
        console.print()
        console.print("Use [bold]research-ralph --reset[/bold] to reset the project")
        return False

    # Get summary
    summary = manager.get_summary()

    # Print header
    console.print()
    console.print(f"[bold {SimpsonsColors.BLUE}]Research-Ralph[/] - Status Report")
    console.print()

    # Create and print status panel
    panel = create_status_panel(summary, project_path)
    console.print(panel)
    console.print()

    # Timing information
    rrd = manager.load()
    timing_data = {}

    if rrd.timing.research_started_at:
        console.print(f"[bold {SimpsonsColors.BLUE}]Timing[/]")

        # Calculate elapsed time
        from datetime import datetime

        start = rrd.timing.research_started_at
        if isinstance(start, str):
            try:
                start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            except ValueError:
                start = None  # Invalid timestamp format

        if start:
            now = datetime.now(start.tzinfo) if start.tzinfo else datetime.now()
            elapsed = int((now - start).total_seconds())
            console.print(f"  Started: {rrd.timing.research_started_at}")
            console.print(f"  Elapsed: {format_duration(elapsed)}")

        # ETA if in analysis phase
        if rrd.phase == "ANALYSIS" and rrd.timing.analysis.avg_seconds_per_paper:
            avg = rrd.timing.analysis.avg_seconds_per_paper
            remaining = rrd.requirements.target_papers - rrd.statistics.total_analyzed
            if remaining > 0 and avg > 0:
                eta_seconds = int(remaining * avg)
                console.print(f"  Avg/paper: {format_duration(int(avg))}")
                console.print(f"  ETA: {format_duration(eta_seconds)} ({remaining} papers remaining)")

        console.print()

    # Status-specific messages
    phase = summary.get("phase", "UNKNOWN")
    analyzing = summary.get("analyzing", 0)
    pool_size = summary.get("pool_size", 0)
    target = summary.get("target_papers", 0)

    if phase == "COMPLETE":
        console.print(f"[{SimpsonsColors.PINK}]Research complete![/]")
        console.print(f"  View report: [bold]cat {project_path}/research-report.md[/bold]")
        if (project_path / "product-ideas.json").exists():
            console.print(f"  View ideas: [bold]cat {project_path}/product-ideas.json[/bold]")
    elif analyzing > 0:
        console.print(
            f"[{SimpsonsColors.YELLOW}]Papers stuck in 'analyzing' status will be re-analyzed on next run[/]"
        )
    elif pool_size < target and phase == "ANALYSIS":
        console.print(
            f"[{SimpsonsColors.YELLOW}]Pool ({pool_size}) < Target ({target}) - will revert to DISCOVERY[/]"
        )

    console.print()
    return True
