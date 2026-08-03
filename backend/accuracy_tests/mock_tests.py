"""Run the independent validator on one fixed BSCS schedule."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# If build_validator was moved into validator_factory.py, use:
# from accuracy_tests.validator_factory import build_validator

# If it is still inside the attached test.py, use:

from schedule_validator import (
    IndependentScheduleValidator,
    ReferenceData,
)

# If these functions are still in accuracy_tests/test.py:
from accuracy_tests.test import (
    build_catalog,
    build_programs,
)

# Raw degree definitions, useful for inspecting program IDs:
from data.degree_requirement import (
    get_supported_program_requirements,
)


CS_BS_PROGRAM_ID = "bs_comp"


request = {
    "current_term": "Fall",
    "year": "Freshman",
    "completed_courses": [],
    "scheduled_courses": {},
    "chosen_degree": [CS_BS_PROGRAM_ID],
    "preferred_courses": [],
    "avoid_courses": [],
}


response = {
    "status": "feasible",
    "schedule": {
        "Freshman Fall": [
            "COMP 140",
            "MATH 101",
            "HIST 101",
            "PHIL 100",
            "FWIS 102",
        ],
        "Freshman Spring": [
            "COMP 182",
            "ECON 100",
            "MATH 102",
            "BUSI 305",
            "COMP 301",
            "LPAP 100"
        ],
        "Sophomore Fall": [
            "MATH 212",
            "COMP 215",
            "COMP 222",
            "PSYC 101",
            "STAT 310"
        ],
        "Sophomore Spring": [
            "ECON 210",
            "MATH 355",
            "COMP 312",
            "COMP 321",
            "PHIL 102",
        ],
        "Junior Fall": [
            "COMP 341",
            
            "AAAS 324",
            "COMP 318",
            "COMP 382",
            "COMP 414",
        ],
        "Junior Spring": [
            "HIST 112",
            "HIST 220",
            "AAAS 110",
            "COMP 449",
            "ANTH 251",
        ],
        "Senior Fall": [
            "ANTH 383",
            "ASIA 302",
            "COMP 410",
            "ANTH 200",
            "ANTH 201",
        ],
        "Senior Spring": [
            "HIST 201",
            "HIST 260",
            "COMP 421",
            "COMP 440",
            "ANTH 206",
        ],
    },
}

def create_validator() -> IndependentScheduleValidator:
    catalog = build_catalog()
    programs = build_programs()

    print(f"Loaded {len(catalog):,} courses")
    print(f"Loaded {len(programs):,} degree programs")

    reference_data = ReferenceData(
        catalog=catalog,
        programs=programs,
        maximum_term_credits=18,
        graduation_credits=120,
        minimum_distribution_courses=3,
        maximum_same_subject_per_distribution=2,
    )

    return IndependentScheduleValidator(
        reference_data,
        manual_term_index_base=0,
        course_code_keys=(
            "class",
            "course_code",
            "courseCode",
            "code",
            "id",
        ),
    )


def main() -> int:
    print("Building independent validator...")
    validator = create_validator()

    # The validator normalizes program identifiers to lowercase.
    available_program_ids = sorted(validator.programs)

    if CS_BS_PROGRAM_ID.lower() not in validator.programs:
        print(
            f"\nProgram ID {CS_BS_PROGRAM_ID!r} was not found."
        )
        print("\nAvailable program IDs:")

        for program_id in available_program_ids:
            print(f"  - {program_id}")

        return 2

    print("Running validator...")
    report = validator.validate(request, response)

    print("\n" + "=" * 70)
    print("VALIDATION RESULT")
    print("=" * 70)

    print(f"Independent validation passed: {report.validation_passed}")
    print(f"Total checks:                 {len(report.checks)}")
    print(f"Failed checks:                {len(report.failed_checks)}")
    print(f"Unverifiable checks:          {len(report.unverifiable_checks)}")

    if report.failed_checks:
        print("\nFAILED CHECKS")

        for check in report.failed_checks:
            print(f"\n- {check.rule}")
            print(f"  {check.details}")

    if report.unverifiable_checks:
        print("\nUNVERIFIABLE CHECKS")

        for check in report.unverifiable_checks:
            print(f"\n- {check.rule}")
            print(f"  {check.details}")

    if report.program_allocations:
        print("\nPROGRAM ALLOCATIONS")
        print(
            json.dumps(
                report.program_allocations,
                indent=2,
                sort_keys=True,
                default=list,
            )
        )

    # Uncomment this to print the entire report.
    #
    # print(
    #     json.dumps(
    #         report.as_dict(),
    #         indent=2,
    #         sort_keys=True,
    #         default=str,
    #     )
    # )

  


if __name__ == "__main__":
    raise SystemExit(main())