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
        config_dir = tmp_path / ".ralph"
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
        config_dir = tmp_path / ".ralph"
        config_file = config_dir / "config.yaml"

        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_file)

        config = Config(default_papers=50)
        save_config(config)

        assert config_file.exists()

    def test_save_writes_correct_values(self, tmp_path, monkeypatch):
        """Save writes correct values to file."""
        config_dir = tmp_path / ".ralph"
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
        config_dir = tmp_path / ".ralph"
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
        config_dir = tmp_path / ".ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("research_dir", str(tmp_path / "new-research"))

        assert success is True
        assert error is None

    def test_set_default_agent_valid(self, tmp_path, monkeypatch):
        """Set handles valid agent value."""
        config_dir = tmp_path / ".ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("default_agent", "amp")

        assert success is True
        assert error is None

    def test_set_default_agent_invalid(self, tmp_path, monkeypatch):
        """Set returns False with error for invalid agent."""
        config_dir = tmp_path / ".ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("default_agent", "invalid_agent")

        assert success is False
        assert error is not None
        assert "Invalid value" in error

    def test_set_integer_field(self, tmp_path, monkeypatch):
        """Set handles integer fields."""
        config_dir = tmp_path / ".ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("default_papers", "50")

        assert success is True
        assert error is None

    def test_set_integer_field_invalid(self, tmp_path, monkeypatch):
        """Set returns False with error for invalid integer."""
        config_dir = tmp_path / ".ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("default_papers", "not_a_number")

        assert success is False
        assert error is not None
        assert "Invalid value" in error

    def test_set_boolean_field_true_values(self, tmp_path, monkeypatch):
        """Set handles boolean true values."""
        config_dir = tmp_path / ".ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        for value in ["true", "1", "yes"]:
            success, error = set_config_value("live_output", value)
            assert success is True
            assert error is None

    def test_set_boolean_field_false_value(self, tmp_path, monkeypatch):
        """Set handles boolean false value."""
        config_dir = tmp_path / ".ralph"
        config_dir.mkdir()
        monkeypatch.setattr("ralph.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("ralph.config.CONFIG_FILE", config_dir / "config.yaml")

        success, error = set_config_value("live_output", "false")

        assert success is True
        assert error is None

    def test_set_unknown_key(self, tmp_path, monkeypatch):
        """Set returns False with error for unknown key."""
        config_dir = tmp_path / ".ralph"
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

    def test_creates_missing_files(self, tmp_path, monkeypatch):
        """Function creates missing template files."""
        monkeypatch.chdir(tmp_path)

        # Create mock templates
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (template_dir / f).write_text(f"# {f}")

        with patch("ralph.config._get_repo_root", return_value=template_dir):
            created, files = ensure_current_dir_initialized()

        assert created is True
        assert len(files) == 4

    def test_no_op_if_all_exist(self, tmp_path, monkeypatch):
        """Function does nothing if all files exist."""
        monkeypatch.chdir(tmp_path)

        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (tmp_path / f).write_text(f"# {f}")

        created, files = ensure_current_dir_initialized()

        assert created is False
        assert files == []

    def test_creates_only_missing(self, tmp_path, monkeypatch):
        """Function creates only missing files."""
        monkeypatch.chdir(tmp_path)

        # Create some existing files
        (tmp_path / "AGENTS.md").write_text("# Existing")
        (tmp_path / "CLAUDE.md").write_text("# Existing")

        # Create templates
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        for f in ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]:
            (template_dir / f).write_text(f"# {f}")

        with patch("ralph.config._get_repo_root", return_value=template_dir):
            created, files = ensure_current_dir_initialized()

        assert created is True
        assert len(files) == 2
        assert "prompt.md" in files
        assert "MISSION.md" in files
