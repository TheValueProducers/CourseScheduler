from __future__ import annotations

from pydantic import BaseModel


class CourseRecommendationFilter(BaseModel):
    course_level: list[int] | None = None
    distribution: int | None = None
    analyzing_diversity: bool | None = None
    subject: str | None = None


class CourseSummary(BaseModel):
    subject: str
    course_number: int
    long_title: str | None = None


class ProgramOption(BaseModel):
    value: str
    label: str


class CourseRecommendationRequest(BaseModel):
    query: str
    filters: CourseRecommendationFilter | None = None


class CourseRecommendationItem(BaseModel):
    course: str
    term: str | None = None
    crn: int | None = None


class CourseRecommendationResponse(BaseModel):
    courses: list[CourseRecommendationItem]
