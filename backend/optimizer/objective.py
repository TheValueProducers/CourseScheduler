from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple, Literal

from ortools.sat.python import cp_model

from optimizer.constraints import CREDIT_UNIT_SCALE





def _set_schedule_objective(
    model: cp_model.CpModel,
    optimization: Literal["balanced", "graduate early"],
    semester_range: List[int],
    semester_used: Dict[int, cp_model.IntVar],
    total_credits: Any,
    required_or_choice: Set[str],
    all_courses: Set[str],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_credit_vars: Dict[int, cp_model.IntVar],
) -> None:
    if optimization == "graduate early":
        model.minimize(
            1000 * sum(semester_used[s] for s in semester_range)
            + total_credits
            + 10
            * sum(
                s * take[(c, s)]
                for c in required_or_choice
                if c in all_courses
                for s in semester_range
                if (c, s) in take
            )
        )
        return

    min_comfort, max_comfort, max_credits = 0, 16 * CREDIT_UNIT_SCALE, 18 * CREDIT_UNIT_SCALE
    comfort_penalties = []
    for sem in semester_range:
        sem_credits = semester_credit_vars[sem]
        penalty = model.new_int_var(0, max_credits, f"penalty_{sem}")
        model.add(penalty >= min_comfort - sem_credits)
        model.add(penalty >= sem_credits - max_comfort)
        model.add(penalty >= 0)
        comfort_penalties.append(penalty)

    imbalance_penalties: List[cp_model.IntVar] = []
    for i in range(len(semester_range)):
        sem_i = semester_range[i]
        for j in range(i + 1, len(semester_range)):
            sem_j = semester_range[j]
            diff = model.new_int_var(0, max_credits, f"credit_diff_{sem_i}_{sem_j}")
            model.add(diff >= semester_credit_vars[sem_i] - semester_credit_vars[sem_j])
            model.add(diff >= semester_credit_vars[sem_j] - semester_credit_vars[sem_i])
            imbalance_penalties.append(diff)

    model.minimize(
        1000 * sum(imbalance_penalties)
        + 100 * sum(comfort_penalties)
        + 50 * total_credits
        + sum(
            s * take[(c, s)]
            for c in required_or_choice
            if c in all_courses
            for s in semester_range
            if (c, s) in take
        )
    )