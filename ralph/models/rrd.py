"""Research Requirements Document (RRD) model."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from ralph.models.paper import Paper


class Phase(str, Enum):
    """Research phase."""

    DISCOVERY = "DISCOVERY"
    ANALYSIS = "ANALYSIS"
    IDEATION = "IDEATION"
    COMPLETE = "COMPLETE"


class Mission(BaseModel):
    """Mission configuration for blue ocean scoring."""

    blue_ocean_scoring: bool = Field(default=True, description="Enable strategic scoring")
    min_blue_ocean_score: int = Field(default=12, ge=0, le=20, description="Minimum blue ocean score")
    min_combined_score: int = Field(default=25, ge=0, le=50, description="Minimum combined score")
    strategic_focus: str = Field(default="balanced", description="balanced, execution, or blue_ocean")


class Requirements(BaseModel):
    """Research requirements configuration."""

    focus_area: str = Field(..., description="Primary research focus area")
    keywords: list[str] = Field(default_factory=list, description="Search keywords")
    time_window_days: int = Field(default=30, ge=1, description="Days to look back for recent papers")
    historical_lookback_days: int = Field(default=365, description="Days for historical context")
    target_papers: int = Field(default=20, ge=1, description="Target number of papers to analyze")
    sources: list[str] = Field(default_factory=lambda: ["arXiv", "Google Scholar", "web"])
    min_score_to_present: int = Field(default=18, ge=0, le=50, description="Minimum score to present")


class PhaseTiming(BaseModel):
    """Timing for a single phase."""

    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class AnalysisTiming(PhaseTiming):
    """Timing for analysis phase with additional metrics."""

    papers_analyzed: int = 0
    avg_seconds_per_paper: Optional[float] = None


class Timing(BaseModel):
    """Timing information for the research."""

    research_started_at: Optional[datetime] = None
    discovery: PhaseTiming = Field(default_factory=PhaseTiming)
    analysis: AnalysisTiming = Field(default_factory=AnalysisTiming)
    ideation: PhaseTiming = Field(default_factory=PhaseTiming)
    complete: PhaseTiming = Field(default_factory=PhaseTiming)


class ProductIdeationConfig(BaseModel):
    """Configuration for product ideation handoff."""

    enabled: bool = True
    min_ideas: int = Field(default=3, ge=1)
    max_ideas: int = Field(default=12, ge=1)
    output_filename: str = "product-ideas.json"
    ranking_goal: str = "pick_one_for_prd"
    assumed_constraints: dict[str, Any] = Field(
        default_factory=lambda: {
            "team_size": 3,
            "time_horizon_months": 3,
            "deployment_preference": ["saas", "on_prem"],
        }
    )


class Handoff(BaseModel):
    """Handoff configuration."""

    product_ideation: ProductIdeationConfig = Field(default_factory=ProductIdeationConfig)


class Insight(BaseModel):
    """An extracted insight from a paper."""

    id: str = Field(..., description="Unique insight ID")
    paper_id: str = Field(..., description="Source paper ID")
    insight: str = Field(..., description="The insight text")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    cross_refs: list[str] = Field(default_factory=list, description="Related paper IDs")
    cross_cluster: Optional[str] = Field(default=None, description="Cross-reference cluster name")


class DiscoveryMetrics(BaseModel):
    """Metrics from the discovery phase."""

    sources_tried: list[str] = Field(default_factory=list)
    sources_successful: list[str] = Field(default_factory=list)
    sources_blocked: list[str] = Field(default_factory=list)
    source_failure_reasons: dict[str, str] = Field(default_factory=dict)


class ScoreDistribution(BaseModel):
    """Distribution of scores across buckets."""

    range_0_17: int = Field(default=0, alias="0-17")
    range_18_24: int = Field(default=0, alias="18-24")
    range_25_34: int = Field(default=0, alias="25-34")
    range_35_50: int = Field(default=0, alias="35-50")

    model_config = ConfigDict(populate_by_name=True)


class BlueOceanDistribution(BaseModel):
    """Distribution of blue ocean scores across buckets."""

    range_0_7: int = Field(default=0, alias="0-7")
    range_8_11: int = Field(default=0, alias="8-11")
    range_12_15: int = Field(default=0, alias="12-15")
    range_16_20: int = Field(default=0, alias="16-20")

    model_config = ConfigDict(populate_by_name=True)


class AnalysisMetrics(BaseModel):
    """Metrics from the analysis phase."""

    avg_combined_score: float = 0
    avg_execution_score: float = 0
    avg_blue_ocean_score: float = 0
    combined_score_distribution: ScoreDistribution = Field(default_factory=ScoreDistribution)
    blue_ocean_distribution: BlueOceanDistribution = Field(default_factory=BlueOceanDistribution)


class IdeationMetrics(BaseModel):
    """Metrics from the ideation phase."""

    product_ideas_generated: int = 0
    top_idea_id: Optional[str] = None


class Statistics(BaseModel):
    """Research statistics."""

    total_discovered: int = 0
    total_analyzed: int = 0
    total_presented: int = 0
    total_rejected: int = 0
    total_insights_extracted: int = 0
    discovery_metrics: DiscoveryMetrics = Field(default_factory=DiscoveryMetrics)
    analysis_metrics: AnalysisMetrics = Field(default_factory=AnalysisMetrics)
    ideation_metrics: IdeationMetrics = Field(default_factory=IdeationMetrics)


class DomainGlossary(BaseModel):
    """Domain-specific glossary."""

    enabled: bool = False
    terms: dict[str, str] = Field(default_factory=dict)


class RRD(BaseModel):
    """Research Requirements Document - the main research state."""

    project: str = Field(..., description="Project name")
    branchName: str = Field(default="", description="Git branch name")
    description: str = Field(default="", description="Research description")

    mission: Mission = Field(default_factory=Mission)
    requirements: Requirements
    domain_glossary: DomainGlossary = Field(default_factory=DomainGlossary)
    open_questions: list[str] = Field(default_factory=list)

    phase: Phase = Field(default=Phase.DISCOVERY)
    timing: Timing = Field(default_factory=Timing)
    handoff: Handoff = Field(default_factory=Handoff)

    papers_pool: list[Paper] = Field(default_factory=list)
    insights: list[Insight] = Field(default_factory=list)
    visited_urls: list[str] = Field(default_factory=list)
    blocked_sources: list[str] = Field(default_factory=list)
    statistics: Statistics = Field(default_factory=Statistics)

    model_config = ConfigDict(use_enum_values=True)

    @property
    def pending_papers(self) -> list[Paper]:
        """Get papers with pending status."""
        return [p for p in self.papers_pool if p.status == "pending"]

    @property
    def analyzing_papers(self) -> list[Paper]:
        """Get papers currently being analyzed."""
        return [p for p in self.papers_pool if p.status == "analyzing"]

    @property
    def analyzed_papers(self) -> list[Paper]:
        """Get papers that have been analyzed."""
        return [
            p for p in self.papers_pool if p.status in ("presented", "rejected", "extract_insights")
        ]

    @property
    def presented_papers(self) -> list[Paper]:
        """Get papers marked as PRESENT."""
        return [p for p in self.papers_pool if p.status == "presented"]

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.requirements.target_papers == 0:
            return 0.0
        return (self.statistics.total_analyzed / self.requirements.target_papers) * 100
