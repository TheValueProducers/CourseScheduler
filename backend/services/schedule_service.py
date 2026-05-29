from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List

from degree_requirement import get_supported_program_options
from repositories.course_repository import get_course_catalog
from scheduler_engine import build_schedule, check_requirements_for_courses
from schemas.schedule_schema import CheckRequirementsInputItem, ScheduleRequest


@lru_cache(maxsize=1)
def get_course_summaries() -> List[Dict[str, Any]]:
    catalog = get_course_catalog()
    return [
        {"subject": record.subject, "course_number": record.course_number, "long_title": record.long_title}
        for record in sorted(catalog.values(), key=lambda c: (c.subject, c.course_number))
    ]


def get_program_options() -> List[Dict[str, str]]:
    return get_supported_program_options()


def generate_schedule(payload: ScheduleRequest) -> Dict[str, Any]:
    catalog = get_course_catalog()
    return build_schedule(
        catalog=catalog,
        current_term=payload.current_term,
        year=payload.year,
        completed_courses=payload.completed_courses,
        preferred_courses=payload.preferred_courses,
        avoid_courses=payload.avoid_courses,
        scheduled_courses=payload.scheduled_courses,
        chosen_degree=payload.chosen_degree,
        optimization=payload.optimization,
    )


def evaluate_requirements(payload: List[CheckRequirementsInputItem]) -> List[Dict[str, Any]]:
    catalog = get_course_catalog()
    output: List[Dict[str, Any]] = []

    for item in payload:
        rows = check_requirements_for_courses(
            catalog=catalog,
            course_codes=item.classes,
            chosen_degree=item.chosen_degree,
        )
        output.append({"type": item.type, "requirements": rows})

    return output
