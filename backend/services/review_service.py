from __future__ import annotations

from typing import Any, Dict, List

from repositories.review_repository import create_review as create_review_record
from repositories.review_repository import list_reviews as list_review_records
from schemas.review_schema import ReviewCreate


def list_reviews() -> List[Dict[str, Any]]:
    return list_review_records()


def create_review(payload: ReviewCreate) -> Dict[str, Any]:
    return create_review_record(payload)
