from dataclasses import dataclass
from typing import Literal, Mapping

from .constants import TermName
from .prerequisites import PrerequisiteRule
from .utils import normalize_course_code


@dataclass(frozen=True)
class CourseSpec:
    code: str
    credits: int
    offered_terms: frozenset[TermName]
    prerequisite: PrerequisiteRule | None = None
    subject: str | None = None
    distribution_groups: frozenset[
        Literal["D1", "D2", "D3"]
    ] = frozenset()
    is_diversity: bool = False
    is_fwis: bool = False
    is_lpap: bool = False
    cross_list_group: str | None = None


@dataclass(frozen=True)
class CourseGroup:
    """
    One all-or-nothing option.

    A singleton group represents one ordinary course option.  A multi-course
    group counts only when every listed course has been completed.
    """

    courses: frozenset[str]
    label: str | None = None


def course_group(*courses: str, label: str | None = None) -> CourseGroup:
    if not courses:
        raise ValueError("course_group() requires at least one course.")
    return CourseGroup(
        frozenset(normalize_course_code(course) for course in courses),
        label,
    )


@dataclass(frozen=True)
class ChoiceRequirement:
    """
    Choose between ``minimum`` and ``maximum`` complete course groups.

    ``maximum`` limits how many options may be *applied* to this requirement.
    It does not prohibit a student from taking extra courses.  Use
    ``RestrictedGroup`` when merely completing too many courses is forbidden.
    """

    requirement_id: str
    options: tuple[CourseGroup, ...]
    minimum: int
    maximum: int | None = None
    name: str | None = None


@dataclass(frozen=True)
class SubjectRequirement:
    requirement_id: str
    subject: str
    minimum: int
    eligible_courses: frozenset[str] | None = None
    name: str | None = None


LeafRequirement = ChoiceRequirement | SubjectRequirement


@dataclass(frozen=True)
class SubrequirementMinimum:
    requirement_id: str
    subrequirements: tuple[LeafRequirement, ...]
    minimum_satisfied: int
    name: str | None = None


@dataclass(frozen=True)
class RestrictedGroup:
    restriction_id: str
    courses: frozenset[str]
    maximum_completed: int
    name: str | None = None


@dataclass(frozen=True)
class ProgramSpec:
    program_id: str
    required_courses: frozenset[str] = frozenset()
    choice_requirements: tuple[ChoiceRequirement, ...] = ()
    subject_requirements: tuple[SubjectRequirement, ...] = ()
    subrequirement_minimums: tuple[SubrequirementMinimum, ...] = ()
    restricted_groups: tuple[RestrictedGroup, ...] = ()


@dataclass(frozen=True)
class ReferenceData:
    catalog: Mapping[str, CourseSpec]
    programs: Mapping[str, ProgramSpec]
    maximum_term_credits: int = 18
    graduation_credits: int = 120
    minimum_distribution_courses: int = 3
    maximum_same_subject_per_distribution: int = 2

    def normalized_catalog(self) -> dict[str, CourseSpec]:
        return {
            normalize_course_code(code): spec for code, spec in self.catalog.items()
        }

