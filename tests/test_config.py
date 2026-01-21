"""Tests for configuration management."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

from ralph.config import (
    Agent,
    Config,
    load_config,
    save_config,
    get_config_value,
    set_config_value,
    resolve_research_path,
    list_research_projects,
    ensure_research_dir,
    check_initialization_status,
    needs_initialization,
    ensure_current_dir_initialized,
    get_config_dir,
    CONFIG_DIR,
    CONFIG_FILE,
)


class TestAgent:
    """Tests for Agent enum."""

    def test_agent_values(self):
        """Test agent values are correct."""
        assert Agent.CLAUDE.value == "claude"
        assert Agent.AMP.value == "amp"
        assert Agent.CODEX.value == "codex"

    def test_agent_count(self):
        """Test we have all expected agents."""
        assert len(Agent) == 3


class TestConfig:
    """Tests for Config model."""

    def test_defaults(self):
        """Test default Config values."""
        config = Config()
        assert config.default_agent == Agent.CLAUDE
        assert config.default_papers == 20
        assert config.live_output is True
        assert config.max_consecutive_failures == 3

    def test_research_dir_default_expanded(self):
        """Test research_dir default is expanded."""
        config = Config()
        # Should not contain ~
        assert "~" not in str(config.research_dir)

    def test_custom_values(self, tmp_path):
        """Test Config with custom values."""
        config = Config(
            research_dir=tmp_path,
            default_agent=Agent.AMP,
            default_papers=50,
            live_output=False,
            max_consecutive_failures=5,
        )
        assert config.research_dir == tmp_path
        assert config.default_agent == Agent.AMP
        assert config.default_papers == 50
        assert config.live_output is False
        assert config.max_consecutive_failures == 5

    def test_serialization(self, tmp_path):
        """Test Config serialization."""
        config = Config(research_dir=tmp_path)
        data = config.model_dump()
        assert "research_dir" in data
        assert "default_agent" in data
        # Agent should serialize as string value
        assert data["default_agent"] == "claude"


class TestGetConfigDir:
    """Tests for get_config_dir function."""

    def test_creates_directory(self, tmp_path, monkeypatch):
        """Test that get_config_dir creates directory."""
        config_dir = tmp_path / ".research-ralph"
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)

        result = get_config_dir()

        assert result.exists()
        assert result == config_dir


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_defaults_when_no_file(self, tmp_path, monkeypatch):
        """Load returns defaults when config file doesn't exist."""
        monkeypatch.setattr("ralph.config.CONFIG_FILE", tmp_path / "nonexistent.yaml")

        config = load_config()

        assert config.default_agent == Agent.CLAUDE
        assert config.default_papers == 20

    def test_load_from_file(self, tmp_path, monkeypatch):
        """Load reads values from config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
research_dir: /tmp/research
default_agent: amp
default_papers: 30
live_output: false
max_consecutive_failures: 5
"""
        )
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        config = load_config()

        assert config.default_agent == Agent.AMP
        assert config.default_papers == 30
        assert config.live_output is False
        assert config.max_consecutive_failures == 5

    def test_load_handles_path_expansion(self, tmp_path, monkeypatch):
        """Load expands ~ in research_dir."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("research_dir: ~/my-research")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        config = load_config()

        assert "~" not in str(config.research_dir)

    def test_load_returns_defaults_on_parse_error(self, tmp_path, monkeypatch):
        """Load returns defaults on YAML parse error."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: {{")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        config = load_config()

        # Should return defaults
        assert config.default_papers == 20

    def test_load_handles_empty_file(self, tmp_path, monkeypatch):
        """Load handles empty config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        config = load_config()

        assert config.default_papers == 20

    def test_load_partial_config(self, tmp_path, monkeypatch):
        """Load handles partial config (uses defaults for missing)."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_papers: 50")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        config = load_config()

        assert config.default_papers == 50
        assert config.default_agent == Agent.CLAUDE  # Default


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_creates_file(self, tmp_path, monkeypatch):
        """Save creates config file."""
        config_dir = tmp_path / ".research-ralph"
        config_file = config_dir / "config.yaml"

        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        config = Config(default_papers=50)
        save_config(config)

        assert config_file.exists()

    def test_save_writes_correct_values(self, tmp_path, monkeypatch):
        """Save writes correct values to file."""
        config_dir = tmp_path / ".research-ralph"
        config_file = config_dir / "config.yaml"
        config_dir.mkdir()

        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        config = Config(
            research_dir=tmp_path / "research",
            default_papers=50,
            default_agent=Agent.AMP,
        )
        save_config(config)

        with open(config_file) as f:
            data = yaml.safe_load(f)

        assert data["default_papers"] == 50
        assert data["default_agent"] == "amp"
        assert "research" in data["research_dir"]

    def test_save_overwrites_existing(self, tmp_path, monkeypatch):
        """Save overwrites existing config file."""
        config_dir = tmp_path / ".research-ralph"
        config_file = config_dir / "config.yaml"
        config_dir.mkdir()
        config_file.write_text("default_papers: 10")

        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        config = Config(default_papers=50)
        save_config(config)

        with open(config_file) as f:
            data = yaml.safe_load(f)

        assert data["default_papers"] == 50


class TestGetConfigValue:
    """Tests for get_config_value function."""

    def test_get_existing_key(self, tmp_path, monkeypatch):
        """Get returns value for existing key."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_papers: 30")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        value = get_config_value("default_papers")

        assert value == "30"

    def test_get_nonexistent_key(self, tmp_path, monkeypatch):
        """Get returns None for nonexistent key."""
        monkeypatch.setattr("ralph.config.CONFIG_FILE", tmp_path / "none.yaml")

        value = get_config_value("nonexistent_key")

        assert value is None

    def test_get_all_keys(self, tmp_path, monkeypatch):
        """Get works for all config keys."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
research_dir: /tmp/test
default_agent: claude
default_papers: 25
live_output: true
max_consecutive_failures: 4
"""
        )
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        assert get_config_value("research_dir") is not None
        assert get_config_value("default_agent") == "claude"
        assert get_config_value("default_papers") == "25"
        assert get_config_value("live_output") == "True"
        assert get_config_value("max_consecutive_failures") == "4"


class TestSetConfigValue:
    """Tests for set_config_value function."""

    def test_set_research_dir(self, tmp_path, monkeypatch):
        """Set handles research_dir path."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("research_dir", str(tmp_path / "new-research"))

        assert success is True
        assert error is None

    def test_set_default_agent_valid(self, tmp_path, monkeypatch):
        """Set handles valid agent value."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("default_agent", "amp")

        assert success is True
        assert error is None

    def test_set_default_agent_invalid(self, tmp_path, monkeypatch):
        """Set returns False with error for invalid agent."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("default_agent", "invalid_agent")

        assert success is False
        assert error is not None
        assert "Invalid value" in error

    def test_set_integer_field(self, tmp_path, monkeypatch):
        """Set handles integer fields."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("default_papers", "50")

        assert success is True
        assert error is None

    def test_set_integer_field_invalid(self, tmp_path, monkeypatch):
        """Set returns False with error for invalid integer."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("default_papers", "not_a_number")

        assert success is False
        assert error is not None
        assert "Invalid value" in error

    def test_set_boolean_field_true_values(self, tmp_path, monkeypatch):
        """Set handles boolean true values."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        for value in ["true", "1", "yes"]:
            success, error = set_config_value("live_output", value)
            assert success is True
            assert error is None

    def test_set_boolean_field_false_value(self, tmp_path, monkeypatch):
        """Set handles boolean false value."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("live_output", "false")

        assert success is True
        assert error is None

    def test_set_unknown_key(self, tmp_path, monkeypatch):
        """Set returns False with error for unknown key."""
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("unknown_key", "value")

        assert success is False
        assert error is not None
        assert "Unknown config key" in error


class TestResolveResearchPath:
    """Tests for resolve_research_path function."""

    def test_resolve_dot_as_cwd(self, tmp_path, monkeypatch):
        """Resolve '.' returns cwd if it has rrd.json."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "rrd.json").write_text("{}")

        result = resolve_research_path(".")

        assert result == tmp_path

    def test_resolve_empty_string(self, tmp_path, monkeypatch):
        """Resolve empty string returns cwd if it has rrd.json."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "rrd.json").write_text("{}")

        result = resolve_research_path("")

        assert result == tmp_path

    def test_resolve_absolute_path(self, tmp_path):
        """Resolve handles absolute path."""
        project = tmp_path / "my-project"
        project.mkdir()

        result = resolve_research_path(str(project))

        assert result == project

    def test_resolve_relative_path(self, tmp_path, monkeypatch):
        """Resolve handles relative path."""
        monkeypatch.chdir(tmp_path)
        project = tmp_path / "subdir"
        project.mkdir()

        result = resolve_research_path("subdir")

        assert result == project.resolve()

    def test_resolve_project_name_in_cwd(self, tmp_path, monkeypatch):
        """Resolve finds project by name in cwd subdirectory."""
        monkeypatch.chdir(tmp_path)
        project = tmp_path / "my-research"
        project.mkdir()
        (project / "rrd.json").write_text("{}")

        result = resolve_research_path("my-research")

        assert result == project

    def test_resolve_not_found(self, tmp_path, monkeypatch):
        """Resolve returns None for non-existent path."""
        monkeypatch.chdir(tmp_path)
        # Also mock config to prevent fallback
        monkeypatch.setattr(
            "ralph.config.load_config",
            lambda: Config(research_dir=tmp_path / "empty"),
        )

        result = resolve_research_path("nonexistent")

        assert result is None

    def test_resolve_from_config_research_dir(self, tmp_path, monkeypatch):
        """Resolve finds project in configured research_dir."""
        research_dir = tmp_path / "research"
        research_dir.mkdir()
        project = research_dir / "my-project"
        project.mkdir()

        monkeypatch.chdir(tmp_path / "elsewhere" if (tmp_path / "elsewhere").exists() else tmp_path)
        monkeypatch.setattr(
            "ralph.config.load_config",
            lambda: Config(research_dir=research_dir),
        )

        result = resolve_research_path("my-project")

        assert result == project


class TestListResearchProjects:
    """Tests for list_research_projects function."""

    def test_returns_list(self, tmp_path, monkeypatch):
        """List returns a list of paths."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            "ralph.config.load_config",
            lambda: Config(research_dir=tmp_path / "empty"),
        )

        projects = list_research_projects()

        # Verify it returns a list (may include legacy projects)
        assert isinstance(projects, list)
        assert all(isinstance(p, Path) for p in projects)

    def test_finds_projects_in_cwd(self, tmp_path, monkeypatch):
        """List finds projects in current directory."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            "ralph.config.load_config",
            lambda: Config(research_dir=tmp_path / "other"),
        )

        # Create projects in cwd
        p1 = tmp_path / "project1"
        p1.mkdir()
        (p1 / "rrd.json").write_text("{}")

        p2 = tmp_path / "project2"
        p2.mkdir()
        (p2 / "rrd.json").write_text("{}")

        projects = list_research_projects()

        assert len(projects) >= 2

    def test_cwd_as_project(self, tmp_path, monkeypatch):
        """List includes cwd if it has rrd.json."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "rrd.json").write_text("{}")
        monkeypatch.setattr(
            "ralph.config.load_config",
            lambda: Config(research_dir=tmp_path / "other"),
        )

        projects = list_research_projects()

        assert tmp_path in projects

    def test_sorted_by_mtime(self, tmp_path, monkeypatch):
        """List returns projects sorted by modification time."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            "ralph.config.load_config",
            lambda: Config(research_dir=tmp_path / "other"),
        )

        import time

        p1 = tmp_path / "older"
        p1.mkdir()
        (p1 / "rrd.json").write_text("{}")

        time.sleep(0.1)

        p2 = tmp_path / "newer"
        p2.mkdir()
        (p2 / "rrd.json").write_text("{}")

        projects = list_research_projects()

        # Newer should be first
        names = [p.name for p in projects if p.name in ("older", "newer")]
        if len(names) == 2:
            assert names.index("newer") < names.index("older")


class TestEnsureResearchDir:
    """Tests for ensure_research_dir function."""

    def test_creates_directory(self, tmp_path, monkeypatch):
        """Test that ensure_research_dir creates directory."""
        research_dir = tmp_path / "new-research"
        monkeypatch.setattr(
            "ralph.config.load_config",
            lambda: Config(research_dir=research_dir),
        )

        result = ensure_research_dir()

        assert result.exists()
        assert result == research_dir

    def test_returns_existing(self, tmp_path, monkeypatch):
        """Test ensure_research_dir returns existing directory."""
        research_dir = tmp_path / "existing"
        research_dir.mkdir()
        monkeypatch.setattr(
            "ralph.config.load_config",
            lambda: Config(research_dir=research_dir),
        )

        result = ensure_research_dir()

        assert result == research_dir


class TestEnsureCurrentDirInitialized:
    """Tests for ensure_current_dir_initialized function."""

    def test_creates_config_file(self, tmp_path, monkeypatch):
        """Function creates config file if missing."""
        monkeypatch.chdir(tmp_path)

        config_dir = tmp_path / ".research-ralph"
        config_file = config_dir / "config.yaml"
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        # Create templates dir (required for _get_repo_root)
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        with patch("ralph.config._get_repo_root", return_value=template_dir):
            result = ensure_current_dir_initialized()

        assert result["config_created"] is True
        assert config_file.exists()

    def test_skips_existing_config(self, tmp_path, monkeypatch):
        """Function does not recreate existing config."""
        monkeypatch.chdir(tmp_path)

        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("default_papers: 42")
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        with patch("ralph.config._get_repo_root", return_value=template_dir):
            result = ensure_current_dir_initialized()

        assert result["config_created"] is False
        # Original content preserved
        assert "42" in config_file.read_text()

    def test_initializes_git_repo(self, tmp_path, monkeypatch):
        """Function initializes git repo if missing."""
        monkeypatch.chdir(tmp_path)

        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        with patch("ralph.config._get_repo_root", return_value=template_dir):
            result = ensure_current_dir_initialized()

        assert result["git_initialized"] is True
        assert (tmp_path / ".git").exists()

    def test_skips_existing_git_repo(self, tmp_path, monkeypatch):
        """Function does not reinitialize existing git repo."""
        monkeypatch.chdir(tmp_path)

        # Create existing .git directory
        (tmp_path / ".git").mkdir()

        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        with patch("ralph.config._get_repo_root", return_value=template_dir):
            result = ensure_current_dir_initialized()

        assert result["git_initialized"] is False

    def test_creates_missing_template_files(self, tmp_path, monkeypatch):
        """Function creates missing template files."""
        monkeypatch.chdir(tmp_path)

        # Pre-create config and git to focus on template files
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)
        (tmp_path / ".git").mkdir()

        # Create mock templates
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (template_dir / f).write_text(f"# {f}")

        with patch("ralph.config._get_repo_root", return_value=template_dir):
            result = ensure_current_dir_initialized()

        assert len(result["files_created"]) == 4
        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            assert (tmp_path / f).exists()

    def test_no_op_if_all_exist(self, tmp_path, monkeypatch):
        """Function does nothing if all files exist."""
        monkeypatch.chdir(tmp_path)

        # Pre-create everything
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)
        (tmp_path / ".git").mkdir()

        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (tmp_path / f).write_text(f"# {f}")

        result = ensure_current_dir_initialized()

        assert result["config_created"] is False
        assert result["git_initialized"] is False
        assert result["files_created"] == []

    def test_creates_only_missing_templates(self, tmp_path, monkeypatch):
        """Function creates only missing template files."""
        monkeypatch.chdir(tmp_path)

        # Pre-create config and git
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)
        (tmp_path / ".git").mkdir()

        # Create some existing files
        (tmp_path / "AGENTS.md").write_text("# Existing")
        (tmp_path / "CLAUDE.md").write_text("# Existing")

        # Create templates
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (template_dir / f).write_text(f"# {f}")

        with patch("ralph.config._get_repo_root", return_value=template_dir):
            result = ensure_current_dir_initialized()

        assert len(result["files_created"]) == 2
        assert "prompt.md" in result["files_created"]
        assert "MISSION.md" in result["files_created"]

    def test_handles_git_not_available(self, tmp_path, monkeypatch):
        """Function handles git command not being available."""
        monkeypatch.chdir(tmp_path)

        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Mock subprocess.run to raise FileNotFoundError (git not found)
        with patch("ralph.config._get_repo_root", return_value=template_dir):
            with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
                result = ensure_current_dir_initialized()

        # Should not crash, just skip git init
        assert result["git_initialized"] is False
        assert not (tmp_path / ".git").exists()


class TestCheckInitializationStatus:
    """Tests for check_initialization_status function."""

    def test_all_missing(self, tmp_path, monkeypatch):
        """Returns all missing when nothing is initialized."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", tmp_path / "nonexistent.yaml")

        status = check_initialization_status()

        assert status["config_missing"] is True
        assert status["git_missing"] is True
        assert len(status["files_missing"]) == 4

    def test_nothing_missing(self, tmp_path, monkeypatch):
        """Returns nothing missing when fully initialized."""
        monkeypatch.chdir(tmp_path)

        # Create config
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        # Create git
        (tmp_path / ".git").mkdir()

        # Create template files
        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (tmp_path / f).write_text(f"# {f}")

        status = check_initialization_status()

        assert status["config_missing"] is False
        assert status["git_missing"] is False
        assert status["files_missing"] == []

    def test_partial_missing(self, tmp_path, monkeypatch):
        """Returns only missing items when partially initialized."""
        monkeypatch.chdir(tmp_path)

        # Create config
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        # Create git but NOT template files
        (tmp_path / ".git").mkdir()

        status = check_initialization_status()

        assert status["config_missing"] is False
        assert status["git_missing"] is False
        assert len(status["files_missing"]) == 4

    def test_some_files_missing(self, tmp_path, monkeypatch):
        """Returns only missing files when some exist."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", tmp_path / "config.yaml")

        # Create some template files
        (tmp_path / "AGENTS.md").write_text("# Agents")
        (tmp_path / "CLAUDE.md").write_text("# Claude")

        status = check_initialization_status()

        assert "AGENTS.md" not in status["files_missing"]
        assert "CLAUDE.md" not in status["files_missing"]
        assert "prompt.md" in status["files_missing"]
        assert "MISSION.md" in status["files_missing"]


class TestNeedsInitialization:
    """Tests for needs_initialization function."""

    def test_returns_true_when_config_missing(self, tmp_path, monkeypatch):
        """Returns True when config is missing."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", tmp_path / "nonexistent.yaml")
        (tmp_path / ".git").mkdir()
        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (tmp_path / f).write_text(f"# {f}")

        assert needs_initialization() is True

    def test_returns_true_when_git_missing(self, tmp_path, monkeypatch):
        """Returns True when git is missing."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)
        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (tmp_path / f).write_text(f"# {f}")

        assert needs_initialization() is True

    def test_returns_true_when_files_missing(self, tmp_path, monkeypatch):
        """Returns True when template files are missing."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)
        (tmp_path / ".git").mkdir()

        assert needs_initialization() is True

    def test_returns_false_when_all_initialized(self, tmp_path, monkeypatch):
        """Returns False when everything is initialized."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_papers: 20")
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)
        (tmp_path / ".git").mkdir()
        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (tmp_path / f).write_text(f"# {f}")

        assert needs_initialization() is False


class TestSaveConfigErrors:
    """Tests for save_config error handling."""

    def test_save_raises_permission_error(self, tmp_path, monkeypatch):
        """Test save raises PermissionError when dir not writable."""
        import os

        # Create a read-only directory
        config_dir = tmp_path / ".research-ralph"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"

        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        # Make directory read-only
        os.chmod(config_dir, 0o444)

        config = Config(default_papers=50)

        try:
            with pytest.raises(PermissionError):
                save_config(config)
        finally:
            # Restore permissions for cleanup
            os.chmod(config_dir, 0o755)


class TestConvertConfigValueEdgeCases:
    """Tests for _convert_config_value edge cases."""

    def test_convert_config_value_invalid_agent(self):
        """Test conversion raises for invalid agent."""
        from ralph.config import _convert_config_value, Agent

        with pytest.raises(ValueError):
            _convert_config_value("invalid_agent", Agent)

    def test_convert_config_value_invalid_int(self):
        """Test conversion raises for invalid int."""
        from ralph.config import _convert_config_value

        with pytest.raises(ValueError):
            _convert_config_value("not_a_number", int)

    def test_convert_config_value_valid_int(self):
        """Test conversion works for valid int."""
        from ralph.config import _convert_config_value

        result = _convert_config_value("42", int)
        assert result == 42

    def test_convert_config_value_valid_agent(self):
        """Test conversion works for valid agent."""
        from ralph.config import _convert_config_value, Agent

        result = _convert_config_value("amp", Agent)
        assert result == Agent.AMP

    def test_convert_config_value_bool_false(self):
        """Test conversion handles boolean false values."""
        from ralph.config import _convert_config_value

        for value in ["false", "0", "no", "FALSE", "False"]:
            result = _convert_config_value(value, bool)
            assert result is False

    def test_convert_config_value_path(self):
        """Test conversion handles Path type."""
        from ralph.config import _convert_config_value
        from pathlib import Path

        result = _convert_config_value("~/test/path", Path)
        assert isinstance(result, Path)
        assert "~" not in str(result)  # Should be expanded
