from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from schemas.course_schema import CourseSummary, ProgramOption
from schemas.schedule_schema import (
    CheckRequirementsInputItem,
    CheckRequirementsOutputItem,
    CheckRequirementsRequirementItem,
    RequirementStatus,
    ScheduleRequest,
    ScheduleResponse,
)
from services.schedule_service import evaluate_requirements, generate_schedule, get_course_summaries, get_program_options

router = APIRouter(tags=["schedule"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/courses", response_model=List[CourseSummary])
def get_all_courses() -> List[CourseSummary]:
    return [CourseSummary(**row) for row in get_course_summaries()]


@router.get("/api/programs", response_model=List[ProgramOption])
def get_supported_programs() -> List[ProgramOption]:
    return [ProgramOption(**row) for row in get_program_options()]


@router.post("/api/schedule", response_model=ScheduleResponse)
def create_schedule(payload: ScheduleRequest) -> ScheduleResponse:
    try:
        result = generate_schedule(payload)
        return ScheduleResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal scheduling error: {exc}") from exc


@router.post("/api/check-requirements", response_model=List[CheckRequirementsOutputItem])
def check_requirements(payload: List[CheckRequirementsInputItem]) -> List[CheckRequirementsOutputItem]:
    try:
        result = evaluate_requirements(payload)
        return [
            CheckRequirementsOutputItem(
                type=row["type"],
                requirements=[CheckRequirementsRequirementItem(**req) for req in row["requirements"]],
            )
            for row in result
        ]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal requirement check error: {exc}") from exc
