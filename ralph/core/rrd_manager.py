"""RRD (Research Requirements Document) file I/O operations."""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from ralph.models.rrd import RRD, Phase


class RRDManager:
    """Manages RRD file operations for a research project."""

    def __init__(self, project_path: Path):
        """
        Initialize RRD manager for a project.

        Args:
            project_path: Path to the research project folder
        """
        self.project_path = project_path
        self.rrd_path = project_path / "rrd.json"
        self.progress_path = project_path / "progress.txt"
        self._rrd: Optional[RRD] = None

    @property
    def exists(self) -> bool:
        """Check if RRD file exists."""
        return self.rrd_path.exists()

    def load(self) -> RRD:
        """Load RRD from file."""
        if not self.exists:
            raise FileNotFoundError(f"RRD file not found: {self.rrd_path}")

        with open(self.rrd_path) as f:
            data = json.load(f)

        self._rrd = RRD(**data)
        return self._rrd

    def save(self, rrd: Optional[RRD] = None) -> None:
        """Save RRD to file using atomic write."""
        if rrd is not None:
            self._rrd = rrd

        if self._rrd is None:
            raise ValueError("No RRD loaded to save")

        # Convert to dict, handling enums and dates
        data = json.loads(self._rrd.model_dump_json())

        # Atomic write: write to temp file, then rename
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", dir=self.rrd_path.parent, delete=False, suffix=".tmp"
            ) as f:
                json.dump(data, f, indent=2)
                temp_path = Path(f.name)
            temp_path.replace(self.rrd_path)
        except OSError:
            # Clean up temp file on failure
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass  # Best effort cleanup
            raise

    @property
    def rrd(self) -> RRD:
        """Get the loaded RRD, loading if necessary."""
        if self._rrd is None:
            self.load()
        return self._rrd  # type: ignore

    def create_backup(self, suffix: Optional[str] = None) -> Path:
        """
        Create a backup of the RRD file.

        Args:
            suffix: Optional suffix for backup filename (default: timestamp)

        Returns:
            Path to the backup file
        """
        if suffix is None:
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_path = self.rrd_path.with_suffix(f".backup.{suffix}.json")
        shutil.copy2(self.rrd_path, backup_path)

        # Also backup progress.txt if it exists
        if self.progress_path.exists():
            progress_backup = self.progress_path.with_suffix(f".backup.{suffix}.txt")
            shutil.copy2(self.progress_path, progress_backup)

        return backup_path

    def reset(self) -> Path:
        """
        Reset the research to DISCOVERY phase.

        Creates a backup first, then resets the RRD state.

        Returns:
            Path to the backup file
        """
        backup_path = self.create_backup()

        rrd = self.load()
        rrd.phase = Phase.DISCOVERY
        rrd.papers_pool = []
        rrd.insights = []
        rrd.statistics.total_discovered = 0
        rrd.statistics.total_analyzed = 0
        rrd.statistics.total_presented = 0
        rrd.statistics.total_rejected = 0
        rrd.statistics.total_insights_extracted = 0

        self.save()

        # Reset progress file
        self._init_progress_file()

        return backup_path

    def _init_progress_file(self) -> None:
        """Initialize or reset the progress file."""
        content = f"""# Research-Ralph Progress Log
Reset: {datetime.now().isoformat()}

## Research Patterns
- (Patterns discovered during research will be added here)

## Cross-Reference Insights
- (Connections between papers will be added here)

---
"""
        with open(self.progress_path, "w") as f:
            f.write(content)

    def ensure_progress_file(self) -> None:
        """Ensure progress file exists."""
        if not self.progress_path.exists():
            self._init_progress_file()

    def update_target_papers(self, target: int, force: bool = False) -> bool:
        """
        Update the target papers count.

        Args:
            target: New target papers count
            force: If True, allow changing even if research in progress

        Returns:
            True if updated successfully
        """
        rrd = self.load()

        # Check if research is in progress
        if not force and (rrd.phase != Phase.DISCOVERY or rrd.statistics.total_analyzed > 0):
            return False

        rrd.requirements.target_papers = target
        self.save()
        return True

    def validate(self) -> list[str]:
        """
        Validate the RRD file and return list of errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        if not self.exists:
            errors.append(f"RRD file not found: {self.rrd_path}")
            return errors

        try:
            with open(self.rrd_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
            return errors

        # Check required fields
        if "project" not in data:
            errors.append("Missing required field: project")
        if "requirements" not in data:
            errors.append("Missing required field: requirements")
        elif "target_papers" not in data.get("requirements", {}):
            errors.append("Missing required field: requirements.target_papers")

        return errors

    def get_summary(self) -> dict:
        """Get a summary of the RRD state."""
        rrd = self.load()
        return {
            "project": rrd.project,
            "phase": rrd.phase,
            "target_papers": rrd.requirements.target_papers,
            "pool_size": len(rrd.papers_pool),
            "analyzed": rrd.statistics.total_analyzed,
            "presented": rrd.statistics.total_presented,
            "rejected": rrd.statistics.total_rejected,
            "pending": len(rrd.pending_papers),
            "analyzing": len(rrd.analyzing_papers),
            "insights": rrd.statistics.total_insights_extracted,
            "completion_pct": rrd.completion_percentage,
        }
