"""Tests for RRDManager class."""

import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from ralph.core.rrd_manager import RRDManager
from ralph.models.rrd import RRD, Phase, Requirements
from ralph.models.paper import Paper, PaperStatus


class TestRRDManagerInit:
    """Tests for RRDManager initialization."""

    def test_init_sets_paths(self, tmp_path):
        """Test initialization sets paths correctly."""
        project = tmp_path / "test-project"
        project.mkdir()

        manager = RRDManager(project)

        assert manager.project_path == project
        assert manager.rrd_path == project / "rrd.json"
        assert manager.progress_path == project / "progress.txt"
        assert manager._rrd is None


class TestRRDManagerExists:
    """Tests for RRDManager.exists property."""

    def test_exists_false_no_file(self, tmp_project_dir):
        """Test exists returns False when no rrd.json."""
        manager = RRDManager(tmp_project_dir)
        assert manager.exists is False

    def test_exists_true_with_file(self, project_with_rrd):
        """Test exists returns True when rrd.json present."""
        manager = RRDManager(project_with_rrd)
        assert manager.exists is True


class TestRRDManagerLoad:
    """Tests for RRDManager.load method."""

    def test_load_success(self, project_with_rrd):
        """Test loading valid RRD file."""
        manager = RRDManager(project_with_rrd)

        rrd = manager.load()

        assert rrd.project == "AI Robotics Research"
        assert manager._rrd is not None
        assert manager._rrd == rrd

    def test_load_file_not_found(self, tmp_project_dir):
        """Test loading non-existent file raises FileNotFoundError."""
        manager = RRDManager(tmp_project_dir)

        with pytest.raises(FileNotFoundError):
            manager.load()

    def test_load_invalid_json(self, tmp_project_dir):
        """Test loading invalid JSON raises error."""
        rrd_path = tmp_project_dir / "rrd.json"
        rrd_path.write_text("not valid json {{{")

        manager = RRDManager(tmp_project_dir)

        with pytest.raises(json.JSONDecodeError):
            manager.load()

    def test_load_caches_result(self, project_with_rrd):
        """Test that load caches the result."""
        manager = RRDManager(project_with_rrd)

        rrd1 = manager.load()
        rrd2 = manager.load()

        # Second load should return same object since it reloads
        assert rrd1.project == rrd2.project


class TestRRDManagerSave:
    """Tests for RRDManager.save method."""

    def test_save_with_rrd_param(self, tmp_project_dir, sample_rrd):
        """Test saving RRD passed as parameter."""
        manager = RRDManager(tmp_project_dir)

        manager.save(sample_rrd)

        assert manager.rrd_path.exists()
        with open(manager.rrd_path) as f:
            data = json.load(f)
        assert data["project"] == "AI Robotics Research"

    def test_save_without_rrd_raises(self, tmp_project_dir):
        """Test saving without loaded RRD raises ValueError."""
        manager = RRDManager(tmp_project_dir)

        with pytest.raises(ValueError, match="No RRD loaded"):
            manager.save()

    def test_save_after_load(self, project_with_rrd):
        """Test saving after loading (modification workflow)."""
        manager = RRDManager(project_with_rrd)
        rrd = manager.load()
        rrd.phase = Phase.ANALYSIS

        manager.save()

        # Reload and verify
        manager2 = RRDManager(project_with_rrd)
        reloaded = manager2.load()
        assert reloaded.phase == Phase.ANALYSIS

    def test_save_preserves_data(self, tmp_project_dir, sample_rrd_with_papers):
        """Test save preserves all data."""
        manager = RRDManager(tmp_project_dir)
        manager.save(sample_rrd_with_papers)

        # Reload
        manager2 = RRDManager(tmp_project_dir)
        loaded = manager2.load()

        assert loaded.project == sample_rrd_with_papers.project
        assert len(loaded.papers_pool) == len(sample_rrd_with_papers.papers_pool)


class TestRRDManagerRrdProperty:
    """Tests for RRDManager.rrd property."""

    def test_rrd_property_loads_if_needed(self, project_with_rrd):
        """Test rrd property auto-loads if not loaded."""
        manager = RRDManager(project_with_rrd)
        assert manager._rrd is None

        rrd = manager.rrd

        assert manager._rrd is not None
        assert rrd.project == "AI Robotics Research"

    def test_rrd_property_returns_cached(self, project_with_rrd):
        """Test rrd property returns cached instance."""
        manager = RRDManager(project_with_rrd)
        rrd1 = manager.rrd
        rrd2 = manager.rrd

        assert rrd1 is rrd2


class TestRRDManagerBackup:
    """Tests for RRDManager.create_backup method."""

    def test_create_backup_default_suffix(self, project_with_rrd):
        """Test backup creation with timestamp suffix."""
        manager = RRDManager(project_with_rrd)

        backup_path = manager.create_backup()

        assert backup_path.exists()
        assert ".backup." in backup_path.name
        assert backup_path.suffix == ".json"

    def test_create_backup_custom_suffix(self, project_with_rrd):
        """Test backup creation with custom suffix."""
        manager = RRDManager(project_with_rrd)

        backup_path = manager.create_backup(suffix="test")

        assert backup_path.name == "rrd.backup.test.json"
        assert backup_path.exists()

    def test_create_backup_also_backs_up_progress(self, project_with_progress):
        """Test backup includes progress.txt if present."""
        manager = RRDManager(project_with_progress)

        manager.create_backup(suffix="test")

        progress_backup = project_with_progress / "progress.backup.test.txt"
        assert progress_backup.exists()

    def test_create_backup_content_preserved(self, project_with_rrd):
        """Test backup contains same content."""
        manager = RRDManager(project_with_rrd)

        backup_path = manager.create_backup(suffix="test")

        with open(manager.rrd_path) as f1, open(backup_path) as f2:
            original = json.load(f1)
            backup = json.load(f2)
        assert original == backup


class TestRRDManagerReset:
    """Tests for RRDManager.reset method."""

    def test_reset_creates_backup(self, project_with_rrd):
        """Test reset creates backup first."""
        manager = RRDManager(project_with_rrd)

        backup_path = manager.reset()

        assert backup_path.exists()

    def test_reset_clears_papers(self, project_with_rrd, sample_rrd_with_papers):
        """Test reset clears papers pool."""
        # Setup with papers
        with open(project_with_rrd / "rrd.json", "w") as f:
            json.dump(json.loads(sample_rrd_with_papers.model_dump_json()), f)

        manager = RRDManager(project_with_rrd)
        manager.reset()
        rrd = manager.load()

        assert len(rrd.papers_pool) == 0

    def test_reset_clears_insights(self, project_with_rrd, sample_rrd):
        """Test reset clears insights."""
        sample_rrd.insights = [
            {"id": "ins_1", "paper_id": "p1", "insight": "test"}
        ]
        with open(project_with_rrd / "rrd.json", "w") as f:
            json.dump(json.loads(sample_rrd.model_dump_json()), f)

        manager = RRDManager(project_with_rrd)
        manager.reset()
        rrd = manager.load()

        assert len(rrd.insights) == 0

    def test_reset_sets_discovery_phase(self, project_with_rrd):
        """Test reset sets phase to DISCOVERY."""
        # Set to ANALYSIS first
        manager = RRDManager(project_with_rrd)
        rrd = manager.load()
        rrd.phase = Phase.ANALYSIS
        manager.save()

        manager.reset()
        rrd = manager.load()

        assert rrd.phase == Phase.DISCOVERY

    def test_reset_clears_statistics(self, project_with_rrd):
        """Test reset clears statistics."""
        manager = RRDManager(project_with_rrd)
        rrd = manager.load()
        rrd.statistics.total_analyzed = 10
        rrd.statistics.total_presented = 5
        manager.save()

        manager.reset()
        rrd = manager.load()

        assert rrd.statistics.total_analyzed == 0
        assert rrd.statistics.total_presented == 0
        assert rrd.statistics.total_discovered == 0

    def test_reset_initializes_progress_file(self, project_with_rrd):
        """Test reset initializes progress file."""
        manager = RRDManager(project_with_rrd)

        manager.reset()

        assert manager.progress_path.exists()
        content = manager.progress_path.read_text()
        assert "Research-Ralph Progress Log" in content
        assert "Reset:" in content


class TestRRDManagerProgressFile:
    """Tests for progress file management."""

    def test_init_progress_file(self, tmp_project_dir):
        """Test progress file initialization."""
        manager = RRDManager(tmp_project_dir)

        manager._init_progress_file()

        assert manager.progress_path.exists()
        content = manager.progress_path.read_text()
        assert "Research-Ralph Progress Log" in content
        assert "Research Patterns" in content
        assert "Cross-Reference Insights" in content

    def test_ensure_progress_file_creates_if_missing(self, tmp_project_dir):
        """Test ensure_progress_file creates file if missing."""
        manager = RRDManager(tmp_project_dir)
        assert not manager.progress_path.exists()

        manager.ensure_progress_file()

        assert manager.progress_path.exists()

    def test_ensure_progress_file_no_op_if_exists(self, project_with_progress):
        """Test ensure_progress_file does nothing if file exists."""
        manager = RRDManager(project_with_progress)
        original_content = manager.progress_path.read_text()

        manager.ensure_progress_file()

        assert manager.progress_path.read_text() == original_content


class TestRRDManagerUpdateTargetPapers:
    """Tests for RRDManager.update_target_papers method."""

    def test_update_success_in_discovery(self, project_with_rrd):
        """Test updating target papers in DISCOVERY phase."""
        manager = RRDManager(project_with_rrd)

        result = manager.update_target_papers(30)

        assert result is True
        rrd = manager.load()
        assert rrd.requirements.target_papers == 30

    def test_update_blocked_in_analysis(self, project_with_rrd):
        """Test update blocked when in ANALYSIS phase."""
        manager = RRDManager(project_with_rrd)
        rrd = manager.load()
        rrd.phase = Phase.ANALYSIS
        manager.save()

        result = manager.update_target_papers(30)

        assert result is False

    def test_update_blocked_when_analyzed(self, project_with_rrd):
        """Test update blocked when papers already analyzed."""
        manager = RRDManager(project_with_rrd)
        rrd = manager.load()
        rrd.statistics.total_analyzed = 5
        manager.save()

        result = manager.update_target_papers(30)

        assert result is False

    def test_update_force_override_analysis(self, project_with_rrd):
        """Test force override when in ANALYSIS phase."""
        manager = RRDManager(project_with_rrd)
        rrd = manager.load()
        rrd.phase = Phase.ANALYSIS
        manager.save()

        result = manager.update_target_papers(30, force=True)

        assert result is True
        rrd = manager.load()
        assert rrd.requirements.target_papers == 30

    def test_update_force_override_with_analyzed(self, project_with_rrd):
        """Test force override when papers analyzed."""
        manager = RRDManager(project_with_rrd)
        rrd = manager.load()
        rrd.statistics.total_analyzed = 5
        manager.save()

        result = manager.update_target_papers(30, force=True)

        assert result is True


class TestRRDManagerValidate:
    """Tests for RRDManager.validate method."""

    def test_validate_valid_file(self, project_with_rrd):
        """Test validation of valid RRD."""
        manager = RRDManager(project_with_rrd)

        errors = manager.validate()

        assert errors == []

    def test_validate_missing_file(self, tmp_project_dir):
        """Test validation when file missing."""
        manager = RRDManager(tmp_project_dir)

        errors = manager.validate()

        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_validate_invalid_json(self, tmp_project_dir):
        """Test validation of invalid JSON."""
        (tmp_project_dir / "rrd.json").write_text("{invalid")
        manager = RRDManager(tmp_project_dir)

        errors = manager.validate()

        assert any("Invalid JSON" in e for e in errors)

    def test_validate_missing_project(self, tmp_project_dir):
        """Test validation missing 'project' field."""
        (tmp_project_dir / "rrd.json").write_text(
            '{"requirements": {"focus_area": "test", "target_papers": 10}}'
        )
        manager = RRDManager(tmp_project_dir)

        errors = manager.validate()

        assert any("project" in e for e in errors)

    def test_validate_missing_requirements(self, tmp_project_dir):
        """Test validation missing 'requirements' field."""
        (tmp_project_dir / "rrd.json").write_text('{"project": "Test"}')
        manager = RRDManager(tmp_project_dir)

        errors = manager.validate()

        assert any("requirements" in e for e in errors)

    def test_validate_missing_target_papers(self, tmp_project_dir):
        """Test validation missing 'target_papers' in requirements."""
        (tmp_project_dir / "rrd.json").write_text(
            '{"project": "Test", "requirements": {"focus_area": "test"}}'
        )
        manager = RRDManager(tmp_project_dir)

        errors = manager.validate()

        assert any("target_papers" in e for e in errors)


class TestRRDManagerGetSummary:
    """Tests for RRDManager.get_summary method."""

    def test_get_summary_keys(self, project_with_rrd):
        """Test get_summary returns correct keys."""
        manager = RRDManager(project_with_rrd)

        summary = manager.get_summary()

        expected_keys = [
            "project",
            "phase",
            "target_papers",
            "pool_size",
            "analyzed",
            "presented",
            "rejected",
            "pending",
            "analyzing",
            "insights",
            "completion_pct",
        ]
        for key in expected_keys:
            assert key in summary

    def test_get_summary_values(self, project_with_rrd):
        """Test get_summary returns correct values."""
        manager = RRDManager(project_with_rrd)

        summary = manager.get_summary()

        assert summary["project"] == "AI Robotics Research"
        assert summary["phase"] == "DISCOVERY"
        assert summary["target_papers"] == 20


class TestRRDManagerLoadErrors:
    """Tests for RRDManager.load error handling."""

    def test_load_pydantic_validation_error(self, tmp_project_dir):
        """Test load handles invalid schema (Pydantic ValidationError)."""
        from pydantic import ValidationError

        # Write JSON that passes JSON parsing but fails Pydantic validation
        # requirements.target_papers must be int, not string
        (tmp_project_dir / "rrd.json").write_text(
            '{"project": "Test", "requirements": {"focus_area": "test", "target_papers": "invalid"}}'
        )
        manager = RRDManager(tmp_project_dir)

        with pytest.raises(ValidationError):
            manager.load()

    def test_load_missing_required_field_pydantic(self, tmp_project_dir):
        """Test load raises ValidationError for missing required fields."""
        from pydantic import ValidationError

        # Missing required 'requirements' field
        (tmp_project_dir / "rrd.json").write_text('{"project": "Test"}')
        manager = RRDManager(tmp_project_dir)

        with pytest.raises(ValidationError):
            manager.load()


class TestAtomicWriteFailures:
    """Tests for atomic write failure handling in RRDManager."""

    def test_save_cleans_temp_on_replace_failure(self, tmp_project_dir, sample_rrd):
        """Test that temp file is cleaned up when replace fails."""
        manager = RRDManager(tmp_project_dir)

        # First save to create the file
        manager.save(sample_rrd)

        # Mock replace to fail
        with patch.object(Path, 'replace', side_effect=OSError("Disk full")):
            with pytest.raises(OSError):
                sample_rrd.project = "Updated"
                manager.save()

        # Temp file should be cleaned up
        temp_files = list(tmp_project_dir.glob("*.tmp"))
        assert len(temp_files) == 0

    def test_save_raises_on_write_failure(self, tmp_project_dir, sample_rrd):
        """Test that save raises on write failure."""
        manager = RRDManager(tmp_project_dir)

        with patch("tempfile.NamedTemporaryFile", side_effect=PermissionError("No permission")):
            with pytest.raises(PermissionError):
                manager.save(sample_rrd)

    def test_save_preserves_original_on_failure(self, project_with_rrd):
        """Test that original file is preserved when save fails."""
        manager = RRDManager(project_with_rrd)

        # Load original
        original_rrd = manager.load()
        original_project = original_rrd.project

        # Try to save with modified data, but mock replace to fail
        original_rrd.project = "Modified"

        with patch.object(Path, 'replace', side_effect=OSError("Disk full")):
            with pytest.raises(OSError):
                manager.save()

        # Original file should still have original content
        manager2 = RRDManager(project_with_rrd)
        reloaded = manager2.load()
        assert reloaded.project == original_project


class TestConcurrentAccess:
    """Tests for concurrent access scenarios."""

    def test_load_fails_if_file_deleted_between_check_and_read(self, project_with_rrd):
        """Test that load raises FileNotFoundError if file deleted mid-operation."""
        manager = RRDManager(project_with_rrd)

        # Verify file exists initially
        assert manager.exists

        # Delete file
        manager.rrd_path.unlink()

        # load() should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            manager.load()

    def test_save_after_external_modification(self, project_with_rrd, sample_rrd):
        """Test save behavior when file was modified externally."""
        manager = RRDManager(project_with_rrd)
        rrd = manager.load()

        # External modification
        with open(project_with_rrd / "rrd.json", "w") as f:
            json.dump({"project": "External", "requirements": {"focus_area": "test", "target_papers": 10}}, f)

        # Our save should overwrite (atomic replace)
        rrd.project = "Our Update"
        manager.save()

        # Verify our update won
        manager2 = RRDManager(project_with_rrd)
        reloaded = manager2.load()
        assert reloaded.project == "Our Update"

    def test_backup_fails_if_file_deleted(self, project_with_rrd):
        """Test backup raises if source file deleted."""
        manager = RRDManager(project_with_rrd)

        # Delete file
        manager.rrd_path.unlink()

        # backup should fail
        with pytest.raises(FileNotFoundError):
            manager.create_backup()
