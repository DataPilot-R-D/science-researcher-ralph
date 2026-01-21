"""Tests for reset command."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ralph.commands.reset import reset_project


class TestResetProject:
    """Tests for reset_project function."""

    @patch("ralph.commands.reset.RRDManager")
    @patch("ralph.commands.reset.resolve_research_path")
    @patch("ralph.commands.reset.print_success")
    @patch("ralph.commands.reset.console")
    def test_reset_project_no_confirm(self, mock_console, mock_print_success, mock_resolve, mock_manager_class, tmp_path):
        """Test reset project without confirmation (CLI mode)."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.exists = True
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "phase": "ANALYSIS",
            "analyzed": 10,
            "pool_size": 20,
            "insights": 5,
        }
        backup_path = project_path / "rrd.backup.test.json"
        mock_manager.reset.return_value = backup_path
        mock_manager_class.return_value = mock_manager

        result = reset_project("test-project", confirm=False)

        assert result is True
        mock_manager.reset.assert_called_once()
        mock_print_success.assert_called()

    @patch("ralph.commands.reset.resolve_research_path")
    @patch("ralph.commands.reset.print_error")
    @patch("ralph.commands.reset.console")
    def test_reset_project_not_found(self, mock_console, mock_print_error, mock_resolve):
        """Test reset for non-existent project."""
        mock_resolve.return_value = None

        result = reset_project("nonexistent")

        assert result is False
        mock_print_error.assert_called()
        assert "not found" in str(mock_print_error.call_args)

    @patch("ralph.commands.reset.RRDManager")
    @patch("ralph.commands.reset.resolve_research_path")
    @patch("ralph.commands.reset.print_error")
    @patch("ralph.commands.reset.console")
    def test_reset_project_no_rrd_file(self, mock_console, mock_print_error, mock_resolve, mock_manager_class, tmp_path):
        """Test reset when rrd.json doesn't exist."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.exists = False
        mock_manager_class.return_value = mock_manager

        result = reset_project("test-project", confirm=False)

        assert result is False
        mock_print_error.assert_called()
        assert "rrd.json not found" in str(mock_print_error.call_args)

    @patch("questionary.confirm")
    @patch("ralph.commands.reset.RRDManager")
    @patch("ralph.commands.reset.resolve_research_path")
    @patch("ralph.commands.reset.print_info")
    @patch("ralph.commands.reset.console")
    def test_reset_project_user_cancels(
        self, mock_console, mock_print_info, mock_resolve, mock_manager_class, mock_confirm, tmp_path
    ):
        """Test reset when user cancels confirmation."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.exists = True
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "phase": "ANALYSIS",
            "analyzed": 10,
            "pool_size": 20,
            "insights": 5,
        }
        mock_manager_class.return_value = mock_manager

        mock_confirm.return_value.ask.return_value = False

        result = reset_project("test-project", confirm=True)

        assert result is False
        mock_print_info.assert_called_with("Reset cancelled")
        mock_manager.reset.assert_not_called()

    @patch("questionary.confirm")
    @patch("ralph.commands.reset.RRDManager")
    @patch("ralph.commands.reset.resolve_research_path")
    @patch("ralph.commands.reset.print_success")
    @patch("ralph.commands.reset.console")
    def test_reset_project_user_confirms(
        self, mock_console, mock_print_success, mock_resolve, mock_manager_class, mock_confirm, tmp_path
    ):
        """Test reset when user confirms."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.exists = True
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "phase": "ANALYSIS",
            "analyzed": 10,
            "pool_size": 20,
            "insights": 5,
        }
        backup_path = project_path / "rrd.backup.test.json"
        mock_manager.reset.return_value = backup_path
        mock_manager_class.return_value = mock_manager

        mock_confirm.return_value.ask.return_value = True

        result = reset_project("test-project", confirm=True)

        assert result is True
        mock_manager.reset.assert_called_once()

    @patch("ralph.commands.reset.RRDManager")
    @patch("ralph.commands.reset.resolve_research_path")
    @patch("ralph.commands.reset.console")
    def test_reset_project_with_validation_warnings(
        self, mock_console, mock_resolve, mock_manager_class, tmp_path
    ):
        """Test reset with validation warnings (proceeds anyway)."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.exists = True
        mock_manager.validate.return_value = ["Missing optional field"]
        mock_manager.get_summary.return_value = {
            "phase": "DISCOVERY",
            "analyzed": 0,
            "pool_size": 0,
            "insights": 0,
        }
        backup_path = project_path / "rrd.backup.test.json"
        mock_manager.reset.return_value = backup_path
        mock_manager_class.return_value = mock_manager

        result = reset_project("test-project", confirm=False)

        assert result is True
        # Warning should be printed
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Warning" in call for call in print_calls)

    @patch("ralph.commands.reset.RRDManager")
    @patch("ralph.commands.reset.resolve_research_path")
    @patch("ralph.commands.reset.print_error")
    @patch("ralph.commands.reset.console")
    def test_reset_project_reset_fails(self, mock_console, mock_print_error, mock_resolve, mock_manager_class, tmp_path):
        """Test reset when reset operation fails."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.exists = True
        mock_manager.validate.return_value = []
        mock_manager.get_summary.return_value = {
            "phase": "ANALYSIS",
            "analyzed": 10,
            "pool_size": 20,
            "insights": 5,
        }
        mock_manager.reset.side_effect = Exception("Disk full")
        mock_manager_class.return_value = mock_manager

        result = reset_project("test-project", confirm=False)

        assert result is False
        mock_print_error.assert_called()
        assert "Unexpected error" in str(mock_print_error.call_args)

    @patch("ralph.commands.reset.RRDManager")
    @patch("ralph.commands.reset.resolve_research_path")
    @patch("ralph.commands.reset.console")
    def test_reset_project_get_summary_fails(self, mock_console, mock_resolve, mock_manager_class, tmp_path):
        """Test reset when get_summary fails (still proceeds)."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.exists = True
        mock_manager.validate.return_value = []
        mock_manager.get_summary.side_effect = ValueError("Invalid RRD structure")
        backup_path = project_path / "rrd.backup.test.json"
        mock_manager.reset.return_value = backup_path
        mock_manager_class.return_value = mock_manager

        result = reset_project("test-project", confirm=False)

        # Should still succeed despite summary failure
        assert result is True
        mock_manager.reset.assert_called_once()
