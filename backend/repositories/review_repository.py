from __future__ import annotations

import re
from typing import Any, Dict, List

from db.database import SessionLocal
from models.review import Review
from schemas.review_schema import ReviewCreate


def _parse_course_code(course: str) -> tuple[str, str] | None:
    value = " ".join((course or "").strip().upper().split())
    match = re.match(r"^([A-Z]{2,5})\s*(\d{3})$", value)
    if not match:
        return None
    return match.group(1), match.group(2)


def _to_dict(review: Review) -> Dict[str, Any]:
    return {
        "id": review.id,
        "overall_workload": review.overall_workload,
        "content_difficulty": review.content_difficulty,
        "exam_difficulty": review.exam_difficulty,
        "project_assignment_difficulty": review.project_assignment_difficulty,
        "instructor": review.instructor,
        "practical_usefulness": review.practical_usefulness,
        "interest_enjoyment": review.interest_enjoyment,
        "user_like": review.user_like,
        "user_dislike": review.user_dislike,
        "course_number": review.course_number,
        "subject": review.subject,
    }


def list_reviews() -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        rows = db.query(Review).order_by(Review.id.asc()).all()
        return [_to_dict(row) for row in rows]


def create_review(payload: ReviewCreate) -> Dict[str, Any]:
    with SessionLocal() as db:
        row = Review(**payload.model_dump())
        db.add(row)
        db.commit()
        db.refresh(row)
        return _to_dict(row)


def get_reviews_for_course(course: str) -> List[Dict[str, Any]]:
    parsed = _parse_course_code(course)
    if parsed is None:
        return []

    subject, course_number = parsed
    with SessionLocal() as db:
        rows = (
            db.query(Review)
            .filter(Review.subject == subject, Review.course_number == course_number)
            .order_by(Review.id.asc())
            .all()
        )
        return [_to_dict(row) for row in rows]
