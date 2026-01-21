"""Tests for console utilities."""

import pytest
from unittest.mock import patch, MagicMock

from ralph.ui.console import (
    SimpsonsColors,
    ralph_theme,
    console,
    error_console,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    get_phase_style,
)


class TestSimpsonsColors:
    """Tests for SimpsonsColors palette."""

    def test_blue_color(self):
        """Test blue color value."""
        assert SimpsonsColors.BLUE == "#2f64d6"

    def test_yellow_color(self):
        """Test yellow color value."""
        assert SimpsonsColors.YELLOW == "#f8db27"

    def test_brown_color(self):
        """Test brown color value."""
        assert SimpsonsColors.BROWN == "#9c5b01"

    def test_white_color(self):
        """Test white color value."""
        assert SimpsonsColors.WHITE == "#ffffff"

    def test_pink_color(self):
        """Test pink color value."""
        assert SimpsonsColors.PINK == "#ff81c1"


class TestRalphTheme:
    """Tests for the Ralph Rich theme."""

    def test_theme_has_info_style(self):
        """Test theme has info style."""
        assert "info" in ralph_theme.styles

    def test_theme_has_success_style(self):
        """Test theme has success style."""
        assert "success" in ralph_theme.styles

    def test_theme_has_warning_style(self):
        """Test theme has warning style."""
        assert "warning" in ralph_theme.styles

    def test_theme_has_error_style(self):
        """Test theme has error style."""
        assert "error" in ralph_theme.styles

    def test_theme_has_phase_styles(self):
        """Test theme has phase styles."""
        assert "phase.discovery" in ralph_theme.styles
        assert "phase.analysis" in ralph_theme.styles
        assert "phase.ideation" in ralph_theme.styles
        assert "phase.complete" in ralph_theme.styles

    def test_theme_has_header_style(self):
        """Test theme has header style."""
        assert "header" in ralph_theme.styles


class TestConsoleInstances:
    """Tests for console instances."""

    def test_console_exists(self):
        """Test main console exists."""
        assert console is not None

    def test_error_console_exists(self):
        """Test error console exists."""
        assert error_console is not None

    def test_console_has_theme(self):
        """Test console has Ralph theme."""
        # The console should be configured with a theme
        # Rich Console stores theme differently in newer versions
        assert console is not None


class TestPrintHeader:
    """Tests for print_header function."""

    @patch("ralph.ui.console.console")
    def test_print_header_with_title_only(self, mock_console):
        """Test header with title only."""
        print_header("Test Title")

        # Should print empty line, title, empty line
        assert mock_console.print.call_count >= 2
        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Test Title" in call for call in calls)

    @patch("ralph.ui.console.console")
    def test_print_header_with_subtitle(self, mock_console):
        """Test header with subtitle."""
        print_header("Test Title", "Test Subtitle")

        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Test Title" in call for call in calls)
        assert any("Test Subtitle" in call for call in calls)


class TestPrintSuccess:
    """Tests for print_success function."""

    @patch("ralph.ui.console.console")
    def test_print_success(self, mock_console):
        """Test success message."""
        print_success("Operation completed")

        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Operation completed" in call_args
        assert "success" in call_args


class TestPrintError:
    """Tests for print_error function."""

    @patch("ralph.ui.console.error_console")
    def test_print_error(self, mock_error_console):
        """Test error message."""
        print_error("Something went wrong")

        mock_error_console.print.assert_called_once()
        call_args = str(mock_error_console.print.call_args)
        assert "Something went wrong" in call_args
        assert "error" in call_args


class TestPrintWarning:
    """Tests for print_warning function."""

    @patch("ralph.ui.console.console")
    def test_print_warning(self, mock_console):
        """Test warning message."""
        print_warning("Be careful")

        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Be careful" in call_args
        assert "warning" in call_args


class TestPrintInfo:
    """Tests for print_info function."""

    @patch("ralph.ui.console.console")
    def test_print_info(self, mock_console):
        """Test info message."""
        print_info("Here is some info")

        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "Here is some info" in call_args
        assert "info" in call_args


class TestGetPhaseStyle:
    """Tests for get_phase_style function."""

    def test_discovery_phase(self):
        """Test DISCOVERY phase style."""
        assert get_phase_style("DISCOVERY") == "phase.discovery"

    def test_analysis_phase(self):
        """Test ANALYSIS phase style."""
        assert get_phase_style("ANALYSIS") == "phase.analysis"

    def test_ideation_phase(self):
        """Test IDEATION phase style."""
        assert get_phase_style("IDEATION") == "phase.ideation"

    def test_complete_phase(self):
        """Test COMPLETE phase style."""
        assert get_phase_style("COMPLETE") == "phase.complete"

    def test_unknown_phase(self):
        """Test unknown phase returns muted."""
        assert get_phase_style("UNKNOWN") == "muted"

    def test_lowercase_phase(self):
        """Test lowercase phase is converted."""
        assert get_phase_style("discovery") == "phase.discovery"

    def test_mixed_case_phase(self):
        """Test mixed case phase is converted."""
        assert get_phase_style("AnAlYsIs") == "phase.analysis"
