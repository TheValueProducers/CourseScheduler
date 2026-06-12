from __future__ import annotations

from typing import Any, Dict, List

from db.database import SessionLocal
from repositories.review_repository import ReviewRepository
from schemas.review_schema import ReviewCreate


def list_reviews() -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        repo = ReviewRepository(db)
        return repo.list_reviews()


def create_review(payload: ReviewCreate) -> Dict[str, Any]:
    with SessionLocal() as db:
        repo = ReviewRepository(db)
        return repo.create_review(payload)
