"""Tests for interactive menu mode."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from ralph.commands.interactive import (
    main_menu,
    run_menu,
    status_menu,
    config_menu,
    show_banner,
    MENU_STYLE,
)
from ralph.config import Agent


class TestShowBanner:
    """Tests for show_banner function."""

    @patch("ralph.commands.interactive.time")
    @patch("ralph.commands.interactive.os")
    @patch("ralph.commands.interactive.console")
    def test_show_banner(self, mock_console, mock_os, mock_time):
        """Test banner display."""
        mock_os.get_terminal_size.return_value = MagicMock(lines=40)

        show_banner()

        mock_console.clear.assert_called_once()
        # Multiple print calls for banner lines
        assert mock_console.print.call_count > 5

    @patch("ralph.commands.interactive.time")
    @patch("ralph.commands.interactive.os")
    @patch("ralph.commands.interactive.console")
    def test_show_banner_terminal_error(self, mock_console, mock_os, mock_time):
        """Test banner with terminal size error."""
        mock_os.get_terminal_size.side_effect = OSError("No terminal")

        show_banner()

        # Should still work with default size
        mock_console.print.assert_called()


class TestMainMenu:
    """Tests for main_menu function."""

    @patch("ralph.commands.interactive.show_banner")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.print_info")
    @patch("ralph.commands.interactive.console")
    def test_main_menu_exit(self, mock_console, mock_print_info, mock_questionary, mock_banner):
        """Test main menu exit selection."""
        mock_questionary.select.return_value.ask.return_value = "exit"
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        main_menu()

        mock_print_info.assert_called_with("Goodbye!")

    @patch("ralph.commands.interactive.show_banner")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.print_info")
    @patch("ralph.commands.interactive.console")
    def test_main_menu_none_selection(self, mock_console, mock_print_info, mock_questionary, mock_banner):
        """Test main menu with None selection (Ctrl+C)."""
        mock_questionary.select.return_value.ask.return_value = None
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        main_menu()

        mock_print_info.assert_called_with("Goodbye!")

    @patch("ralph.commands.interactive.create_project_interactive")
    @patch("ralph.commands.interactive.show_banner")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_main_menu_create(self, mock_console, mock_questionary, mock_banner, mock_create):
        """Test main menu create selection."""
        mock_questionary.select.return_value.ask.side_effect = ["create", "exit"]
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        main_menu()

        mock_create.assert_called_once()

    @patch("ralph.commands.interactive.run_menu")
    @patch("ralph.commands.interactive.show_banner")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_main_menu_run(self, mock_console, mock_questionary, mock_banner, mock_run_menu):
        """Test main menu run selection."""
        mock_questionary.select.return_value.ask.side_effect = ["run", "exit"]
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        main_menu()

        mock_run_menu.assert_called_once()

    @patch("ralph.commands.interactive.status_menu")
    @patch("ralph.commands.interactive.show_banner")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_main_menu_status(self, mock_console, mock_questionary, mock_banner, mock_status_menu):
        """Test main menu status selection."""
        mock_questionary.select.return_value.ask.side_effect = ["status", "exit"]
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        main_menu()

        mock_status_menu.assert_called_once()

    @patch("ralph.commands.interactive.list_projects")
    @patch("ralph.commands.interactive.show_banner")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_main_menu_list(self, mock_console, mock_questionary, mock_banner, mock_list):
        """Test main menu list selection."""
        mock_questionary.select.return_value.ask.side_effect = ["list", "exit"]
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        main_menu()

        mock_list.assert_called_once()

    @patch("ralph.commands.interactive.config_menu")
    @patch("ralph.commands.interactive.show_banner")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_main_menu_config(self, mock_console, mock_questionary, mock_banner, mock_config_menu):
        """Test main menu config selection."""
        mock_questionary.select.return_value.ask.side_effect = ["config", "exit"]
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        main_menu()

        mock_config_menu.assert_called_once()


class TestRunMenu:
    """Tests for run_menu function."""

    @patch("ralph.commands.interactive.list_research_projects")
    @patch("ralph.commands.interactive.print_info")
    @patch("ralph.commands.interactive.console")
    def test_run_menu_no_projects(self, mock_console, mock_print_info, mock_list_projects):
        """Test run menu with no projects."""
        mock_list_projects.return_value = []

        run_menu()

        mock_print_info.assert_called_with("No research projects found. Create one first!")

    @patch("ralph.commands.interactive.run_research")
    @patch("ralph.commands.interactive.list_research_projects")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_run_menu_back_to_main(self, mock_console, mock_questionary, mock_list_projects, mock_run):
        """Test run menu back to main selection."""
        mock_list_projects.return_value = [Path("/tmp/project")]

        # Select None (back to main)
        mock_questionary.select.return_value.ask.return_value = None
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        run_menu()

        mock_run.assert_not_called()

    @patch("ralph.commands.interactive.load_config")
    @patch("ralph.commands.interactive.run_research")
    @patch("ralph.commands.interactive.list_research_projects")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_run_menu_default_settings(self, mock_console, mock_questionary, mock_list_projects, mock_run, mock_load_config, tmp_path):
        """Test run menu with default settings (no modifications)."""
        project = tmp_path / "test-project"
        project.mkdir()
        (project / "rrd.json").write_text(json.dumps({
            "phase": "DISCOVERY",
            "statistics": {"total_analyzed": 0},
            "requirements": {"target_papers": 20},
        }))
        mock_list_projects.return_value = [project]

        mock_config = MagicMock()
        mock_config.default_agent = "claude"  # String, not enum
        mock_config.default_papers = 20
        mock_load_config.return_value = mock_config

        # Setup questionary responses
        mock_questionary.select.return_value.ask.return_value = project
        mock_questionary.confirm.return_value.ask.return_value = False  # Don't modify settings
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        run_menu()

        mock_run.assert_called_once_with(str(project))

    @patch("ralph.commands.interactive.load_config")
    @patch("ralph.commands.interactive.run_research")
    @patch("ralph.commands.interactive.list_research_projects")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_run_menu_custom_settings(self, mock_console, mock_questionary, mock_list_projects, mock_run, mock_load_config, tmp_path):
        """Test run menu with custom settings (user modifies)."""
        project = tmp_path / "test-project"
        project.mkdir()
        (project / "rrd.json").write_text(json.dumps({
            "phase": "DISCOVERY",
            "statistics": {"total_analyzed": 0},
            "requirements": {"target_papers": 20},
        }))
        mock_list_projects.return_value = [project]

        mock_config = MagicMock()
        mock_config.default_agent = "claude"  # String, not enum
        mock_config.default_papers = 20
        mock_load_config.return_value = mock_config

        # Setup questionary responses
        select_responses = [project, "amp"]  # project selection, agent selection
        mock_questionary.select.return_value.ask.side_effect = select_responses
        mock_questionary.confirm.return_value.ask.return_value = True  # Yes, modify settings
        mock_questionary.text.return_value.ask.side_effect = ["30", "50"]  # papers, iterations
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        run_menu()

        mock_run.assert_called_once_with(
            str(project),
            papers=30,
            iterations=50,
            agent="amp",
        )


class TestStatusMenu:
    """Tests for status_menu function."""

    @patch("ralph.commands.interactive.list_research_projects")
    @patch("ralph.commands.interactive.print_info")
    @patch("ralph.commands.interactive.console")
    def test_status_menu_no_projects(self, mock_console, mock_print_info, mock_list_projects):
        """Test status menu with no projects."""
        mock_list_projects.return_value = []

        status_menu()

        mock_print_info.assert_called_with("No research projects found. Create one first!")

    @patch("ralph.commands.interactive.list_research_projects")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_status_menu_back_to_main(self, mock_console, mock_questionary, mock_list_projects):
        """Test status menu back to main selection."""
        mock_list_projects.return_value = [Path("/tmp/project")]

        mock_questionary.select.return_value.ask.return_value = None
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        status_menu()

    @patch("ralph.commands.interactive.run_research")
    @patch("ralph.commands.interactive.show_status")
    @patch("ralph.commands.interactive.list_research_projects")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_status_menu_run_action(self, mock_console, mock_questionary, mock_list_projects, mock_show_status, mock_run):
        """Test status menu with run action."""
        project = Path("/tmp/test-project")
        mock_list_projects.return_value = [project]

        # Select project, then run action
        mock_questionary.select.return_value.ask.side_effect = [project, "run"]
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        status_menu()

        mock_show_status.assert_called_once_with(str(project))
        mock_run.assert_called_once_with(str(project))

    @patch("ralph.commands.interactive.reset_project")
    @patch("ralph.commands.interactive.show_status")
    @patch("ralph.commands.interactive.list_research_projects")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_status_menu_reset_action(self, mock_console, mock_questionary, mock_list_projects, mock_show_status, mock_reset):
        """Test status menu with reset action."""
        project = Path("/tmp/test-project")
        mock_list_projects.return_value = [project]

        # Select project, then reset action
        mock_questionary.select.return_value.ask.side_effect = [project, "reset"]
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        status_menu()

        mock_show_status.assert_called_once_with(str(project))
        mock_reset.assert_called_once_with(str(project))


class TestConfigMenu:
    """Tests for config_menu function."""

    @patch("ralph.commands.interactive.save_config")
    @patch("ralph.commands.interactive.load_config")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.print_info")
    @patch("ralph.commands.interactive.console")
    def test_config_menu_save_and_exit(self, mock_console, mock_print_info, mock_questionary, mock_load_config, mock_save_config):
        """Test config menu save and exit."""
        mock_config = MagicMock()
        mock_config.research_dir = Path("/tmp/researches")
        mock_config.default_agent = Agent.CLAUDE
        mock_config.default_papers = 20
        mock_config.live_output = True
        mock_load_config.return_value = mock_config

        mock_questionary.select.return_value.ask.return_value = None  # Save and go back
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        config_menu()

        mock_save_config.assert_called_once_with(mock_config)
        mock_print_info.assert_called_with("Settings saved!")

    @patch("ralph.commands.interactive.save_config")
    @patch("ralph.commands.interactive.load_config")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_config_menu_change_agent(self, mock_console, mock_questionary, mock_load_config, mock_save_config):
        """Test config menu change agent."""
        mock_config = MagicMock()
        mock_config.research_dir = Path("/tmp/researches")
        mock_config.default_agent = Agent.CLAUDE
        mock_config.default_papers = 20
        mock_config.live_output = True
        mock_load_config.return_value = mock_config

        # Select default_agent, then amp, then save
        mock_questionary.select.return_value.ask.side_effect = ["default_agent", "amp", None]
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        config_menu()

        assert mock_config.default_agent == Agent.AMP

    @patch("ralph.commands.interactive.save_config")
    @patch("ralph.commands.interactive.load_config")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_config_menu_change_papers(self, mock_console, mock_questionary, mock_load_config, mock_save_config):
        """Test config menu change papers count."""
        mock_config = MagicMock()
        mock_config.research_dir = Path("/tmp/researches")
        mock_config.default_agent = Agent.CLAUDE
        mock_config.default_papers = 20
        mock_config.live_output = True
        mock_load_config.return_value = mock_config

        # Select default_papers, enter 30, then save
        mock_questionary.select.return_value.ask.side_effect = ["default_papers", None]
        mock_questionary.text.return_value.ask.return_value = "30"
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        config_menu()

        assert mock_config.default_papers == 30

    @patch("ralph.commands.interactive.save_config")
    @patch("ralph.commands.interactive.load_config")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_config_menu_change_live_output(self, mock_console, mock_questionary, mock_load_config, mock_save_config):
        """Test config menu toggle live output."""
        mock_config = MagicMock()
        mock_config.research_dir = Path("/tmp/researches")
        mock_config.default_agent = Agent.CLAUDE
        mock_config.default_papers = 20
        mock_config.live_output = True
        mock_load_config.return_value = mock_config

        # Select live_output, then confirm False, then save
        mock_questionary.select.return_value.ask.side_effect = ["live_output", None]
        mock_questionary.confirm.return_value.ask.return_value = False
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        config_menu()

        assert mock_config.live_output is False

    @patch("ralph.commands.interactive.save_config")
    @patch("ralph.commands.interactive.load_config")
    @patch("ralph.commands.interactive.questionary")
    @patch("ralph.commands.interactive.console")
    def test_config_menu_change_research_dir(self, mock_console, mock_questionary, mock_load_config, mock_save_config):
        """Test config menu change research directory."""
        mock_config = MagicMock()
        mock_config.research_dir = Path("/tmp/researches")
        mock_config.default_agent = Agent.CLAUDE
        mock_config.default_papers = 20
        mock_config.live_output = True
        mock_load_config.return_value = mock_config

        # Select research_dir, enter new path, then save
        mock_questionary.select.return_value.ask.side_effect = ["research_dir", None]
        mock_questionary.path.return_value.ask.return_value = "/new/path/researches"
        mock_questionary.Choice = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", args[0]))
        mock_questionary.Separator = MagicMock()

        config_menu()

        assert mock_config.research_dir == Path("/new/path/researches")


class TestMenuStyle:
    """Tests for menu style configuration."""

    def test_menu_style_exists(self):
        """Test that MENU_STYLE is defined."""
        assert MENU_STYLE is not None
