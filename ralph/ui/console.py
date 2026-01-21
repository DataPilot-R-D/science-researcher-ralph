"""Shared Rich console instance."""

from rich.console import Console
from rich.theme import Theme


# Simpsons Color Palette
class SimpsonsColors:
    """The Simpsons inspired color palette for Research-Ralph."""

    BLUE = "#2f64d6"      # Headers, primary UI elements, borders
    YELLOW = "#f8db27"    # Warnings, discovery phase, banner, highlights
    BROWN = "#9c5b01"     # Analysis phase, secondary info
    WHITE = "#ffffff"     # Text on dark, clean elements
    PINK = "#ff81c1"      # Ideation phase, success, special highlights


# Custom theme for Research-Ralph using Simpsons colors
ralph_theme = Theme(
    {
        "info": SimpsonsColors.BLUE,
        "success": SimpsonsColors.PINK,
        "warning": SimpsonsColors.YELLOW,
        "error": f"bold {SimpsonsColors.BROWN}",
        "phase.discovery": SimpsonsColors.YELLOW,
        "phase.analysis": SimpsonsColors.BROWN,
        "phase.ideation": SimpsonsColors.PINK,
        "phase.complete": SimpsonsColors.PINK,
        "header": f"bold {SimpsonsColors.BLUE}",
        "muted": "dim",
        "highlight": f"bold {SimpsonsColors.YELLOW}",
        "primary": SimpsonsColors.BLUE,
        "secondary": SimpsonsColors.BROWN,
        "accent": SimpsonsColors.PINK,
    }
)

# Main console for output
console = Console(theme=ralph_theme)

# Error console (writes to stderr)
error_console = Console(theme=ralph_theme, stderr=True)


def print_header(title: str, subtitle: str = "") -> None:
    """Print a styled header."""
    console.print()
    console.print(f"[header]{title}[/header]")
    if subtitle:
        console.print(f"[muted]{subtitle}[/muted]")
    console.print()


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[success]{message}[/success]")


def print_error(message: str) -> None:
    """Print an error message."""
    error_console.print(f"[error]{message}[/error]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[warning]{message}[/warning]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[info]{message}[/info]")


def get_phase_style(phase: str) -> str:
    """Get the style for a phase."""
    phase_styles = {
        "DISCOVERY": "phase.discovery",
        "ANALYSIS": "phase.analysis",
        "IDEATION": "phase.ideation",
        "COMPLETE": "phase.complete",
    }
    return phase_styles.get(phase.upper(), "muted")
