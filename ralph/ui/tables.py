"""Table displays using Rich."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from rich.panel import Panel
from rich.progress import BarColumn, Progress, TaskProgressColumn
from rich.table import Table
from rich.text import Text

from ralph.ui.console import console, get_phase_style, SimpsonsColors


def create_project_table(projects: list[dict]) -> Table:
    """
    Create a table listing research projects.

    Args:
        projects: List of project info dicts with keys:
            - name: Project name
            - path: Project path
            - phase: Current phase
            - target: Target papers
            - analyzed: Papers analyzed
            - pending: Papers pending

    Returns:
        Rich Table
    """
    table = Table(
        title="Research Projects",
        show_header=True,
        header_style="bold",
        border_style=SimpsonsColors.BLUE,
    )

    table.add_column("Project", style=SimpsonsColors.BLUE, no_wrap=True)
    table.add_column("Phase", justify="center")
    table.add_column("Progress", justify="center")
    table.add_column("Pending", justify="right", style=SimpsonsColors.YELLOW)

    for project in projects:
        name = project.get("name", "Unknown")
        phase = project.get("phase", "UNKNOWN")
        target = project.get("target", 0)
        analyzed = project.get("analyzed", 0)
        pending = project.get("pending", 0)

        # Phase with style
        phase_text = Text(phase)
        phase_text.stylize(get_phase_style(phase))

        # Progress as fraction
        if target > 0:
            progress = f"{analyzed}/{target}"
        else:
            progress = f"{analyzed}/?"

        table.add_row(name, phase_text, progress, str(pending))

    return table


def create_status_panel(summary: dict, project_path: Path) -> Panel:
    """
    Create a detailed status panel for a research project.

    Args:
        summary: Project summary dict from RRDManager.get_summary()
        project_path: Path to the project

    Returns:
        Rich Panel
    """
    # Create content
    content = Table.grid(padding=(0, 2))
    content.add_column(style=f"bold {SimpsonsColors.BLUE}", justify="right")
    content.add_column()

    # Basic info
    content.add_row("Project:", summary.get("project", "Unknown"))
    content.add_row("Path:", str(project_path))

    # Phase with style
    phase = summary.get("phase", "UNKNOWN")
    phase_text = Text(phase)
    phase_text.stylize(get_phase_style(phase))
    content.add_row("Phase:", phase_text)

    content.add_row("", "")  # Spacer

    # Papers section
    content.add_row("Papers:", "")
    content.add_row("  Target:", str(summary.get("target_papers", 0)))
    content.add_row("  In Pool:", str(summary.get("pool_size", 0)))
    content.add_row("  Analyzed:", str(summary.get("analyzed", 0)))
    content.add_row("  Presented:", str(summary.get("presented", 0)))
    content.add_row("  Rejected:", str(summary.get("rejected", 0)))
    content.add_row("  Pending:", str(summary.get("pending", 0)))

    analyzing = summary.get("analyzing", 0)
    if analyzing > 0:
        analyzing_text = Text(f"{analyzing} (will be re-analyzed)")
        analyzing_text.stylize(SimpsonsColors.YELLOW)
        content.add_row("  Analyzing:", analyzing_text)

    content.add_row("", "")  # Spacer

    # Insights
    content.add_row("Insights:", str(summary.get("insights", 0)))

    content.add_row("", "")  # Spacer

    # Progress bar
    completion = summary.get("completion_pct", 0)
    target = summary.get("target_papers", 0)
    analyzed = summary.get("analyzed", 0)

    if target > 0:
        progress_bar = create_mini_progress_bar(analyzed, target)
        content.add_row("Progress:", progress_bar)

    return Panel(
        content,
        title="[bold]Research Status[/bold]",
        border_style=SimpsonsColors.BLUE,
        padding=(1, 2),
    )


def create_mini_progress_bar(current: int, total: int, width: int = 30) -> Text:
    """Create a simple text-based progress bar."""
    if total == 0:
        pct = 0
    else:
        pct = min(100, int((current / total) * 100))

    filled = int(width * pct / 100)
    empty = width - filled

    bar = Text()
    bar.append("[")
    bar.append("=" * filled, style=SimpsonsColors.PINK)
    bar.append("-" * empty, style="dim")
    bar.append(f"] {pct}%")

    return bar


def create_completion_summary(summary: dict) -> Panel:
    """Create a completion summary panel."""
    content = Table.grid(padding=(0, 2))
    content.add_column(style="bold", justify="right")
    content.add_column()

    content.add_row("Papers Analyzed:", str(summary.get("analyzed", 0)))
    content.add_row("Papers Presented:", str(summary.get("presented", 0)))
    content.add_row("Papers Rejected:", str(summary.get("rejected", 0)))
    content.add_row("Insights:", str(summary.get("insights", 0)))

    return Panel(
        content,
        title=f"[bold {SimpsonsColors.PINK}]Research Complete![/]",
        border_style=SimpsonsColors.PINK,
        padding=(1, 2),
    )


def create_timing_table(timing_data: dict) -> Optional[Table]:
    """Create a table showing timing information."""
    if not timing_data:
        return None

    table = Table(
        show_header=True,
        header_style="bold",
        border_style=SimpsonsColors.BROWN,
    )

    table.add_column("Phase", style=SimpsonsColors.BLUE)
    table.add_column("Started", justify="center")
    table.add_column("Duration", justify="right")

    for phase in ["discovery", "analysis", "ideation"]:
        phase_timing = timing_data.get(phase, {})
        started = phase_timing.get("started_at")
        duration = phase_timing.get("duration_seconds")

        if started:
            if isinstance(started, str):
                started_str = started[:19]  # Truncate ISO format
            else:
                started_str = started.strftime("%Y-%m-%d %H:%M")
        else:
            started_str = "-"

        if duration:
            duration_str = format_duration(duration)
        else:
            duration_str = "-"

        table.add_row(phase.capitalize(), started_str, duration_str)

    return table


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
