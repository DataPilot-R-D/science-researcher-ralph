"""Tests for create command."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ralph.commands.create import create_project, create_project_interactive
from ralph.config import Agent


class TestCreateProject:
    """Tests for create_project function."""

    @patch("ralph.commands.create.SkillRunner")
    @patch("ralph.commands.create.load_config")
    @patch("ralph.commands.create.console")
    def test_create_project_success(self, mock_console, mock_load_config, mock_skill_runner, tmp_path):
        """Test successful project creation."""
        # Setup config
        mock_config = MagicMock()
        mock_config.default_papers = 20
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        # Setup skill runner
        mock_runner = MagicMock()
        mock_runner.list_skills.return_value = [{"name": "rrd", "path": Path("skills/rrd")}]
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_runner.run_rrd_skill.return_value = (project_path, "Success output")
        mock_skill_runner.return_value = mock_runner

        result = create_project("Test research topic")

        assert result == project_path
        mock_runner.run_rrd_skill.assert_called_once()

    @patch("ralph.commands.create.SkillRunner")
    @patch("ralph.commands.create.load_config")
    @patch("ralph.commands.create.console")
    def test_create_project_with_custom_papers(self, mock_console, mock_load_config, mock_skill_runner, tmp_path):
        """Test project creation with custom papers count."""
        mock_config = MagicMock()
        mock_config.default_papers = 20
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.list_skills.return_value = [{"name": "rrd", "path": Path("skills/rrd")}]
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_runner.run_rrd_skill.return_value = (project_path, "Success")
        mock_skill_runner.return_value = mock_runner

        result = create_project("Topic", papers=30)

        assert result == project_path
        call_kwargs = mock_runner.run_rrd_skill.call_args[1]
        assert call_kwargs["target_papers"] == 30

    @patch("ralph.commands.create.SkillRunner")
    @patch("ralph.commands.create.load_config")
    @patch("ralph.commands.create.console")
    def test_create_project_with_custom_agent(self, mock_console, mock_load_config, mock_skill_runner, tmp_path):
        """Test project creation with custom agent."""
        mock_config = MagicMock()
        mock_config.default_papers = 20
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.list_skills.return_value = [{"name": "rrd", "path": Path("skills/rrd")}]
        project_path = tmp_path / "test-project"
        project_path.mkdir()
        mock_runner.run_rrd_skill.return_value = (project_path, "Success")
        mock_skill_runner.return_value = mock_runner

        result = create_project("Topic", agent="amp")

        assert result == project_path
        call_kwargs = mock_runner.run_rrd_skill.call_args[1]
        assert call_kwargs["agent"] == Agent.AMP

    @patch("ralph.commands.create.load_config")
    @patch("ralph.commands.create.print_error")
    def test_create_project_invalid_agent(self, mock_print_error, mock_load_config):
        """Test project creation with invalid agent."""
        mock_config = MagicMock()
        mock_config.default_papers = 20
        mock_load_config.return_value = mock_config

        result = create_project("Topic", agent="invalid")

        assert result is None
        mock_print_error.assert_called()
        assert "Invalid agent" in str(mock_print_error.call_args)

    @patch("ralph.commands.create.SkillRunner")
    @patch("ralph.commands.create.load_config")
    @patch("ralph.commands.create.print_error")
    @patch("ralph.commands.create.console")
    def test_create_project_rrd_skill_not_found(self, mock_console, mock_print_error, mock_load_config, mock_skill_runner):
        """Test project creation when RRD skill not found."""
        mock_config = MagicMock()
        mock_config.default_papers = 20
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.list_skills.return_value = []  # No skills
        mock_skill_runner.return_value = mock_runner

        result = create_project("Topic")

        assert result is None
        mock_print_error.assert_called_with("RRD skill not found in skills/ directory")

    @patch("ralph.commands.create.SkillRunner")
    @patch("ralph.commands.create.load_config")
    @patch("ralph.commands.create.print_error")
    @patch("ralph.commands.create.console")
    def test_create_project_skill_fails(self, mock_console, mock_print_error, mock_load_config, mock_skill_runner):
        """Test project creation when skill fails."""
        mock_config = MagicMock()
        mock_config.default_papers = 20
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.list_skills.return_value = [{"name": "rrd", "path": Path("skills/rrd")}]
        mock_runner.run_rrd_skill.return_value = (None, "Error output")
        mock_skill_runner.return_value = mock_runner

        result = create_project("Topic")

        assert result is None
        mock_print_error.assert_called_with("Failed to create research project")


class TestCreateProjectInteractive:
    """Tests for create_project_interactive function."""

    @patch("questionary.select")
    @patch("questionary.text")
    @patch("questionary.Choice")
    @patch("questionary.Style")
    @patch("ralph.commands.create.create_project")
    @patch("ralph.commands.create.load_config")
    @patch("ralph.commands.create.console")
    def test_interactive_success(
        self, mock_console, mock_load_config, mock_create, mock_style, mock_choice, mock_text, mock_select, tmp_path
    ):
        """Test successful interactive project creation."""
        mock_config = MagicMock()
        mock_config.default_papers = 20
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        # Setup questionary mocks
        mock_text.return_value.ask.side_effect = [
            "Test research topic for testing",  # topic
            "25",  # papers
        ]
        mock_select.return_value.ask.return_value = "claude"
        mock_choice.side_effect = lambda *args, **kwargs: kwargs.get("value", args[0])

        project_path = tmp_path / "test-project"
        mock_create.return_value = project_path

        result = create_project_interactive()

        assert result == project_path
        mock_create.assert_called_once_with("Test research topic for testing", 25, "claude")

    @patch("questionary.text")
    @patch("questionary.Style")
    @patch("ralph.commands.create.print_info")
    @patch("ralph.commands.create.console")
    def test_interactive_cancel_on_topic(self, mock_console, mock_print_info, mock_style, mock_text):
        """Test interactive cancellation on topic prompt."""
        mock_text.return_value.ask.return_value = None

        result = create_project_interactive()

        assert result is None
        mock_print_info.assert_called_with("Cancelled")

    @patch("questionary.text")
    @patch("questionary.Style")
    @patch("ralph.commands.create.load_config")
    @patch("ralph.commands.create.print_info")
    @patch("ralph.commands.create.console")
    def test_interactive_cancel_on_papers(self, mock_console, mock_print_info, mock_load_config, mock_style, mock_text):
        """Test interactive cancellation on papers prompt."""
        mock_config = MagicMock()
        mock_config.default_papers = 20
        mock_load_config.return_value = mock_config

        mock_text.return_value.ask.side_effect = [
            "Test topic description here",  # topic
            None,  # papers - cancelled
        ]

        result = create_project_interactive()

        assert result is None
        mock_print_info.assert_called_with("Cancelled")

    @patch("questionary.select")
    @patch("questionary.text")
    @patch("questionary.Choice")
    @patch("questionary.Style")
    @patch("ralph.commands.create.load_config")
    @patch("ralph.commands.create.print_info")
    @patch("ralph.commands.create.console")
    def test_interactive_cancel_on_agent(
        self, mock_console, mock_print_info, mock_load_config, mock_style, mock_choice, mock_text, mock_select
    ):
        """Test interactive cancellation on agent selection."""
        mock_config = MagicMock()
        mock_config.default_papers = 20
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        mock_text.return_value.ask.side_effect = [
            "Test topic description here",  # topic
            "20",  # papers
        ]
        mock_select.return_value.ask.return_value = None
        mock_choice.side_effect = lambda *args, **kwargs: kwargs.get("value", args[0])

        result = create_project_interactive()

        assert result is None
        mock_print_info.assert_called_with("Cancelled")
