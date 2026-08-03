"""
Run every mock request through the solver and the independent validator, then
report median runtime and accuracy.

    python3 test.py
    python3 test.py --repeat 5        # run each case 5x, keep its median
    python3 test.py --tag manual_placement
    python3 test.py --detail          # list failing rules for disagreements

On "accuracy"
-------------
A raw satisfied rate would be misleading: some mock cases are built to be
impossible (avoiding a required course, one term left with four terms of work).
For those, "Not Satisfied" is the correct answer.

So each case carries an explicit feasibility flag:

    is_feasible = False  ->  expected NOT satisfied
    is_feasible = True   ->  expected satisfied

Agreement rate is the fraction matching that expectation, reported next to the
raw satisfied rate. The expectation is a heuristic drawn from the fixtures, not
ground truth - read a disagreement as "inspect this case", not as a proven bug.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
import time
import traceback
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence
from unittest.mock import patch

# Patch sys.path BEFORE importing anything from the backend package.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from schedule_validator import (  # noqa: E402
    ChoiceRequirement,
    CourseSpec,
    IndependentScheduleValidator,
    ProgramSpec,
    ReferenceData,
    RestrictedGroup,
    SubrequirementMinimum,
    all_of,
    any_of,
    course_group,
    course_prerequisite,
    normalize_course_code,
)
from mock_requests import MOCK_CASES  # noqa: E402
from data.degree_requirement import get_supported_program_requirements  # noqa: E402
from db.database import SessionLocal  # noqa: E402
from repositories.course_repository import CourseRepository  # noqa: E402
import services.schedule_service as schedule_service  # noqa: E402
from services.schedule_service import generate_schedule  # noqa: E402

# The solver emits {"class": "COMP 140", "reason": ..., "prereqs": [...]}.
COURSE_CODE_KEYS = ("class", "course_code", "courseCode", "code", "id")


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


def _to_prerequisite_rule(prereq_tree):
    if not isinstance(prereq_tree, dict):
        return None

    if prereq_tree.get("course"):
        return course_prerequisite(str(prereq_tree["course"]))

    node_type = str(prereq_tree.get("type", "")).upper()
    parsed_children = []
    for child in prereq_tree.get("conditions", []):
        parsed = _to_prerequisite_rule(child)
        if parsed is not None:
            parsed_children.append(parsed)

    if not parsed_children:
        return None
    if len(parsed_children) == 1:
        # A one-child AND/OR is the child itself; avoid a pointless wrapper.
        return parsed_children[0]
    if node_type == "AND":
        return all_of(*parsed_children)
    if node_type == "OR":
        return any_of(*parsed_children)
    return None


# "GROUP I" is a prefix of "GROUP II", which is a prefix of "GROUP III", so a
# plain substring test tags every Group III course as D1 and D2 as well.
_DISTRIBUTION_PATTERNS = (
    (re.compile(r"\bGROUP\s+III\b"), "D3"),
    (re.compile(r"\bGROUP\s+II\b"), "D2"),
    (re.compile(r"\bGROUP\s+I\b"), "D1"),
)


def _distribution_groups(distribution_value):
    if not distribution_value:
        return frozenset()
    text = str(distribution_value).upper()
    return frozenset(
        label for pattern, label in _DISTRIBUTION_PATTERNS if pattern.search(text)
    )


def _credit_hours_to_int(credit_hours) -> int:
    """Round half-up; round() is banker's rounding and silently loses credits."""
    if credit_hours is None:
        return 0
    try:
        value = float(credit_hours)
    except (TypeError, ValueError):
        return 0
    return max(0, int(value + 0.5))


def build_catalog() -> dict[str, CourseSpec]:
    with SessionLocal() as db:
        catalog = CourseRepository(db).get_course_catalog()

    independent_catalog: dict[str, CourseSpec] = {}
    for raw_code, record in catalog.items():
        code = normalize_course_code(raw_code)
        cross_list = [normalize_course_code(c) for c in (record.cross_list or [])]
        independent_catalog[code] = CourseSpec(
            code=code,
            credits=_credit_hours_to_int(record.credit_hours),
            offered_terms=frozenset(
                term for term in record.offered_terms if term in {"Fall", "Spring"}
            ),
            prerequisite=_to_prerequisite_rule(record.prereq_tree),
            subject=record.subject,
            distribution_groups=_distribution_groups(record.distribution),
            is_diversity=bool(record.analyzing_diversity),
            is_fwis=code.startswith("FWIS"),
            is_lpap=code.startswith("LPAP"),
            cross_list_group=(
                "|".join(sorted({code, *cross_list})) if cross_list else None
            ),
        )
    return independent_catalog


# ---------------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------------


def _max_count(req: dict) -> int | None:
    raw = req.get("max_count")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    return int(raw)


def _restricted_groups_for(req: dict) -> list[RestrictedGroup]:
    req_id = str(req.get("id", "requirement"))
    groups: list[RestrictedGroup] = []
    constraints = req.get("constraints") or {}
    for index, group in enumerate(constraints.get("max_from_group") or []):
        courses = [normalize_course_code(str(c)) for c in group.get("courses", [])]
        group_max = group.get("max_count")
        if courses and isinstance(group_max, int) and not isinstance(group_max, bool):
            groups.append(
                RestrictedGroup(
                    restriction_id=f"{req_id}_restricted_{index}",
                    courses=frozenset(courses),
                    maximum_completed=group_max,
                    name=req_id,
                )
            )
    return groups


def _as_leaf_requirement(req: dict) -> ChoiceRequirement | None:
    """
    Convert a leaf requirement dict into a ChoiceRequirement.

    required_courses becomes a ChoiceRequirement whose minimum equals the option
    count, which is the same as "all of these" and lets it sit inside a
    composite.
    """
    req_id = str(req.get("id", "requirement"))
    req_type = req.get("requirement_type")
    min_count = int(req.get("min_count", 0) or 0)

    if req_type in {"required_courses", "choose_n"}:
        courses = [normalize_course_code(str(c)) for c in req.get("courses", [])]
        if not courses:
            return None
        all_required = req_type == "required_courses"
        return ChoiceRequirement(
            requirement_id=req_id,
            name=req_id,
            options=tuple(course_group(course) for course in courses),
            minimum=len(courses) if all_required else min_count,
            maximum=len(courses) if all_required else _max_count(req),
        )

    if req_type == "choose_group":
        option_groups = []
        for index, option in enumerate(req.get("options", [])):
            if not isinstance(option, list) or not option:
                continue
            normalized = [normalize_course_code(str(c)) for c in option]
            option_groups.append(
                course_group(*normalized, label=f"{req_id}_group_{index}")
            )
        if not option_groups:
            return None
        return ChoiceRequirement(
            requirement_id=req_id,
            name=req_id,
            options=tuple(option_groups),
            minimum=min_count,
            maximum=_max_count(req),
        )

    return None


def build_programs() -> dict[str, ProgramSpec]:
    requirement_map = get_supported_program_requirements()
    programs: dict[str, ProgramSpec] = {}

    for program_id, requirements in requirement_map.items():
        required_courses: set[str] = set()
        choice_requirements: list[ChoiceRequirement] = []
        subrequirement_minimums: list[SubrequirementMinimum] = []
        restricted_groups: list[RestrictedGroup] = []

        for req in requirements:
            req_type = req.get("requirement_type")
            restricted_groups.extend(_restricted_groups_for(req))

            if req_type == "required_courses":
                required_courses.update(
                    normalize_course_code(str(c)) for c in req.get("courses", [])
                )
                continue

            if req_type in {"choose_n", "choose_group"}:
                leaf = _as_leaf_requirement(req)
                if leaf is not None:
                    choice_requirements.append(leaf)
                continue

            if req_type != "composite":
                continue

            # Composite: honour min_count instead of making every child mandatory.
            req_id = str(req.get("id", "composite"))
            children: list[ChoiceRequirement] = []
            for sub_req in req.get("sub_requirements", []) or []:
                restricted_groups.extend(_restricted_groups_for(sub_req))
                leaf = _as_leaf_requirement(sub_req)
                if leaf is not None:
                    children.append(leaf)
            if not children:
                continue

            raw_min = req.get("min_count")
            min_satisfied = (
                int(raw_min)
                if isinstance(raw_min, (int, float)) and not isinstance(raw_min, bool)
                else len(children)
            )
            min_satisfied = max(0, min(min_satisfied, len(children)))

            if min_satisfied >= len(children):
                # "satisfy all children" - flattening is correct here.
                choice_requirements.extend(children)
            else:
                subrequirement_minimums.append(
                    SubrequirementMinimum(
                        requirement_id=req_id,
                        name=req_id,
                        subrequirements=tuple(children),
                        minimum_satisfied=min_satisfied,
                    )
                )

        programs[program_id] = ProgramSpec(
            program_id=program_id,
            required_courses=frozenset(required_courses),
            choice_requirements=tuple(choice_requirements),
            subrequirement_minimums=tuple(subrequirement_minimums),
            restricted_groups=tuple(restricted_groups),
        )

    return programs


def build_validator() -> IndependentScheduleValidator:
    return IndependentScheduleValidator(
        ReferenceData(
            catalog=build_catalog(),
            programs=build_programs(),
            maximum_term_credits=18,
            graduation_credits=120,
            minimum_distribution_courses=3,
            maximum_same_subject_per_distribution=2,
        ),
        manual_term_index_base=0,
        course_code_keys=COURSE_CODE_KEYS,
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


@dataclass
class CaseResult:
    case_id: str
    tags: tuple[str, ...]
    expected_satisfied: bool
    generate_seconds: list[float] = field(default_factory=list)
    validate_seconds: list[float] = field(default_factory=list)
    satisfied: bool | None = None
    verdict: str = ""
    failed_rules: tuple[str, ...] = ()
    unverifiable_rules: tuple[str, ...] = ()
    matched_expected_infeasible: bool = False
    error: str | None = None

    @property
    def generate_median(self) -> float:
        return statistics.median(self.generate_seconds) if self.generate_seconds else 0.0

    @property
    def validate_median(self) -> float:
        return statistics.median(self.validate_seconds) if self.validate_seconds else 0.0

    @property
    def total_median(self) -> float:
        return self.generate_median + self.validate_median

    @property
    def agrees(self) -> bool:
        if self.error is not None:
            return False
        if self.expected_satisfied:
            return bool(self.satisfied)
        return (not bool(self.satisfied)) or self.matched_expected_infeasible


def run_case(case, validator, repeat: int) -> CaseResult:
    # Keep an untouched fixture snapshot and deep-copy it per run so validation
    # cannot leak mutable state across repeats.
    request_snapshot = case.request.model_dump(mode="python")
    original_degree_selector = (
        schedule_service._selected_degree_requirements
    )

    result = CaseResult(
        case_id=case.case_id,
        tags=tuple(case.tags),
        expected_satisfied=case.is_feasible,
    )

    run_matches: list[bool] = []
    failed_rules: set[str] = set()
    unverifiable_rules: set[str] = set()

    for _ in range(repeat):
        try:
            # Isolate both the request and the mutable requirement dictionaries
            # that the optimizer receives from schedule_service.
            request_for_solver = case.request.model_copy(deep=True)

            with patch.object(
                schedule_service,
                "_selected_degree_requirements",
                side_effect=lambda degrees: deepcopy(
                    original_degree_selector(degrees)
                ),
            ):
                start = time.perf_counter()
                response = generate_schedule(
                    request_for_solver,
                )

            result.generate_seconds.append(time.perf_counter() - start)

            if case.request.model_dump(mode="python") != request_snapshot:
                raise RuntimeError(
                    f"{case.case_id} mutated its shared mock request"
                )

            request_for_validation = deepcopy(request_snapshot)

            if isinstance(response, dict):
                status = str(response.get("status", "")).strip().lower()
                response_has_error = (
                    status == "error"
                    or bool(response.get("error"))
                )
            else:
                status = str(getattr(response, "status", "")).strip().lower()
                response_has_error = (
                    status == "error"
                    or bool(getattr(response, "error", None))
                )

            if case.is_feasible:
                # Expected-feasible cases must return a schedule.
                if status != "feasible":
                    run_matches.append(False)
                    failed_rules.add("solver_did_not_return_feasible")
                    continue

                # Validate every hard requirement in the returned schedule.
                start = time.perf_counter()
                report = validator.validate(
                    request_for_validation,
                    response,
                )
                result.validate_seconds.append(
                    time.perf_counter() - start
                )

                run_matches.append(report.validation_passed)
                failed_rules.update(
                    check.rule for check in report.failed_checks
                )
                unverifiable_rules.update(
                    check.rule for check in report.unverifiable_checks
                )

            else:
                # An explicit solver error also matches an expected-infeasible
                # case: the solver correctly declined to produce a schedule.
                returned_infeasible = status == "infeasible"
                matched_expected_failure = (
                    returned_infeasible
                    or response_has_error
                )
                run_matches.append(matched_expected_failure)

                if not matched_expected_failure:
                    failed_rules.add(
                        "solver_did_not_return_infeasible_or_error"
                    )

        except Exception:
            result.error = (
                traceback.format_exc(limit=3)
                .strip()
                .splitlines()[-1]
            )
            return result

    all_runs_matched = bool(run_matches) and all(run_matches)

    if case.is_feasible:
        result.satisfied = all_runs_matched
    else:
        result.matched_expected_infeasible = all_runs_matched

        # CaseResult.agrees expects False for an expected-infeasible case.
        result.satisfied = not all_runs_matched

    result.verdict = (
        "Test Passed"
        if all_runs_matched
        else "Test Failed"
    )
    result.failed_rules = tuple(sorted(failed_rules))
    result.unverifiable_rules = tuple(
        sorted(unverifiable_rules)
    )

    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _percent(numerator: int, denominator: int) -> str:
    return f"{100.0 * numerator / denominator:5.1f}%" if denominator else "    -"


def _percentile(values: Sequence[float], percentile: float) -> float:
    """Return a linearly interpolated percentile for a non-empty sequence."""
    if not values:
        return 0.0

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile / 100.0
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    return ordered[lower_index] + fraction * (
        ordered[upper_index] - ordered[lower_index]
    )


def _spread(values: Sequence[float]) -> tuple[float, float, float, float, float]:
    """Return median, mean, p95, minimum, and maximum."""
    if not values:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    return (
        statistics.median(values),
        statistics.fmean(values),
        _percentile(values, 95.0),
        min(values),
        max(values),
    )


def print_report(results: list[CaseResult], repeat: int, detail: bool) -> None:
    total = len(results)
    ok = [r for r in results if r.error is None]
    errored = [r for r in results if r.error is not None]
    satisfied = [r for r in ok if r.satisfied]

    print("=" * 70)
    print(f"VALIDATION BENCHMARK   {total} cases x {repeat} run(s)")
    print("=" * 70)

    print("\nRUNTIME (seconds; distribution of per-case medians)")
    print(
        f"  {'phase':<12}{'median':>11}{'mean':>11}"
        f"{'p95':>11}{'min':>11}{'max':>11}"
    )
    for label, values in (
        ("generate", [r.generate_median for r in ok]),
        ("validate", [r.validate_median for r in ok]),
        ("total", [r.total_median for r in ok]),
    ):
        median, mean, p95, low, high = _spread(values)
        print(
            f"  {label:<12}{median:>11.4f}{mean:>11.4f}"
            f"{p95:>11.4f}{low:>11.4f}{high:>11.4f}"
        )
    print(f"\n  wall time across all cases: {sum(r.total_median for r in ok):.2f}s")

    solvable = [r for r in ok if r.expected_satisfied]
    infeasible = [r for r in ok if not r.expected_satisfied]
    solvable_ok = [r for r in solvable if r.satisfied]
    infeasible_ok = [r for r in infeasible if r.agrees]
    agreeing = [r for r in results if r.agrees]

    print("\nACCURACY")
    print(
        f"  satisfied (raw)        {len(satisfied):>4} / {total:<4} "
        f"{_percent(len(satisfied), total)}"
    )
    print(
        f"  expected solvable      {len(solvable):>4}   satisfied "
        f"{len(solvable_ok):>4}  {_percent(len(solvable_ok), len(solvable))}"
    )
    print(
        f"  expected infeasible    {len(infeasible):>4}   matched   "
        f"{len(infeasible_ok):>4}  {_percent(len(infeasible_ok), len(infeasible))}"
    )
    print(
        f"  overall agreement      {len(agreeing):>4} / {total:<4} "
        f"{_percent(len(agreeing), total)}"
    )
    if errored:
        print(f"  errored                {len(errored):>4} / {total:<4} "
              f"{_percent(len(errored), total)}")

    rule_counts: dict[str, int] = {}
    for result in ok:
        for rule in result.failed_rules:
            rule_counts[rule] = rule_counts.get(rule, 0) + 1
    if rule_counts:
        print("\nMOST FREQUENT FAILING CHECKS")
        for rule, count in sorted(rule_counts.items(), key=lambda kv: -kv[1])[:12]:
            print(f"  {count:>4}  {rule}")

    unverifiable_counts: dict[str, int] = {}
    for result in ok:
        for rule in result.unverifiable_rules:
            unverifiable_counts[rule] = unverifiable_counts.get(rule, 0) + 1
    if unverifiable_counts:
        print("\nUNVERIFIABLE (validator lacked the input to decide)")
        for rule, count in sorted(unverifiable_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {count:>4}  {rule}")

    slowest = sorted(ok, key=lambda r: -r.total_median)[:5]
    if slowest:
        print("\nSLOWEST CASES")
        for result in slowest:
            print(
                f"  {result.total_median:>7.3f}s  "
                f"(gen {result.generate_median:.3f} / val {result.validate_median:.3f})  "
                f"{result.case_id}"
            )

    disagreements = [r for r in ok if not r.agrees]
    if disagreements:
        print("\nDISAGREEMENTS WITH EXPECTATION")
        for result in disagreements:
            expectation = (
                "expected satisfied" if result.expected_satisfied else "expected infeasible"
            )
            print(f"  {result.case_id}  ({expectation}, got {result.verdict})")
            if detail:
                for rule in result.failed_rules[:6]:
                    print(f"        {rule}")

    if errored:
        print("\nERRORS")
        for result in errored:
            print(f"  {result.case_id}: {result.error}")

    print()


# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark schedule validation.")
    parser.add_argument(
        "--repeat", type=int, default=1, help="runs per case; the median is kept"
    )
    parser.add_argument("--tag", action="append", help="only cases carrying this tag")
    parser.add_argument(
        "--detail", action="store_true", help="list failing rules for disagreements"
    )
    args = parser.parse_args(argv)

    cases = list(MOCK_CASES)
    if args.tag:
        wanted = set(args.tag)
        cases = [c for c in cases if wanted & set(c.tags)]
    if not cases:
        print("no cases matched the filters", file=sys.stderr)
        return 2

    repeat = max(1, args.repeat)
    validator = build_validator()

    results = []
    for index, case in enumerate(cases, start=1):
        print(f"  [{index:>2}/{len(cases)}] {case.case_id}", end="\r",
              file=sys.stderr, flush=True)
        results.append(run_case(case, validator, repeat))
    print(" " * 78, end="\r", file=sys.stderr)

    print_report(results, repeat, args.detail)
    return 0 if all(r.agrees for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())