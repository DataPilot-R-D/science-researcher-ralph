"""Tests for status command."""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from ralph.commands.status import show_status
from ralph.models.rrd import Phase


class TestShowStatus:
    """Tests for show_status function."""

    @patch("ralph.commands.status.create_status_panel")
    @patch("ralph.commands.status.RRDManager")
    @patch("ralph.commands.status.resolve_research_path")
    @patch("ralph.commands.status.console")
    def test_show_status_success(self, mock_console, mock_resolve, mock_manager_class, mock_create_panel, tmp_path):
        """Test successful status display."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "project": "Test Project",
            "phase": "ANALYSIS",
            "target_papers": 20,
            "pool_size": 20,
            "analyzed": 10,
            "presented": 5,
            "rejected": 3,
            "pending": 10,
            "analyzing": 0,
            "insights": 8,
            "completion_pct": 50.0,
        }

        mock_rrd = MagicMock()
        mock_rrd.timing.research_started_at = None
        mock_rrd.phase = "ANALYSIS"
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_create_panel.return_value = MagicMock()

        result = show_status("test-project")

        assert result is True
        mock_create_panel.assert_called_once()
        mock_console.print.assert_called()

    @patch("ralph.commands.status.resolve_research_path")
    @patch("ralph.commands.status.print_error")
    @patch("ralph.commands.status.console")
    def test_show_status_project_not_found(self, mock_console, mock_print_error, mock_resolve):
        """Test status for non-existent project."""
        mock_resolve.return_value = None

        result = show_status("nonexistent")

        assert result is False
        mock_print_error.assert_called()
        assert "not found" in str(mock_print_error.call_args)

    @patch("ralph.commands.status.RRDManager")
    @patch("ralph.commands.status.resolve_research_path")
    @patch("ralph.commands.status.print_error")
    @patch("ralph.commands.status.console")
    def test_show_status_invalid_rrd(self, mock_console, mock_print_error, mock_resolve, mock_manager_class, tmp_path):
        """Test status with invalid RRD file."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = ["Missing 'project' field", "Missing 'requirements'"]
        mock_manager_class.return_value = mock_manager

        result = show_status("test-project")

        assert result is False
        mock_print_error.assert_called_with("Invalid RRD file:")

    @patch("ralph.commands.status.create_status_panel")
    @patch("ralph.commands.status.RRDManager")
    @patch("ralph.commands.status.resolve_research_path")
    @patch("ralph.commands.status.console")
    def test_show_status_complete_phase(self, mock_console, mock_resolve, mock_manager_class, mock_create_panel, tmp_path):
        """Test status display for complete research."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "project": "Test Project",
            "phase": "COMPLETE",
            "target_papers": 20,
            "pool_size": 20,
            "analyzed": 20,
            "presented": 15,
            "rejected": 5,
            "pending": 0,
            "analyzing": 0,
            "insights": 25,
            "completion_pct": 100.0,
        }

        mock_rrd = MagicMock()
        mock_rrd.timing.research_started_at = None
        mock_rrd.phase = "COMPLETE"
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_create_panel.return_value = MagicMock()

        result = show_status("test-project")

        assert result is True
        # Check that "Research complete!" message is shown
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("complete" in call.lower() for call in print_calls)

    @patch("ralph.commands.status.create_status_panel")
    @patch("ralph.commands.status.RRDManager")
    @patch("ralph.commands.status.resolve_research_path")
    @patch("ralph.commands.status.console")
    def test_show_status_with_analyzing_papers(self, mock_console, mock_resolve, mock_manager_class, mock_create_panel, tmp_path):
        """Test status with papers stuck in analyzing state."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "project": "Test Project",
            "phase": "ANALYSIS",
            "target_papers": 20,
            "pool_size": 20,
            "analyzed": 10,
            "presented": 5,
            "rejected": 3,
            "pending": 8,
            "analyzing": 2,  # Papers stuck in analyzing
            "insights": 8,
            "completion_pct": 50.0,
        }

        mock_rrd = MagicMock()
        mock_rrd.timing.research_started_at = None
        mock_rrd.phase = "ANALYSIS"
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_create_panel.return_value = MagicMock()

        result = show_status("test-project")

        assert result is True
        # Check for warning about analyzing papers
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("analyzing" in call.lower() for call in print_calls)

    @patch("ralph.commands.status.create_status_panel")
    @patch("ralph.commands.status.RRDManager")
    @patch("ralph.commands.status.resolve_research_path")
    @patch("ralph.commands.status.console")
    def test_show_status_pool_less_than_target(self, mock_console, mock_resolve, mock_manager_class, mock_create_panel, tmp_path):
        """Test status when pool size is less than target."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "project": "Test Project",
            "phase": "ANALYSIS",
            "target_papers": 20,
            "pool_size": 15,  # Less than target
            "analyzed": 10,
            "presented": 5,
            "rejected": 3,
            "pending": 5,
            "analyzing": 0,
            "insights": 8,
            "completion_pct": 50.0,
        }

        mock_rrd = MagicMock()
        mock_rrd.timing.research_started_at = None
        mock_rrd.phase = "ANALYSIS"
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_create_panel.return_value = MagicMock()

        result = show_status("test-project")

        assert result is True
        # Check for warning about pool < target
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("DISCOVERY" in call for call in print_calls)

    @patch("ralph.commands.status.format_duration")
    @patch("ralph.commands.status.create_status_panel")
    @patch("ralph.commands.status.RRDManager")
    @patch("ralph.commands.status.resolve_research_path")
    @patch("ralph.commands.status.console")
    def test_show_status_with_timing(self, mock_console, mock_resolve, mock_manager_class, mock_create_panel, mock_format_duration, tmp_path):
        """Test status display with timing information."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "project": "Test Project",
            "phase": "ANALYSIS",
            "target_papers": 20,
            "pool_size": 20,
            "analyzed": 10,
            "presented": 5,
            "rejected": 3,
            "pending": 10,
            "analyzing": 0,
            "insights": 8,
            "completion_pct": 50.0,
        }

        mock_rrd = MagicMock()
        mock_rrd.timing.research_started_at = datetime.now(timezone.utc).isoformat()
        mock_rrd.timing.analysis.avg_seconds_per_paper = 120.5
        mock_rrd.phase = "ANALYSIS"
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 10
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_create_panel.return_value = MagicMock()
        mock_format_duration.return_value = "2m 0s"

        result = show_status("test-project")

        assert result is True
        # Check that timing info is displayed
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Timing" in call for call in print_calls)

    @patch("ralph.commands.status.create_status_panel")
    @patch("ralph.commands.status.RRDManager")
    @patch("ralph.commands.status.resolve_research_path")
    @patch("ralph.commands.status.console")
    def test_show_status_with_product_ideas(self, mock_console, mock_resolve, mock_manager_class, mock_create_panel, tmp_path):
        """Test status display when product-ideas.json exists."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        (project_path / "product-ideas.json").write_text("{}")

        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "project": "Test Project",
            "phase": "COMPLETE",
            "target_papers": 20,
            "pool_size": 20,
            "analyzed": 20,
            "presented": 15,
            "rejected": 5,
            "pending": 0,
            "analyzing": 0,
            "insights": 25,
            "completion_pct": 100.0,
        }

        mock_rrd = MagicMock()
        mock_rrd.timing.research_started_at = None
        mock_rrd.phase = "COMPLETE"
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_create_panel.return_value = MagicMock()

        result = show_status("test-project")

        assert result is True
        # Check that product-ideas.json is mentioned
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("product-ideas" in call for call in print_calls)
