from dataclasses import dataclass

from .utils import normalize_course_code


@dataclass(frozen=True)
class CoursePrerequisite:
    course: str


@dataclass(frozen=True)
class AllOf:
    conditions: tuple["PrerequisiteRule", ...]


@dataclass(frozen=True)
class AnyOf:
    conditions: tuple["PrerequisiteRule", ...]


PrerequisiteRule = CoursePrerequisite | AllOf | AnyOf



def course_prerequisite(course: str) -> CoursePrerequisite:
    return CoursePrerequisite(normalize_course_code(course))


def all_of(*conditions: PrerequisiteRule) -> AllOf:
    """
    Build an AND node.

    An empty AND is vacuously true and is almost always a data-modelling
    mistake, so it is rejected rather than silently accepted.
    """
    if not conditions:
        raise ValueError(
            "all_of() requires at least one condition; an empty AND is "
            "vacuously true and silently disables the prerequisite."
        )
    return AllOf(tuple(conditions))


def any_of(*conditions: PrerequisiteRule) -> AnyOf:
    """
    Build an OR node.

    An empty OR is unsatisfiable and would make the course permanently
    unschedulable, so it is rejected.
    """
    if not conditions:
        raise ValueError(
            "any_of() requires at least one condition; an empty OR is "
            "unsatisfiable and makes the course impossible to schedule."
        )
    return AnyOf(tuple(conditions))


def prerequisite_is_satisfied(
    rule: PrerequisiteRule,
    courses_completed_before_term: set[str],
) -> bool:
    """
    Evaluate the prerequisite tree.

    The caller passes only courses completed before the dependent course's
    term, which intentionally prevents same-term prerequisites from counting.
    """
    if isinstance(rule, CoursePrerequisite):
        return normalize_course_code(rule.course) in courses_completed_before_term
    if isinstance(rule, AllOf):
        return all(
            prerequisite_is_satisfied(child, courses_completed_before_term)
            for child in rule.conditions
        )
    if isinstance(rule, AnyOf):
        return any(
            prerequisite_is_satisfied(child, courses_completed_before_term)
            for child in rule.conditions
        )
    raise TypeError(f"Unsupported prerequisite rule: {type(rule)!r}")


def describe_prerequisite(rule: PrerequisiteRule) -> str:
    """Render a prerequisite tree as a readable boolean expression."""
    if isinstance(rule, CoursePrerequisite):
        return normalize_course_code(rule.course)
    if isinstance(rule, AllOf):
        return "(" + " AND ".join(describe_prerequisite(c) for c in rule.conditions) + ")"
    if isinstance(rule, AnyOf):
        return "(" + " OR ".join(describe_prerequisite(c) for c in rule.conditions) + ")"
    raise TypeError(f"Unsupported prerequisite rule: {type(rule)!r}")


def unmet_prerequisite_parts(
    rule: PrerequisiteRule,
    available: set[str],
) -> tuple[list[str], set[str]]:
    """
    Explain *why* a prerequisite tree failed.

    Returns ``(descriptions, kinds)`` where ``kinds`` is a subset of
    ``{"course", "and", "or"}`` naming the node types actually responsible for
    the failure.  Unlike a blanket "does this tree contain an AllOf anywhere"
    test, an AND node is only blamed when one of its own children is unmet, and
    an OR node is only blamed when every alternative is unmet.
    """
    if prerequisite_is_satisfied(rule, available):
        return [], set()

    if isinstance(rule, CoursePrerequisite):
        return [normalize_course_code(rule.course)], {"course"}

    if isinstance(rule, AllOf):
        descriptions: list[str] = []
        kinds: set[str] = {"and"}
        for child in rule.conditions:
            child_descriptions, child_kinds = unmet_prerequisite_parts(child, available)
            descriptions.extend(child_descriptions)
            kinds |= child_kinds
        return descriptions, kinds

    if isinstance(rule, AnyOf):
        # Every alternative failed; blame the OR itself rather than recursing
        # and blaming nested ANDs that were never required individually.
        return [describe_prerequisite(rule)], {"or"}

    raise TypeError(f"Unsupported prerequisite rule: {type(rule)!r}")

