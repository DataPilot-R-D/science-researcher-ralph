"""List command - show all research projects."""

import json
from pathlib import Path

from ralph.config import list_research_projects
from ralph.ui.console import console, print_info
from ralph.ui.tables import create_project_table


def _get_project_info(project_path: Path) -> dict:
    """Extract project info from a project path."""
    base_info = {
        "name": project_path.name,
        "path": project_path,
        "phase": "ERROR",
        "target": 0,
        "analyzed": 0,
        "pending": 0,
    }

    try:
        with open(project_path / "rrd.json") as f:
            rrd = json.load(f)

        papers = rrd.get("papers_pool", [])
        return {
            **base_info,
            "phase": rrd.get("phase", "UNKNOWN"),
            "target": rrd.get("requirements", {}).get("target_papers", 0),
            "analyzed": rrd.get("statistics", {}).get("total_analyzed", 0),
            "pending": sum(1 for p in papers if p.get("status") in ("pending", "analyzing")),
        }
    except json.JSONDecodeError:
        return {**base_info, "phase": "INVALID JSON"}
    except PermissionError:
        return {**base_info, "phase": "NO ACCESS"}
    except FileNotFoundError:
        return {**base_info, "phase": "NO RRD"}
    except Exception as e:
        return {**base_info, "phase": f"ERR:{type(e).__name__}"}


def list_projects() -> list[dict]:
    """
    List all research projects with their status.

    Returns:
        List of project info dicts
    """
    projects = list_research_projects()

    if not projects:
        print_info("No research projects found.")
        console.print()
        console.print("Create one with: [bold]research-ralph --new \"Your topic\"[/bold]")
        return []

    project_info = [_get_project_info(p) for p in projects]

    table = create_project_table(project_info)
    console.print(table)
    console.print()

    return project_info
