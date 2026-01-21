"""Paper model with scoring and status."""

from datetime import date as dt_date
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class PaperStatus(str, Enum):
    """Status of a paper in the research pipeline."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    PRESENTED = "presented"
    REJECTED = "rejected"
    EXTRACT_INSIGHTS = "extract_insights"
    INSIGHTS_EXTRACTED = "insights_extracted"


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown for a paper."""

    # Execution Rubric (0-30)
    novelty: int = Field(default=0, ge=0, le=5, description="How new/different is this approach?")
    feasibility: int = Field(default=0, ge=0, le=5, description="Can a small team build this?")
    time_to_poc: int = Field(default=0, ge=0, le=5, description="How quickly can we prototype?")
    value_market: int = Field(default=0, ge=0, le=5, description="Is there clear demand?")
    defensibility: int = Field(default=0, ge=0, le=5, description="What's the competitive advantage?")
    adoption: int = Field(default=0, ge=0, le=5, description="How easy to deploy?")

    # Blue Ocean Rubric (0-20)
    market_creation: int = Field(default=0, ge=0, le=5, description="New market or existing competition?")
    first_mover_window: int = Field(default=0, ge=0, le=5, description="Time until competitors replicate?")
    network_data_effects: int = Field(default=0, ge=0, le=5, description="Does value compound over time?")
    strategic_clarity: int = Field(default=0, ge=0, le=5, description="How focused is the opportunity?")

    @property
    def execution_score(self) -> int:
        """Calculate execution rubric score (0-30)."""
        return (
            self.novelty
            + self.feasibility
            + self.time_to_poc
            + self.value_market
            + self.defensibility
            + self.adoption
        )

    @property
    def blue_ocean_score(self) -> int:
        """Calculate blue ocean rubric score (0-20)."""
        return (
            self.market_creation
            + self.first_mover_window
            + self.network_data_effects
            + self.strategic_clarity
        )

    @property
    def combined_score(self) -> int:
        """Calculate combined score (0-50)."""
        return self.execution_score + self.blue_ocean_score


class Paper(BaseModel):
    """A research paper in the pool."""

    id: str = Field(..., description="Unique identifier (e.g., arxiv_2501.12345)")
    title: str = Field(..., description="Paper title")
    url: str = Field(..., description="Paper URL")
    pdf_url: Optional[str] = Field(default=None, description="Direct PDF URL")
    authors: list[str] = Field(default_factory=list, description="List of authors")
    date: Optional[dt_date] = Field(default=None, description="Publication date")
    source: str = Field(default="unknown", description="Source (arXiv, Google Scholar, etc.)")
    priority: int = Field(default=3, ge=1, le=5, description="Discovery priority (1-5)")
    status: PaperStatus = Field(default=PaperStatus.PENDING, description="Current status")
    score: Optional[int] = Field(default=None, ge=0, le=50, description="Combined score (0-50)")
    score_breakdown: Optional[ScoreBreakdown] = Field(default=None, description="Detailed score breakdown")
    analysis: Optional[Union[str, dict[str, Any]]] = Field(default=None, description="Analysis summary or detailed analysis dict")
    decision: Optional[str] = Field(default=None, description="PRESENT/REJECT/EXTRACT_INSIGHTS")
    notes: str = Field(default="", description="Additional notes")
    implementation_url: Optional[str] = Field(default=None, description="GitHub/implementation URL")
    commercialized: Optional[bool] = Field(default=None, description="Whether already commercialized")

    class Config:
        use_enum_values = True
