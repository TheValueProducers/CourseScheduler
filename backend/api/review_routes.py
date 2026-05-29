from __future__ import annotations

from typing import List

from fastapi import APIRouter

from schemas.review_schema import ReviewCreate, ReviewItem
from services.review_service import create_review, list_reviews

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("", response_model=List[ReviewItem])
def get_reviews() -> List[ReviewItem]:
    return [ReviewItem(**review) for review in list_reviews()]


@router.post("", response_model=ReviewItem)
def submit_review(payload: ReviewCreate) -> ReviewItem:
    return ReviewItem(**create_review(payload))
