from __future__ import annotations

from typing import Any, Mapping, Sequence

from .constants import DEFAULT_COURSE_CODE_KEYS
from .models import CourseSpec, ProgramSpec, ReferenceData
from .program_validation import ProgramEvaluation, evaluate_program
from .reporting import CheckResult, ValidationReport
from .schedule_checks import (
    check_catalog_coverage,
    check_course_uniqueness,
    check_distributions,
    check_offerings,
    check_preferences,
    check_prerequisites,
    check_semester_continuity,
    check_special_requirements,
    check_term_credits,
    check_total_credits,
)
from .terms import build_term_slots, manual_schedule_failures
from .utils import normalize_course_code, read_field, unique_in_order


class IndependentScheduleValidator:
    def __init__(
        self,
        reference_data: ReferenceData,
        *,
        manual_term_index_base: int = 0,
        maximum_allocation_states: int = 250_000,
        course_code_keys: Sequence[str] = DEFAULT_COURSE_CODE_KEYS,
        unverifiable_is_failure: bool = True,
    ) -> None:
        self.reference = reference_data

        self.catalog: dict[str, CourseSpec] = (
            reference_data.normalized_catalog()
        )

        self.programs: dict[str, ProgramSpec] = {
            program_id.lower(): program
            for program_id, program in reference_data.programs.items()
        }

        self.manual_term_index_base = manual_term_index_base
        self.maximum_allocation_states = maximum_allocation_states
        self.course_code_keys = tuple(course_code_keys)
        self.unverifiable_is_failure = unverifiable_is_failure

    def is_satisfied(
        self,
        request: Any,
        response: Any,
    ) -> bool:
        """Return only the raw independent validation result."""
        return self.validate(
            request,
            response,
        ).validation_passed

    def validate(
        self,
        request: Any,
        response: Any,
    ) -> ValidationReport:
        """Independently validate the schedule contained in the response."""
        checks: list[CheckResult] = []

        # ---------------------------------------------------------------
        # Response schedule shape
        # ---------------------------------------------------------------

        raw_schedule = read_field(
            response,
            "schedule",
            None,
        )

        schedule_is_mapping = isinstance(
            raw_schedule,
            Mapping,
        )

        schedule_mapping: Mapping[Any, Any] = (
            raw_schedule
            if schedule_is_mapping
            else {}
        )

        checks.append(
            CheckResult(
                rule="response_schedule_is_a_term_mapping",
                satisfied=schedule_is_mapping,
                details=(
                    "response.schedule is a mapping of term keys "
                    "to course lists."
                    if schedule_is_mapping
                    else (
                        f"response.schedule is "
                        f"{type(raw_schedule).__name__}, not a mapping; "
                        "schedule-dependent checks are vacuous."
                    )
                ),
            )
        )

        # ---------------------------------------------------------------
        # Term sequence
        # ---------------------------------------------------------------

        term_keys = [
            str(key)
            for key in schedule_mapping.keys()
        ]

        slots, term_metadata_errors = build_term_slots(
            request,
            term_keys,
        )

        checks.append(
            CheckResult(
                rule="term_sequence_is_consistent",
                satisfied=not term_metadata_errors,
                details=(
                    "; ".join(term_metadata_errors)
                    if term_metadata_errors
                    else (
                        "Schedule keys match the request's "
                        "chronological term sequence."
                    )
                ),
            )
        )

        # ---------------------------------------------------------------
        # Extract scheduled courses
        # ---------------------------------------------------------------

        scheduled_by_term: list[list[str]] = []
        extraction_errors: list[str] = []

        for key in schedule_mapping.keys():
            raw_courses = schedule_mapping[key] or []

            if (
                not isinstance(raw_courses, Sequence)
                or isinstance(raw_courses, (str, bytes))
            ):
                extraction_errors.append(
                    f"{key!r} does not contain a course sequence."
                )
                raw_courses = []

            term_courses: list[str] = []

            for raw_course in raw_courses:
                code = self._extract_course_code(raw_course)

                if code is None:
                    extraction_errors.append(
                        "Could not extract a course code from "
                        f"{raw_course!r} "
                        f"(looked for keys "
                        f"{list(self.course_code_keys)})."
                    )
                else:
                    term_courses.append(
                        normalize_course_code(code)
                    )

            scheduled_by_term.append(term_courses)

        checks.append(
            CheckResult(
                rule="schedule_course_items_are_readable",
                satisfied=not extraction_errors,
                details=(
                    "; ".join(extraction_errors)
                    if extraction_errors
                    else (
                        "Every scheduled item contains a "
                        "readable course code."
                    )
                ),
            )
        )

        # ---------------------------------------------------------------
        # Completed and scheduled courses
        # ---------------------------------------------------------------

        completed_list = [
            normalize_course_code(course)
            for course in (
                read_field(
                    request,
                    "completed_courses",
                    [],
                )
                or []
            )
        ]

        completed_set = set(completed_list)

        scheduled_flat = [
            course
            for term_courses in scheduled_by_term
            for course in term_courses
        ]

        scheduled_set = set(scheduled_flat)
        all_courses = completed_set | scheduled_set

        checks.extend(
            check_course_uniqueness(
                completed_list,
                scheduled_flat,
            )
        )

        checks.append(
            check_catalog_coverage(
                all_courses,
                self.catalog,
            )
        )

        # ---------------------------------------------------------------
        # Manually scheduled courses
        # ---------------------------------------------------------------

        manual_failures = manual_schedule_failures(
            request,
            scheduled_by_term,
            manual_term_index_base=self.manual_term_index_base,
        )

        checks.append(
            CheckResult(
                rule=(
                    "manually_scheduled_courses_"
                    "match_selected_terms"
                ),
                satisfied=not manual_failures,
                details=(
                    "; ".join(manual_failures)
                    if manual_failures
                    else (
                        "Every manually scheduled course "
                        "appears in its selected term."
                    )
                ),
            )
        )

        # ---------------------------------------------------------------
        # Course offerings
        # ---------------------------------------------------------------

        checks.extend(
            check_offerings(
                slots,
                scheduled_by_term,
                self.catalog,
            )
        )

        # ---------------------------------------------------------------
        # Prerequisites
        # ---------------------------------------------------------------

        checks.extend(
            check_prerequisites(
                slots,
                scheduled_by_term,
                completed_set,
                self.catalog,
            )
        )

        # ---------------------------------------------------------------
        # Credits
        # ---------------------------------------------------------------

        checks.append(
            check_term_credits(
                slots,
                scheduled_by_term,
                self.catalog,
                self.reference.maximum_term_credits,
            )
        )

        checks.append(
            check_total_credits(
                all_courses,
                self.catalog,
                self.reference.graduation_credits,
            )
        )

        # ---------------------------------------------------------------
        # Distribution requirements
        # ---------------------------------------------------------------

        checks.extend(
            check_distributions(
                all_courses,
                self.catalog,
                self.reference,
            )
        )

        # ---------------------------------------------------------------
        # Diversity, FWIS, LPAP and cross-list requirements
        # ---------------------------------------------------------------

        checks.extend(
            check_special_requirements(
                request,
                slots,
                scheduled_by_term,
                completed_set,
                self.catalog,
                all_courses,
            )
        )

        # ---------------------------------------------------------------
        # Preferences
        # ---------------------------------------------------------------

        checks.extend(
            check_preferences(
                request,
                completed_set,
                scheduled_set,
            )
        )

        # ---------------------------------------------------------------
        # Semester continuity
        # ---------------------------------------------------------------

        checks.extend(
            check_semester_continuity(
                slots,
                scheduled_by_term,
            )
        )

        # ---------------------------------------------------------------
        # Selected degree programs
        # ---------------------------------------------------------------

        selected_program_ids = unique_in_order(
            str(program_id).lower()
            for program_id in (
                read_field(
                    request,
                    "chosen_degree",
                    [],
                )
                or []
            )
        )

        unknown_programs = sorted(
            program_id
            for program_id in selected_program_ids
            if program_id not in self.programs
        )

        checks.append(
            CheckResult(
                rule="selected_programs_exist_in_reference_rules",
                satisfied=not unknown_programs,
                details=(
                    "; ".join(unknown_programs)
                    if unknown_programs
                    else (
                        "Every selected program has an "
                        "independent rule definition."
                    )
                ),
            )
        )

        # ---------------------------------------------------------------
        # Program evaluation and course allocation
        # ---------------------------------------------------------------

        program_allocations: dict[
            str,
            Mapping[str, tuple[str, ...]],
        ] = {}

        evaluations: dict[
            str,
            ProgramEvaluation,
        ] = {}

        for program_id in selected_program_ids:
            program = self.programs.get(program_id)

            if program is None:
                continue

            evaluation = evaluate_program(
                program,
                all_courses,
                self.catalog,
                maximum_allocation_states=(
                    self.maximum_allocation_states
                ),
            )

            evaluations[program_id] = evaluation

            if evaluation.allocation is not None:
                program_allocations[program_id] = (
                    evaluation.allocation
                )

        checks.extend(
            _program_evaluation_checks(evaluations)
        )

        # ---------------------------------------------------------------
        # Final independent report
        # ---------------------------------------------------------------

        return ValidationReport(
            checks=tuple(
                self._resolve_unverifiable(checks)
            ),
            program_allocations=program_allocations,
        )

    def _extract_course_code(
        self,
        value: Any,
    ) -> str | None:
        if isinstance(value, str):
            return value if value.strip() else None

        for key in self.course_code_keys:
            candidate = read_field(
                value,
                key,
                None,
            )

            if (
                isinstance(candidate, str)
                and candidate.strip()
            ):
                return candidate

        return None

    def _resolve_unverifiable(
        self,
        checks: Sequence[CheckResult],
    ) -> list[CheckResult]:
        if self.unverifiable_is_failure:
            return list(checks)

        resolved: list[CheckResult] = []

        for check in checks:
            if (
                check.unverifiable
                and not check.satisfied
            ):
                resolved.append(
                    CheckResult(
                        rule=check.rule,
                        satisfied=True,
                        details=check.details,
                        informational=check.informational,
                        unverifiable=True,
                    )
                )
            else:
                resolved.append(check)

        return resolved


def _program_evaluation_checks(
    evaluations: Mapping[str, ProgramEvaluation],
) -> list[CheckResult]:
    def collect(attribute: str) -> list[str]:
        failures: list[str] = []

        for program, evaluation in evaluations.items():
            for value in getattr(
                evaluation,
                attribute,
            ):
                failures.append(
                    f"{program}: {value}"
                )

        return failures

    checks: list[CheckResult] = []

    # ---------------------------------------------------------------
    # Reference rule definitions
    # ---------------------------------------------------------------

    definitions = collect(
        "rule_definition_failures"
    )

    checks.append(
        CheckResult(
            rule=(
                "reference_rules_are_"
                "internally_consistent"
            ),
            satisfied=not definitions,
            details=(
                "; ".join(definitions)
                if definitions
                else (
                    "Every reference requirement "
                    "definition is self-consistent."
                )
            ),
        )
    )

    # ---------------------------------------------------------------
    # Required program courses
    # ---------------------------------------------------------------

    missing_required = collect(
        "required_missing"
    )

    checks.append(
        CheckResult(
            rule=(
                "all_required_program_"
                "courses_completed"
            ),
            satisfied=not missing_required,
            details=(
                "; ".join(missing_required)
                if missing_required
                else (
                    "Every required course in every "
                    "selected program is completed."
                )
            ),
        )
    )

    # ---------------------------------------------------------------
    # Choice minimums
    # ---------------------------------------------------------------

    choice_minimum = collect(
        "choice_minimum_failures"
    )

    checks.append(
        CheckResult(
            rule=(
                "choose_n_requirements_"
                "meet_minimum"
            ),
            satisfied=not choice_minimum,
            details=(
                "; ".join(choice_minimum)
                if choice_minimum
                else (
                    "Every choose-N requirement has "
                    "enough complete options."
                )
            ),
        )
    )

    # ---------------------------------------------------------------
    # Choice maximums
    # ---------------------------------------------------------------

    choice_maximum = collect(
        "choice_maximum_failures"
    )

    checks.append(
        CheckResult(
            rule=(
                "choose_n_allocations_"
                "respect_maximum"
            ),
            satisfied=not choice_maximum,
            details=(
                "; ".join(choice_maximum)
                if choice_maximum
                else (
                    "Every choose-N allocation applies "
                    "no more options than its maximum."
                )
            ),
        )
    )

    # ---------------------------------------------------------------
    # Grouped options
    # ---------------------------------------------------------------

    grouped = collect(
        "grouped_option_failures"
    )

    checks.append(
        CheckResult(
            rule=(
                "grouped_options_count_only_when_"
                "every_course_is_completed"
            ),
            satisfied=not grouped,
            details=(
                "; ".join(grouped)
                if grouped
                else (
                    "Only all-complete course groups "
                    "were counted."
                )
            ),
        )
    )


    # ---------------------------------------------------------------
    # Subject requirements
    # ---------------------------------------------------------------

    subject = collect(
        "subject_failures"
    )

    checks.append(
        CheckResult(
            rule=(
                "minimum_courses_from_"
                "required_subjects"
            ),
            satisfied=not subject,
            details=(
                "; ".join(subject)
                if subject
                else (
                    "Every subject-specific course "
                    "minimum is met."
                )
            ),
        )
    )

    # ---------------------------------------------------------------
    # Composite subrequirements
    # ---------------------------------------------------------------

    subrequirements = collect(
        "subrequirement_failures"
    )

    checks.append(
        CheckResult(
            rule=(
                "minimum_number_of_"
                "subrequirements_satisfied"
            ),
            satisfied=not subrequirements,
            details=(
                "; ".join(subrequirements)
                if subrequirements
                else (
                    "Every subrequirement-count "
                    "minimum is met."
                )
            ),
        )
    )

    # ---------------------------------------------------------------
    # Disjoint course allocation
    # ---------------------------------------------------------------

    no_allocation = sorted(
        program
        for program, evaluation in evaluations.items()
        if evaluation.allocation is None
    )

    exhausted = sorted(
        program
        for program, evaluation in evaluations.items()
        if evaluation.search_exhausted
    )

    if not no_allocation and not exhausted:
        allocation_details = (
            "A disjoint course-to-requirement "
            "allocation exists for every selected degree."
        )
    else:
        allocation_parts: list[str] = []

        if no_allocation:
            allocation_parts.append(
                "no disjoint allocation exists for "
                f"{no_allocation}"
            )

        if exhausted:
            allocation_parts.append(
                "search budget exhausted for "
                f"{exhausted}"
            )

        allocation_details = "; ".join(
            allocation_parts
        )

    checks.append(
        CheckResult(
            rule=(
                "course_used_at_most_once_"
                "within_each_degree"
            ),
            satisfied=(
                not no_allocation
                and not exhausted
            ),
            details=allocation_details,
            unverifiable=(
                bool(exhausted)
                and not no_allocation
            ),
        )
    )

    return checks