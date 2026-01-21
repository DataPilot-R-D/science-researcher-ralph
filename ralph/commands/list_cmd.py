"""List command - show all research projects."""

import json
from pathlib import Path
from typing import Optional

from ralph.config import list_research_projects
from ralph.ui.console import console, print_error, print_info
from ralph.ui.tables import create_project_table


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

    project_info: list[dict] = []

    for project_path in projects:
        rrd_path = project_path / "rrd.json"

        try:
            with open(rrd_path) as f:
                rrd_data = json.load(f)

            # Extract info
            phase = rrd_data.get("phase", "UNKNOWN")
            target = rrd_data.get("requirements", {}).get("target_papers", 0)
            analyzed = rrd_data.get("statistics", {}).get("total_analyzed", 0)

            # Count pending papers
            papers = rrd_data.get("papers_pool", [])
            pending = sum(1 for p in papers if p.get("status") in ("pending", "analyzing"))

            project_info.append(
                {
                    "name": project_path.name,
                    "path": project_path,
                    "phase": phase,
                    "target": target,
                    "analyzed": analyzed,
                    "pending": pending,
                }
            )
        except json.JSONDecodeError:
            project_info.append(
                {
                    "name": project_path.name,
                    "path": project_path,
                    "phase": "INVALID JSON",
                    "target": 0,
                    "analyzed": 0,
                    "pending": 0,
                }
            )
        except Exception as e:
            project_info.append(
                {
                    "name": project_path.name,
                    "path": project_path,
                    "phase": "ERROR",
                    "target": 0,
                    "analyzed": 0,
                    "pending": 0,
                }
            )

    # Display table
    table = create_project_table(project_info)
    console.print(table)
    console.print()

    return project_info
