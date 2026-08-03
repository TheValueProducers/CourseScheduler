from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CheckResult:
    rule: str
    satisfied: bool
    details: str
    informational: bool = False
    unverifiable: bool = False

    @property
    def verdict(self) -> str:
        if self.informational:
            return "Informational"

        if self.unverifiable and not self.satisfied:
            return "Unverifiable"

        return "Satisfied" if self.satisfied else "Not Satisfied"


@dataclass(frozen=True)
class ValidationReport:
    checks: tuple[CheckResult, ...]

    program_allocations: Mapping[
        str,
        Mapping[str, tuple[str, ...]],
    ] = field(default_factory=dict)

    @property
    def asserted_checks(self) -> tuple[CheckResult, ...]:
        """Checks that affect the independent validation result."""
        return tuple(
            check
            for check in self.checks
            if not check.informational
        )

    @property
    def validation_passed(self) -> bool:
        """Whether every asserted validation check passed."""
        return all(
            check.satisfied
            for check in self.asserted_checks
        )

    @property
    def satisfied(self) -> bool:
        """Short alias for validation_passed."""
        return self.validation_passed

    @property
    def failed_checks(self) -> tuple[CheckResult, ...]:
        """Failed checks for which the validator could make a decision."""
        return tuple(
            check
            for check in self.asserted_checks
            if not check.satisfied
            and not check.unverifiable
        )

    @property
    def unverifiable_checks(self) -> tuple[CheckResult, ...]:
        """Checks lacking enough information for a reliable decision."""
        return tuple(
            check
            for check in self.checks
            if check.unverifiable
        )

    @property
    def informational_notes(self) -> tuple[CheckResult, ...]:
        """Diagnostic notes that do not affect validation."""
        return tuple(
            check
            for check in self.checks
            if check.informational
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "validation_passed": self.validation_passed,
            "checks": [
                {
                    "rule": check.rule,
                    "verdict": check.verdict,
                    "satisfied": check.satisfied,
                    "informational": check.informational,
                    "unverifiable": check.unverifiable,
                    "details": check.details,
                }
                for check in self.checks
            ],
            "program_allocations": {
                program: {
                    requirement: list(courses)
                    for requirement, courses in allocation.items()
                }
                for program, allocation
                in self.program_allocations.items()
            },
        }