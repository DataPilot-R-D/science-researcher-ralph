"""Tests for ResearchLoop class."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ralph.config import Agent
from ralph.models.rrd import Phase
from ralph.core.research_loop import (
    ResearchLoop,
    IterationResult,
    LoopResult,
)
from ralph.core.agent_runner import AgentResult, ErrorType


class TestIterationResult:
    """Tests for IterationResult dataclass."""

    def test_basic_creation(self):
        """Test basic IterationResult creation."""
        agent_result = AgentResult(output="Success", exit_code=0, success=True)
        result = IterationResult(
            iteration=1,
            success=True,
            agent_result=agent_result,
            phase=Phase.DISCOVERY,
        )

        assert result.iteration == 1
        assert result.success is True
        assert result.phase == Phase.DISCOVERY
        assert result.papers_delta == 0
        assert result.should_continue is True
        assert result.is_complete is False

    def test_with_papers_delta(self):
        """Test IterationResult with papers delta."""
        agent_result = AgentResult(output="Success", exit_code=0, success=True)
        result = IterationResult(
            iteration=5,
            success=True,
            agent_result=agent_result,
            phase=Phase.ANALYSIS,
            papers_delta=3,
        )

        assert result.papers_delta == 3

    def test_complete_result(self):
        """Test IterationResult marked as complete."""
        agent_result = AgentResult(output="<promise>COMPLETE</promise>", exit_code=0, success=True)
        result = IterationResult(
            iteration=20,
            success=True,
            agent_result=agent_result,
            phase=Phase.COMPLETE,
            is_complete=True,
            should_continue=False,
        )

        assert result.is_complete is True
        assert result.should_continue is False

    def test_failure_result(self):
        """Test IterationResult for failure."""
        agent_result = AgentResult(output="Error", exit_code=1, success=False)
        result = IterationResult(
            iteration=3,
            success=False,
            agent_result=agent_result,
            phase=Phase.DISCOVERY,
            error_message="Rate limit exceeded",
        )

        assert result.success is False
        assert result.error_message is not None


class TestLoopResult:
    """Tests for LoopResult dataclass."""

    def test_successful_completion(self):
        """Test successful LoopResult."""
        result = LoopResult(
            completed=True,
            iterations_run=25,
            final_phase=Phase.COMPLETE,
            total_analyzed=20,
            total_presented=15,
            total_insights=30,
        )

        assert result.completed is True
        assert result.iterations_run == 25
        assert result.final_phase == Phase.COMPLETE
        assert result.error_message is None

    def test_incomplete_result(self):
        """Test incomplete LoopResult."""
        result = LoopResult(
            completed=False,
            iterations_run=26,
            final_phase=Phase.ANALYSIS,
            total_analyzed=15,
            total_presented=10,
            total_insights=20,
            error_message="Max iterations reached",
        )

        assert result.completed is False
        assert result.error_message == "Max iterations reached"


class TestResearchLoopInit:
    """Tests for ResearchLoop initialization."""

    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_init_with_defaults(self, mock_manager_class, mock_load_config, tmp_path):
        """Test initialization with default values."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_rrd = MagicMock()
        mock_rrd.requirements.target_papers = 20
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        loop = ResearchLoop(project_path=tmp_path)

        assert loop.project_path == tmp_path
        assert loop.agent == Agent.CLAUDE
        assert loop.max_iterations == 26  # 20 + 6

    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_init_with_custom_values(self, mock_manager_class, mock_load_config, tmp_path):
        """Test initialization with custom values."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager_class.return_value = MagicMock()

        loop = ResearchLoop(
            project_path=tmp_path,
            agent=Agent.AMP,
            max_iterations=50,
        )

        assert loop.agent == Agent.AMP
        assert loop.max_iterations == 50

    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_init_with_callbacks(self, mock_manager_class, mock_load_config, tmp_path):
        """Test initialization with callbacks."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager_class.return_value = MagicMock()

        on_start = MagicMock()
        on_end = MagicMock()
        on_output = MagicMock()

        loop = ResearchLoop(
            project_path=tmp_path,
            max_iterations=10,
            on_iteration_start=on_start,
            on_iteration_end=on_end,
            on_output=on_output,
        )

        assert loop.on_iteration_start == on_start
        assert loop.on_iteration_end == on_end
        assert loop.on_output == on_output


class TestResearchLoopValidate:
    """Tests for ResearchLoop.validate method."""

    @patch("ralph.core.research_loop.AgentRunner")
    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_validate_success(self, mock_manager_class, mock_load_config, mock_runner_class, tmp_path):
        """Test successful validation."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager_class.return_value = mock_manager

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_runner_class.return_value = mock_runner

        # Create prompt.md
        (tmp_path / "prompt.md").write_text("Test prompt")

        loop = ResearchLoop(project_path=tmp_path, max_iterations=10)
        errors = loop.validate()

        assert errors == []

    @patch("ralph.core.research_loop.AgentRunner")
    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_validate_rrd_errors(self, mock_manager_class, mock_load_config, mock_runner_class, tmp_path):
        """Test validation with RRD errors."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.validate.return_value = ["Missing 'project' field"]
        mock_manager_class.return_value = mock_manager

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_runner_class.return_value = mock_runner

        loop = ResearchLoop(project_path=tmp_path, max_iterations=10)
        errors = loop.validate()

        assert "Missing 'project' field" in errors

    @patch("ralph.core.research_loop.AgentRunner")
    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_validate_agent_not_available(self, mock_manager_class, mock_load_config, mock_runner_class, tmp_path):
        """Test validation when agent not available."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_manager_class.return_value = mock_manager

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = False
        mock_runner.get_install_instructions.return_value = "Install claude"
        mock_runner_class.return_value = mock_runner

        loop = ResearchLoop(project_path=tmp_path, max_iterations=10)
        errors = loop.validate()

        assert any("not found" in e for e in errors)


class TestResearchLoopRun:
    """Tests for ResearchLoop.run method."""

    @patch("ralph.core.research_loop.AgentRunner")
    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_run_validation_fails(self, mock_manager_class, mock_load_config, mock_runner_class, tmp_path):
        """Test run when validation fails."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.validate.return_value = ["Critical error"]
        mock_manager_class.return_value = mock_manager

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_runner_class.return_value = mock_runner

        loop = ResearchLoop(project_path=tmp_path, max_iterations=10)
        result = loop.run()

        assert result.completed is False
        assert "Critical error" in result.error_message

    @patch("ralph.core.research_loop.time")
    @patch("ralph.core.research_loop.AgentRunner")
    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_run_completes_on_signal(self, mock_manager_class, mock_load_config, mock_runner_class, mock_time, tmp_path):
        """Test run completes on COMPLETE signal."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.COMPLETE
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 20
        mock_rrd.statistics.total_presented = 15
        mock_rrd.statistics.total_insights_extracted = 25
        mock_rrd.papers_pool = []
        mock_rrd.pending_papers = []
        mock_rrd.analyzing_papers = []
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_runner.run.return_value = AgentResult(
            output="<promise>COMPLETE</promise>",
            exit_code=0,
            success=True,
        )
        mock_runner_class.return_value = mock_runner

        # Create prompt.md
        (tmp_path / "prompt.md").write_text("Test")

        loop = ResearchLoop(project_path=tmp_path, max_iterations=30)
        result = loop.run()

        assert result.completed is True
        assert result.final_phase == Phase.COMPLETE

    @patch("ralph.core.research_loop.time")
    @patch("ralph.core.research_loop.AgentRunner")
    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_run_max_iterations(self, mock_manager_class, mock_load_config, mock_runner_class, mock_time, tmp_path):
        """Test run stops at max iterations."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.ANALYSIS
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 10
        mock_rrd.statistics.total_presented = 5
        mock_rrd.statistics.total_insights_extracted = 10
        mock_rrd.papers_pool = [MagicMock(status="pending")] * 10
        mock_rrd.pending_papers = [MagicMock()] * 10
        mock_rrd.analyzing_papers = []
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_runner.run.return_value = AgentResult(output="Still working", exit_code=0, success=True)
        mock_runner_class.return_value = mock_runner

        (tmp_path / "prompt.md").write_text("Test")

        loop = ResearchLoop(project_path=tmp_path, max_iterations=3)
        result = loop.run()

        assert result.completed is False
        assert result.iterations_run == 3
        assert "Max iterations" in result.error_message

    @patch("ralph.core.research_loop.time")
    @patch("ralph.core.research_loop.AgentRunner")
    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_run_consecutive_failures(self, mock_manager_class, mock_load_config, mock_runner_class, mock_time, tmp_path):
        """Test run stops on too many consecutive failures."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.DISCOVERY
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 0
        mock_rrd.statistics.total_presented = 0
        mock_rrd.statistics.total_insights_extracted = 0
        mock_rrd.papers_pool = []
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_runner.run.return_value = AgentResult(
            output="Rate limit exceeded",
            exit_code=1,
            success=False,
            error_type="rate_limit",
        )
        mock_runner_class.return_value = mock_runner

        (tmp_path / "prompt.md").write_text("Test")

        loop = ResearchLoop(project_path=tmp_path, max_iterations=10)
        result = loop.run()

        assert result.completed is False
        assert "consecutive failures" in result.error_message.lower()


class TestResearchLoopCallbacks:
    """Tests for ResearchLoop callbacks."""

    @patch("ralph.core.research_loop.time")
    @patch("ralph.core.research_loop.AgentRunner")
    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_callbacks_called(self, mock_manager_class, mock_load_config, mock_runner_class, mock_time, tmp_path):
        """Test callbacks are invoked."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.COMPLETE
        mock_rrd.requirements.target_papers = 1
        mock_rrd.statistics.total_analyzed = 1
        mock_rrd.statistics.total_presented = 1
        mock_rrd.statistics.total_insights_extracted = 1
        mock_rrd.papers_pool = []
        mock_rrd.pending_papers = []
        mock_rrd.analyzing_papers = []
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_runner.run.return_value = AgentResult(
            output="<promise>COMPLETE</promise>",
            exit_code=0,
            success=True,
        )
        mock_runner_class.return_value = mock_runner

        (tmp_path / "prompt.md").write_text("Test")

        on_start = MagicMock()
        on_end = MagicMock()

        loop = ResearchLoop(
            project_path=tmp_path,
            max_iterations=5,
            on_iteration_start=on_start,
            on_iteration_end=on_end,
        )
        loop.run()

        on_start.assert_called()
        on_end.assert_called()


class TestEnsureValidPhase:
    """Tests for ResearchLoop._ensure_valid_phase method."""

    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_ensure_valid_phase_reverts_analysis_if_insufficient_papers(
        self, mock_manager_class, mock_load_config, tmp_path
    ):
        """Test phase reverts to DISCOVERY if papers < target."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_rrd = MagicMock()
        # Phase is ANALYSIS but not enough papers
        mock_rrd.phase = Phase.ANALYSIS
        mock_rrd.requirements.target_papers = 20
        mock_rrd.papers_pool = [MagicMock()] * 10  # Only 10 papers, need 20
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        loop = ResearchLoop(project_path=tmp_path, max_iterations=10)
        phase = loop._ensure_valid_phase()

        # Should revert to DISCOVERY
        assert phase == Phase.DISCOVERY
        assert mock_rrd.phase == Phase.DISCOVERY
        mock_manager.save.assert_called_once()

    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_ensure_valid_phase_keeps_analysis_if_sufficient_papers(
        self, mock_manager_class, mock_load_config, tmp_path
    ):
        """Test phase stays ANALYSIS if papers >= target."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_rrd = MagicMock()
        # Phase is ANALYSIS with enough papers
        mock_rrd.phase = Phase.ANALYSIS
        mock_rrd.requirements.target_papers = 20
        mock_rrd.papers_pool = [MagicMock()] * 20  # Exactly 20 papers
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        loop = ResearchLoop(project_path=tmp_path, max_iterations=10)
        phase = loop._ensure_valid_phase()

        # Should keep ANALYSIS
        assert phase == Phase.ANALYSIS
        mock_manager.save.assert_not_called()

    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_ensure_valid_phase_discovery_unchanged(
        self, mock_manager_class, mock_load_config, tmp_path
    ):
        """Test DISCOVERY phase is not modified."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = False
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.DISCOVERY
        mock_rrd.requirements.target_papers = 20
        mock_rrd.papers_pool = [MagicMock()] * 5  # Only 5 papers
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        loop = ResearchLoop(project_path=tmp_path, max_iterations=10)
        phase = loop._ensure_valid_phase()

        # DISCOVERY stays as DISCOVERY
        assert phase == Phase.DISCOVERY
        mock_manager.save.assert_not_called()


class TestResearchLoopStreamingExceptions:
    """Tests for streaming exception handling."""

    @patch("ralph.core.research_loop.time")
    @patch("ralph.core.research_loop.AgentRunner")
    @patch("ralph.core.research_loop.load_config")
    @patch("ralph.core.research_loop.RRDManager")
    def test_run_agent_streaming_exception(
        self, mock_manager_class, mock_load_config, mock_runner_class, mock_time, tmp_path
    ):
        """Test streaming handles generator exceptions."""
        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_config.max_consecutive_failures = 3
        mock_config.live_output = True  # Enable streaming
        mock_load_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.validate.return_value = []
        mock_rrd = MagicMock()
        mock_rrd.phase = Phase.DISCOVERY
        mock_rrd.requirements.target_papers = 20
        mock_rrd.statistics.total_analyzed = 0
        mock_rrd.statistics.total_presented = 0
        mock_rrd.statistics.total_insights_extracted = 0
        mock_rrd.papers_pool = []
        mock_rrd.pending_papers = []
        mock_rrd.analyzing_papers = []
        mock_manager.load.return_value = mock_rrd
        mock_manager_class.return_value = mock_manager

        # Simulate streaming generator that raises exception mid-iteration
        def mock_streaming_generator(*args, **kwargs):
            yield "First line"
            raise IOError("Network error during streaming")

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_runner.run_streaming.side_effect = mock_streaming_generator
        # Also mock regular run as fallback
        mock_runner.run.return_value = AgentResult(
            output="Fallback result",
            exit_code=1,
            success=False,
            error_type="network",
        )
        mock_runner_class.return_value = mock_runner

        (tmp_path / "prompt.md").write_text("Test")

        loop = ResearchLoop(project_path=tmp_path, max_iterations=3)
        # Should not crash - loop handles the exception gracefully
        result = loop.run()

        # Loop should have run and completed (possibly with failures)
        assert result.iterations_run > 0 or result.error_message is not None
