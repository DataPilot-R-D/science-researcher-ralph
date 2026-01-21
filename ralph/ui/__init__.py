"""UI components for Research-Ralph using Rich."""

from ralph.ui.console import console, error_console
from ralph.ui.progress import create_progress, create_spinner
from ralph.ui.tables import create_project_table, create_status_panel

__all__ = [
    "console",
    "error_console",
    "create_progress",
    "create_spinner",
    "create_project_table",
    "create_status_panel",
]
