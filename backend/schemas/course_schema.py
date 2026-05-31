from __future__ import annotations

from pydantic import BaseModel


class CourseSummary(BaseModel):
    subject: str
    course_number: int
    long_title: str | None = None


class ProgramOption(BaseModel):
    value: str
    label: str


class CourseRecommendationRequest(BaseModel):
    query: str


class CourseRecommendationItem(BaseModel):
    course: str
    term: str | None = None
    crn: int | None = None


class CourseRecommendationResponse(BaseModel):
    courses: list[CourseRecommendationItem]
