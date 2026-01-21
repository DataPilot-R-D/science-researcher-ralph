"""Tests for SkillRunner class."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ralph.config import Agent
from ralph.core.skill_runner import SkillRunner, _get_repo_root


class TestGetRepoRoot:
    """Tests for _get_repo_root helper function."""

    def test_returns_path(self):
        """Test _get_repo_root returns a Path."""
        result = _get_repo_root()
        assert isinstance(result, Path)

    def test_finds_pyproject(self, tmp_path, monkeypatch):
        """Test finding repo root by pyproject.toml."""
        # Create pyproject.toml in tmp_path
        (tmp_path / "pyproject.toml").write_text("[project]")

        # Can't easily test this without mocking __file__ location


class TestSkillRunnerInit:
    """Tests for SkillRunner initialization."""

    def test_init_default_script_dir(self):
        """Test initialization with default script_dir."""
        runner = SkillRunner()
        assert runner.script_dir is not None
        assert runner.skills_dir == runner.script_dir / "skills"

    def test_init_custom_script_dir(self, tmp_path):
        """Test initialization with custom script_dir."""
        runner = SkillRunner(script_dir=tmp_path)
        assert runner.script_dir == tmp_path
        assert runner.skills_dir == tmp_path / "skills"


class TestSkillRunnerListSkills:
    """Tests for SkillRunner.list_skills method."""

    def test_list_skills_no_skills_dir(self, tmp_path):
        """Test listing skills when skills directory doesn't exist."""
        runner = SkillRunner(script_dir=tmp_path)
        result = runner.list_skills()
        assert result == []

    def test_list_skills_empty_dir(self, tmp_path):
        """Test listing skills when skills directory is empty."""
        (tmp_path / "skills").mkdir()
        runner = SkillRunner(script_dir=tmp_path)
        result = runner.list_skills()
        assert result == []

    def test_list_skills_single_skill(self, tmp_path):
        """Test listing single skill."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "rrd"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            '---\ndescription: "Create research documents"\n---\n\n# RRD Skill'
        )

        runner = SkillRunner(script_dir=tmp_path)
        result = runner.list_skills()

        assert len(result) == 1
        assert result[0]["name"] == "rrd"
        assert "Create research" in result[0]["description"]

    def test_list_skills_multiple_skills(self, tmp_path):
        """Test listing multiple skills."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        for name in ["alpha", "beta", "gamma"]:
            skill_dir = skills_dir / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f'---\ndescription: "{name} skill"\n---\n')

        runner = SkillRunner(script_dir=tmp_path)
        result = runner.list_skills()

        assert len(result) == 3
        # Should be sorted
        assert result[0]["name"] == "alpha"
        assert result[1]["name"] == "beta"
        assert result[2]["name"] == "gamma"

    def test_list_skills_no_skill_md(self, tmp_path):
        """Test listing skills when SKILL.md missing."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "invalid"
        skill_dir.mkdir()
        # No SKILL.md file

        runner = SkillRunner(script_dir=tmp_path)
        result = runner.list_skills()

        assert result == []

    def test_list_skills_description_truncation(self, tmp_path):
        """Test description is truncated to 60 chars."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "test"
        skill_dir.mkdir()
        long_desc = "A" * 100
        (skill_dir / "SKILL.md").write_text(f'---\ndescription: "{long_desc}"\n---\n')

        runner = SkillRunner(script_dir=tmp_path)
        result = runner.list_skills()

        assert len(result[0]["description"]) <= 60


class TestSkillRunnerGetSkillContent:
    """Tests for SkillRunner.get_skill_content method."""

    def test_get_skill_content_not_found(self, tmp_path):
        """Test getting content for non-existent skill."""
        runner = SkillRunner(script_dir=tmp_path)
        result = runner.get_skill_content("nonexistent")
        assert result is None

    def test_get_skill_content_strips_frontmatter(self, tmp_path):
        """Test content strips YAML frontmatter."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            '---\ndescription: "Test"\nversion: 1\n---\n\n# Main Content\n\nBody here.'
        )

        runner = SkillRunner(script_dir=tmp_path)
        result = runner.get_skill_content("test")

        assert result is not None
        assert "description" not in result
        assert "# Main Content" in result
        assert "Body here" in result

    def test_get_skill_content_no_frontmatter(self, tmp_path):
        """Test content when no frontmatter present."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Just Content\n\nNo frontmatter here.")

        runner = SkillRunner(script_dir=tmp_path)
        result = runner.get_skill_content("test")

        assert result is not None
        assert "# Just Content" in result


class TestSkillRunnerRunRrdSkill:
    """Tests for SkillRunner.run_rrd_skill method."""

    def test_run_rrd_skill_no_skill(self, tmp_path):
        """Test running RRD skill when not found."""
        runner = SkillRunner(script_dir=tmp_path)

        result_path, output = runner.run_rrd_skill("Test topic")

        assert result_path is None
        assert "not found" in output

    @patch("ralph.core.skill_runner.subprocess.run")
    @patch("ralph.core.skill_runner.AgentRunner")
    @patch("ralph.core.skill_runner.load_config")
    def test_run_rrd_skill_agent_not_available(
        self, mock_load_config, mock_agent_runner_class, mock_subprocess, tmp_path
    ):
        """Test running RRD skill when agent not available."""
        # Setup skill
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "rrd"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n---\n# RRD Content")

        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = False
        mock_runner.get_install_instructions.return_value = "Install claude"
        mock_agent_runner_class.return_value = mock_runner

        runner = SkillRunner(script_dir=tmp_path)
        result_path, output = runner.run_rrd_skill("Test topic")

        assert result_path is None
        assert "not available" in output

    @patch("ralph.core.skill_runner.subprocess.run")
    @patch("ralph.core.skill_runner.AgentRunner")
    @patch("ralph.core.skill_runner.load_config")
    def test_run_rrd_skill_timeout(
        self, mock_load_config, mock_agent_runner_class, mock_subprocess, tmp_path, monkeypatch
    ):
        """Test running RRD skill with timeout."""
        import subprocess

        monkeypatch.chdir(tmp_path)

        # Setup skill
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "rrd"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n---\n# RRD Content")

        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_agent_runner_class.return_value = mock_runner

        mock_subprocess.side_effect = subprocess.TimeoutExpired("cmd", 300)

        runner = SkillRunner(script_dir=tmp_path)
        result_path, output = runner.run_rrd_skill("Test topic")

        assert result_path is None
        assert "timed out" in output

    @patch("ralph.core.skill_runner.subprocess.run")
    @patch("ralph.core.skill_runner.AgentRunner")
    @patch("ralph.core.skill_runner.load_config")
    def test_run_rrd_skill_no_rrd_created(
        self, mock_load_config, mock_agent_runner_class, mock_subprocess, tmp_path, monkeypatch
    ):
        """Test running RRD skill when rrd.json not created."""
        monkeypatch.chdir(tmp_path)

        # Setup skill
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "rrd"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n---\n# RRD Content")

        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_agent_runner_class.return_value = mock_runner

        mock_subprocess.return_value = MagicMock(stdout="No RRD", stderr="", returncode=0)

        runner = SkillRunner(script_dir=tmp_path)
        result_path, output = runner.run_rrd_skill("Test topic")

        assert result_path is None
        assert "was not created" in output

    @patch("ralph.core.skill_runner.subprocess.run")
    @patch("ralph.core.skill_runner.AgentRunner")
    @patch("ralph.core.skill_runner.load_config")
    def test_run_rrd_skill_success(
        self, mock_load_config, mock_agent_runner_class, mock_subprocess, tmp_path, monkeypatch
    ):
        """Test successful RRD skill run."""
        from datetime import date

        monkeypatch.chdir(tmp_path)

        # Setup skill
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "rrd"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n---\n# RRD Content")

        mock_config = MagicMock()
        mock_config.default_agent = Agent.CLAUDE
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_agent_runner_class.return_value = mock_runner

        # Create rrd.json after subprocess "runs"
        today = date.today().isoformat()
        temp_path = tmp_path / f"rrd-temp-{today}"

        def create_rrd(*args, **kwargs):
            temp_path.mkdir(exist_ok=True)
            (temp_path / "rrd.json").write_text(
                json.dumps({"project": "Test Research Project", "requirements": {}})
            )
            return MagicMock(stdout="Success", stderr="", returncode=0)

        mock_subprocess.side_effect = create_rrd

        runner = SkillRunner(script_dir=tmp_path)
        result_path, output = runner.run_rrd_skill("Test topic")

        assert result_path is not None
        assert "Success" in output

    @patch("ralph.core.skill_runner.subprocess.run")
    @patch("ralph.core.skill_runner.AgentRunner")
    @patch("ralph.core.skill_runner.load_config")
    def test_run_rrd_skill_with_amp_agent(
        self, mock_load_config, mock_agent_runner_class, mock_subprocess, tmp_path, monkeypatch
    ):
        """Test RRD skill with AMP agent."""
        from datetime import date

        monkeypatch.chdir(tmp_path)

        # Setup skill
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "rrd"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n---\n# RRD Content")

        mock_config = MagicMock()
        mock_config.default_agent = Agent.AMP
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_agent_runner_class.return_value = mock_runner

        today = date.today().isoformat()
        temp_path = tmp_path / f"rrd-temp-{today}"

        def create_rrd(*args, **kwargs):
            temp_path.mkdir(exist_ok=True)
            (temp_path / "rrd.json").write_text(json.dumps({"project": "Test", "requirements": {}}))
            return MagicMock(stdout="Success", stderr="", returncode=0)

        mock_subprocess.side_effect = create_rrd

        runner = SkillRunner(script_dir=tmp_path)
        result_path, output = runner.run_rrd_skill("Test topic", agent=Agent.AMP)

        # Verify amp command was used
        call_args = mock_subprocess.call_args[0][0]
        assert "amp" in call_args

    @patch("ralph.core.skill_runner.subprocess.run")
    @patch("ralph.core.skill_runner.AgentRunner")
    @patch("ralph.core.skill_runner.load_config")
    def test_run_rrd_skill_with_codex_agent(
        self, mock_load_config, mock_agent_runner_class, mock_subprocess, tmp_path, monkeypatch
    ):
        """Test RRD skill with Codex agent."""
        from datetime import date

        monkeypatch.chdir(tmp_path)

        # Setup skill
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "rrd"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n---\n# RRD Content")

        mock_config = MagicMock()
        mock_config.default_agent = Agent.CODEX
        mock_load_config.return_value = mock_config

        mock_runner = MagicMock()
        mock_runner.is_available.return_value = True
        mock_agent_runner_class.return_value = mock_runner

        today = date.today().isoformat()
        temp_path = tmp_path / f"rrd-temp-{today}"

        def create_rrd(*args, **kwargs):
            temp_path.mkdir(exist_ok=True)
            (temp_path / "rrd.json").write_text(json.dumps({"project": "Test", "requirements": {}}))
            return MagicMock(stdout="Success", stderr="", returncode=0)

        mock_subprocess.side_effect = create_rrd

        runner = SkillRunner(script_dir=tmp_path)
        result_path, output = runner.run_rrd_skill("Test topic", agent=Agent.CODEX)

        # Verify codex command was used
        call_args = mock_subprocess.call_args[0][0]
        assert "codex" in call_args


class TestFinalizeProject:
    """Tests for _finalize_project error recovery."""

    def test_finalize_project_rename_permission_error(self, tmp_path, monkeypatch):
        """Test handling when rename fails due to permission error."""
        from datetime import date

        monkeypatch.chdir(tmp_path)

        # Create temp directory with rrd.json
        today = date.today().isoformat()
        temp_path = tmp_path / f"rrd-temp-{today}"
        temp_path.mkdir()
        (temp_path / "rrd.json").write_text(
            json.dumps({"project": "Test Project", "requirements": {}})
        )

        runner = SkillRunner(script_dir=tmp_path)

        # Mock rename to raise PermissionError
        original_rename = Path.rename

        def mock_rename(self, target):
            raise PermissionError("Cannot rename")

        monkeypatch.setattr(Path, "rename", mock_rename)

        result_path, output = runner._finalize_project(temp_path, "test topic", "Agent output")

        # Should return temp_path on error with explanation
        assert result_path == temp_path
        assert "failed to rename" in output.lower()

    def test_finalize_project_handles_name_collision(self, tmp_path, monkeypatch):
        """Test project creation when directory name already exists."""
        from datetime import date

        monkeypatch.chdir(tmp_path)

        today = date.today().isoformat()

        # Create temp directory with rrd.json
        temp_path = tmp_path / f"rrd-temp-{today}"
        temp_path.mkdir()
        (temp_path / "rrd.json").write_text(
            json.dumps({"project": "Test Project", "requirements": {}})
        )

        # Pre-create the target directory to cause collision
        expected_name = f"test-project-{today}"
        (tmp_path / expected_name).mkdir()

        runner = SkillRunner(script_dir=tmp_path)
        result_path, output = runner._finalize_project(temp_path, "test topic", "Agent output")

        # Should succeed with a numbered suffix
        assert result_path is not None
        assert result_path.exists()
        assert f"{expected_name}-1" in str(result_path)

    def test_finalize_project_no_rrd_file(self, tmp_path, monkeypatch):
        """Test handling when rrd.json was not created."""
        from datetime import date

        monkeypatch.chdir(tmp_path)

        today = date.today().isoformat()
        temp_path = tmp_path / f"rrd-temp-{today}"
        temp_path.mkdir()
        # Don't create rrd.json

        runner = SkillRunner(script_dir=tmp_path)
        result_path, output = runner._finalize_project(temp_path, "test topic", "Agent output")

        assert result_path is None
        assert "was not created" in output
