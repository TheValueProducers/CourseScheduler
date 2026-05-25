from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from degree_requirement import get_supported_program_options
from scheduler_engine import build_schedule, check_requirements_for_courses, load_course_catalog


class ScheduleRequest(BaseModel):
    current_term: Literal["Fall", "Spring"]
    year: Literal["Freshman", "Sophomore", "Junior", "Senior"]
    completed_courses: List[str] = Field(default_factory=list)
    preferred_courses: List[str] = Field(default_factory=list)
    avoid_courses: List[str] = Field(default_factory=list)
    scheduled_courses: Dict[str, int] = Field(default_factory=dict)
    chosen_degree: List[str] = Field(default_factory=lambda: ["bs_comp"])
    optimization: Literal["balanced", "graduate early"] = "balanced"


class RequirementStatus(BaseModel):
    satisfied: bool
    progress: List[int]


class ScheduleResponse(BaseModel):
    status: str
    schedule: Dict[str, List[List[str]]]
    requirements: Dict[str, RequirementStatus]
    message: str | None = None


class CourseSummary(BaseModel):
    subject: str
    course_number: int
    long_title: str | None = None


class ProgramOption(BaseModel):
    value: str
    label: str


class CheckRequirementsInputItem(BaseModel):
    type: Literal["planned", "attended"]
    classes: List[str] = Field(default_factory=list)
    chosen_degree: List[str] = Field(default_factory=lambda: ["bs_comp"])


class CheckRequirementsRequirementItem(BaseModel):
    type: str
    satisfied: bool
    progress: List[int]


class CheckRequirementsOutputItem(BaseModel):
    type: Literal["planned", "attended"]
    requirements: List[CheckRequirementsRequirementItem]


app = FastAPI(
    title="Course Scheduler Backend",
    version="1.0.0",
    description="CP-SAT based course scheduler using Rice catalog data.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "https://course-scheduler-nu.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_catalog() -> Dict[str, Any]:
    data_path = Path(__file__).with_name("rice_course_pages.json")
    if not data_path.exists():
        raise FileNotFoundError(f"Course catalog data file not found: {data_path}")
    return load_course_catalog(data_path)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/courses", response_model=List[CourseSummary])
def get_all_courses() -> List[CourseSummary]:
    catalog = get_catalog()
    courses: List[CourseSummary] = []

    for record in catalog.values():
        courses.append(
            CourseSummary(
                subject=record.subject,
                course_number=record.course_number,
                long_title=record.long_title,
            )
        )

    return sorted(courses, key=lambda c: (c.subject, c.course_number))


@app.get("/api/programs", response_model=List[ProgramOption])
def get_supported_programs() -> List[ProgramOption]:
    return [ProgramOption(**row) for row in get_supported_program_options()]


@app.post("/api/schedule", response_model=ScheduleResponse)
def generate_schedule(payload: ScheduleRequest) -> ScheduleResponse:
    try:
        result = build_schedule(
            catalog=get_catalog(),
            current_term=payload.current_term,
            year=payload.year,
            completed_courses=payload.completed_courses,
            preferred_courses=payload.preferred_courses,
            avoid_courses=payload.avoid_courses,
            scheduled_courses=payload.scheduled_courses,
            chosen_degree=payload.chosen_degree,
            optimization=payload.optimization,
        )
        return ScheduleResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal scheduling error: {exc}") from exc


@app.post("/api/check-requirements", response_model=List[CheckRequirementsOutputItem])
def check_requirements(payload: List[CheckRequirementsInputItem]) -> List[CheckRequirementsOutputItem]:
    try:
        catalog = get_catalog()
        output: List[CheckRequirementsOutputItem] = []

        for item in payload:
            rows = check_requirements_for_courses(
                catalog=catalog,
                course_codes=item.classes,
                chosen_degree=item.chosen_degree,
            )
            output.append(
                CheckRequirementsOutputItem(
                    type=item.type,
                    requirements=[CheckRequirementsRequirementItem(**row) for row in rows],
                )
            )

        return output
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal requirement check error: {exc}") from exc
