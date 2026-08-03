from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from .models import CourseSpec, ReferenceData
from .prerequisites import (
    describe_prerequisite,
    prerequisite_is_satisfied,
    unmet_prerequisite_parts,
)
from .reporting import CheckResult
from .terms import TermSlot, fwis_year_condition
from .utils import format_issues, normalize_course_code, read_field


def check_course_uniqueness(
    completed: list[str],
    scheduled: list[str],
) -> list[CheckResult]:
    occurrence_counts = Counter(completed + scheduled)
    repeated_courses = sorted(
        f"{course} appears {count} times"
        for course, count in occurrence_counts.items()
        if count > 1
    )
    completed_set = set(completed)
    scheduled_set = set(scheduled)
    completed_rescheduled = sorted(completed_set & scheduled_set)

    return [
        CheckResult(
            rule="course_taken_at_most_once",
            satisfied=not repeated_courses,
            details=format_issues(
                repeated_courses,
                "No course appears more than once across completed and planned work.",
            ),
        ),
        CheckResult(
            rule="completed_course_not_scheduled_again",
            satisfied=not completed_rescheduled,
            details=format_issues(
                completed_rescheduled,
                "No completed course appears in the generated schedule.",
            ),
        ),
    ]


def check_catalog_coverage(
    courses: set[str],
    catalog: Mapping[str, CourseSpec],
) -> CheckResult:
    unknown_courses = sorted(course for course in courses if course not in catalog)
    return CheckResult(
        rule="independent_catalog_covers_all_courses",
        satisfied=not unknown_courses,
        details=format_issues(
            unknown_courses,
            "Every completed and scheduled course exists in the reference catalog.",
        ),
    )


def check_offerings(
    slots: Sequence[TermSlot],
    scheduled_by_term: Sequence[Sequence[str]],
    catalog: Mapping[str, CourseSpec],
) -> list[CheckResult]:
    offering_failures: list[str] = []
    no_offering_data_failures: list[str] = []
    unconfirmed_term_courses: list[str] = []

    for slot, courses in zip(slots, scheduled_by_term):
        for course in courses:
            spec = catalog.get(course)
            if spec is None:
                continue
            if not spec.offered_terms:
                no_offering_data_failures.append(
                    f"{course} is scheduled in {slot.key} but has no offered terms."
                )
            elif slot.term not in spec.offered_terms:
                offering_failures.append(
                    f"{course} is scheduled in {slot.key} ({slot.term}) but is offered only in {sorted(spec.offered_terms)}."
                )
            elif not slot.term_confirmed:
                unconfirmed_term_courses.append(f"{course} in {slot.key}")

    return [
        CheckResult(
            rule="courses_are_scheduled_only_when_offered",
            satisfied=not offering_failures,
            details=format_issues(
                offering_failures,
                (
                    "Every course is scheduled during an offered term"
                    + (
                        f", but {len(unconfirmed_term_courses)} placements were checked against an inferred semester."
                        if unconfirmed_term_courses
                        else "."
                    )
                ),
            ),
            unverifiable=bool(unconfirmed_term_courses) and not offering_failures,
        ),
        CheckResult(
            rule="courses_without_offered_terms_are_not_scheduled",
            satisfied=not no_offering_data_failures,
            details=format_issues(
                no_offering_data_failures,
                "No course lacking offering data is scheduled.",
            ),
        ),
    ]


def check_prerequisites(
    slots: Sequence[TermSlot],
    scheduled_by_term: Sequence[Sequence[str]],
    completed: set[str],
    catalog: Mapping[str, CourseSpec],
) -> list[CheckResult]:
    prerequisite_failures: list[str] = []
    and_failures: list[str] = []
    or_failures: list[str] = []
    same_term_failures: list[str] = []

    courses_before_term = set(completed)
    for slot, courses in zip(slots, scheduled_by_term):
        same_term_courses = set(courses)
        for course in courses:
            spec = catalog.get(course)
            if spec is None or spec.prerequisite is None:
                continue
            if prerequisite_is_satisfied(spec.prerequisite, courses_before_term):
                continue

            missing, kinds = unmet_prerequisite_parts(spec.prerequisite, courses_before_term)
            satisfied_with_same_term = prerequisite_is_satisfied(
                spec.prerequisite,
                courses_before_term | same_term_courses,
            )
            cause = (
                "the missing work is scheduled in the same term"
                if satisfied_with_same_term
                else "the missing work is never scheduled earlier"
            )
            failure = (
                f"{course} in {slot.key} needs {describe_prerequisite(spec.prerequisite)}; "
                f"unmet: {sorted(set(missing))} ({cause})."
            )
            prerequisite_failures.append(failure)
            if "and" in kinds:
                and_failures.append(failure)
            if "or" in kinds:
                or_failures.append(failure)
            if satisfied_with_same_term:
                same_term_failures.append(
                    f"{course} relies on a prerequisite taken in the same term ({slot.key}): {sorted(set(missing))}."
                )

        courses_before_term.update(same_term_courses)

    return [
        CheckResult(
            rule="prerequisites_completed_before_dependent_courses",
            satisfied=not prerequisite_failures,
            details=format_issues(
                prerequisite_failures,
                "Every prerequisite expression is satisfied before its dependent course.",
            ),
        ),
        CheckResult(
            rule="and_prerequisites_require_all_conditions",
            satisfied=not and_failures,
            details=format_issues(
                and_failures,
                "Every AND prerequisite has all of its conditions satisfied.",
            ),
        ),
        CheckResult(
            rule="or_prerequisites_require_at_least_one_condition",
            satisfied=not or_failures,
            details=format_issues(
                or_failures,
                "Every OR prerequisite has at least one alternative satisfied.",
            ),
        ),
        CheckResult(
            rule="same_term_prerequisites_do_not_count",
            satisfied=not same_term_failures,
            details=format_issues(
                same_term_failures,
                "No course depends on a prerequisite taken in the same term.",
            ),
        ),
    ]


def check_term_credits(
    slots: Sequence[TermSlot],
    scheduled_by_term: Sequence[Sequence[str]],
    catalog: Mapping[str, CourseSpec],
    maximum_term_credits: int,
) -> CheckResult:
    term_credit_failures: list[str] = []
    term_credit_totals: dict[str, int] = {}

    for slot, courses in zip(slots, scheduled_by_term):
        credits = sum(catalog[course].credits for course in courses if course in catalog)
        term_credit_totals[slot.key] = credits
        if credits > maximum_term_credits:
            term_credit_failures.append(
                f"{slot.key}: {credits} credits (maximum {maximum_term_credits})."
            )

    return CheckResult(
        rule=f"maximum_{maximum_term_credits}_credits_per_term",
        satisfied=not term_credit_failures,
        details=format_issues(term_credit_failures, f"Term totals: {term_credit_totals}."),
    )


def check_total_credits(
    courses: set[str],
    catalog: Mapping[str, CourseSpec],
    graduation_credits: int,
) -> CheckResult:
    unknown_courses = sorted(course for course in courses if course not in catalog)
    unique_known_courses = {course for course in courses if course in catalog}
    total_credits = sum(catalog[course].credits for course in unique_known_courses)
    credits_reached = total_credits >= graduation_credits

    return CheckResult(
        rule=f"minimum_{graduation_credits}_total_credits",
        satisfied=credits_reached and not unknown_courses,
        details=(
            f"Verified {total_credits} of the required {graduation_credits} credits"
            + (
                f"; {len(unknown_courses)} course(s) carry no verifiable credit value because they are absent from the reference catalog: {unknown_courses}."
                if unknown_courses
                else "."
            )
        ),
        unverifiable=bool(unknown_courses) and credits_reached,
    )


def check_distributions(
    courses: set[str],
    catalog: Mapping[str, CourseSpec],
    reference: ReferenceData,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for distribution in ("D1", "D2", "D3"):
        subject_counts: Counter[str] = Counter()
        group_courses: list[str] = []

        for course in sorted(courses):
            spec = catalog.get(course)
            if spec is None or distribution not in spec.distribution_groups:
                continue
            subject = (spec.subject or "").upper()
            if not subject:
                subject = "UNKNOWN"
            subject_counts[subject] += 1
            group_courses.append(course)

        cap = reference.maximum_same_subject_per_distribution
        countable = sum(min(count, cap) for count in subject_counts.values())
        uncapped = sum(subject_counts.values())
        minimum = reference.minimum_distribution_courses

        checks.append(
            CheckResult(
                rule=f"minimum_three_distribution_{distribution[-1]}_courses",
                satisfied=countable >= minimum,
                details=(
                    f"{group_courses}; {countable} of {uncapped} count toward the required {minimum} after applying the per-subject cap of {cap}."
                ),
            )
        )

        over_cap = {
            subject: count for subject, count in subject_counts.items() if count > cap
        }
        cap_is_binding = uncapped >= minimum and countable < minimum
        checks.append(
            CheckResult(
                rule=f"maximum_two_same_subject_in_distribution_{distribution[-1]}",
                satisfied=not cap_is_binding,
                details=(
                    f"The per-subject cap of {cap} is the binding constraint: {uncapped} raw course(s) drop to {countable} countable. Over-cap subjects: {over_cap}."
                    if cap_is_binding
                    else f"The per-subject cap of {cap} is applied; over-cap subjects: {over_cap or '{}'}."
                ),
            )
        )

    return checks


def check_special_requirements(
    request: Any,
    slots: Sequence[TermSlot],
    scheduled_by_term: Sequence[Sequence[str]],
    completed_set: set[str],
    catalog: Mapping[str, CourseSpec],
    all_courses: set[str],
) -> list[CheckResult]:
    diversity_courses = sorted(
        course for course in all_courses if course in catalog and catalog[course].is_diversity
    )
    fwis_courses = sorted(course for course in all_courses if course in catalog and catalog[course].is_fwis)
    lpap_courses = sorted(course for course in all_courses if course in catalog and catalog[course].is_lpap)

    fwis_year_satisfied, fwis_year_details = fwis_year_condition(
        request=request,
        slots=slots,
        scheduled_by_term=scheduled_by_term,
        completed_set=completed_set,
        catalog=catalog,
    )

    cross_listed: dict[str, list[str]] = {}
    for course in sorted(all_courses):
        spec = catalog.get(course)
        if spec is not None and spec.cross_list_group:
            cross_listed.setdefault(spec.cross_list_group, []).append(course)
    cross_list_failures = {
        group: courses for group, courses in cross_listed.items() if len(courses) > 1
    }

    return [
        CheckResult(
            rule="minimum_one_diversity_course",
            satisfied=len(diversity_courses) >= 1,
            details=f"Diversity courses: {diversity_courses}.",
        ),
        CheckResult(
            rule="exactly_one_fwis_course",
            satisfied=len(fwis_courses) == 1,
            details=(
                f"Found {len(fwis_courses)} FWIS course(s), expected exactly 1: {fwis_courses}."
            ),
        ),
        CheckResult(
            rule="fwis_taken_during_freshman_year",
            satisfied=fwis_year_satisfied,
            details=fwis_year_details,
        ),
        CheckResult(
            rule="at_leat_one_lpap_course",
            satisfied=len(lpap_courses) >= 1,
            details=(
                f"Found {len(lpap_courses)} LPAP course(s), expected 1 or more: {lpap_courses}."
            ),
        ),
        CheckResult(
            rule="maximum_one_course_per_cross_list_group",
            satisfied=not cross_list_failures,
            details=(
                f"Conflicting cross-list groups: {cross_list_failures}."
                if cross_list_failures
                else "No cross-listed group contributes more than one course."
            ),
        ),
    ]


def check_preferences(
    request: Any,
    completed_set: set[str],
    scheduled_set: set[str],
) -> list[CheckResult]:
    preferred = {
        normalize_course_code(course)
        for course in (read_field(request, "preferred_courses", []) or [])
    }
    missing_preferred = sorted(preferred - scheduled_set - completed_set)

    avoided = {
        normalize_course_code(course)
        for course in (read_field(request, "avoid_courses", []) or [])
    }
    included_avoided = sorted(avoided & scheduled_set)

    return [
        CheckResult(
            rule="preferred_courses_included_in_schedule",
            satisfied=not missing_preferred,
            details=format_issues(
                missing_preferred,
                "Every preferred course appears in the schedule or is already complete.",
            ),
        ),
        CheckResult(
            rule="avoided_courses_excluded_from_schedule",
            satisfied=not included_avoided,
            details=format_issues(
                included_avoided,
                "No avoided course appears in the generated schedule.",
            ),
        ),
    ]


def check_semester_continuity(
    slots: Sequence[TermSlot],
    scheduled_by_term: Sequence[Sequence[str]],
) -> list[CheckResult]:
    used_term_indices = [index for index, courses in enumerate(scheduled_by_term) if courses]
    gap_indices: list[int] = []
    if used_term_indices:
        first_used = min(used_term_indices)
        last_used = max(used_term_indices)
        gap_indices = [
            index
            for index in range(first_used, last_used + 1)
            if not scheduled_by_term[index]
        ]

    gap_keys = [
        slots[index].key if index < len(slots) else str(index)
        for index in gap_indices
    ]

    leading_empty = [
        slots[index].key
        for index in range(min(used_term_indices) if used_term_indices else 0)
    ]

    return [
        CheckResult(
            rule="semesters_used_consecutively_without_internal_gaps",
            satisfied=not gap_indices,
            details=format_issues(
                [f"{key} is empty" for key in gap_keys],
                "No empty semester occurs between the first and last used semesters.",
            ),
        ),
        CheckResult(
            rule="schedule_starts_in_the_first_available_term",
            satisfied=True,
            details=(
                f"{len(leading_empty)} leading empty term(s): {leading_empty}."
                if leading_empty
                else "The schedule begins in the first available term."
            ),
            informational=True,
        ),
    ]
