"""Generate and print schedules for mock request cases.

Usage examples
--------------
python3 ./accuracy_tests/mock_responses.py
python3 ./accuracy_tests/mock_responses.py --case-id freshman_fall_blank_slate
python3 ./accuracy_tests/mock_responses.py --limit 20
python3 ./accuracy_tests/mock_responses.py --test --case-id freshman_fall_blank_slate
"""

from __future__ import annotations

import json
import sys
import argparse
import importlib.util
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
	sys.path.insert(0, str(BACKEND_ROOT))

from mock_requests import MOCK_CASES  # noqa: E402
from schedule_validator import (  # noqa: E402
	IndependentScheduleValidator,
	ReferenceData,
)
from services.schedule_service import generate_schedule  # noqa: E402


def _load_validator_builders():
	"""Load accuracy_tests/test.py helpers without importing backend/test.py."""
	test_file = Path(__file__).resolve().parent / "test.py"
	module_name = "accuracy_tests_test"
	spec = importlib.util.spec_from_file_location(module_name, test_file)
	if spec is None or spec.loader is None:
		raise RuntimeError(f"Unable to load validator builders from {test_file}")
	module = importlib.util.module_from_spec(spec)
	sys.modules[module_name] = module
	spec.loader.exec_module(module)
	return module.COURSE_CODE_KEYS, module.build_catalog, module.build_programs


def _find_case(case_id: str):
	for case in MOCK_CASES:
		if case.case_id == case_id:
			return case
	return None


def print_schedule_for_case(case_id: str) -> None:
	"""Run schedule generation for one case and print the result."""
	case = _find_case(case_id)
	if case is None:
		available = ", ".join(c.case_id for c in MOCK_CASES)
		raise ValueError(f"Unknown case_id: {case_id}. Available case_ids: {available}")

	response = generate_schedule(case.request)
	print(f"[1/1] {case.case_id}")
	print(json.dumps(response, indent=2, sort_keys=True, default=str))


def print_validation_for_case(case_id: str) -> None:
	"""Run schedule generation and independent validation for one case."""
	case = _find_case(case_id)
	if case is None:
		available = ", ".join(c.case_id for c in MOCK_CASES)
		raise ValueError(f"Unknown case_id: {case_id}. Available case_ids: {available}")

	response = generate_schedule(case.request)
	course_code_keys, build_catalog, build_programs = _load_validator_builders()
	validator = IndependentScheduleValidator(
		ReferenceData(
			catalog=build_catalog(),
			programs=build_programs(),
			maximum_term_credits=18,
			graduation_credits=120,
			minimum_distribution_courses=3,
			maximum_same_subject_per_distribution=2,
		),
		manual_term_index_base=0,
		course_code_keys=course_code_keys,
	)
	request_for_validation = case.request.model_dump()
	request_for_validation["is_feasible"] = case.is_feasible
	report = validator.validate(request_for_validation, response)

	print(f"[1/1] {case.case_id}")
	print(json.dumps(report.as_dict(), indent=2, sort_keys=True, default=str))


def print_all_schedules(limit: int | None = 20) -> None:
	"""Run schedule generation for the first `limit` mock cases and print each result."""
	cases_to_run = MOCK_CASES if limit is None else MOCK_CASES[:limit]
	print(f"Generating schedules for {len(cases_to_run)} cases...\n")

	for index, case in enumerate(cases_to_run, start=1):
		response = generate_schedule(case.request)
		print(f"[{index:02d}/{len(cases_to_run)}] {case.case_id}")
		print(json.dumps(response, indent=2, sort_keys=True, default=str))
		print()


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Generate schedules from mock request cases.")
	parser.add_argument(
		"--case-id",
		dest="case_id",
		help="Run only a single case by case_id.",
	)
	parser.add_argument(
		"--limit",
		type=int,
		default=20,
		help="Number of cases to run when --case-id is not provided. Use -1 for all.",
	)
	parser.add_argument(
		"--test",
		action="store_true",
		help="Run independent validator.validate(case.request, response). Requires --case-id.",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = _parse_args()
	if args.test:
		if not args.case_id:
			raise ValueError("--test requires --case-id")
		print_validation_for_case(args.case_id)
	elif args.case_id:
		print_schedule_for_case(args.case_id)
	else:
		limit = None if args.limit == -1 else args.limit
		if limit is not None and limit < 1:
			raise ValueError("--limit must be a positive integer or -1 for all cases")
		print_all_schedules(limit=limit)
