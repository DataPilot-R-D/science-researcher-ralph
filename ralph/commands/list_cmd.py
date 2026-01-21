"""List command - show all research projects."""

import json
from pathlib import Path

from ralph.config import list_research_projects
from ralph.ui.console import console, print_info
from ralph.ui.tables import create_project_table


def _infer_phase(rrd: dict, project_path: Path) -> str:
    """Infer phase from statistics when stored phase may be inconsistent."""
    stored_phase = rrd.get("phase", "DISCOVERY")
    stats = rrd.get("statistics", {})
    reqs = rrd.get("requirements", {})

    total_analyzed = stats.get("total_analyzed", 0)
    target = reqs.get("target_papers", 0)

    # If in IDEATION but product-ideas.json exists → should be COMPLETE
    if stored_phase == "IDEATION":
        product_ideas_path = project_path / "product-ideas.json"
        if product_ideas_path.exists() and total_analyzed >= target and target > 0:
            return "COMPLETE"

    return stored_phase


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
            "phase": _infer_phase(rrd, project_path),
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
