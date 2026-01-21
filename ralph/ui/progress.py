"""Progress indicators using Rich."""

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from ralph.ui.console import console, SimpsonsColors


def create_progress() -> Progress:
    """Create a progress bar for research tracking."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )


def create_spinner(text: str = "Working...") -> Progress:
    """Create a simple spinner for indeterminate progress."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def create_iteration_progress() -> Progress:
    """Create progress bar for research loop iterations."""
    return Progress(
        TextColumn(f"[bold {SimpsonsColors.BLUE}]Iteration {{task.completed}}/{{task.total}}"),
        BarColumn(bar_width=30, complete_style=SimpsonsColors.PINK),
        TaskProgressColumn(),
        TextColumn("[muted]|[/muted]"),
        TextColumn(f"[{SimpsonsColors.BLUE}]{{task.fields[phase]}}[/]"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )


def create_papers_progress() -> Progress:
    """Create progress bar for papers analysis."""
    return Progress(
        TextColumn(f"[bold {SimpsonsColors.BLUE}]Papers"),
        BarColumn(bar_width=30, complete_style=SimpsonsColors.PINK, finished_style=SimpsonsColors.PINK),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        console=console,
        transient=False,
    )
