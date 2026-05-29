from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class ScheduleRequest(BaseModel):
    current_term: Literal["Fall", "Spring"]
    year: Literal["Freshman", "Sophomore", "Junior", "Senior"]
    completed_courses: List[str] = Field(default_factory=list)
    preferred_courses: List[str] = Field(default_factory=list)
    avoid_courses: List[str] = Field(default_factory=list)
    scheduled_courses: Dict[str, int] = Field(default_factory=dict)
    chosen_degree: List[str] = Field(default_factory=lambda: ["bs_comp"])
    optimization: Literal["balanced", "graduate early"] = "balanced"


class RequirementStatus(BaseModel):
    satisfied: bool
    progress: List[int]


class ScheduleResponse(BaseModel):
    status: str
    schedule: Dict[str, List[List[str]]]
    requirements: Dict[str, RequirementStatus]
    message: str | None = None


class CheckRequirementsInputItem(BaseModel):
    type: Literal["planned", "attended"]
    classes: List[str] = Field(default_factory=list)
    chosen_degree: List[str] = Field(default_factory=lambda: ["bs_comp"])


class CheckRequirementsRequirementItem(BaseModel):
    type: str
    satisfied: bool
    progress: List[int]


class CheckRequirementsOutputItem(BaseModel):
    type: Literal["planned", "attended"]
    requirements: List[CheckRequirementsRequirementItem]
