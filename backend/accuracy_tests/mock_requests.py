"""
Feasible ScheduleRequest fixtures for schedule-generation accuracy testing.

The suite contains exactly the requested 26 demands:

* 7 different starting semesters
* 4 degree selections
* 8 preference/avoidance requests
* 5 manual-placement requests
* 2 optimization requests

Defaults
--------
Unless a case explicitly overrides them:

* Degree: Bachelor of Science in Computer Science
* Optimization: graduate early
* Starting point: freshman Fall
* Completed, preferred, avoided, and manually scheduled courses: empty

Exports
-------
MOCK_CASES
    tuple[MockCase, ...] containing all 26 feasible cases.
MOCK_REQUESTS
    list[ScheduleRequest] containing the same requests without metadata.
INVALID_REQUEST_FACTORIES
    Empty compatibility export. This file contains only feasible demands.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from schemas.schedule_schema import ScheduleRequest  # noqa: E402


# ---------------------------------------------------------------------------
# Schema values
# ---------------------------------------------------------------------------

OPTIMIZATIONS = {
    "graduate_early": "graduate early",
    "balanced": "balanced",
}

PROGRAM_IDS = {
    "cs_bs": "bs_comp",
    "stats_bs": "statistics_bs",
    "data_science_minor": "data_science_minor",
    "economics_ba": "economics_ba"
}


# ---------------------------------------------------------------------------
# Completed-course histories
#
# Each later starting point contains five completed courses for every elapsed
# semester. The histories follow the known feasible eight-semester plan.
# ---------------------------------------------------------------------------

FRESHMAN_FALL = [
    "COMP 140",
    "MATH 101",
    "HIST 101",
    "PHIL 100",
    "FWIS 102",
]

FRESHMAN_SPRING = [
    "COMP 182",
    "ECON 100",
    "MATH 102",
    "BUSI 305",
    "COMP 301",
    "LPAP 100",
]

SOPHOMORE_FALL = [
    "MATH 212",
    "COMP 215",
    "COMP 222",
    "PSYC 101",
    "STAT 310",
]

SOPHOMORE_SPRING = [
    "ECON 210",
    "MATH 355",
    "COMP 312",
    "COMP 321",
    "PHIL 102",
]

JUNIOR_FALL = [
    "COMP 341",
    "AAAS 324",
    "COMP 318",
    "COMP 382",
    "COMP 414",
]

JUNIOR_SPRING = [
    "HIST 112",
    "HIST 220",
    "AAAS 110",
    "COMP 449",
    "ANTH 251",
]

SENIOR_FALL = [
    "ANTH 383",
    "ASIA 302",
    "COMP 410",
    "ANTH 200",
    "ANTH 201",
]

SENIOR_SPRING = [
    "HIST 201",
    "HIST 260",
    "COMP 421",
    "COMP 440",
    "ANTH 206",
]

THROUGH_FRESHMAN_FALL = [
    *FRESHMAN_FALL,
]

THROUGH_FRESHMAN = [
    *THROUGH_FRESHMAN_FALL,
    *FRESHMAN_SPRING,
]

THROUGH_SOPHOMORE_FALL = [
    *THROUGH_FRESHMAN,
    *SOPHOMORE_FALL,
]

THROUGH_SOPHOMORE = [
    *THROUGH_SOPHOMORE_FALL,
    *SOPHOMORE_SPRING,
]

THROUGH_JUNIOR_FALL = [
    *THROUGH_SOPHOMORE,
    *JUNIOR_FALL,
]

THROUGH_JUNIOR = [
    *THROUGH_JUNIOR_FALL,
    *JUNIOR_SPRING,
]

THROUGH_SENIOR_FALL = [
    *THROUGH_JUNIOR,
    *SENIOR_FALL,
]


# ---------------------------------------------------------------------------
# Case containers and constructors
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MockCase:
    case_id: str
    description: str
    tags: tuple[str, ...]
    is_feasible: bool
    request: ScheduleRequest


@dataclass(frozen=True)
class InvalidCase:
    """Compatibility container retained for existing imports."""

    case_id: str
    description: str
    build: Callable[[], Any]


def _request(
    *,
    current_term: str = "Fall",
    year: str = "Freshman",
    completed_courses: list[str] | None = None,
    preferred_courses: list[str] | None = None,
    avoid_courses: list[str] | None = None,
    scheduled_courses: dict[str, int] | None = None,
    chosen_degree: list[str] | None = None,
    optimization: str = OPTIMIZATIONS["graduate_early"],
) -> ScheduleRequest:
    """Build one request using BSCS and graduate-early defaults."""
    return ScheduleRequest(
        current_term=current_term,
        year=year,
        completed_courses=list(completed_courses or []),
        preferred_courses=list(preferred_courses or []),
        avoid_courses=list(avoid_courses or []),
        scheduled_courses=dict(scheduled_courses or {}),
        chosen_degree=list(
            chosen_degree
            if chosen_degree is not None
            else [PROGRAM_IDS["cs_bs"]]
        ),
        optimization=optimization,
    )


def _case(
    case_id: str,
    description: str,
    tags: tuple[str, ...],
    is_feasible: bool = True,
    **request_kwargs: Any,
) -> MockCase:
    """Construct one mock case with request payload and feasibility label."""
    return MockCase(
        case_id=case_id,
        description=description,
        tags=tags,
        is_feasible=is_feasible,
        request=_request(**request_kwargs),
    )


# ---------------------------------------------------------------------------
# A. Different starting semesters
# ---------------------------------------------------------------------------

_SEMESTER_CASES = [
    _case(
        "freshman_spring",
        "Start scheduling in freshman Spring after completing freshman Fall.",
        ("semester", "freshman", "spring"),
        current_term="Spring",
        year="Freshman",
        completed_courses=THROUGH_FRESHMAN_FALL,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ]
    ),
    _case(
        "sophomore_fall",
        "Start scheduling in sophomore Fall after completing freshman year.",
        ("semester", "sophomore", "fall"),
        current_term="Fall",
        year="Sophomore",
        completed_courses=THROUGH_FRESHMAN,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ]
        
    ),
    _case(
        "sophomore_spring",
        "Start scheduling in sophomore Spring after three completed semesters.",
        ("semester", "sophomore", "spring"),
        current_term="Spring",
        year="Sophomore",
        completed_courses=THROUGH_SOPHOMORE_FALL,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ]
    ),
    _case(
        "junior_fall",
        "Start scheduling in junior Fall after completing sophomore year.",
        ("semester", "junior", "fall"),
        current_term="Fall",
        year="Junior",
        completed_courses=THROUGH_SOPHOMORE,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ]
    ),
    _case(
        "junior_spring",
        "Start scheduling in junior Spring after five completed semesters.",
        ("semester", "junior", "spring"),
        current_term="Spring",
        year="Junior",
        completed_courses=THROUGH_JUNIOR_FALL,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ]
    ),
    _case(
        "senior_fall",
        "Start scheduling in senior Fall after completing junior year.",
        ("semester", "senior", "fall"),
        current_term="Fall",
        year="Senior",
        completed_courses=THROUGH_JUNIOR,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ]
    ),
    _case(
        "senior_spring",
        "Start scheduling in senior Spring after seven completed semesters.",
        ("semester", "senior", "spring"),
        current_term="Spring",
        year="Senior",
        completed_courses=THROUGH_SENIOR_FALL,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ]
    ),
]


# ---------------------------------------------------------------------------
# B. Degree selections, all starting from freshman Fall
# ---------------------------------------------------------------------------

_DEGREE_CASES = [
    _case(
        "degree_cs",
        "Bachelor of Science in Computer Science.",
        ("degree", "cs", "single_program"),
        current_term="Fall",
        year="Freshman",
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
    ),
    _case(
        "degree_cs_data_science_minor",
        "BSCS with a Data Science minor.",
        ("degree", "cs", "minor", "multi_program"),
        current_term="Fall",
        year="Freshman",
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
            PROGRAM_IDS["data_science_minor"],
        ],
    ),
    _case(
        "degree_cs_statistics_bs",
        "Double major: BSCS and BS Statistics.",
        ("degree", "cs", "statistics", "double_major", "multi_program"),
        current_term="Fall",
        year="Freshman",
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
            PROGRAM_IDS["stats_bs"],
        ],
    ),
    _case(
        "degree_cs_statistics_bs_data_science_minor",
        "Double major in CS and Statistics with a Data Science minor.",
        (
            "degree",
            "cs",
            "statistics",
            "double_major",
            "minor",
            "multi_program",
        ),
        current_term="Fall",
        year="Freshman",
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
            PROGRAM_IDS["stats_bs"],
            PROGRAM_IDS["data_science_minor"],
        ],
    ),
]


# ---------------------------------------------------------------------------
# C. Preference and avoidance requests
# ---------------------------------------------------------------------------

_PREFERENCE_CASES = [
    _case(
        "preferred_random_course",
        "Prefer one non-required course without constraining its semester.",
        ("preference", "preferred", "random_course"),
        current_term="Fall",
        year="Freshman",
        preferred_courses=[
            "PHIL 150",
        ],
    ),
    _case(
        "preferred_random_course_with_prereq_chain",
        "Prefer a course whose prerequisite chain must be scheduled first.",
        ("preference", "preferred", "prerequisite_chain"),
        current_term="Fall",
        year="Freshman",
        preferred_courses=[
            "COMP 312",
        ],
    ),
    _case(
        "preferred_optional_upper_with_deep_prereq_chain",
        "Prefer an optional upper-level course with a deep prerequisite chain.",
        (
            "preference",
            "preferred",
            "optional_upper",
            "deep_prerequisite_chain",
        ),
        current_term="Fall",
        year="Freshman",
        preferred_courses=[
            "COMP 440",
        ],
    ),
    _case(
        "preferred_already_completed",
        "Prefer a course already completed; it should not be scheduled again.",
        ("preference", "preferred", "already_completed"),
        current_term="Fall",
        year="Sophomore",
        completed_courses=THROUGH_FRESHMAN,
        preferred_courses=[
            "COMP 140",
        ],
    ),
    _case(
        "preferred_required_course",
        "Prefer a BSCS-required course that the degree already demands.",
        ("preference", "preferred", "required_course"),
        current_term="Fall",
        year="Freshman",
        preferred_courses=[
            "COMP 318",
        ],
    ),
    _case(
        "preferred_optional_upper_level_courses",
        "Prefer multiple optional upper-level COMP courses.",
        ("preference", "preferred", "optional_upper", "multiple_courses"),
        current_term="Fall",
        year="Freshman",
        preferred_courses=[
            "COMP 414",
            "COMP 449",
        ],
    ),
    _case(
        "avoid_optional_upper_level_courses",
        "Avoid optional upper-level courses while leaving valid alternatives.",
        ("preference", "avoid", "optional_upper", "multiple_courses"),
        current_term="Fall",
        year="Freshman",
        avoid_courses=[
            "COMP 414",
            "COMP 447",
        ],
    ),
    _case(
        "avoid_random_course",
        "Avoid one non-required course while leaving the BSCS plan feasible.",
        ("preference", "avoid", "random_course"),
        current_term="Fall",
        year="Freshman",
        avoid_courses=[
            "PHIL 150",
        ],
    ),
]


# ---------------------------------------------------------------------------
# D. Manual-placement requests
#
# Term indices are zero-based for a freshman-Fall start:
# 0 freshman Fall, 1 freshman Spring, ..., 7 senior Spring.
# ---------------------------------------------------------------------------

_MANUAL_CASES = [
    _case(
        "schedule_random_course",
        "Place one non-required course in freshman Fall.",
        ("manual_placement", "random_course"),
        current_term="Fall",
        year="Freshman",
        scheduled_courses={
            "PHIL 100": 0,
        },
    ),
    _case(
        "schedule_required_course",
        "Place the first required CS course in freshman Fall.",
        ("manual_placement", "required_course"),
        current_term="Fall",
        year="Freshman",
        scheduled_courses={
            "COMP 140": 0,
        },
    ),
    _case(
        "schedule_optional_upper_level_courses",
        "Place optional upper-level courses in known feasible terms.",
        ("manual_placement", "optional_upper", "multiple_courses"),
        current_term="Fall",
        year="Freshman",
        scheduled_courses={
            "COMP 341": 4,
            "COMP 414": 4,
        },
    ),
    _case(
        "schedule_random_course_with_prereq_chain",
        "Place a course after enough terms remain for its prerequisite chain.",
        ("manual_placement", "prerequisite_chain"),
        current_term="Fall",
        year="Freshman",
        scheduled_courses={
            "COMP 312": 3,
        },
    ),
    _case(
        "schedule_optional_upper_with_prereq_chain",
        "Place an optional upper-level course after its prerequisite chain.",
        (
            "manual_placement",
            "optional_upper",
            "prerequisite_chain",
        ),
        current_term="Fall",
        year="Freshman",
        scheduled_courses={
            "COMP 449": 5,
        },
    ),
]


# ---------------------------------------------------------------------------
# E. Optimization requests
# ---------------------------------------------------------------------------

_OPTIMIZATION_CASES = [
    _case(
        "graduate_early",
        "Use the graduate-early optimization objective.",
        ("optimization", "graduate_early"),
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "balanced",
        "Use the balanced-load optimization objective.",
        ("optimization", "balanced"),
        optimization=OPTIMIZATIONS["balanced"],
    ),
]


# ---------------------------------------------------------------------------
# Supporting completed-course histories
# ---------------------------------------------------------------------------

REDUCED_SENIOR_SPRING_HISTORY = [
    *FRESHMAN_FALL[:3],
    *FRESHMAN_SPRING[:3],
    *SOPHOMORE_FALL[:3],
    *SOPHOMORE_SPRING[:3],
    *JUNIOR_FALL[:3],
    *JUNIOR_SPRING[:3],
    *SENIOR_FALL[:3],
]

CORE_REPLACEMENTS = {
    "COMP 140": "ASIA 213",
    "COMP 182": "ASIA 205",
    "COMP 215": "ASIA 215",
    "COMP 222": "ASIA 217",
}

JUNIOR_FALL_WITHOUT_CORE_CHAIN = [
    CORE_REPLACEMENTS.get(course, course)
    for course in THROUGH_SOPHOMORE
]

FRESHMAN_HISTORY_WITHOUT_FWIS = [
    course
    for course in THROUGH_FRESHMAN
    if not course.upper().startswith("FWIS")
]



# ---------------------------------------------------------------------------
# Infeasible cases
# ---------------------------------------------------------------------------

_INFEASIBLE_CASES = [
    # -----------------------------------------------------------------------
    # Constrained schedules
    # -----------------------------------------------------------------------

    _case(
        "triple_major_cs_bs_stat_bs_econ_ba",
        "Attempt CS BS, Statistics BS, and Economics BA together.",
        ("infeasible", "constrained", "triple_major"),
        is_feasible=False,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
            PROGRAM_IDS["stats_bs"],
            PROGRAM_IDS["economics_ba"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "remaining_credit_capacity_below_graduation_requirement",
        "Start in senior Spring after taking only three courses per prior term.",
        ("infeasible", "constrained", "credit_capacity"),
        is_feasible=False,
        current_term="Spring",
        year="Senior",
        completed_courses=REDUCED_SENIOR_SPRING_HISTORY,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "required_course_taken_late",
        "Force COMP 182 into junior Spring.",
        ("infeasible", "constrained", "required_course", "late"),
        is_feasible=False,
        scheduled_courses={
            "COMP 182": 5,
        },
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "double_major_added_in_senior_year",
        "Add the Statistics BS to the CS BS at the start of senior year.",
        ("infeasible", "constrained", "double_major", "senior"),
        is_feasible=False,
        current_term="Fall",
        year="Senior",
        completed_courses=THROUGH_JUNIOR,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
            PROGRAM_IDS["stats_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "prerequisite_chain_longer_than_remaining_horizon",
        "Start in junior Fall without the early CS prerequisite chain.",
        ("infeasible", "constrained", "prerequisite_chain", "junior"),
        is_feasible=False,
        current_term="Fall",
        year="Junior",
        completed_courses=JUNIOR_FALL_WITHOUT_CORE_CHAIN,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "fwis_missing_after_freshman_year",
        "Start in sophomore Fall without an FWIS course.",
        ("infeasible", "constrained", "fwis", "sophomore"),
        is_feasible=False,
        current_term="Fall",
        year="Sophomore",
        completed_courses=FRESHMAN_HISTORY_WITHOUT_FWIS,
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),

    # -----------------------------------------------------------------------
    # Impossible preference and avoidance requests
    # -----------------------------------------------------------------------

    _case(
        "avoid_a_required_course",
        "Avoid required course COMP 182.",
        ("infeasible", "preference", "avoid", "required_course"),
        is_feasible=False,
        avoid_courses=[
            "COMP 182",
        ],
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "avoid_all_optional_electives",
        "Avoid all listed optional upper-level electives.",
        ("infeasible", "preference", "avoid", "optional_upper"),
        is_feasible=False,
        avoid_courses=[
            "COMP 402",
            "COMP 410",
            "COMP 413",
            "COMP 416",
            "COMP 460",
            "ARTS 460",
            "COMP 461",
        ],
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "preferred_and_avoid_same_course",
        "Prefer and avoid COMP 140 in the same request.",
        ("infeasible", "preference", "preferred", "avoid", "conflict"),
        is_feasible=False,
        preferred_courses=[
            "COMP 140",
        ],
        avoid_courses=[
            "COMP 140",
        ],
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "taking_cross_listed_classes",
        "Prefer both STAT 315 and its cross-listed equivalent DSCI 301.",
        ("infeasible", "preference", "cross_listed"),
        is_feasible=False,
        preferred_courses=[
            "STAT 315",
            "DSCI 301",
        ],
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "avoid_all_math_requirement_options",
        "Avoid every listed mathematics requirement option.",
        ("infeasible", "preference", "avoid", "math_requirement"),
        is_feasible=False,
        avoid_courses=[
            "MATH 355",
            "MATH 354",
            "MATH 221",
            "CMOR 303",
            "CMOR 302",
        ],
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "avoid_duplicate_classes",
        "List COMP 140 twice as an avoided course.",
        ("infeasible", "preference", "avoid", "duplicate"),
        is_feasible=False,
        avoid_courses=[
            "COMP 140",
            "COMP 140",
        ],
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "preferred_course_with_avoided_prerequisite",
        "Prefer COMP 182 while avoiding its prerequisite COMP 140.",
        ("infeasible", "preference", "preferred", "avoid", "prerequisite"),
        is_feasible=False,
        preferred_courses=[
            "COMP 182",
        ],
        avoid_courses=[
            "COMP 140",
        ],
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),

    # -----------------------------------------------------------------------
    # Infeasible manual-placement requests
    # -----------------------------------------------------------------------

    _case(
        "schedule_required_course_too_early_without_prereq",
        "Place COMP 182 in freshman Fall without completing COMP 140.",
        ("infeasible", "manual_placement", "required_course", "prerequisite"),
        is_feasible=False,
        scheduled_courses={
            "COMP 182": 0,
        },
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "schedule_random_course_too_early_without_prereq",
        "Place ECON 200 in freshman Fall without its prerequisite.",
        ("infeasible", "manual_placement", "random_course", "prerequisite"),
        is_feasible=False,
        scheduled_courses={
            "ECON 200": 0,
        },
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "schedule_prereq_at_same_semester",
        "Place COMP 140 and COMP 182 in the same semester.",
        ("infeasible", "manual_placement", "same_term", "prerequisite"),
        is_feasible=False,
        scheduled_courses={
            "COMP 140": 0,
            "COMP 182": 0,
        },
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "schedule_course_from_past",
        "Start in freshman Spring and schedule COMP 140 in a past semester.",
        ("infeasible", "manual_placement", "past_term"),
        is_feasible=False,
        current_term="Spring",
        year="Freshman",
        completed_courses=THROUGH_FRESHMAN_FALL,
        scheduled_courses={
            "COMP 140": 0,
        },
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "schedule_above_18_credits",
        "Place eight courses in freshman Fall.",
        ("infeasible", "manual_placement", "term_credit_limit"),
        is_feasible=False,
        scheduled_courses={
            "COMP 140": 0,
            "MATH 101": 0,
            "HIST 101": 0,
            "PHIL 100": 0,
            "FWIS 102": 0,
            "MATH 102": 0,
            "MATH 212": 0,
            "MATH 355": 0,
        },
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "satisfy_partial_prerequisite",
        "Place COMP 341 after completing only part of its prerequisite path.",
        ("infeasible", "manual_placement", "partial_prerequisite"),
        is_feasible=False,
        current_term="Fall",
        year="Sophomore",
        completed_courses=THROUGH_FRESHMAN,
        scheduled_courses={
            "COMP 341": 0,
        },
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "schedule_completed_course_again",
        "Schedule completed course COMP 140 again in freshman Spring.",
        ("infeasible", "manual_placement", "completed_course", "duplicate"),
        is_feasible=False,
        current_term="Spring",
        year="Freshman",
        completed_courses=THROUGH_FRESHMAN_FALL,
        scheduled_courses={
            "COMP 140": 0,
        },
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
    _case(
        "schedule_duplicate_classes",
        "Schedule two course-code spellings that normalize to COMP 140.",
        ("infeasible", "manual_placement", "duplicate"),
        is_feasible=False,
        scheduled_courses={
            "COMP 140": 0,
            "COMP140": 0,
        },
        chosen_degree=[
            PROGRAM_IDS["cs_bs"],
        ],
        optimization=OPTIMIZATIONS["graduate_early"],
    ),
]


# ---------------------------------------------------------------------------
# Public collections and invariants
# ---------------------------------------------------------------------------

MOCK_CASES: tuple[MockCase, ...] = tuple(
    [
        *_SEMESTER_CASES,
        *_DEGREE_CASES,
        *_PREFERENCE_CASES,
        *_MANUAL_CASES,
        *_OPTIMIZATION_CASES,
        *_INFEASIBLE_CASES
    ]
)

MOCK_REQUESTS: list[ScheduleRequest] = [
    case.request
    for case in MOCK_CASES
]

# Retained so existing imports do not fail. Deliberately empty because this
# fixture file now contains only feasible demands.
INVALID_REQUEST_FACTORIES: tuple[InvalidCase, ...] = ()

EXPECTED_CASE_COUNT = 26



# ---------------------------------------------------------------------------
# Convenience accessors
# ---------------------------------------------------------------------------


def get_case(case_id: str) -> MockCase:
    for case in MOCK_CASES:
        if case.case_id == case_id:
            return case

    raise KeyError(
        f"No mock case with id {case_id!r}"
    )


def cases_with_tag(tag: str) -> tuple[MockCase, ...]:
    return tuple(
        case
        for case in MOCK_CASES
        if tag in case.tags
    )


def all_tags() -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                tag
                for case in MOCK_CASES
                for tag in case.tags
            }
        )
    )


if __name__ == "__main__":
    print(
        f"{len(MOCK_CASES)} feasible mock cases\n"
    )

    for tag in all_tags():
        matches = cases_with_tag(tag)
        print(
            f"  {tag:<24} {len(matches):>2}"
        )

    print()

    for case in MOCK_CASES:
        print(
            f"  {case.case_id}"
        )