"""Configuration management for Research-Ralph."""

import os
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field


class Agent(str, Enum):
    """Supported AI agents."""

    CLAUDE = "claude"
    AMP = "amp"
    CODEX = "codex"


class Config(BaseModel):
    """Research-Ralph configuration."""

    research_dir: Path = Field(
        default=Path("~/research").expanduser(),
        description="Directory to store research projects",
    )
    default_agent: Agent = Field(default=Agent.CLAUDE, description="Default AI agent to use")
    default_papers: int = Field(default=20, ge=1, description="Default target papers count")
    live_output: bool = Field(default=True, description="Show live agent output during run")
    max_consecutive_failures: int = Field(default=3, ge=1, description="Max failures before aborting")

    model_config = ConfigDict(use_enum_values=True)


# Default config path
CONFIG_DIR = Path.home() / ".research-ralph"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def get_config_dir() -> Path:
    """Get or create the config directory."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> Config:
    """Load configuration from ~/.research-ralph/config.yaml or return defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = yaml.safe_load(f) or {}
            # Handle path expansion
            if "research_dir" in data:
                data["research_dir"] = Path(data["research_dir"]).expanduser()
            return Config(**data)
        except yaml.YAMLError as e:
            print(f"Warning: Config file has invalid YAML: {e}. Using defaults.", file=sys.stderr)
            return Config()
        except (PermissionError, OSError) as e:
            print(f"Warning: Cannot read config file: {e}. Using defaults.", file=sys.stderr)
            return Config()
        except Exception as e:
            print(f"Warning: Config load failed ({type(e).__name__}). Using defaults.", file=sys.stderr)
            return Config()
    return Config()


def save_config(config: Config) -> None:
    """Save configuration to ~/.research-ralph/config.yaml.

    Raises:
        PermissionError: If config file is not writable
        OSError: If config file cannot be saved
    """
    try:
        get_config_dir()
        data = config.model_dump()
        # Convert Path to string for YAML serialization
        data["research_dir"] = str(data["research_dir"])
        # Note: use_enum_values=True should handle this, but model_dump() returns
        # the string value directly, so this check is a safety fallback
        if hasattr(data["default_agent"], "value"):
            data["default_agent"] = data["default_agent"].value
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except PermissionError:
        print(f"Error: Cannot write config file (permission denied): {CONFIG_FILE}", file=sys.stderr)
        raise
    except OSError as e:
        print(f"Error: Cannot save config file: {e}", file=sys.stderr)
        raise


def get_config_value(key: str) -> Optional[str]:
    """Get a single config value as string."""
    config = load_config()
    if hasattr(config, key):
        return str(getattr(config, key))
    return None


def set_config_value(key: str, value: str) -> tuple[bool, Optional[str]]:
    """Set a single config value.

    Returns:
        Tuple of (success, error_message). error_message is None on success.
    """
    config = load_config()
    if key not in Config.model_fields:
        valid_keys = ", ".join(sorted(Config.model_fields.keys()))
        return False, f"Unknown config key: {key}. Valid keys: {valid_keys}"

    try:
        field_type = Config.model_fields[key].annotation
        converted = _convert_config_value(value, field_type)
        setattr(config, key, converted)
        save_config(config)
        return True, None
    except ValueError as e:
        return False, f"Invalid value for {key}: {e}"
    except (PermissionError, OSError) as e:
        return False, f"Failed to save config: {e}"


def _convert_config_value(value: str, field_type: type) -> object:
    """Convert a string value to the appropriate type for config."""
    if field_type is Path:
        return Path(value).expanduser()
    if field_type is Agent:
        return Agent(value)
    if field_type is int:
        return int(value)
    if field_type is bool:
        return value.lower() in ("true", "1", "yes")
    return value


def _get_repo_root() -> Path:
    """Get the repository root directory."""
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Max 5 levels up
        if (current / "pyproject.toml").exists() or (current / "prompt.md").exists():
            return current
        current = current.parent
    return Path(__file__).parent.parent


def resolve_research_path(path: str) -> Optional[Path]:
    """
    Resolve a research project path. Checks:
    1. Current directory if "." or empty
    2. Absolute path
    3. Relative to current directory
    4. Project name in current directory subdirs
    5. Project name in research_dir (fallback)
    6. Legacy researches/ folder

    Returns None if not found.
    """
    cwd = Path.cwd()

    # If "." or empty, check if cwd is a research project
    if path in (".", "") and (cwd / "rrd.json").exists():
        return cwd

    p = Path(path)

    # Try as-is (absolute or relative to cwd)
    if p.is_absolute() and p.exists():
        return p
    if p.exists():
        return p.resolve()

    # Try as project name in cwd subdirectories
    cwd_project = cwd / path
    if cwd_project.exists() and (cwd_project / "rrd.json").exists():
        return cwd_project

    # Fallback to configured research_dir
    config = load_config()
    if (config.research_dir / path).exists():
        return config.research_dir / path

    # Legacy researches/ folder
    script_dir = Path(__file__).parent.parent
    legacy_path = script_dir / "researches" / path
    if legacy_path.exists():
        return legacy_path

    return None


def _collect_projects_from_dir(
    directory: Path, projects: list[Path], seen_names: set[str]
) -> None:
    """Collect research projects from a directory into the projects list."""
    try:
        for item in directory.iterdir():
            if item.is_dir() and item.name not in seen_names and (item / "rrd.json").exists():
                projects.append(item)
                seen_names.add(item.name)
    except PermissionError:
        pass


def list_research_projects() -> list[Path]:
    """
    List all research projects. Looks in:
    1. Current directory (if it has rrd.json, treat as single project)
    2. Subdirectories of current directory
    3. Configured research_dir (fallback)
    4. Script's researches/ folder (legacy)

    Returns list of project paths sorted by modification time (most recent first).
    """
    projects: list[Path] = []
    seen_names: set[str] = set()
    cwd = Path.cwd()

    # Check if current directory itself is a research project
    if (cwd / "rrd.json").exists():
        projects.append(cwd)
        seen_names.add(cwd.name)

    # Check subdirectories of current directory
    _collect_projects_from_dir(cwd, projects, seen_names)

    # Fallback to configured research_dir (if different from cwd)
    config = load_config()
    if config.research_dir.exists() and config.research_dir.resolve() != cwd.resolve():
        _collect_projects_from_dir(config.research_dir, projects, seen_names)

    # Check legacy researches/ folder
    script_dir = Path(__file__).parent.parent
    legacy_dir = script_dir / "researches"
    if legacy_dir.exists() and legacy_dir.resolve() != cwd.resolve():
        _collect_projects_from_dir(legacy_dir, projects, seen_names)

    return sorted(projects, key=lambda p: p.stat().st_mtime, reverse=True)


def ensure_research_dir() -> Path:
    """Ensure the research directory exists and return its path."""
    config = load_config()
    config.research_dir.mkdir(parents=True, exist_ok=True)
    return config.research_dir


def ensure_current_dir_initialized() -> dict[str, object]:
    """
    Ensure current directory is fully initialized for Research-Ralph.

    Performs:
    1. Creates ~/.research-ralph/config.yaml if missing
    2. Initializes git repo if not present
    3. Creates AGENTS.md, CLAUDE.md, prompt.md, MISSION.md if missing

    Returns:
        Dict with keys: config_created, git_initialized, files_created
    """
    import shutil
    import subprocess

    result: dict[str, object] = {
        "config_created": False,
        "git_initialized": False,
        "files_created": [],
    }

    cwd = Path.cwd()

    # 1. Ensure config file exists
    if not CONFIG_FILE.exists():
        save_config(Config())
        result["config_created"] = True

    # 2. Initialize git repo if not exists
    if not (cwd / ".git").exists():
        try:
            subprocess.run(
                ["git", "init"],
                cwd=cwd,
                capture_output=True,
                check=True,
            )
            result["git_initialized"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # Git not available or init failed

    # 3. Copy template files
    templates = ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]
    created_files: list[str] = []

    for template in templates:
        target = cwd / template
        if not target.exists():
            source = _get_repo_root() / template
            if source.exists():
                shutil.copy(source, target)
                created_files.append(template)

    result["files_created"] = created_files
    return result
