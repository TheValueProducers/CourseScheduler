from __future__ import annotations

from fastapi import APIRouter, HTTPException

from schemas.course_schema import CourseRecommendationRequest, CourseRecommendationResponse
from schemas.rank_schema import GroupedCourseRankings
from services.course_service import get_course_recommendations as get_course_recommendations_service
from services.ranking_service import get_all_rankings_by_group

router = APIRouter(tags=["rankings"])


@router.post("/api/course-recommendations", response_model=CourseRecommendationResponse)
def get_course_recommendations(payload: CourseRecommendationRequest) -> CourseRecommendationResponse:
    try:
        query = payload.query.strip()
        if not query:
            raise ValueError("Query must not be empty.")
        courses = get_course_recommendations_service(query=query)
        return CourseRecommendationResponse(courses=courses)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal course recommendation error: {exc}") from exc


@router.get("/api/rankings", response_model=GroupedCourseRankings)
def get_rankings() -> GroupedCourseRankings:
    return get_all_rankings_by_group()


@router.get("/api/rankings/by-group", response_model=GroupedCourseRankings)
def get_rankings_by_group() -> GroupedCourseRankings:
    return get_all_rankings_by_group()
