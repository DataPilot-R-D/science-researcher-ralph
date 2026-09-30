"""Validate the content and evidence needed for a product-ideation handoff."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IdeaText(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)


class IdeaProblem(IdeaText):
    who: str
    pain: str
    why_now: str


class IdeaSolution(IdeaText):
    what: str
    mvp_scope: list[str] = Field(min_length=1)


class IdeaEvidence(IdeaText):
    paper_ids: list[str] = Field(min_length=1)
    insight_ids: list[str] = Field(default_factory=list)


class IdeaScores(BaseModel):
    execution_0_30: int = Field(ge=0, le=30)
    blue_ocean_0_20: int = Field(ge=0, le=20)
    combined_0_50: int = Field(ge=0, le=50)
    confidence_0_1: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def check_total(self) -> Self:
        if self.combined_0_50 != self.execution_0_30 + self.blue_ocean_0_20:
            raise ValueError("combined score must equal execution plus blue ocean")
        return self


class ProductIdea(IdeaText):
    id: str
    name: str
    one_liner: str
    problem: IdeaProblem
    solution: IdeaSolution
    evidence: IdeaEvidence
    scores: IdeaScores


class ProductIdeas(IdeaText):
    schema_version: Literal["1.0"]
    project: str
    ideas: list[ProductIdea] = Field(min_length=1)
