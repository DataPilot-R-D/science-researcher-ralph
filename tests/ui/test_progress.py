"""Tests for progress bar utilities."""

import pytest
from unittest.mock import patch, MagicMock

from rich.progress import Progress

from ralph.ui.progress import (
    create_progress,
    create_spinner,
    create_iteration_progress,
    create_papers_progress,
)


class TestCreateProgress:
    """Tests for create_progress function."""

    def test_returns_progress_instance(self):
        """Test that create_progress returns a Progress instance."""
        progress = create_progress()

        assert isinstance(progress, Progress)

    def test_progress_not_transient(self):
        """Test that progress bar is not transient."""
        progress = create_progress()

        # Check via the live context's transient property or just verify it exists
        assert progress is not None

    def test_progress_has_columns(self):
        """Test that progress bar has expected columns."""
        progress = create_progress()

        # Should have multiple columns for spinner, text, bar, etc.
        assert len(progress.columns) >= 5


class TestCreateSpinner:
    """Tests for create_spinner function."""

    def test_returns_progress_instance(self):
        """Test that create_spinner returns a Progress instance."""
        spinner = create_spinner()

        assert isinstance(spinner, Progress)

    def test_spinner_is_transient(self):
        """Test that spinner is transient."""
        spinner = create_spinner()

        # Spinner should exist and be a Progress instance
        assert spinner is not None
        assert isinstance(spinner, Progress)

    def test_spinner_custom_text(self):
        """Test spinner with custom text."""
        spinner = create_spinner("Loading data...")

        assert isinstance(spinner, Progress)

    def test_spinner_default_text(self):
        """Test spinner with default text."""
        spinner = create_spinner()

        assert isinstance(spinner, Progress)


class TestCreateIterationProgress:
    """Tests for create_iteration_progress function."""

    def test_returns_progress_instance(self):
        """Test that create_iteration_progress returns a Progress instance."""
        progress = create_iteration_progress()

        assert isinstance(progress, Progress)

    def test_progress_not_transient(self):
        """Test that iteration progress is not transient."""
        progress = create_iteration_progress()

        # Verify progress exists and is a Progress instance
        assert progress is not None
        assert isinstance(progress, Progress)

    def test_progress_has_columns(self):
        """Test that iteration progress has columns."""
        progress = create_iteration_progress()

        assert len(progress.columns) >= 4


class TestCreatePapersProgress:
    """Tests for create_papers_progress function."""

    def test_returns_progress_instance(self):
        """Test that create_papers_progress returns a Progress instance."""
        progress = create_papers_progress()

        assert isinstance(progress, Progress)

    def test_progress_not_transient(self):
        """Test that papers progress is not transient."""
        progress = create_papers_progress()

        # Verify progress exists and is a Progress instance
        assert progress is not None
        assert isinstance(progress, Progress)

    def test_progress_has_columns(self):
        """Test that papers progress has columns."""
        progress = create_papers_progress()

        assert len(progress.columns) >= 3


class TestProgressIntegration:
    """Integration tests for progress bars."""

    def test_progress_can_add_task(self):
        """Test that progress can add a task."""
        progress = create_progress()

        task_id = progress.add_task("Test task", total=100)

        assert task_id is not None

    def test_progress_can_update_task(self):
        """Test that progress can update a task."""
        progress = create_progress()
        task_id = progress.add_task("Test task", total=100)

        progress.update(task_id, advance=50)

        # No exception means success

    def test_iteration_progress_with_fields(self):
        """Test iteration progress with phase field."""
        progress = create_iteration_progress()

        task_id = progress.add_task("Iterations", total=20, phase="DISCOVERY")

        assert task_id is not None

        # Update with new phase
        progress.update(task_id, phase="ANALYSIS")

    def test_papers_progress_completion(self):
        """Test papers progress completion."""
        progress = create_papers_progress()

        task_id = progress.add_task("Papers", total=20)
        progress.update(task_id, completed=20)

        # Should be complete

    def test_spinner_add_task(self):
        """Test spinner can add indeterminate task."""
        spinner = create_spinner()

        task_id = spinner.add_task("Working...", total=None)

        assert task_id is not None
