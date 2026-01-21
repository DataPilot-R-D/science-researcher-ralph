"""Tests for CLI application."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from ralph.cli import app
from ralph.config import Config, Agent


runner = CliRunner()


class TestCLIVersion:
    """Tests for version flag."""

    def test_version_short_flag(self):
        """Test -v flag shows version."""
        result = runner.invoke(app, ["-v"])

        assert result.exit_code == 0
        assert "Research-Ralph" in result.stdout

    def test_version_long_flag(self):
        """Test --version flag shows version."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "Research-Ralph" in result.stdout


class TestCLINoArgs:
    """Tests for CLI with no arguments (interactive mode)."""

    def test_no_args_invokes_interactive(self):
        """Test no args invokes interactive menu."""
        with patch("ralph.commands.interactive.main_menu") as mock_menu:
            result = runner.invoke(app, [])

            mock_menu.assert_called_once()


class TestCLIListFlag:
    """Tests for --list flag."""

    def test_list_flag(self, tmp_path, monkeypatch):
        """Test --list flag shows projects."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.commands.list_cmd.list_projects") as mock_list:
            result = runner.invoke(app, ["--list"])

            mock_list.assert_called_once()

    def test_list_short_flag(self, tmp_path, monkeypatch):
        """Test -l flag shows projects."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.commands.list_cmd.list_projects") as mock_list:
            result = runner.invoke(app, ["-l"])

            mock_list.assert_called_once()


class TestCLIConfigFlag:
    """Tests for --config flag."""

    def test_show_all_config(self, tmp_path, monkeypatch):
        """Test showing all config with empty --config."""
        config_file = tmp_path / "config.yaml"
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        result = runner.invoke(app, ["--config", ""])

        assert result.exit_code == 0
        assert "Configuration" in result.stdout

    def test_get_config_value(self, tmp_path, monkeypatch):
        """Test getting specific config value."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_papers: 30")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        result = runner.invoke(app, ["--config", "default_papers"])

        assert result.exit_code == 0
        assert "30" in result.stdout

    def test_set_config_value(self, tmp_path, monkeypatch):
        """Test setting config value."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        result = runner.invoke(app, ["--config", "default_papers=30"])

        assert result.exit_code == 0
        assert "Set" in result.stdout

    def test_set_invalid_config_key(self, tmp_path, monkeypatch):
        """Test setting invalid config key."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        result = runner.invoke(app, ["--config", "invalid_key=value"])

        assert result.exit_code == 1


class TestCLINewFlag:
    """Tests for --new flag."""

    def test_new_flag_calls_create(self, tmp_path, monkeypatch):
        """Test --new flag calls create_project."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.commands.create.create_project") as mock_create:
            mock_create.return_value = tmp_path / "new-project"

            result = runner.invoke(app, ["--new", "Test topic"])

            mock_create.assert_called_once()
            assert "Test topic" in mock_create.call_args[0]

    def test_new_flag_with_papers(self, tmp_path, monkeypatch):
        """Test --new flag with --papers option."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.commands.create.create_project") as mock_create:
            mock_create.return_value = tmp_path / "new-project"

            result = runner.invoke(app, ["--new", "Topic", "--papers", "30"])

            mock_create.assert_called_once()
            assert mock_create.call_args[1]["papers"] == 30

    def test_new_flag_with_agent(self, tmp_path, monkeypatch):
        """Test --new flag with --agent option."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.commands.create.create_project") as mock_create:
            mock_create.return_value = tmp_path / "new-project"

            result = runner.invoke(app, ["--new", "Topic", "--agent", "amp"])

            mock_create.assert_called_once()
            assert mock_create.call_args[1]["agent"] == "amp"


class TestCLIStatusFlag:
    """Tests for --status flag."""

    def test_status_flag_calls_show_status(self, tmp_path, monkeypatch):
        """Test --status flag calls show_status."""
        with patch("ralph.commands.status.show_status") as mock_status:
            mock_status.return_value = True

            result = runner.invoke(app, ["--status", "test-project"])

            mock_status.assert_called_once_with("test-project")

    def test_status_flag_not_found(self, tmp_path, monkeypatch):
        """Test --status flag with non-existent project."""
        with patch("ralph.commands.status.show_status") as mock_status:
            mock_status.return_value = False

            result = runner.invoke(app, ["--status", "nonexistent"])

            assert result.exit_code == 1


class TestCLIResetFlag:
    """Tests for --reset flag."""

    def test_reset_flag_calls_reset(self, tmp_path, monkeypatch):
        """Test --reset flag calls reset_project."""
        with patch("ralph.commands.reset.reset_project") as mock_reset:
            mock_reset.return_value = True

            result = runner.invoke(app, ["--reset", "test-project"])

            mock_reset.assert_called_once()
            # CLI mode skips confirmation
            assert mock_reset.call_args[1]["confirm"] is False


class TestCLIRunFlag:
    """Tests for --run flag."""

    def test_run_flag_calls_run_research(self, tmp_path, monkeypatch):
        """Test --run flag calls run_research."""
        with patch("ralph.commands.run.run_research") as mock_run:
            mock_run.return_value = True

            result = runner.invoke(app, ["--run", "test-project"])

            mock_run.assert_called_once()

    def test_run_flag_with_all_options(self, tmp_path, monkeypatch):
        """Test --run flag with all options."""
        with patch("ralph.commands.run.run_research") as mock_run:
            mock_run.return_value = True

            result = runner.invoke(
                app,
                [
                    "--run",
                    "project",
                    "--papers",
                    "30",
                    "--iterations",
                    "50",
                    "--agent",
                    "amp",
                    "--force",
                ],
            )

            mock_run.assert_called_once()
            kwargs = mock_run.call_args[1]
            assert kwargs["papers"] == 30
            assert kwargs["iterations"] == 50
            assert kwargs["agent"] == "amp"
            assert kwargs["force"] is True


class TestCLISubcommands:
    """Tests for subcommand-style usage."""

    def test_list_subcommand(self, tmp_path, monkeypatch):
        """Test 'list' subcommand."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.commands.list_cmd.list_projects") as mock_list:
            result = runner.invoke(app, ["list"])

            mock_list.assert_called_once()

    def test_status_subcommand(self, tmp_path, monkeypatch):
        """Test 'status' subcommand."""
        with patch("ralph.commands.status.show_status") as mock_status:
            mock_status.return_value = True

            result = runner.invoke(app, ["status", "test-project"])

            mock_status.assert_called_once_with("test-project")

    def test_create_subcommand(self, tmp_path, monkeypatch):
        """Test 'create' subcommand."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.commands.create.create_project") as mock_create:
            mock_create.return_value = tmp_path / "project"

            result = runner.invoke(app, ["create", "Test topic"])

            mock_create.assert_called_once()

    def test_run_subcommand(self, tmp_path, monkeypatch):
        """Test 'run' subcommand."""
        with patch("ralph.commands.run.run_research") as mock_run:
            mock_run.return_value = True

            result = runner.invoke(app, ["run", "test-project"])

            mock_run.assert_called_once()

    def test_reset_subcommand(self, tmp_path, monkeypatch):
        """Test 'reset' subcommand."""
        with patch("ralph.commands.reset.reset_project") as mock_reset:
            mock_reset.return_value = True

            result = runner.invoke(app, ["reset", "test-project", "--yes"])

            mock_reset.assert_called_once()
            # --yes skips confirmation
            assert mock_reset.call_args[1]["confirm"] is False

    def test_config_subcommand_show_all(self, tmp_path, monkeypatch):
        """Test 'config' subcommand showing all."""
        config_file = tmp_path / "config.yaml"
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        result = runner.invoke(app, ["config"])

        assert result.exit_code == 0
        assert "Configuration" in result.stdout

    def test_config_subcommand_set_value(self, tmp_path, monkeypatch):
        """Test 'config' subcommand setting value."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        result = runner.invoke(app, ["config", "default_papers=25"])

        assert result.exit_code == 0

    def test_init_subcommand_with_yes_creates_all(self, tmp_path, monkeypatch):
        """Test 'init -y' creates config, git, and files without prompts."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.config.ensure_current_dir_initialized") as mock_init:
            mock_init.return_value = {
                "config_created": True,
                "git_initialized": True,
                "files_created": ["AGENTS.md", "CLAUDE.md"],
            }

            result = runner.invoke(app, ["init", "-y"])

            assert result.exit_code == 0
            mock_init.assert_called_once()
            assert "Initialized" in result.stdout
            assert "config" in result.stdout.lower()
            assert "git" in result.stdout.lower()

    def test_init_subcommand_with_yes_creates_only_files(self, tmp_path, monkeypatch):
        """Test 'init -y' when only files need creation."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.config.ensure_current_dir_initialized") as mock_init:
            mock_init.return_value = {
                "config_created": False,
                "git_initialized": False,
                "files_created": ["prompt.md", "MISSION.md"],
            }

            result = runner.invoke(app, ["init", "-y"])

            assert result.exit_code == 0
            assert "prompt.md" in result.stdout
            assert "MISSION.md" in result.stdout

    def test_init_subcommand_with_yes_already_initialized(self, tmp_path, monkeypatch):
        """Test 'init -y' when already initialized."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.config.ensure_current_dir_initialized") as mock_init:
            mock_init.return_value = {
                "config_created": False,
                "git_initialized": False,
                "files_created": [],
            }

            result = runner.invoke(app, ["init", "-y"])

            assert result.exit_code == 0
            assert "already initialized" in result.stdout.lower()

    def test_init_subcommand_interactive_mode(self, tmp_path, monkeypatch):
        """Test 'init' without -y calls interactive init."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.commands.interactive.check_and_prompt_init") as mock_prompt:
            mock_prompt.return_value = True  # User accepted initialization
            with patch("ralph.config.check_initialization_status") as mock_status:
                mock_status.return_value = {
                    "config_missing": False,
                    "git_missing": False,
                    "files_missing": [],
                }

                result = runner.invoke(app, ["init"])

                assert result.exit_code == 0
                mock_prompt.assert_called_once()

    def test_init_subcommand_interactive_already_initialized(self, tmp_path, monkeypatch):
        """Test 'init' when already initialized shows message."""
        monkeypatch.chdir(tmp_path)

        with patch("ralph.commands.interactive.check_and_prompt_init") as mock_prompt:
            mock_prompt.return_value = False  # Nothing to do
            with patch("ralph.config.check_initialization_status") as mock_status:
                mock_status.return_value = {
                    "config_missing": False,
                    "git_missing": False,
                    "files_missing": [],
                }

                result = runner.invoke(app, ["init"])

                assert result.exit_code == 0
                assert "already initialized" in result.stdout.lower()
