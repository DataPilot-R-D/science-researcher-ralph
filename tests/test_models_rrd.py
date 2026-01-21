"""Tests for RRD model and related classes."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from ralph.models.paper import Paper, PaperStatus
from ralph.models.rrd import (
    RRD,
    Phase,
    Mission,
    Requirements,
    Statistics,
    Insight,
    PhaseTiming,
    AnalysisTiming,
    Timing,
    Handoff,
    ProductIdeationConfig,
    DiscoveryMetrics,
    AnalysisMetrics,
    IdeationMetrics,
    ScoreDistribution,
    BlueOceanDistribution,
    DomainGlossary,
)


class TestPhase:
    """Tests for Phase enum."""

    def test_all_phases_exist(self):
        """Verify all expected phases."""
        assert Phase.DISCOVERY.value == "DISCOVERY"
        assert Phase.ANALYSIS.value == "ANALYSIS"
        assert Phase.IDEATION.value == "IDEATION"
        assert Phase.COMPLETE.value == "COMPLETE"

    def test_phase_count(self):
        """Verify we have all expected phases."""
        assert len(Phase) == 4


class TestMission:
    """Tests for Mission model."""

    def test_defaults(self):
        """Test default Mission values."""
        mission = Mission()
        assert mission.blue_ocean_scoring is True
        assert mission.min_blue_ocean_score == 12
        assert mission.min_combined_score == 25
        assert mission.strategic_focus == "balanced"

    def test_blue_ocean_score_validation_max(self):
        """Blue ocean score max is 20."""
        with pytest.raises(ValidationError):
            Mission(min_blue_ocean_score=21)

    def test_blue_ocean_score_validation_min(self):
        """Blue ocean score min is 0."""
        with pytest.raises(ValidationError):
            Mission(min_blue_ocean_score=-1)

    def test_combined_score_validation_max(self):
        """Combined score max is 50."""
        with pytest.raises(ValidationError):
            Mission(min_combined_score=51)

    def test_combined_score_validation_min(self):
        """Combined score min is 0."""
        with pytest.raises(ValidationError):
            Mission(min_combined_score=-1)

    def test_valid_score_boundaries(self):
        """Test valid boundary values."""
        mission = Mission(min_blue_ocean_score=0, min_combined_score=0)
        assert mission.min_blue_ocean_score == 0

        mission2 = Mission(min_blue_ocean_score=20, min_combined_score=50)
        assert mission2.min_blue_ocean_score == 20
        assert mission2.min_combined_score == 50


class TestRequirements:
    """Tests for Requirements model."""

    def test_required_focus_area(self):
        """Focus area is required."""
        with pytest.raises(ValidationError):
            Requirements(target_papers=10)

    def test_defaults(self):
        """Test default Requirements values."""
        req = Requirements(focus_area="test")
        assert req.time_window_days == 30
        assert req.historical_lookback_days == 365
        assert req.target_papers == 20
        assert "arXiv" in req.sources
        assert "Google Scholar" in req.sources
        assert "web" in req.sources
        assert req.min_score_to_present == 18
        assert req.keywords == []

    def test_target_papers_validation_min(self):
        """Target papers must be >= 1."""
        with pytest.raises(ValidationError):
            Requirements(focus_area="test", target_papers=0)

    def test_time_window_validation_min(self):
        """Time window must be >= 1."""
        with pytest.raises(ValidationError):
            Requirements(focus_area="test", time_window_days=0)

    def test_custom_values(self):
        """Test custom Requirements values."""
        req = Requirements(
            focus_area="AI research",
            keywords=["AI", "ML", "robotics"],
            time_window_days=60,
            historical_lookback_days=730,
            target_papers=50,
            sources=["arXiv"],
            min_score_to_present=30,
        )
        assert req.focus_area == "AI research"
        assert len(req.keywords) == 3
        assert req.time_window_days == 60
        assert req.target_papers == 50


class TestStatistics:
    """Tests for Statistics model."""

    def test_defaults_are_zero(self):
        """All stats default to zero."""
        stats = Statistics()
        assert stats.total_discovered == 0
        assert stats.total_analyzed == 0
        assert stats.total_presented == 0
        assert stats.total_rejected == 0
        assert stats.total_insights_extracted == 0

    def test_nested_defaults(self):
        """Test nested model defaults."""
        stats = Statistics()
        assert stats.discovery_metrics is not None
        assert stats.analysis_metrics is not None
        assert stats.ideation_metrics is not None


class TestDiscoveryMetrics:
    """Tests for DiscoveryMetrics model."""

    def test_defaults(self):
        """Test default values."""
        metrics = DiscoveryMetrics()
        assert metrics.sources_tried == []
        assert metrics.sources_successful == []
        assert metrics.sources_blocked == []
        assert metrics.source_failure_reasons == {}

    def test_custom_values(self):
        """Test custom values."""
        metrics = DiscoveryMetrics(
            sources_tried=["arXiv", "Scholar"],
            sources_successful=["arXiv"],
            sources_blocked=["Scholar"],
            source_failure_reasons={"Scholar": "Rate limited"},
        )
        assert len(metrics.sources_tried) == 2
        assert "arXiv" in metrics.sources_successful


class TestScoreDistribution:
    """Tests for ScoreDistribution model with aliases."""

    def test_defaults(self):
        """Test default values."""
        dist = ScoreDistribution()
        assert dist.range_0_17 == 0
        assert dist.range_18_24 == 0
        assert dist.range_25_34 == 0
        assert dist.range_35_50 == 0

    def test_alias_parsing(self):
        """Test that aliases work for field names."""
        dist = ScoreDistribution(**{"0-17": 5, "18-24": 3, "25-34": 2, "35-50": 1})
        assert dist.range_0_17 == 5
        assert dist.range_18_24 == 3
        assert dist.range_25_34 == 2
        assert dist.range_35_50 == 1


class TestBlueOceanDistribution:
    """Tests for BlueOceanDistribution model with aliases."""

    def test_defaults(self):
        """Test default values."""
        dist = BlueOceanDistribution()
        assert dist.range_0_7 == 0
        assert dist.range_8_11 == 0
        assert dist.range_12_15 == 0
        assert dist.range_16_20 == 0

    def test_alias_parsing(self):
        """Test that aliases work for field names."""
        dist = BlueOceanDistribution(**{"0-7": 3, "8-11": 4, "12-15": 2, "16-20": 1})
        assert dist.range_0_7 == 3
        assert dist.range_8_11 == 4


class TestAnalysisMetrics:
    """Tests for AnalysisMetrics model."""

    def test_defaults(self):
        """Test default values."""
        metrics = AnalysisMetrics()
        assert metrics.avg_combined_score == 0
        assert metrics.avg_execution_score == 0
        assert metrics.avg_blue_ocean_score == 0


class TestIdeationMetrics:
    """Tests for IdeationMetrics model."""

    def test_defaults(self):
        """Test default values."""
        metrics = IdeationMetrics()
        assert metrics.product_ideas_generated == 0
        assert metrics.top_idea_id is None


class TestPhaseTiming:
    """Tests for PhaseTiming model."""

    def test_defaults(self):
        """Test default values."""
        timing = PhaseTiming()
        assert timing.started_at is None
        assert timing.ended_at is None
        assert timing.duration_seconds is None

    def test_with_values(self):
        """Test with actual values."""
        now = datetime.now()
        timing = PhaseTiming(
            started_at=now,
            ended_at=now,
            duration_seconds=3600,
        )
        assert timing.started_at == now
        assert timing.duration_seconds == 3600


class TestAnalysisTiming:
    """Tests for AnalysisTiming model."""

    def test_defaults(self):
        """Test default values (inherits from PhaseTiming)."""
        timing = AnalysisTiming()
        assert timing.started_at is None
        assert timing.papers_analyzed == 0
        assert timing.avg_seconds_per_paper is None

    def test_with_values(self):
        """Test with actual values."""
        timing = AnalysisTiming(
            papers_analyzed=10,
            avg_seconds_per_paper=120.5,
        )
        assert timing.papers_analyzed == 10
        assert timing.avg_seconds_per_paper == 120.5


class TestTiming:
    """Tests for Timing model."""

    def test_defaults(self):
        """Test default values."""
        timing = Timing()
        assert timing.research_started_at is None
        assert timing.discovery is not None
        assert timing.analysis is not None
        assert timing.ideation is not None
        assert timing.complete is not None


class TestProductIdeationConfig:
    """Tests for ProductIdeationConfig model."""

    def test_defaults(self):
        """Test default values."""
        config = ProductIdeationConfig()
        assert config.enabled is True
        assert config.min_ideas == 3
        assert config.max_ideas == 12
        assert config.output_filename == "product-ideas.json"
        assert config.ranking_goal == "pick_one_for_prd"
        assert "team_size" in config.assumed_constraints

    def test_min_ideas_validation(self):
        """Min ideas must be >= 1."""
        with pytest.raises(ValidationError):
            ProductIdeationConfig(min_ideas=0)

    def test_max_ideas_validation(self):
        """Max ideas must be >= 1."""
        with pytest.raises(ValidationError):
            ProductIdeationConfig(max_ideas=0)


class TestHandoff:
    """Tests for Handoff model."""

    def test_defaults(self):
        """Test default values."""
        handoff = Handoff()
        assert handoff.product_ideation is not None
        assert handoff.product_ideation.enabled is True


class TestInsight:
    """Tests for Insight model."""

    def test_required_fields(self):
        """Test required fields."""
        insight = Insight(id="ins_1", paper_id="paper_1", insight="Key finding")
        assert insight.id == "ins_1"
        assert insight.paper_id == "paper_1"
        assert insight.insight == "Key finding"

    def test_defaults(self):
        """Test default values."""
        insight = Insight(id="ins_1", paper_id="paper_1", insight="Finding")
        assert insight.tags == []
        assert insight.cross_refs == []
        assert insight.cross_cluster is None

    def test_with_all_fields(self):
        """Test with all fields populated."""
        insight = Insight(
            id="ins_1",
            paper_id="paper_1",
            insight="Key finding about AI",
            tags=["AI", "ML"],
            cross_refs=["paper_2", "paper_3"],
            cross_cluster="VLA_ARCHITECTURES",
        )
        assert len(insight.tags) == 2
        assert len(insight.cross_refs) == 2
        assert insight.cross_cluster == "VLA_ARCHITECTURES"


class TestDomainGlossary:
    """Tests for DomainGlossary model."""

    def test_defaults(self):
        """Test default values."""
        glossary = DomainGlossary()
        assert glossary.enabled is False
        assert glossary.terms == {}

    def test_with_terms(self):
        """Test with terms populated."""
        glossary = DomainGlossary(
            enabled=True,
            terms={"VLA": "Vision-Language-Action", "LLM": "Large Language Model"},
        )
        assert glossary.enabled is True
        assert len(glossary.terms) == 2


class TestRRD:
    """Tests for RRD model."""

    def test_minimal_creation(self, sample_requirements):
        """Test creating RRD with minimal fields."""
        rrd = RRD(project="Test Research", requirements=sample_requirements)
        assert rrd.project == "Test Research"
        assert rrd.phase == Phase.DISCOVERY
        assert len(rrd.papers_pool) == 0

    def test_missing_project_raises(self):
        """Missing project raises ValidationError."""
        with pytest.raises(ValidationError):
            RRD(requirements=Requirements(focus_area="test"))

    def test_missing_requirements_raises(self):
        """Missing requirements raises ValidationError."""
        with pytest.raises(ValidationError):
            RRD(project="Test")

    def test_default_values(self, sample_requirements):
        """Test default RRD values."""
        rrd = RRD(project="Test", requirements=sample_requirements)
        assert rrd.branchName == ""
        assert rrd.description == ""
        assert rrd.phase == Phase.DISCOVERY
        assert rrd.papers_pool == []
        assert rrd.insights == []
        assert rrd.visited_urls == []
        assert rrd.blocked_sources == []
        assert rrd.open_questions == []

    def test_pending_papers_property(self, sample_requirements):
        """Test pending_papers property."""
        rrd = RRD(
            project="Test",
            requirements=sample_requirements,
            papers_pool=[
                Paper(id="1", title="P1", url="http://1", status=PaperStatus.PENDING),
                Paper(id="2", title="P2", url="http://2", status=PaperStatus.PRESENTED),
                Paper(id="3", title="P3", url="http://3", status=PaperStatus.PENDING),
            ],
        )
        pending = rrd.pending_papers
        assert len(pending) == 2
        assert all(p.status == "pending" for p in pending)

    def test_analyzing_papers_property(self, sample_requirements):
        """Test analyzing_papers property."""
        rrd = RRD(
            project="Test",
            requirements=sample_requirements,
            papers_pool=[
                Paper(id="1", title="P1", url="http://1", status=PaperStatus.ANALYZING),
                Paper(id="2", title="P2", url="http://2", status=PaperStatus.PENDING),
            ],
        )
        assert len(rrd.analyzing_papers) == 1

    def test_analyzed_papers_property(self, sample_requirements):
        """Test analyzed_papers property."""
        rrd = RRD(
            project="Test",
            requirements=sample_requirements,
            papers_pool=[
                Paper(id="1", title="P1", url="http://1", status=PaperStatus.PRESENTED),
                Paper(id="2", title="P2", url="http://2", status=PaperStatus.REJECTED),
                Paper(
                    id="3", title="P3", url="http://3", status=PaperStatus.EXTRACT_INSIGHTS
                ),
                Paper(id="4", title="P4", url="http://4", status=PaperStatus.PENDING),
            ],
        )
        analyzed = rrd.analyzed_papers
        assert len(analyzed) == 3

    def test_presented_papers_property(self, sample_requirements):
        """Test presented_papers property."""
        rrd = RRD(
            project="Test",
            requirements=sample_requirements,
            papers_pool=[
                Paper(id="1", title="P1", url="http://1", status=PaperStatus.PRESENTED),
                Paper(id="2", title="P2", url="http://2", status=PaperStatus.REJECTED),
            ],
        )
        assert len(rrd.presented_papers) == 1
        assert rrd.presented_papers[0].status == "presented"

    def test_completion_percentage_zero_target(self, sample_requirements):
        """Test completion percentage with zero target (edge case)."""
        # Manually construct with target=0 validation bypassed
        rrd = RRD(project="Test", requirements=sample_requirements)
        rrd.requirements.target_papers = 0  # Direct assignment
        # This should return 0.0 to avoid division by zero
        assert rrd.completion_percentage == 0.0

    def test_completion_percentage_normal(self, sample_requirements):
        """Test normal completion percentage."""
        rrd = RRD(project="Test", requirements=sample_requirements)
        rrd.requirements.target_papers = 10
        rrd.statistics.total_analyzed = 5
        assert rrd.completion_percentage == 50.0

    def test_completion_percentage_complete(self, sample_requirements):
        """Test 100% completion."""
        rrd = RRD(project="Test", requirements=sample_requirements)
        rrd.requirements.target_papers = 10
        rrd.statistics.total_analyzed = 10
        assert rrd.completion_percentage == 100.0

    def test_completion_percentage_over_100(self, sample_requirements):
        """Test over 100% (analyzed more than target)."""
        rrd = RRD(project="Test", requirements=sample_requirements)
        rrd.requirements.target_papers = 10
        rrd.statistics.total_analyzed = 15
        assert rrd.completion_percentage == 150.0

    def test_all_phases_assignable(self, sample_requirements):
        """Test that all phases can be assigned."""
        for phase in Phase:
            rrd = RRD(project="Test", requirements=sample_requirements, phase=phase)
            assert rrd.phase == phase

    def test_serialization_uses_enum_values(self, sample_requirements):
        """Test that phase serializes as string value."""
        rrd = RRD(project="Test", requirements=sample_requirements)
        data = rrd.model_dump()
        assert data["phase"] == "DISCOVERY"

    def test_full_rrd(self, sample_requirements, sample_insight):
        """Test RRD with all fields populated."""
        rrd = RRD(
            project="Full Research Project",
            branchName="research/full-test",
            description="A comprehensive test",
            mission=Mission(blue_ocean_scoring=True, min_combined_score=30),
            requirements=sample_requirements,
            domain_glossary=DomainGlossary(enabled=True, terms={"AI": "Artificial Intelligence"}),
            open_questions=["What is the best approach?"],
            phase=Phase.ANALYSIS,
            papers_pool=[
                Paper(id="1", title="P1", url="http://1"),
                Paper(id="2", title="P2", url="http://2"),
            ],
            insights=[sample_insight],
            visited_urls=["http://arxiv.org", "http://scholar.google.com"],
            blocked_sources=["http://blocked.com"],
        )
        assert rrd.project == "Full Research Project"
        assert len(rrd.papers_pool) == 2
        assert len(rrd.insights) == 1
        assert rrd.phase == Phase.ANALYSIS
