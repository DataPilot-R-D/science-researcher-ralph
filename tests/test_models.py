"""Tests for Pydantic models."""

import pytest
from datetime import date

from ralph.models.paper import Paper, PaperStatus, ScoreBreakdown
from ralph.models.rrd import RRD, Phase, Requirements, Mission


class TestPaper:
    """Tests for Paper model."""

    def test_create_basic_paper(self):
        """Test creating a paper with minimal fields."""
        paper = Paper(
            id="arxiv_2501.12345",
            title="Test Paper",
            url="https://arxiv.org/abs/2501.12345",
        )
        assert paper.id == "arxiv_2501.12345"
        assert paper.title == "Test Paper"
        assert paper.status == PaperStatus.PENDING
        assert paper.score is None

    def test_paper_with_score(self):
        """Test paper with score breakdown."""
        breakdown = ScoreBreakdown(
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
        assert breakdown.execution_score == 19
        assert breakdown.blue_ocean_score == 12
        assert breakdown.combined_score == 31


class TestRRD:
    """Tests for RRD model."""

    def test_create_minimal_rrd(self):
        """Test creating RRD with minimal fields."""
        rrd = RRD(
            project="Test Research",
            requirements=Requirements(
                focus_area="test",
                target_papers=10,
            ),
        )
        assert rrd.project == "Test Research"
        assert rrd.phase == Phase.DISCOVERY
        assert rrd.requirements.target_papers == 10

    def test_rrd_pending_papers(self):
        """Test getting pending papers."""
        rrd = RRD(
            project="Test",
            requirements=Requirements(focus_area="test", target_papers=10),
            papers_pool=[
                Paper(id="1", title="Paper 1", url="http://1", status=PaperStatus.PENDING),
                Paper(id="2", title="Paper 2", url="http://2", status=PaperStatus.PRESENTED),
                Paper(id="3", title="Paper 3", url="http://3", status=PaperStatus.PENDING),
            ],
        )
        assert len(rrd.pending_papers) == 2

    def test_rrd_completion_percentage(self):
        """Test completion percentage calculation."""
        rrd = RRD(
            project="Test",
            requirements=Requirements(focus_area="test", target_papers=10),
        )
        rrd.statistics.total_analyzed = 5
        assert rrd.completion_percentage == 50.0


class TestScoreBreakdown:
    """Tests for ScoreBreakdown model."""

    def test_score_ranges(self):
        """Test that scores stay within valid ranges."""
        breakdown = ScoreBreakdown()
        assert 0 <= breakdown.execution_score <= 30
        assert 0 <= breakdown.blue_ocean_score <= 20
        assert 0 <= breakdown.combined_score <= 50

    def test_max_scores(self):
        """Test maximum possible scores."""
        breakdown = ScoreBreakdown(
            novelty=5,
            feasibility=5,
            time_to_poc=5,
            value_market=5,
            defensibility=5,
            adoption=5,
            market_creation=5,
            first_mover_window=5,
            network_data_effects=5,
            strategic_clarity=5,
        )
        assert breakdown.execution_score == 30
        assert breakdown.blue_ocean_score == 20
        assert breakdown.combined_score == 50
