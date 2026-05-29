from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    overall_workload: int = Field(ge=1, le=5)
    content_difficulty: int = Field(ge=1, le=5)
    exam_difficulty: int = Field(ge=1, le=5)
    project_assignment_difficulty: int = Field(ge=1, le=5)
    instructor: int = Field(ge=1, le=5)
    practical_usefulness: int = Field(ge=1, le=5)
    interest_enjoyment: int = Field(ge=1, le=5)
    user_like: str
    user_dislike: str
    course_number: str
    subject: str


class ReviewItem(ReviewCreate):
    id: int
