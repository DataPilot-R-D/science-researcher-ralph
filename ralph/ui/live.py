"""Live output display for research loop using Rich."""

from typing import Optional

from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from ralph.ui.console import console, get_phase_style, SimpsonsColors


class LiveResearchDisplay:
    """
    Live display for research loop progress.

    Shows:
    - Current iteration and phase
    - Papers progress
    - Recent agent output (scrolling)
    """

    def __init__(self, max_iterations: int, target_papers: int):
        """
        Initialize live display.

        Args:
            max_iterations: Maximum number of iterations
            target_papers: Target number of papers to analyze
        """
        self.max_iterations = max_iterations
        self.target_papers = target_papers
        self.current_iteration = 0
        self.current_phase = "DISCOVERY"
        self.papers_analyzed = 0
        self.output_lines: list[str] = []
        self.max_output_lines = 10

        # Progress bars
        self.iteration_progress = Progress(
            SpinnerColumn(),
            TextColumn(f"[bold {SimpsonsColors.BLUE}]Iteration"),
            BarColumn(bar_width=20, complete_style=SimpsonsColors.PINK),
            MofNCompleteColumn(),
            TextColumn("[muted]|[/muted]"),
            TextColumn("{task.fields[phase]}"),
            TimeElapsedColumn(),
        )

        self.papers_progress = Progress(
            TextColumn(f"[bold {SimpsonsColors.BLUE}]Papers"),
            BarColumn(bar_width=20, complete_style=SimpsonsColors.PINK),
            MofNCompleteColumn(),
            TaskProgressColumn(),
        )

        self.iteration_task = self.iteration_progress.add_task(
            "Iterations",
            total=max_iterations,
            phase=self.current_phase,
        )

        self.papers_task = self.papers_progress.add_task(
            "Papers",
            total=target_papers,
        )

    def _make_layout(self) -> Table:
        """Create the layout for live display."""
        layout = Table.grid(expand=True)
        layout.add_row(self.iteration_progress)
        layout.add_row(self.papers_progress)
        layout.add_row("")  # Spacer

        # Output panel
        if self.output_lines:
            output_text = "\n".join(self.output_lines[-self.max_output_lines :])
            output_panel = Panel(
                output_text,
                title="[dim]Agent Output[/dim]",
                border_style=SimpsonsColors.BROWN,
                height=min(12, len(self.output_lines) + 2),
            )
            layout.add_row(output_panel)

        return layout

    def start(self) -> Live:
        """Start the live display and return the Live context."""
        return Live(self._make_layout(), console=console, refresh_per_second=4)

    def update_iteration(self, iteration: int, phase: str) -> None:
        """Update iteration progress."""
        self.current_iteration = iteration
        self.current_phase = phase

        # Style the phase
        phase_style = get_phase_style(phase)
        phase_text = f"[{phase_style}]{phase}[/{phase_style}]"

        self.iteration_progress.update(
            self.iteration_task,
            completed=iteration,
            phase=phase_text,
        )

    def update_papers(self, analyzed: int) -> None:
        """Update papers progress."""
        self.papers_analyzed = analyzed
        self.papers_progress.update(self.papers_task, completed=analyzed)

    def add_output(self, line: str) -> None:
        """Add a line of agent output."""
        # Clean up the line
        line = line.rstrip()
        if line:
            self.output_lines.append(line)
            # Keep only recent lines
            if len(self.output_lines) > 100:
                self.output_lines = self.output_lines[-50:]

    def get_layout(self) -> Table:
        """Get the current layout for Live.update()."""
        return self._make_layout()


class SimpleProgressDisplay:
    """
    Simpler progress display without live updating.

    Used when live_output is disabled.
    """

    def __init__(self):
        """Initialize simple display."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        )

    def start_iteration(self, iteration: int, max_iterations: int, phase: str) -> None:
        """Print iteration start message."""
        phase_style = get_phase_style(phase)
        console.print()
        console.print("=" * 60)
        console.print(
            f"  Iteration [bold]{iteration}[/bold] of {max_iterations} "
            f"| Phase: [{phase_style}]{phase}[/{phase_style}]"
        )
        console.print("=" * 60)

    def end_iteration(self, papers_delta: int) -> None:
        """Print iteration end message."""
        if papers_delta > 0:
            console.print(f"  [{SimpsonsColors.PINK}]+{papers_delta} paper(s) analyzed[/]")
