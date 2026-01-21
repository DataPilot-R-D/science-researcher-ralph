"""Configuration management for Research-Ralph."""

import os
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


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

    class Config:
        use_enum_values = True


# Default config path
CONFIG_DIR = Path.home() / ".ralph"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def get_config_dir() -> Path:
    """Get or create the config directory."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> Config:
    """Load configuration from ~/.ralph/config.yaml or return defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = yaml.safe_load(f) or {}
            # Handle path expansion
            if "research_dir" in data:
                data["research_dir"] = Path(data["research_dir"]).expanduser()
            return Config(**data)
        except Exception:
            # Return defaults on any error
            return Config()
    return Config()


def save_config(config: Config) -> None:
    """Save configuration to ~/.ralph/config.yaml."""
    get_config_dir()
    data = config.model_dump()
    # Convert Path to string for YAML serialization
    data["research_dir"] = str(data["research_dir"])
    # Convert enum to string value for YAML serialization
    if hasattr(data["default_agent"], "value"):
        data["default_agent"] = data["default_agent"].value
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def get_config_value(key: str) -> Optional[str]:
    """Get a single config value as string."""
    config = load_config()
    if hasattr(config, key):
        return str(getattr(config, key))
    return None


def set_config_value(key: str, value: str) -> bool:
    """Set a single config value. Returns True on success."""
    config = load_config()
    if not hasattr(config, key):
        return False

    # Type conversion based on field type
    if key == "research_dir":
        setattr(config, key, Path(value).expanduser())
    elif key == "default_agent":
        try:
            setattr(config, key, Agent(value))
        except ValueError:
            return False
    elif key in ("default_papers", "max_consecutive_failures"):
        try:
            setattr(config, key, int(value))
        except ValueError:
            return False
    elif key == "live_output":
        setattr(config, key, value.lower() in ("true", "1", "yes"))
    else:
        setattr(config, key, value)

    save_config(config)
    return True


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


def list_research_projects() -> list[Path]:
    """
    List all research projects. Looks in:
    1. Current directory (if it has rrd.json, treat as single project)
    2. Subdirectories of current directory
    3. Configured research_dir (fallback)
    4. Script's researches/ folder (legacy)

    Returns list of project paths.
    """
    projects: list[Path] = []
    seen_names: set[str] = set()
    cwd = Path.cwd()

    # Check if current directory itself is a research project
    if (cwd / "rrd.json").exists():
        projects.append(cwd)
        seen_names.add(cwd.name)

    # Check subdirectories of current directory
    try:
        for item in cwd.iterdir():
            if item.is_dir() and item.name not in seen_names and (item / "rrd.json").exists():
                projects.append(item)
                seen_names.add(item.name)
    except PermissionError:
        pass

    # Fallback to configured research_dir (if different from cwd)
    config = load_config()
    if config.research_dir.exists() and config.research_dir.resolve() != cwd.resolve():
        try:
            for item in config.research_dir.iterdir():
                if item.is_dir() and item.name not in seen_names and (item / "rrd.json").exists():
                    projects.append(item)
                    seen_names.add(item.name)
        except PermissionError:
            pass

    # Check legacy researches/ folder
    script_dir = Path(__file__).parent.parent
    legacy_dir = script_dir / "researches"
    if legacy_dir.exists() and legacy_dir.resolve() != cwd.resolve():
        try:
            for item in legacy_dir.iterdir():
                if item.is_dir() and item.name not in seen_names and (item / "rrd.json").exists():
                    projects.append(item)
        except PermissionError:
            pass

    # Sort by modification time (most recent first)
    return sorted(projects, key=lambda p: p.stat().st_mtime, reverse=True)


def ensure_research_dir() -> Path:
    """Ensure the research directory exists and return its path."""
    config = load_config()
    config.research_dir.mkdir(parents=True, exist_ok=True)
    return config.research_dir


def ensure_current_dir_initialized() -> tuple[bool, list[str]]:
    """
    Ensure current directory has necessary agent files.

    Creates AGENTS.md, CLAUDE.md, prompt.md, MISSION.md if missing.

    Returns:
        Tuple of (any_created, list_of_created_files)
    """
    import shutil

    cwd = Path.cwd()
    created_files: list[str] = []

    # Template files to copy
    templates = ["AGENTS.md", "CLAUDE.md", "prompt.md", "MISSION.md"]

    for template in templates:
        target = cwd / template
        if not target.exists():
            # Find template from package/repo root
            source = _get_repo_root() / template
            if source.exists():
                shutil.copy(source, target)
                created_files.append(template)

    return len(created_files) > 0, created_files
