"""Tests for list command."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ralph.commands.list_cmd import list_projects


class TestListProjects:
    """Tests for list_projects function."""

    @patch("ralph.commands.list_cmd.create_project_table")
    @patch("ralph.commands.list_cmd.list_research_projects")
    @patch("ralph.commands.list_cmd.console")
    def test_list_projects_success(self, mock_console, mock_list_research, mock_create_table, tmp_path):
        """Test successful project listing."""
        # Setup projects
        project1 = tmp_path / "project-1"
        project1.mkdir()
        rrd1 = project1 / "rrd.json"
        rrd1.write_text(json.dumps({
            "phase": "ANALYSIS",
            "requirements": {"target_papers": 20},
            "statistics": {"total_analyzed": 10},
            "papers_pool": [
                {"status": "pending"},
                {"status": "analyzing"},
                {"status": "presented"},
            ],
        }))

        project2 = tmp_path / "project-2"
        project2.mkdir()
        rrd2 = project2 / "rrd.json"
        rrd2.write_text(json.dumps({
            "phase": "COMPLETE",
            "requirements": {"target_papers": 15},
            "statistics": {"total_analyzed": 15},
            "papers_pool": [],
        }))

        mock_list_research.return_value = [project1, project2]
        mock_create_table.return_value = MagicMock()

        result = list_projects()

        assert len(result) == 2
        assert result[0]["name"] == "project-1"
        assert result[0]["phase"] == "ANALYSIS"
        assert result[0]["analyzed"] == 10
        assert result[0]["pending"] == 2  # pending + analyzing
        assert result[1]["name"] == "project-2"
        assert result[1]["phase"] == "COMPLETE"
        mock_create_table.assert_called_once()

    @patch("ralph.commands.list_cmd.list_research_projects")
    @patch("ralph.commands.list_cmd.print_info")
    @patch("ralph.commands.list_cmd.console")
    def test_list_projects_empty(self, mock_console, mock_print_info, mock_list_research):
        """Test listing when no projects exist."""
        mock_list_research.return_value = []

        result = list_projects()

        assert result == []
        mock_print_info.assert_called_with("No research projects found.")

    @patch("ralph.commands.list_cmd.create_project_table")
    @patch("ralph.commands.list_cmd.list_research_projects")
    @patch("ralph.commands.list_cmd.console")
    def test_list_projects_invalid_json(self, mock_console, mock_list_research, mock_create_table, tmp_path):
        """Test listing with invalid JSON file."""
        project = tmp_path / "bad-project"
        project.mkdir()
        (project / "rrd.json").write_text("{invalid json")

        mock_list_research.return_value = [project]
        mock_create_table.return_value = MagicMock()

        result = list_projects()

        assert len(result) == 1
        assert result[0]["phase"] == "INVALID JSON"
        assert result[0]["target"] == 0

    @patch("ralph.commands.list_cmd.create_project_table")
    @patch("ralph.commands.list_cmd.list_research_projects")
    @patch("ralph.commands.list_cmd.console")
    def test_list_projects_error_reading(self, mock_console, mock_list_research, mock_create_table, tmp_path):
        """Test listing with error reading file."""
        project = tmp_path / "error-project"
        project.mkdir()
        # No rrd.json file - will cause FileNotFoundError

        mock_list_research.return_value = [project]
        mock_create_table.return_value = MagicMock()

        result = list_projects()

        assert len(result) == 1
        assert result[0]["phase"] == "NO RRD"  # FileNotFoundError case
        assert result[0]["target"] == 0

    @patch("ralph.commands.list_cmd.create_project_table")
    @patch("ralph.commands.list_cmd.list_research_projects")
    @patch("ralph.commands.list_cmd.console")
    def test_list_projects_missing_fields(self, mock_console, mock_list_research, mock_create_table, tmp_path):
        """Test listing with missing fields in RRD."""
        project = tmp_path / "partial-project"
        project.mkdir()
        (project / "rrd.json").write_text(json.dumps({
            "phase": "DISCOVERY",
            # Missing requirements and statistics
        }))

        mock_list_research.return_value = [project]
        mock_create_table.return_value = MagicMock()

        result = list_projects()

        assert len(result) == 1
        assert result[0]["phase"] == "DISCOVERY"
        assert result[0]["target"] == 0
        assert result[0]["analyzed"] == 0
        assert result[0]["pending"] == 0

    @patch("ralph.commands.list_cmd.create_project_table")
    @patch("ralph.commands.list_cmd.list_research_projects")
    @patch("ralph.commands.list_cmd.console")
    def test_list_projects_counts_pending_statuses(self, mock_console, mock_list_research, mock_create_table, tmp_path):
        """Test that pending count includes 'pending' and 'analyzing' status."""
        project = tmp_path / "test-project"
        project.mkdir()
        (project / "rrd.json").write_text(json.dumps({
            "phase": "ANALYSIS",
            "requirements": {"target_papers": 20},
            "statistics": {"total_analyzed": 5},
            "papers_pool": [
                {"status": "pending"},
                {"status": "pending"},
                {"status": "pending"},
                {"status": "analyzing"},
                {"status": "analyzing"},
                {"status": "presented"},
                {"status": "rejected"},
            ],
        }))

        mock_list_research.return_value = [project]
        mock_create_table.return_value = MagicMock()

        result = list_projects()

        assert len(result) == 1
        assert result[0]["pending"] == 5  # 3 pending + 2 analyzing

    @patch("ralph.commands.list_cmd.create_project_table")
    @patch("ralph.commands.list_cmd.list_research_projects")
    @patch("ralph.commands.list_cmd.console")
    def test_list_projects_multiple_projects(self, mock_console, mock_list_research, mock_create_table, tmp_path):
        """Test listing multiple projects with different states."""
        projects = []
        for i, (phase, analyzed, target) in enumerate([
            ("DISCOVERY", 0, 20),
            ("ANALYSIS", 10, 20),
            ("IDEATION", 20, 20),
            ("COMPLETE", 20, 20),
        ]):
            project = tmp_path / f"project-{i}"
            project.mkdir()
            (project / "rrd.json").write_text(json.dumps({
                "phase": phase,
                "requirements": {"target_papers": target},
                "statistics": {"total_analyzed": analyzed},
                "papers_pool": [],
            }))
            projects.append(project)

        mock_list_research.return_value = projects
        mock_create_table.return_value = MagicMock()

        result = list_projects()

        assert len(result) == 4
        assert result[0]["phase"] == "DISCOVERY"
        assert result[1]["phase"] == "ANALYSIS"
        assert result[2]["phase"] == "IDEATION"
        assert result[3]["phase"] == "COMPLETE"
