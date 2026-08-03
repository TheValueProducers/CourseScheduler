from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations, product
from typing import Mapping, Sequence

from .allocation import AllocationSlot, solve_slots
from .models import (
	ChoiceRequirement,
	CourseGroup,
	CourseSpec,
	LeafRequirement,
	ProgramSpec,
	SubjectRequirement,
)
from .utils import infer_subject, normalize_course_code


@dataclass(frozen=True)
class ProgramEvaluation:
	allocation: Mapping[str, tuple[str, ...]] | None
	required_missing: tuple[str, ...]
	choice_minimum_failures: tuple[str, ...]
	choice_maximum_failures: tuple[str, ...]
	grouped_option_failures: tuple[str, ...]
	subject_failures: tuple[str, ...]
	subrequirement_failures: tuple[str, ...]
	restricted_failures: tuple[str, ...]
	rule_definition_failures: tuple[str, ...]
	search_exhausted: bool


def evaluate_program(
	program: ProgramSpec,
	completed: set[str],
	catalog: Mapping[str, CourseSpec],
	*,
	maximum_allocation_states: int,
) -> ProgramEvaluation:
	required_courses = {normalize_course_code(course) for course in program.required_courses}
	required_missing = tuple(sorted(required_courses - completed))

	rule_definition_failures: list[str] = []
	choice_minimum_failures: list[str] = []
	choice_maximum_failures: list[str] = []
	grouped_option_failures: list[str] = []
	subject_failures: list[str] = []
	subrequirement_failures: list[str] = []
	restricted_failures: list[str] = []

	for requirement in program.choice_requirements:
		if requirement.minimum < 0:
			rule_definition_failures.append(
				f"{requirement.requirement_id}: negative minimum {requirement.minimum}"
			)
		if requirement.maximum is not None and requirement.maximum < requirement.minimum:
			rule_definition_failures.append(
				f"{requirement.requirement_id}: maximum {requirement.maximum} < minimum {requirement.minimum}"
			)

		complete_options = [
			option for option in requirement.options if normalized_group(option) <= completed
		]
		if len(complete_options) < requirement.minimum:
			choice_minimum_failures.append(
				f"{requirement.requirement_id}: {len(complete_options)} of {len(requirement.options)} option(s) complete, needs {requirement.minimum}"
			)
			if any(len(option.courses) > 1 for option in requirement.options):
				partial = [
					sorted(normalized_group(option) - completed)
					for option in requirement.options
					if not normalized_group(option) <= completed
					and normalized_group(option) & completed
				]
				if partial:
					grouped_option_failures.append(
						f"{requirement.requirement_id}: partially completed group(s), still missing {partial}"
					)

	for requirement in program.subject_requirements:
		eligible = eligible_subject_courses(requirement, completed, catalog)
		if len(eligible) < requirement.minimum:
			subject_failures.append(
				f"{requirement.requirement_id}: {len(eligible)} eligible {requirement.subject} course(s), needs {requirement.minimum}"
			)

	for requirement in program.subrequirement_minimums:
		satisfiable = [
			child
			for child in requirement.subrequirements
			if leaf_is_satisfiable(child, completed, catalog)
		]
		if len(satisfiable) < requirement.minimum_satisfied:
			subrequirement_failures.append(
				f"{requirement.requirement_id}: {len(satisfiable)} of {len(requirement.subrequirements)} subrequirement(s) satisfiable, needs {requirement.minimum_satisfied}"
			)

	for restriction in program.restricted_groups:
		restricted = {normalize_course_code(course) for course in restriction.courses}
		selected = sorted(restricted & completed)
		if len(selected) > restriction.maximum_completed:
			restricted_failures.append(
				f"{restriction.restriction_id}: {selected} (maximum {restriction.maximum_completed})"
			)

	allocation, search_exhausted = allocate_program(
		program=program,
		completed=completed,
		catalog=catalog,
		maximum_allocation_states=maximum_allocation_states,
	)

	if allocation is not None:
		for requirement in program.choice_requirements:
			if requirement.maximum is None:
				continue
			applied = allocation.get(requirement.requirement_id, ())
			option_count = count_applied_options(requirement, applied)
			if option_count > requirement.maximum:
				choice_maximum_failures.append(
					f"{requirement.requirement_id}: {option_count} option(s) applied, maximum {requirement.maximum}"
				)

	return ProgramEvaluation(
		allocation=allocation,
		required_missing=required_missing,
		choice_minimum_failures=tuple(choice_minimum_failures),
		choice_maximum_failures=tuple(choice_maximum_failures),
		grouped_option_failures=tuple(grouped_option_failures),
		subject_failures=tuple(subject_failures),
		subrequirement_failures=tuple(subrequirement_failures),
		restricted_failures=tuple(restricted_failures),
		rule_definition_failures=tuple(rule_definition_failures),
		search_exhausted=search_exhausted,
	)


def allocate_program(
	program: ProgramSpec,
	completed: set[str],
	catalog: Mapping[str, CourseSpec],
	*,
	maximum_allocation_states: int,
) -> tuple[Mapping[str, tuple[str, ...]] | None, bool]:
	"""Find a disjoint course-to-requirement allocation for one degree program."""
	_ = catalog
	base_slots: list[AllocationSlot] = []

	for course in sorted(normalize_course_code(c) for c in program.required_courses):
		if course not in completed:
			return None, False
		base_slots.append(
			AllocationSlot(
				slot_id=f"required:{course}",
				requirement_id=f"required:{course}",
				options=(frozenset({course}),),
			)
		)

	for requirement in program.choice_requirements:
		base_slots.extend(leaf_slots(requirement, completed, catalog))
	for requirement in program.subject_requirements:
		base_slots.extend(leaf_slots(requirement, completed, catalog))

	child_choices: list[list[list[AllocationSlot]]] = []
	for requirement in program.subrequirement_minimums:
		satisfiable = [
			child
			for child in requirement.subrequirements
			if leaf_is_satisfiable(child, completed, catalog)
		]
		if len(satisfiable) < requirement.minimum_satisfied:
			return None, False

		subsets: list[list[AllocationSlot]] = []
		for chosen in combinations(satisfiable, requirement.minimum_satisfied):
			slots: list[AllocationSlot] = []
			for child in chosen:
				slots.extend(
					leaf_slots(
						child,
						completed,
						catalog,
						prefix=f"{requirement.requirement_id}/",
					)
				)
			subsets.append(slots)
		child_choices.append(subsets)

	exhausted = False
	combos = product(*child_choices) if child_choices else [()]
	for combo in combos:
		slots = list(base_slots)
		for extra in combo:
			slots.extend(extra)

		assignment, combo_exhausted = solve_slots(slots, maximum_allocation_states)
		exhausted = exhausted or combo_exhausted
		if assignment is None:
			continue

		allocation: dict[str, list[str]] = defaultdict(list)
		slot_by_id = {slot.slot_id: slot for slot in slots}
		for slot_id, courses in assignment.items():
			requirement_id = slot_by_id[slot_id].requirement_id
			allocation[requirement_id].extend(sorted(courses))

		return (
			{
				requirement_id: tuple(sorted(courses))
				for requirement_id, courses in allocation.items()
			},
			exhausted,
		)

	return None, exhausted


def eligible_subject_courses(
	requirement: SubjectRequirement,
	completed: set[str],
	catalog: Mapping[str, CourseSpec],
) -> list[str]:
	return [
		course
		for course in sorted(completed)
		if course_matches_subject_requirement(course, requirement, catalog)
	]


def course_matches_subject_requirement(
	course: str,
	requirement: SubjectRequirement,
	catalog: Mapping[str, CourseSpec],
) -> bool:
	if requirement.eligible_courses is not None:
		eligible = {normalize_course_code(item) for item in requirement.eligible_courses}
		if course not in eligible:
			return False

	spec = catalog.get(course)
	subject = (spec.subject if spec is not None else None) or infer_subject(course)
	return subject.upper() == requirement.subject.upper()


def leaf_is_satisfiable(
	requirement: LeafRequirement,
	completed: set[str],
	catalog: Mapping[str, CourseSpec],
) -> bool:
	if isinstance(requirement, ChoiceRequirement):
		complete_options = sum(
			1
			for option in requirement.options
			if normalized_group(option) <= completed
		)
		return requirement.minimum >= 0 and complete_options >= requirement.minimum

	return len(eligible_subject_courses(requirement, completed, catalog)) >= requirement.minimum


def leaf_slots(
	requirement: LeafRequirement,
	completed: set[str],
	catalog: Mapping[str, CourseSpec],
	*,
	prefix: str = "",
) -> list[AllocationSlot]:
	"""Expand one leaf requirement into minimum interchangeable allocation slots."""
	requirement_id = requirement.requirement_id
	if isinstance(requirement, ChoiceRequirement):
		options = tuple(
			normalized_group(option)
			for option in requirement.options
			if normalized_group(option) <= completed
		)
		count = max(0, requirement.minimum)
	else:
		options = tuple(
			frozenset({course})
			for course in eligible_subject_courses(requirement, completed, catalog)
		)
		count = max(0, requirement.minimum)

	return [
		AllocationSlot(
			slot_id=f"{prefix}{requirement_id}#{index}",
			requirement_id=requirement_id,
			options=options,
		)
		for index in range(count)
	]


def count_applied_options(
	requirement: ChoiceRequirement,
	applied: Sequence[str],
) -> int:
	remaining = set(applied)
	count = 0
	for option in requirement.options:
		courses = normalized_group(option)
		if courses and courses <= remaining:
			remaining -= courses
			count += 1
	return count + len(remaining)


def normalized_group(group: CourseGroup) -> frozenset[str]:
	return frozenset(normalize_course_code(course) for course in group.courses)

