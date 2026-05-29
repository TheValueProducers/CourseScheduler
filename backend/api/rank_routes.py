from __future__ import annotations

from fastapi import APIRouter

from schemas.rank_schema import GroupedCourseRankings
from services.ranking_service import get_all_rankings_by_group

router = APIRouter(prefix="/api/rankings", tags=["rankings"])


@router.get("", response_model=GroupedCourseRankings)
def get_rankings() -> GroupedCourseRankings:
    return get_all_rankings_by_group()


@router.get("/by-group", response_model=GroupedCourseRankings)
def get_rankings_by_group() -> GroupedCourseRankings:
    return get_all_rankings_by_group()
