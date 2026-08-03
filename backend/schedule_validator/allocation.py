from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class AllocationSlot:
    slot_id: str
    requirement_id: str
    options: tuple[frozenset[str], ...]


def match_singleton_slots(
    slots: Sequence[AllocationSlot],
) -> dict[str, frozenset[str]] | None:
    """Solve the one-course-per-option case via exact bipartite matching."""
    adjacency: list[list[str]] = [
        [next(iter(option)) for option in slot.options] for slot in slots
    ]
    course_to_slot: dict[str, int] = {}

    def augment(slot_index: int, visited: set[str]) -> bool:
        for course in adjacency[slot_index]:
            if course in visited:
                continue
            visited.add(course)
            holder = course_to_slot.get(course)
            if holder is None or augment(holder, visited):
                course_to_slot[course] = slot_index
                return True
        return False

    order = sorted(range(len(slots)), key=lambda i: len(adjacency[i]))
    for slot_index in order:
        if not augment(slot_index, set()):
            return None

    assignment: dict[str, frozenset[str]] = {}
    for course, slot_index in course_to_slot.items():
        assignment[slots[slot_index].slot_id] = frozenset({course})
    return assignment


def search_general_slots(
    slots: Sequence[AllocationSlot],
    budget: int,
) -> tuple[dict[str, frozenset[str]] | None, bool]:
    """Backtracking search for grouped options; returns (assignment, exhausted)."""
    ordered = sorted(slots, key=lambda slot: len(slot.options))
    states = 0
    exhausted = False
    failed: set[tuple[int, frozenset[str]]] = set()

    def dfs(
        index: int, used: frozenset[str], assignment: dict[str, frozenset[str]]
    ) -> dict[str, frozenset[str]] | None:
        nonlocal states, exhausted
        if exhausted:
            return None
        states += 1
        if states > budget:
            exhausted = True
            return None
        if index == len(ordered):
            return dict(assignment)

        memo_key = (index, used)
        if memo_key in failed:
            return None

        slot = ordered[index]
        for option in slot.options:
            if used & option:
                continue
            assignment[slot.slot_id] = option
            result = dfs(index + 1, used | option, assignment)
            if result is not None:
                return result
            del assignment[slot.slot_id]

        if not exhausted:
            failed.add(memo_key)
        return None

    result = dfs(0, frozenset(), {})
    return result, exhausted


def solve_slots(
    slots: Sequence[AllocationSlot],
    budget: int,
) -> tuple[dict[str, frozenset[str]] | None, bool]:
    """Choose matching or backtracking based on slot shape."""
    if not slots:
        return {}, False
    if any(not slot.options for slot in slots):
        return None, False
    if all(len(option) == 1 for slot in slots for option in slot.options):
        return match_singleton_slots(slots), False
    return search_general_slots(slots, budget)

