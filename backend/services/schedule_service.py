from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from ortools.sat.python import cp_model
from optimizer.build_schedule import _course_matches_filter

from data.degree_requirement import get_supported_program_options, get_supported_program_requirements
from db.database import SessionLocal
from repositories.course_repository import CourseRepository
from parsers.parse_schedule import (
    normalize_course_code,
)
from schemas.schedule_schema import CheckRequirementsInputItem, ScheduleRequest

from optimizer.constraints import DISTRIBUTION_REQUIREMENTS, YEAR_ORDER, TERM_ORDER, TOTAL_SEMESTERS
from optimizer.build_model import build_schedule

from optimizer.build_schedule import _evaluate_requirement_from_taken

# -----------------------------
# Important information
# -----------------------------




SUPPORTED_DEGREE_REQUIREMENTS: Dict[str, List[Dict[str, Any]]] = get_supported_program_requirements()


def _supported_program_message() -> str:
    supported = sorted(SUPPORTED_DEGREE_REQUIREMENTS.keys())
    if not supported:
        return "No supported degree selected. No programs are currently configured."
    listed = ", ".join(f"'{name}'" for name in supported)
    return f"No supported degree selected. Include one or more of: {listed} in chosen_degree."


def _selected_degree_requirements(chosen_degree: List[str]) -> List[Dict[str, Any]]:
    selected_degrees = [d for d in chosen_degree if d in SUPPORTED_DEGREE_REQUIREMENTS]
    is_multi_degree = len(selected_degrees) > 1
    selected: List[Dict[str, Any]] = []
    for degree in selected_degrees:
        requirements = SUPPORTED_DEGREE_REQUIREMENTS.get(degree)
        if requirements:
            for req in requirements:
                req_copy = dict(req)
                if is_multi_degree:
                    req_copy["id"] = f"{degree}:{req['id']}"
                selected.append(req_copy)
    return selected


# -----------------------------
# Class Information
# -----------------------------

@dataclass
class CourseRecord:
    code: str
    subject: str
    course_number: int
    long_title: Optional[str]
    offered_terms: Set[str]
    credit_hours: Optional[float]
    distribution: Optional[str]
    analyzing_diversity: bool
    cross_list: List[str]
    prereq_tree: Optional[Dict[str, Any]]




# -----------------------------
# Defining important information
# -----------------------------

_normalize_course_code = normalize_course_code


def _remaining_semester_indices(current_term: str, year: str) -> Tuple[List[int], int]:
    """
    Return a list of remaining semesters and the current semester based on year and term

    Input: current_term e.g. Spring, and year e.g. Freshman
    Output:
    - A list of remaining semesters. e.g. Sophomore Spring returns [0,1,2,3,4]
    - An integer representing the semester e.g. Sophomore Spring returns 3
    
    """
    if year not in YEAR_ORDER:
        raise ValueError(f"Invalid year: {year}. Expected one of {YEAR_ORDER}.")
    if current_term not in TERM_ORDER:
        raise ValueError(f"Invalid current_term: {current_term}. Expected one of {TERM_ORDER}.")

    current_year_idx = YEAR_ORDER.index(year)
    current_term_idx = TERM_ORDER.index(current_term)
    current_semester_number = current_year_idx * 2 + current_term_idx
    remaining = TOTAL_SEMESTERS - current_semester_number
    if remaining <= 0:
        raise ValueError("No semesters remain based on current_term and year.")
    return list(range(remaining)), current_semester_number













def _collect_special_course_buckets(
    catalog: Dict[str, CourseRecord],
) -> Tuple[Dict[str, List[str]], List[str], List[str], List[str]]:
    distribution_courses: Dict[str, List[str]] = {
        "Distribution Group I": [],
        "Distribution Group II": [],
        "Distribution Group III": [],
    }
    diversity_courses: List[str] = []
    fwis_courses: List[str] = []
    lpap_courses: List[str] = []

    for code, rec in catalog.items():
        if rec.distribution in distribution_courses:
            distribution_courses[rec.distribution].append(code)
        if rec.analyzing_diversity:
            diversity_courses.append(code)
        if code.startswith("FWIS"):
            fwis_courses.append(code)
        if code.startswith("LPAP"):
            lpap_courses.append(code)

    return distribution_courses, diversity_courses, fwis_courses, lpap_courses


def _build_candidate_course_pool(
    expanded_requirements: List[Dict[str, Any]],
    distribution_courses: Dict[str, List[str]],
    diversity_courses: List[str],
    fwis_courses: List[str],
    lpap_courses: List[str],
    preferred: Set[str],
    avoid: Set[str],
    scheduled: Dict[str, int],
    catalog: Dict[str, CourseRecord],
) -> Set[str]:
    all_courses: Set[str] = set()

    for req in expanded_requirements:
        if "courses" in req:
            all_courses.update(_normalize_course_code(c) for c in req["courses"])
        if "options" in req:
            for option in req["options"]:
                if isinstance(option, list):
                    all_courses.update(_normalize_course_code(c) for c in option)

    for dist_list in distribution_courses.values():
        all_courses.update(dist_list)

    all_courses.update(diversity_courses)
    all_courses.update(fwis_courses)
    all_courses.update(lpap_courses)
    all_courses.update(preferred)
    all_courses.update(avoid)
    all_courses.update(scheduled.keys())

    for req in expanded_requirements:
        if "filters" not in req:
            continue
        filters = req.get("filters", {})
        constraints = req.get("constraints", {})
        for code, rec in catalog.items():
            if _course_matches_filter(rec, filters, constraints):
                all_courses.add(code)

    return {c for c in all_courses if c in catalog}


def _validate_scheduled_course_indices(
    scheduled: Dict[str, int],
    catalog: Dict[str, CourseRecord],
) -> None:
    for course, absolute_sem in scheduled.items():
        if course not in catalog:
            raise ValueError(f"Scheduled course not found in catalog: {course}")
        if absolute_sem < 0 or absolute_sem >= TOTAL_SEMESTERS:
            raise ValueError(
                f"Scheduled semester index for {course} must be between 0 and {TOTAL_SEMESTERS - 1}."
            )












def _collect_required_or_choice_courses(expanded_requirements: List[Dict[str, Any]]) -> Set[str]:
    required_or_choice: Set[str] = set()
    for req in expanded_requirements:
        if "courses" in req:
            required_or_choice.update(_normalize_course_code(c) for c in req["courses"])
        if "options" in req:
            for option in req["options"]:
                if isinstance(option, list):
                    required_or_choice.update(_normalize_course_code(c) for c in option)
    return required_or_choice






def check_requirements_for_courses(
    catalog: Dict[str, CourseRecord],
    course_codes: List[str],
    chosen_degree: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    taken = {_normalize_course_code(c) for c in course_codes if isinstance(c, str) and c.strip()}
    chosen_degree_normalized = [str(d).strip().lower() for d in (chosen_degree or ["bs_comp"]) if str(d).strip()]
    degree_requirements = _selected_degree_requirements(chosen_degree_normalized)
    if not degree_requirements:
        raise ValueError(_supported_program_message())

    rows: List[Dict[str, Any]] = []

    for req in degree_requirements:
        req_type = req["id"]
        if req.get("requirement_type") == "composite":
            sub_requirements = [sub for sub in req.get("sub_requirements", []) if isinstance(sub, dict)]
            sub_satisfied_count = 0
            for sub_req in sub_requirements:
                sub_satisfied, _ = _evaluate_requirement_from_taken(sub_req, taken, catalog)
                if sub_satisfied:
                    sub_satisfied_count += 1

            min_subject_ok = True
            for rule in req.get("constraints", {}).get("min_from_subject", []):
                subject = str(rule.get("subject", "")).upper()
                min_count = int(rule.get("min_count", 0))
                if not subject or min_count <= 0:
                    continue
                eligible_subject_courses: Set[str] = set()
                for sub_req in sub_requirements:
                    if "courses" in sub_req:
                        eligible_subject_courses.update(_normalize_course_code(c) for c in sub_req.get("courses", []))
                    elif "options" in sub_req:
                        for option in sub_req.get("options", []):
                            if isinstance(option, list):
                                eligible_subject_courses.update(_normalize_course_code(c) for c in option)
                    elif "filters" in sub_req:
                        filters = sub_req.get("filters", {})
                        constraints = sub_req.get("constraints", {})
                        eligible_subject_courses.update(
                            code for code, rec in catalog.items() if _course_matches_filter(rec, filters, constraints)
                        )

                subject_count = sum(1 for c in taken if c in eligible_subject_courses and c.split(" ")[0] == subject)
                if subject_count < min_count:
                    min_subject_ok = False
                    break

            total_needed = len(sub_requirements)
            rows.append(
                {
                    "type": req_type,
                    "satisfied": sub_satisfied_count >= total_needed and min_subject_ok,
                    "progress": [sub_satisfied_count, total_needed],
                }
            )
            continue

        satisfying_courses: List[str] = []

        if "courses" in req:
            satisfying_courses = sorted(
                _normalize_course_code(c)
                for c in req["courses"]
                if _normalize_course_code(c) in catalog
            )
        elif "filters" in req:
            filters = req.get("filters", {})
            constraints = req.get("constraints", {})
            satisfying_courses = sorted(
                code
                for code, rec in catalog.items()
                if _course_matches_filter(rec, filters, constraints)
            )
        elif "options" in req:
            option_courses: List[str] = []
            for option in req.get("options", []):
                if isinstance(option, list):
                    option_courses.extend(_normalize_course_code(c) for c in option)
            satisfying_courses = sorted({c for c in option_courses if c in catalog})

        taken_count = len([c for c in satisfying_courses if c in taken])
        total_count = len(satisfying_courses)

        if req["requirement_type"] == "required_courses":
            satisfied = taken_count >= total_count
        elif req["requirement_type"] == "choose_group":
            satisfied_groups = 0
            for raw_group in req.get("options", []):
                if not isinstance(raw_group, list):
                    continue
                group_courses = [_normalize_course_code(c) for c in raw_group]
                if group_courses and all(course in taken for course in group_courses):
                    satisfied_groups += 1

            target = int(req.get("min_count", 1))
            satisfied = satisfied_groups >= target
            total_count = target
            taken_count = min(satisfied_groups, target)
        else:
            target = int(req.get("min_count", 0))
            satisfied = taken_count >= target
            total_count = target
            taken_count = min(taken_count, target)

        rows.append(
            {
                "type": req_type,
                "satisfied": satisfied,
                "progress": [taken_count, total_count],
            }
        )

    for dist, min_courses in DISTRIBUTION_REQUIREMENTS.items():
        dist_courses = [code for code, rec in catalog.items() if rec.distribution == dist]
        taken_count = len([c for c in dist_courses if c in taken])
        rows.append(
            {
                "type": dist,
                "satisfied": taken_count >= min_courses,
                "progress": [min(taken_count, min_courses), min_courses],
            }
        )

    diversity_courses = [code for code, rec in catalog.items() if rec.analyzing_diversity]
    diversity_taken = len([c for c in diversity_courses if c in taken])
    rows.append(
        {
            "type": "analyzing_diversity",
            "satisfied": diversity_taken >= 1,
            "progress": [1 if diversity_taken >= 1 else 0, 1],
        }
    )

    fwis_courses = [code for code in catalog if code.startswith("FWIS")]
    fwis_taken = len([c for c in fwis_courses if c in taken])
    rows.append(
        {
            "type": "FWIS",
            "satisfied": fwis_taken >= 1,
            "progress": [1 if fwis_taken >= 1 else 0, 1],
        }
    )

    lpap_courses = [code for code in catalog if code.startswith("LPAP")]
    lpap_taken = len([c for c in lpap_courses if c in taken])
    rows.append(
        {
            "type": "LPAP",
            "satisfied": lpap_taken >= 1,
            "progress": [1 if lpap_taken >= 1 else 0, 1],
        }
    )

    total_credits = sum((catalog[c].credit_hours or 0) for c in taken if c in catalog)
    rows.append(
        {
            "type": "total_credits",
            "satisfied": total_credits >= 120,
            "progress": [min(total_credits, 120), 120],
        }
    )

    return rows


@lru_cache(maxsize=1)
def get_course_summaries() -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        catalog = CourseRepository(db).get_course_catalog()
    return [
        {"subject": record.subject, "course_number": record.course_number, "long_title": record.long_title}
        for record in sorted(catalog.values(), key=lambda c: (c.subject, c.course_number))
    ]


def get_program_options() -> List[Dict[str, str]]:
    return get_supported_program_options()


def generate_schedule(payload: ScheduleRequest) -> Dict[str, Any]:
    with SessionLocal() as db:
        catalog = CourseRepository(db).get_course_catalog()
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
    with SessionLocal() as db:
        catalog = CourseRepository(db).get_course_catalog()
    output: List[Dict[str, Any]] = []

    for item in payload:
        rows = check_requirements_for_courses(
            catalog=catalog,
            course_codes=item.classes,
            chosen_degree=item.chosen_degree,
        )
        output.append({"type": item.type, "requirements": rows})

    return output
