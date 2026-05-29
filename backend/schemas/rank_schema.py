from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class RankingCategory(BaseModel):
    name: str
    courses: list[str] = Field(default_factory=list)


class RankingGroup(BaseModel):
    title: str
    categories: list[RankingCategory]


class CourseRankRow(BaseModel):
    course: str
    bayesian_score: float
    numerical_score: float | None = None
    num_reviews: int


class MetricRankings(BaseModel):
    workload: List[CourseRankRow] = Field(default_factory=list)
    content_diff: List[CourseRankRow] = Field(default_factory=list)
    exam_diff: List[CourseRankRow] = Field(default_factory=list)
    assignment_diff: List[CourseRankRow] = Field(default_factory=list)
    overall_diff: List[CourseRankRow] = Field(default_factory=list)
    instructor: List[CourseRankRow] = Field(default_factory=list)
    usefulness: List[CourseRankRow] = Field(default_factory=list)
    interest: List[CourseRankRow] = Field(default_factory=list)


class GroupedCourseRankings(BaseModel):
    d1: MetricRankings = Field(default_factory=MetricRankings)
    d2: MetricRankings = Field(default_factory=MetricRankings)
    d3: MetricRankings = Field(default_factory=MetricRankings)
    diversity: MetricRankings = Field(default_factory=MetricRankings)
    lpap: MetricRankings = Field(default_factory=MetricRankings)
