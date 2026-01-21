"""Tests for live display utilities."""

import pytest
from unittest.mock import patch, MagicMock

from rich.live import Live
from rich.table import Table

from ralph.ui.live import LiveResearchDisplay, SimpleProgressDisplay


class TestLiveResearchDisplay:
    """Tests for LiveResearchDisplay class."""

    def test_init_sets_values(self):
        """Test initialization sets correct values."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        assert display.max_iterations == 30
        assert display.target_papers == 25
        assert display.current_iteration == 0
        assert display.current_phase == "DISCOVERY"
        assert display.papers_analyzed == 0
        assert display.output_lines == []

    def test_init_creates_progress_bars(self):
        """Test initialization creates progress bars."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        assert display.iteration_progress is not None
        assert display.papers_progress is not None

    def test_start_returns_live(self):
        """Test start returns Live context."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        live = display.start()

        assert isinstance(live, Live)

    def test_update_iteration(self):
        """Test update_iteration updates state."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        display.update_iteration(5, "ANALYSIS")

        assert display.current_iteration == 5
        assert display.current_phase == "ANALYSIS"

    def test_update_papers(self):
        """Test update_papers updates state."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        display.update_papers(10)

        assert display.papers_analyzed == 10

    def test_add_output_single_line(self):
        """Test add_output adds single line."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        display.add_output("Test line")

        assert len(display.output_lines) == 1
        assert display.output_lines[0] == "Test line"

    def test_add_output_strips_whitespace(self):
        """Test add_output strips trailing whitespace."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        display.add_output("Test line   \n")

        assert display.output_lines[0] == "Test line"

    def test_add_output_ignores_empty(self):
        """Test add_output ignores empty lines."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        display.add_output("")
        display.add_output("   ")
        display.add_output("\n")

        assert len(display.output_lines) == 0

    def test_add_output_trims_old_lines(self):
        """Test add_output trims old lines when over limit."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        # Add more than 100 lines
        for i in range(120):
            display.add_output(f"Line {i}")

        # Should trim to 50 (keeps last 50 when over 100)
        assert len(display.output_lines) <= 100
        # Should keep recent lines
        assert "Line 119" in display.output_lines[-1]

    def test_get_layout_returns_table(self):
        """Test get_layout returns Table."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        layout = display.get_layout()

        assert isinstance(layout, Table)

    def test_get_layout_with_output(self):
        """Test get_layout includes output panel when lines exist."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)
        display.add_output("Test output")

        layout = display.get_layout()

        assert isinstance(layout, Table)

    def test_make_layout_private(self):
        """Test _make_layout creates layout."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        layout = display._make_layout()

        assert isinstance(layout, Table)


class TestLiveResearchDisplayPhases:
    """Tests for LiveResearchDisplay phase handling."""

    def test_update_iteration_discovery_phase(self):
        """Test update_iteration with DISCOVERY phase."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        display.update_iteration(1, "DISCOVERY")

        assert display.current_phase == "DISCOVERY"

    def test_update_iteration_analysis_phase(self):
        """Test update_iteration with ANALYSIS phase."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        display.update_iteration(5, "ANALYSIS")

        assert display.current_phase == "ANALYSIS"

    def test_update_iteration_ideation_phase(self):
        """Test update_iteration with IDEATION phase."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        display.update_iteration(25, "IDEATION")

        assert display.current_phase == "IDEATION"

    def test_update_iteration_complete_phase(self):
        """Test update_iteration with COMPLETE phase."""
        display = LiveResearchDisplay(max_iterations=30, target_papers=25)

        display.update_iteration(26, "COMPLETE")

        assert display.current_phase == "COMPLETE"


class TestSimpleProgressDisplay:
    """Tests for SimpleProgressDisplay class."""

    def test_init_creates_progress(self):
        """Test initialization creates progress bar."""
        display = SimpleProgressDisplay()

        assert display.progress is not None

    @patch("ralph.ui.live.console")
    def test_start_iteration_prints(self, mock_console):
        """Test start_iteration prints message."""
        display = SimpleProgressDisplay()

        display.start_iteration(5, 30, "ANALYSIS")

        assert mock_console.print.call_count >= 3

    @patch("ralph.ui.live.console")
    def test_start_iteration_includes_phase(self, mock_console):
        """Test start_iteration includes phase in output."""
        display = SimpleProgressDisplay()

        display.start_iteration(5, 30, "ANALYSIS")

        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("ANALYSIS" in call for call in calls)

    @patch("ralph.ui.live.console")
    def test_start_iteration_includes_numbers(self, mock_console):
        """Test start_iteration includes iteration numbers."""
        display = SimpleProgressDisplay()

        display.start_iteration(5, 30, "DISCOVERY")

        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("5" in call and "30" in call for call in calls)

    @patch("ralph.ui.live.console")
    def test_end_iteration_prints_delta(self, mock_console):
        """Test end_iteration prints papers delta."""
        display = SimpleProgressDisplay()

        display.end_iteration(3)

        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "+3" in call_args or "3" in call_args

    @patch("ralph.ui.live.console")
    def test_end_iteration_zero_delta_no_print(self, mock_console):
        """Test end_iteration doesn't print for zero delta."""
        display = SimpleProgressDisplay()

        display.end_iteration(0)

        mock_console.print.assert_not_called()


class TestLiveDisplayIntegration:
    """Integration tests for live display."""

    def test_full_workflow(self):
        """Test full workflow of live display."""
        display = LiveResearchDisplay(max_iterations=10, target_papers=5)

        # Simulate iterations
        for i in range(1, 6):
            display.update_iteration(i, "DISCOVERY" if i < 3 else "ANALYSIS")
            display.add_output(f"Processing iteration {i}")
            display.update_papers(i - 1)

        assert display.current_iteration == 5
        assert display.papers_analyzed == 4
        assert len(display.output_lines) == 5

    def test_simple_display_workflow(self):
        """Test simple display workflow."""
        display = SimpleProgressDisplay()

        # No exceptions should be raised
        with patch("ralph.ui.live.console"):
            display.start_iteration(1, 10, "DISCOVERY")
            display.end_iteration(2)
            display.start_iteration(2, 10, "ANALYSIS")
            display.end_iteration(1)
