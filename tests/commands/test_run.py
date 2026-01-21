"""Tests for run command."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ralph.commands.run import run_research
from ralph.config import Agent
from ralph.models.rrd import Phase
from ralph.core.research_loop import LoopResult


class TestRunResearch:
    """Tests for run_research function."""

    @patch("ralph.commands.run.ResearchLoop")
    @patch("ralph.commands.run.RRDManager")
    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.load_config")
    @patch("ralph.commands.run.console")
    def test_run_research_success(
        self, mock_console, mock_load_config, mock_resolve, mock_manager_class, mock_loop_class, tmp_path
    ):
        """Test successful research run."""
        # Setup config
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        # Setup path resolution
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        # Setup RRD manager
        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.DISCOVERY
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 0
        mock_manager.load.return_value = mock_rrd
        mock_manager.get_summary.return_value = {
            "project": "Test",
            "phase": "COMPLETE",
            "target_papers": 20,
            "analyzed": 20,
        }
        mock_manager_class.return_value = mock_manager

        # Setup research loop
        mock_loop = MagicMock()
        mock_loop.run.return_value = LoopResult(
            completed=True,
            iterations_run=20,
            final_phase="COMPLETE",
            total_analyzed=20,
            total_presented=15,
            total_insights=25,
            error_message=None,
        )
        mock_loop_class.return_value = mock_loop

        result = run_research("test-project")

        assert result is True
        mock_loop.run.assert_called_once()

    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.print_error")
    @patch("ralph.commands.run.console")
    def test_run_research_project_not_found(self, mock_console, mock_print_error, mock_resolve):
        """Test run with non-existent project."""
        mock_resolve.return_value = None

        result = run_research("nonexistent")

        assert result is False
        mock_print_error.assert_called()
        assert "not found" in str(mock_print_error.call_args)

    @patch("ralph.commands.run.RRDManager")
    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.print_error")
    @patch("ralph.commands.run.console")
    def test_run_research_invalid_rrd(self, mock_console, mock_print_error, mock_resolve, mock_manager_class, tmp_path):
        """Test run with invalid RRD file."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = ["Missing 'project' field"]
        mock_manager_class.return_value = mock_manager

        result = run_research("test-project")

        assert result is False
        mock_print_error.assert_called_with("Invalid RRD file:")

    @patch("ralph.commands.run.RRDManager")
    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.print_error")
    @patch("ralph.commands.run.console")
    def test_run_research_invalid_agent(self, mock_console, mock_print_error, mock_resolve, mock_manager_class, tmp_path):
        """Test run with invalid agent."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager.update_target_papers.return_value = True
        mock_manager_class.return_value = mock_manager

        result = run_research("test-project", agent="invalid")

        assert result is False
        mock_print_error.assert_called()
        assert "Invalid agent" in str(mock_print_error.call_args)

    @patch("ralph.commands.run.RRDManager")
    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.print_error")
    @patch("ralph.commands.run.console")
    def test_run_research_cannot_update_papers(
        self, mock_console, mock_print_error, mock_resolve, mock_manager_class, tmp_path
    ):
        """Test run when papers update blocked."""
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager.update_target_papers.return_value = False
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.ANALYSIS
        mock_rrd.statistics.total_analyzed = 5
        mock_rrd.requirements.target_papers = 20
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        result = run_research("test-project", papers=30)

        assert result is False
        mock_print_error.assert_called()
        assert "Cannot change target_papers" in str(mock_print_error.call_args)

    @patch("ralph.commands.run.RRDManager")
    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.load_config")
    @patch("ralph.commands.run.print_success")
    @patch("ralph.commands.run.console")
    def test_run_research_already_complete(
        self, mock_console, mock_print_success, mock_load_config, mock_resolve, mock_manager_class, tmp_path
    ):
        """Test run when research already complete."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.COMPLETE
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 20
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        result = run_research("test-project")

        assert result is True
        mock_print_success.assert_called_with("Research already complete!")

    @patch("ralph.commands.run.ResearchLoop")
    @patch("ralph.commands.run.RRDManager")
    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.load_config")
    @patch("ralph.commands.run.print_warning")
    @patch("ralph.commands.run.console")
    def test_run_research_did_not_complete(
        self, mock_console, mock_print_warning, mock_load_config, mock_resolve, mock_manager_class, mock_loop_class, tmp_path
    ):
        """Test run when research does not complete."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.DISCOVERY
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 0
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_loop = MagicMock()
        mock_loop.run.return_value = LoopResult(
            completed=False,
            iterations_run=26,
            final_phase="ANALYSIS",
            total_analyzed=15,
            total_presented=10,
            total_insights=20,
            error_message="Max iterations reached",
        )
        mock_loop_class.return_value = mock_loop

        result = run_research("test-project")

        assert result is False
        mock_print_warning.assert_called()

    @patch("ralph.commands.run.ResearchLoop")
    @patch("ralph.commands.run.RRDManager")
    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.load_config")
    @patch("ralph.commands.run.console")
    def test_run_research_with_custom_iterations(
        self, mock_console, mock_load_config, mock_resolve, mock_manager_class, mock_loop_class, tmp_path
    ):
        """Test run with custom iterations."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.DISCOVERY
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 0
        mock_manager.load.return_value = mock_rrd
        mock_manager.get_summary.return_value = {"project": "Test"}
        mock_manager_class.return_value = mock_manager

        mock_loop = MagicMock()
        mock_loop.run.return_value = LoopResult(
            completed=True,
            iterations_run=50,
            final_phase="COMPLETE",
            total_analyzed=20,
            total_presented=15,
            total_insights=25,
        )
        mock_loop_class.return_value = mock_loop

        result = run_research("test-project", iterations=50)

        assert result is True
        # Check that loop was created with custom iterations
        call_kwargs = mock_loop_class.call_args[1]
        assert call_kwargs["max_iterations"] == 50

    @patch("ralph.commands.run.LiveResearchDisplay")
    @patch("ralph.commands.run.ResearchLoop")
    @patch("ralph.commands.run.RRDManager")
    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.load_config")
    @patch("ralph.commands.run.console")
    def test_run_research_with_live_output(
        self, mock_console, mock_load_config, mock_resolve, mock_manager_class, mock_loop_class, mock_live_display, tmp_path
    ):
        """Test run with live output enabled."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.live_output = True
        mock_load_config.return_value = mock_config

        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.DISCOVERY
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 0
        mock_manager.load.return_value = mock_rrd
        mock_manager.get_summary.return_value = {"project": "Test"}
        mock_manager_class.return_value = mock_manager

        mock_display = MagicMock()
        mock_live = MagicMock()
        mock_display.start.return_value.__enter__ = MagicMock(return_value=mock_live)
        mock_display.start.return_value.__exit__ = MagicMock(return_value=False)
        mock_live_display.return_value = mock_display

        mock_loop = MagicMock()
        mock_loop.run.return_value = LoopResult(
            completed=True,
            iterations_run=20,
            final_phase="COMPLETE",
            total_analyzed=20,
            total_presented=15,
            total_insights=25,
        )
        mock_loop_class.return_value = mock_loop

        result = run_research("test-project")

        assert result is True
        mock_live_display.assert_called_once()

    @patch("ralph.commands.run.ResearchLoop")
    @patch("ralph.commands.run.RRDManager")
    @patch("ralph.commands.run.resolve_research_path")
    @patch("ralph.commands.run.load_config")
    @patch("ralph.commands.run.console")
    def test_run_research_force_update_papers(
        self, mock_console, mock_load_config, mock_resolve, mock_manager_class, mock_loop_class, tmp_path
    ):
        """Test run with force update of papers."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_resolve.return_value = project_path

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager.update_target_papers.return_value = True
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.DISCOVERY
        mock_rrd.requirements.target_papers = 30
        mock_rrd.statistics.total_analyzed = 0
        mock_manager.load.return_value = mock_rrd
        mock_manager.get_summary.return_value = {"project": "Test"}
        mock_manager_class.return_value = mock_manager

        mock_loop = MagicMock()
        mock_loop.run.return_value = LoopResult(
            completed=True, iterations_run=36, final_phase="COMPLETE",
            total_analyzed=30, total_presented=20, total_insights=35
        )
        mock_loop_class.return_value = mock_loop

        result = run_research("test-project", papers=30, force=True)

        assert result is True
        mock_manager.update_target_papers.assert_called_once_with(30, force=True)
