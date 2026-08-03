import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .constants import AcademicYear, TermName, YEAR_NAMES
from .models import CourseSpec
from .utils import normalize_course_code, read_field


@dataclass(frozen=True)
class TermSlot:
    index: int
    key: str
    term: TermName
    academic_year: AcademicYear | None
    term_confirmed: bool
    year_confirmed: bool


def parse_term(value: Any) -> TermName | None:
    text = str(value).lower()
    if re.search(r"\bfall\b", text):
        return "Fall"
    if re.search(r"\bspring\b", text):
        return "Spring"
    return None


def parse_academic_year(value: Any) -> AcademicYear | None:
    text = str(value).lower()
    for year in YEAR_NAMES:
        if re.search(rf"\b{year.lower()}\b", text):
            return year
    return None


def build_term_slots(
    request: Any,
    term_keys: Sequence[str],
) -> tuple[list[TermSlot], list[str]]:
    current_term = str(read_field(request, "current_term", "Fall")).title()
    if current_term not in {"Fall", "Spring"}:
        current_term = "Fall"
    start_year_name = str(read_field(request, "year", "Freshman")).title()
    try:
        start_year_index = YEAR_NAMES.index(start_year_name)  # type: ignore[arg-type]
    except ValueError:
        start_year_index = 0

    errors: list[str] = []
    slots: list[TermSlot] = []
    for index, key in enumerate(term_keys):
        if current_term == "Fall":
            expected_term: TermName = "Fall" if index % 2 == 0 else "Spring"
            year_offset = index // 2
        else:
            expected_term = "Spring" if index % 2 == 0 else "Fall"
            year_offset = (index + 1) // 2

        parsed_term = parse_term(key)
        if parsed_term is not None and parsed_term != expected_term:
            errors.append(
                f"{key!r} implies {parsed_term}, expected {expected_term} "
                f"at chronological index {index}."
            )

        year_index = start_year_index + year_offset
        academic_year: AcademicYear | None = (
            YEAR_NAMES[year_index] if year_index < len(YEAR_NAMES) else None
        )
        parsed_year = parse_academic_year(key)
        if (
            parsed_year is not None
            and academic_year is not None
            and parsed_year != academic_year
        ):
            errors.append(f"{key!r} implies {parsed_year}, expected {academic_year}.")
        slots.append(
            TermSlot(
                index=index,
                key=key,
                term=parsed_term or expected_term,
                academic_year=parsed_year or academic_year,
                term_confirmed=parsed_term is not None,
                year_confirmed=parsed_year is not None,
            )
        )
    return slots, errors

def manual_schedule_failures(
    request: Any,
    scheduled_by_term: Sequence[Sequence[str]],
    *,
    manual_term_index_base: int = 0,
) -> list[str]:
    raw_manual = read_field(request, "scheduled_courses", {}) or {}
    if not isinstance(raw_manual, Mapping):
        return ["request.scheduled_courses is not a mapping."]

    failures: list[str] = []
    for raw_course, raw_index in raw_manual.items():
        course = normalize_course_code(str(raw_course))
        if isinstance(raw_index, bool):
            failures.append(f"{course} has non-integer selected term {raw_index!r}.")
            continue
        try:
            index = int(raw_index) - manual_term_index_base
        except (TypeError, ValueError):
            failures.append(f"{course} has non-integer selected term {raw_index!r}.")
            continue
        if index < 0 or index >= len(scheduled_by_term):
            failures.append(
                f"{course} selects term index {raw_index}, outside the "
                f"{len(scheduled_by_term)} returned terms."
            )
        elif course not in scheduled_by_term[index]:
            actual = [
                term_index + manual_term_index_base
                for term_index, courses in enumerate(scheduled_by_term)
                if course in courses
            ]
            failures.append(
                f"{course} selected term {raw_index}, actual returned terms {actual}."
            )
    return failures


def fwis_year_condition(
    *,
    request: Any,
    slots: Sequence[TermSlot],
    scheduled_by_term: Sequence[Sequence[str]],
    completed_set: set[str],
    catalog: Mapping[str, CourseSpec],
) -> tuple[bool, str]:
    """
    Evaluate the freshman-year FWIS condition as a strict two-branch rule.

    1. A completed FWIS satisfies the condition regardless of when it was
        taken.
    2. Otherwise, the request must start in freshman year and an FWIS must
        be scheduled in freshman Fall or freshman Spring.
    """
    completed_fwis = sorted(
        course
        for course in completed_set
        if course in catalog and catalog[course].is_fwis
    )
    if completed_fwis:
        return (
            True,
            "A completed FWIS automatically satisfies the freshman-year "
            f"timing condition: {completed_fwis}.",
        )

    scheduled_fwis: list[tuple[str, TermSlot]] = []
    for slot, courses in zip(slots, scheduled_by_term):
        for course in courses:
            spec = catalog.get(course)
            if spec is not None and spec.is_fwis:
                scheduled_fwis.append((course, slot))

    starts_in_freshman_year = (
        str(read_field(request, "year", "")).strip().title() == "Freshman"
    )
    freshman_fwis = [
        (course, slot)
        for course, slot in scheduled_fwis
        if slot.academic_year == "Freshman"
        and slot.term in {"Fall", "Spring"}
    ]
    if starts_in_freshman_year and freshman_fwis:
        placements = [
            f"{course} in {slot.key}" for course, slot in freshman_fwis
        ]
        return (
            True,
            "No FWIS was previously completed, but the schedule starts in "
            f"freshman year and includes an FWIS there: {placements}.",
        )

    if not starts_in_freshman_year:
        return (
            False,
            "No FWIS is in completed_courses, and the request does not start "
            "in freshman year.",
        )

    placements = [
        f"{course} in {slot.key}" for course, slot in scheduled_fwis
    ]
    return (
        False,
        "No FWIS is in completed_courses, and the freshman-year schedule "
        "does not contain an FWIS in Fall or Spring"
        + (f"; scheduled FWIS placements: {placements}." if placements else "."),
    )


