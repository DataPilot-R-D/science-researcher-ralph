"""Tests for table creation utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ralph.ui.tables import (
    create_project_table,
    create_status_panel,
    create_mini_progress_bar,
    create_completion_summary,
    create_timing_table,
    format_duration,
)


class TestCreateProjectTable:
    """Tests for create_project_table function."""

    def test_create_table_empty_list(self):
        """Test table creation with empty list."""
        table = create_project_table([])

        assert isinstance(table, Table)
        assert table.title == "Research Projects"

    def test_create_table_single_project(self):
        """Test table creation with single project."""
        projects = [
            {
                "name": "test-project",
                "path": Path("/tmp/test-project"),
                "phase": "ANALYSIS",
                "target": 20,
                "analyzed": 10,
                "pending": 10,
            }
        ]

        table = create_project_table(projects)

        assert isinstance(table, Table)
        assert table.row_count == 1

    def test_create_table_multiple_projects(self):
        """Test table creation with multiple projects."""
        projects = [
            {"name": "project-1", "path": Path("/tmp/p1"), "phase": "DISCOVERY", "target": 20, "analyzed": 0, "pending": 20},
            {"name": "project-2", "path": Path("/tmp/p2"), "phase": "ANALYSIS", "target": 15, "analyzed": 10, "pending": 5},
            {"name": "project-3", "path": Path("/tmp/p3"), "phase": "COMPLETE", "target": 10, "analyzed": 10, "pending": 0},
        ]

        table = create_project_table(projects)

        assert isinstance(table, Table)
        assert table.row_count == 3

    def test_create_table_missing_fields(self):
        """Test table creation with missing fields."""
        projects = [{"name": "incomplete"}]

        table = create_project_table(projects)

        assert isinstance(table, Table)
        assert table.row_count == 1

    def test_create_table_zero_target(self):
        """Test table creation with zero target papers."""
        projects = [
            {
                "name": "zero-target",
                "path": Path("/tmp/zero"),
                "phase": "DISCOVERY",
                "target": 0,
                "analyzed": 0,
                "pending": 0,
            }
        ]

        table = create_project_table(projects)

        assert isinstance(table, Table)
        # Should show "0/?" for progress

    def test_create_table_unknown_phase(self):
        """Test table creation with unknown phase."""
        projects = [
            {
                "name": "unknown-phase",
                "path": Path("/tmp/unknown"),
                "phase": "INVALID",
                "target": 20,
                "analyzed": 5,
                "pending": 15,
            }
        ]

        table = create_project_table(projects)

        assert isinstance(table, Table)
        assert table.row_count == 1


class TestCreateStatusPanel:
    """Tests for create_status_panel function."""

    def test_create_panel_basic(self):
        """Test basic panel creation."""
        summary = {
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

        panel = create_status_panel(summary, Path("/tmp/test"))

        assert isinstance(panel, Panel)

    def test_create_panel_with_analyzing(self):
        """Test panel with papers in analyzing state."""
        summary = {
            "project": "Test Project",
            "phase": "ANALYSIS",
            "target_papers": 20,
            "pool_size": 20,
            "analyzed": 10,
            "presented": 5,
            "rejected": 3,
            "pending": 8,
            "analyzing": 2,
            "insights": 8,
            "completion_pct": 50.0,
        }

        panel = create_status_panel(summary, Path("/tmp/test"))

        assert isinstance(panel, Panel)

    def test_create_panel_zero_target(self):
        """Test panel with zero target papers."""
        summary = {
            "project": "Test Project",
            "phase": "DISCOVERY",
            "target_papers": 0,
            "pool_size": 0,
            "analyzed": 0,
            "presented": 0,
            "rejected": 0,
            "pending": 0,
            "analyzing": 0,
            "insights": 0,
            "completion_pct": 0,
        }

        panel = create_status_panel(summary, Path("/tmp/test"))

        assert isinstance(panel, Panel)


class TestCreateMiniProgressBar:
    """Tests for create_mini_progress_bar function."""

    def test_progress_bar_zero(self):
        """Test progress bar at 0%."""
        bar = create_mini_progress_bar(0, 100)

        assert isinstance(bar, Text)
        text = str(bar)
        assert "0%" in text or "0" in text

    def test_progress_bar_fifty_percent(self):
        """Test progress bar at 50%."""
        bar = create_mini_progress_bar(50, 100)

        assert isinstance(bar, Text)

    def test_progress_bar_hundred_percent(self):
        """Test progress bar at 100%."""
        bar = create_mini_progress_bar(100, 100)

        assert isinstance(bar, Text)
        text = str(bar)
        assert "100%" in text or "100" in text

    def test_progress_bar_zero_total(self):
        """Test progress bar with zero total."""
        bar = create_mini_progress_bar(0, 0)

        assert isinstance(bar, Text)
        text = str(bar)
        assert "0%" in text or "0" in text

    def test_progress_bar_over_hundred(self):
        """Test progress bar over 100% capped."""
        bar = create_mini_progress_bar(150, 100)

        assert isinstance(bar, Text)
        text = str(bar)
        assert "100%" in text or "100" in text

    def test_progress_bar_custom_width(self):
        """Test progress bar with custom width."""
        bar = create_mini_progress_bar(50, 100, width=50)

        assert isinstance(bar, Text)


class TestCreateCompletionSummary:
    """Tests for create_completion_summary function."""

    def test_completion_summary_basic(self):
        """Test basic completion summary."""
        summary = {
            "analyzed": 20,
            "presented": 15,
            "rejected": 5,
            "insights": 25,
        }

        panel = create_completion_summary(summary)

        assert isinstance(panel, Panel)

    def test_completion_summary_missing_fields(self):
        """Test completion summary with missing fields."""
        summary = {}

        panel = create_completion_summary(summary)

        assert isinstance(panel, Panel)


class TestCreateTimingTable:
    """Tests for create_timing_table function."""

    def test_timing_table_none_data(self):
        """Test timing table with None data."""
        result = create_timing_table(None)

        assert result is None

    def test_timing_table_empty_data(self):
        """Test timing table with empty data."""
        result = create_timing_table({})

        assert result is None

    def test_timing_table_with_data(self):
        """Test timing table with timing data."""
        timing_data = {
            "discovery": {
                "started_at": "2026-01-15T10:00:00",
                "duration_seconds": 3600,
            },
            "analysis": {
                "started_at": "2026-01-15T11:00:00",
                "duration_seconds": 7200,
            },
        }

        table = create_timing_table(timing_data)

        assert isinstance(table, Table)

    def test_timing_table_partial_data(self):
        """Test timing table with partial data."""
        timing_data = {
            "discovery": {
                "started_at": "2026-01-15T10:00:00",
            },
        }

        table = create_timing_table(timing_data)

        assert isinstance(table, Table)


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_format_seconds_only(self):
        """Test formatting seconds only."""
        result = format_duration(30)
        assert result == "30s"

    def test_format_one_second(self):
        """Test formatting one second."""
        result = format_duration(1)
        assert result == "1s"

    def test_format_minutes_and_seconds(self):
        """Test formatting minutes and seconds."""
        result = format_duration(90)
        assert result == "1m 30s"

    def test_format_exact_minute(self):
        """Test formatting exact minute."""
        result = format_duration(60)
        assert result == "1m 0s"

    def test_format_hours_and_minutes(self):
        """Test formatting hours and minutes."""
        result = format_duration(3660)
        assert result == "1h 1m"

    def test_format_exact_hour(self):
        """Test formatting exact hour."""
        result = format_duration(3600)
        assert result == "1h 0m"

    def test_format_multiple_hours(self):
        """Test formatting multiple hours."""
        result = format_duration(7320)  # 2h 2m
        assert result == "2h 2m"

    def test_format_zero_seconds(self):
        """Test formatting zero seconds."""
        result = format_duration(0)
        assert result == "0s"
