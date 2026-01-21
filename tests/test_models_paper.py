"""Tests for Paper model and related classes."""

import pytest
from datetime import date
from pydantic import ValidationError

from ralph.models.paper import Paper, PaperStatus, ScoreBreakdown


class TestPaperStatus:
    """Tests for PaperStatus enum."""

    def test_all_status_values_exist(self):
        """Verify all expected status values."""
        assert PaperStatus.PENDING.value == "pending"
        assert PaperStatus.ANALYZING.value == "analyzing"
        assert PaperStatus.PRESENTED.value == "presented"
        assert PaperStatus.REJECTED.value == "rejected"
        assert PaperStatus.EXTRACT_INSIGHTS.value == "extract_insights"
        assert PaperStatus.INSIGHTS_EXTRACTED.value == "insights_extracted"

    def test_status_count(self):
        """Verify we have all expected statuses."""
        assert len(PaperStatus) == 6

    def test_status_is_string_enum(self):
        """Verify status behaves as string enum."""
        assert isinstance(PaperStatus.PENDING.value, str)


class TestScoreBreakdown:
    """Tests for ScoreBreakdown model."""

    def test_default_scores_are_zero(self):
        """All scores default to 0."""
        breakdown = ScoreBreakdown()
        assert breakdown.novelty == 0
        assert breakdown.feasibility == 0
        assert breakdown.time_to_poc == 0
        assert breakdown.value_market == 0
        assert breakdown.defensibility == 0
        assert breakdown.adoption == 0
        assert breakdown.market_creation == 0
        assert breakdown.first_mover_window == 0
        assert breakdown.network_data_effects == 0
        assert breakdown.strategic_clarity == 0

    def test_execution_score_calculation(self):
        """Test execution score = sum of 6 dimensions."""
        breakdown = ScoreBreakdown(
            novelty=5,
            feasibility=4,
            time_to_poc=3,
            value_market=2,
            defensibility=1,
            adoption=5,
        )
        assert breakdown.execution_score == 20

    def test_blue_ocean_score_calculation(self):
        """Test blue ocean score = sum of 4 dimensions."""
        breakdown = ScoreBreakdown(
            market_creation=5,
            first_mover_window=4,
            network_data_effects=3,
            strategic_clarity=2,
        )
        assert breakdown.blue_ocean_score == 14

    def test_combined_score_calculation(self):
        """Test combined = execution + blue_ocean."""
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

    def test_score_field_validation_min(self):
        """Scores cannot be negative."""
        with pytest.raises(ValidationError):
            ScoreBreakdown(novelty=-1)

    def test_score_field_validation_max(self):
        """Scores cannot exceed 5."""
        with pytest.raises(ValidationError):
            ScoreBreakdown(novelty=6)

    def test_all_fields_at_max(self):
        """Test all fields at maximum value."""
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

    def test_score_ranges_valid(self):
        """Test that computed scores stay within valid ranges."""
        breakdown = ScoreBreakdown()
        assert 0 <= breakdown.execution_score <= 30
        assert 0 <= breakdown.blue_ocean_score <= 20
        assert 0 <= breakdown.combined_score <= 50


class TestPaper:
    """Tests for Paper model."""

    def test_required_fields_only(self):
        """Test creating paper with only required fields."""
        paper = Paper(id="test", title="Test Paper", url="http://test.com")
        assert paper.id == "test"
        assert paper.title == "Test Paper"
        assert paper.url == "http://test.com"

    def test_missing_id_raises(self):
        """Missing id raises ValidationError."""
        with pytest.raises(ValidationError):
            Paper(title="Test", url="http://test")

    def test_missing_title_raises(self):
        """Missing title raises ValidationError."""
        with pytest.raises(ValidationError):
            Paper(id="test", url="http://test")

    def test_missing_url_raises(self):
        """Missing url raises ValidationError."""
        with pytest.raises(ValidationError):
            Paper(id="test", title="Test")

    def test_default_values(self):
        """Test default field values."""
        paper = Paper(id="test", title="Test", url="http://test")
        assert paper.status == PaperStatus.PENDING
        assert paper.priority == 3
        assert paper.score is None
        assert paper.authors == []
        assert paper.notes == ""
        assert paper.pdf_url is None
        assert paper.date is None
        assert paper.source == "unknown"
        assert paper.score_breakdown is None
        assert paper.analysis is None
        assert paper.decision is None
        assert paper.implementation_url is None
        assert paper.commercialized is None

    def test_paper_with_date(self):
        """Test paper with date field."""
        paper = Paper(
            id="test",
            title="Test",
            url="http://test",
            date=date(2025, 1, 20),
        )
        assert paper.date == date(2025, 1, 20)

    def test_paper_with_score_breakdown(self, sample_score_breakdown):
        """Test paper with full score breakdown."""
        paper = Paper(
            id="test",
            title="Test",
            url="http://test",
            score=35,
            score_breakdown=sample_score_breakdown,
        )
        assert paper.score == 35
        assert paper.score_breakdown is not None
        assert paper.score_breakdown.execution_score == 19
        assert paper.score_breakdown.blue_ocean_score == 12

    def test_priority_validation_min(self):
        """Priority must be >= 1."""
        with pytest.raises(ValidationError):
            Paper(id="test", title="Test", url="http://test", priority=0)

    def test_priority_validation_max(self):
        """Priority must be <= 5."""
        with pytest.raises(ValidationError):
            Paper(id="test", title="Test", url="http://test", priority=6)

    def test_priority_valid_range(self):
        """Test valid priority values."""
        for p in [1, 2, 3, 4, 5]:
            paper = Paper(id="test", title="Test", url="http://test", priority=p)
            assert paper.priority == p

    def test_score_validation_min(self):
        """Score cannot be negative."""
        with pytest.raises(ValidationError):
            Paper(id="test", title="Test", url="http://test", score=-1)

    def test_score_validation_max(self):
        """Score cannot exceed 50."""
        with pytest.raises(ValidationError):
            Paper(id="test", title="Test", url="http://test", score=51)

    def test_score_valid_range(self):
        """Test valid score values."""
        for s in [0, 25, 50]:
            paper = Paper(id="test", title="Test", url="http://test", score=s)
            assert paper.score == s

    def test_analysis_as_string(self):
        """Analysis field accepts string."""
        paper = Paper(
            id="test",
            title="Test",
            url="http://test",
            analysis="Good paper about AI",
        )
        assert paper.analysis == "Good paper about AI"

    def test_analysis_as_dict(self):
        """Analysis field accepts dict."""
        analysis_dict = {"summary": "Good paper", "rating": 5, "key_points": ["AI", "ML"]}
        paper = Paper(
            id="test",
            title="Test",
            url="http://test",
            analysis=analysis_dict,
        )
        assert paper.analysis == analysis_dict
        assert paper.analysis["summary"] == "Good paper"

    def test_status_values_work(self):
        """Test all status values can be assigned."""
        for status in PaperStatus:
            paper = Paper(
                id="test",
                title="Test",
                url="http://test",
                status=status,
            )
            assert paper.status == status

    def test_all_fields_populated(self, sample_score_breakdown):
        """Test paper with all fields populated."""
        paper = Paper(
            id="arxiv_2501.12345",
            title="Comprehensive AI Paper",
            url="https://arxiv.org/abs/2501.12345",
            pdf_url="https://arxiv.org/pdf/2501.12345.pdf",
            authors=["John Doe", "Jane Smith"],
            date=date(2025, 1, 20),
            source="arXiv",
            priority=5,
            status=PaperStatus.PRESENTED,
            score=45,
            score_breakdown=sample_score_breakdown,
            analysis={"summary": "Excellent paper"},
            decision="PRESENT",
            notes="High quality research",
            implementation_url="https://github.com/example/repo",
            commercialized=False,
        )
        assert paper.id == "arxiv_2501.12345"
        assert len(paper.authors) == 2
        assert paper.commercialized is False
        assert paper.implementation_url == "https://github.com/example/repo"

    def test_serialization_uses_enum_values(self):
        """Test that status serializes as string value."""
        paper = Paper(id="test", title="Test", url="http://test")
        data = paper.model_dump()
        assert data["status"] == "pending"

    def test_authors_list_operations(self):
        """Test authors field as list."""
        paper = Paper(
            id="test",
            title="Test",
            url="http://test",
            authors=["Author 1", "Author 2", "Author 3"],
        )
        assert len(paper.authors) == 3
        assert "Author 1" in paper.authors

    def test_empty_authors_list(self):
        """Test empty authors list."""
        paper = Paper(id="test", title="Test", url="http://test", authors=[])
        assert paper.authors == []
