"""Shared pytest fixtures for Research-Ralph tests."""

import json
import pytest
from datetime import date
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

from ralph.models.paper import Paper, PaperStatus, ScoreBreakdown
from ralph.models.rrd import RRD, Phase, Requirements, Statistics, Mission, Insight
from ralph.config import Config, Agent


# ============================================================
# Temporary Directory Fixtures
# ============================================================


@pytest.fixture
def tmp_research_dir(tmp_path: Path) -> Path:
    """Create a temporary research directory."""
    research_dir = tmp_path / "research"
    research_dir.mkdir()
    return research_dir


@pytest.fixture
def tmp_project_dir(tmp_research_dir: Path) -> Path:
    """Create a temporary project directory with basic structure."""
    project_dir = tmp_research_dir / "test-project-2025-01-20"
    project_dir.mkdir()
    return project_dir


# ============================================================
# Sample Data Fixtures
# ============================================================


@pytest.fixture
def sample_paper() -> Paper:
    """Create a sample Paper instance."""
    return Paper(
        id="arxiv_2501.12345",
        title="Test Paper: AI in Research",
        url="https://arxiv.org/abs/2501.12345",
        pdf_url="https://arxiv.org/pdf/2501.12345.pdf",
        authors=["John Doe", "Jane Smith"],
        date=date(2025, 1, 20),
        source="arXiv",
        priority=4,
        status=PaperStatus.PENDING,
    )


@pytest.fixture
def sample_score_breakdown() -> ScoreBreakdown:
    """Create a sample ScoreBreakdown with mid-range scores."""
    return ScoreBreakdown(
        novelty=4,
        feasibility=3,
        time_to_poc=4,
        value_market=3,
        defensibility=2,
        adoption=3,
        market_creation=4,
        first_mover_window=3,
        network_data_effects=2,
        strategic_clarity=3,
    )


@pytest.fixture
def sample_requirements() -> Requirements:
    """Create sample research requirements."""
    return Requirements(
        focus_area="AI in robotics",
        keywords=["robotics", "LLM", "VLA"],
        time_window_days=30,
        target_papers=20,
        sources=["arXiv", "Google Scholar"],
    )


@pytest.fixture
def sample_rrd(sample_requirements: Requirements) -> RRD:
    """Create a sample RRD instance."""
    return RRD(
        project="AI Robotics Research",
        branchName="research/ai-robotics",
        description="Research on AI applications in robotics",
        requirements=sample_requirements,
        phase=Phase.DISCOVERY,
    )


@pytest.fixture
def sample_rrd_with_papers(sample_rrd: RRD) -> RRD:
    """Create an RRD with papers in the pool."""
    papers = [
        Paper(
            id=f"arxiv_{i}",
            title=f"Paper {i}",
            url=f"http://test/{i}",
            status=PaperStatus.PENDING if i < 5 else PaperStatus.PRESENTED,
        )
        for i in range(10)
    ]
    sample_rrd.papers_pool = papers
    sample_rrd.statistics.total_discovered = 10
    sample_rrd.statistics.total_analyzed = 5
    sample_rrd.statistics.total_presented = 3
    sample_rrd.statistics.total_rejected = 2
    return sample_rrd


@pytest.fixture
def rrd_json_data(sample_rrd: RRD) -> dict:
    """Get RRD as JSON-serializable dict."""
    return json.loads(sample_rrd.model_dump_json())


# ============================================================
# File System Fixtures
# ============================================================


@pytest.fixture
def project_with_rrd(tmp_project_dir: Path, rrd_json_data: dict) -> Path:
    """Create a project directory with rrd.json."""
    rrd_path = tmp_project_dir / "rrd.json"
    with open(rrd_path, "w") as f:
        json.dump(rrd_json_data, f, indent=2)
    return tmp_project_dir


@pytest.fixture
def project_with_progress(project_with_rrd: Path) -> Path:
    """Create a project with progress.txt."""
    progress_path = project_with_rrd / "progress.txt"
    progress_path.write_text("# Research Progress\n\n## Findings\n- Initial setup\n")
    return project_with_rrd


# ============================================================
# Config Fixtures
# ============================================================


@pytest.fixture
def mock_config(tmp_research_dir: Path) -> Config:
    """Create a mock configuration."""
    return Config(
        research_dir=tmp_research_dir,
        default_agent=Agent.CLAUDE,
        default_papers=20,
        live_output=False,
        max_consecutive_failures=3,
    )


@pytest.fixture
def mock_config_file(tmp_path: Path, mock_config: Config) -> Path:
    """Create a mock config file."""
    config_dir = tmp_path / ".ralph"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"

    import yaml

    data = mock_config.model_dump()
    data["research_dir"] = str(data["research_dir"])
    with open(config_file, "w") as f:
        yaml.dump(data, f)

    return config_file


# ============================================================
# Mock Subprocess Fixtures
# ============================================================


@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run returning success."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Success output"
    mock_result.stderr = ""
    return mock_result


@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.run returning failure."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Error: 429 Too Many Requests"
    return mock_result


@pytest.fixture
def mock_subprocess_complete():
    """Mock subprocess.run returning completion signal."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Research done! <promise>COMPLETE</promise>"
    mock_result.stderr = ""
    return mock_result


# ============================================================
# Agent Mock Fixtures
# ============================================================


@pytest.fixture
def mock_agent_available():
    """Mock shutil.which to return agent is available."""
    with patch("shutil.which", return_value="/usr/local/bin/claude"):
        yield


@pytest.fixture
def mock_agent_unavailable():
    """Mock shutil.which to return agent not available."""
    with patch("shutil.which", return_value=None):
        yield


# ============================================================
# Console Mock Fixture
# ============================================================


@pytest.fixture
def mock_console():
    """Mock Rich console for output capture."""
    with patch("ralph.ui.console.console") as mock:
        yield mock


# ============================================================
# Sample Insight Fixture
# ============================================================


@pytest.fixture
def sample_insight() -> Insight:
    """Create a sample Insight instance."""
    return Insight(
        id="ins_1",
        paper_id="arxiv_2501.12345",
        insight="Key finding about VLA architectures",
        tags=["VLA", "robotics"],
        cross_refs=["arxiv_2501.12346"],
    )
