# from __future__ import annotations

# from typing import Any, Dict, List, Literal, Optional, Set, Tuple

# import services.schedule_service as svc

# from ortools.sat.python import cp_model

# from optimizer.build_schedule import _build_schedule_result
# from optimizer.constraints import (
#     DISTRIBUTION_REQUIREMENTS,
#     _credit_hours_to_units,
#     _add_compact_semester_constraints,
#     _add_course_requirement_constraints,
#     _add_credit_constraints,
#     _add_cross_list_constraints,
#     _add_general_graduation_constraints,
#     _add_preference_constraints,
#     _add_prerequisite_constraints,
#     _add_requirement_overlap_constraints,
#     _add_scheduled_course_constraints,
#     _add_single_take_constraints,
#     _add_term_offering_constraints,
# )
# from optimizer.objective import _set_schedule_objective
# from optimizer.variables import (
#     _build_requirement_usage_variables,
#     _build_sub_requirement_variables,
#     _create_take_variables,
# )



# def print_model_size(model: cp_model.CpModel, stage: str) -> None:
#     proto = model.Proto()

#     print(
#         f"{stage}: "
#         f"{len(proto.variables):,} variables, "
#         f"{len(proto.constraints):,} constraints"
#     )


# def build_model(*args: Any, **kwargs: Any) -> Any:
#     raise NotImplementedError(
#         "Model construction will be moved into this module "
#         "during optimizer refactoring."
#     )


# def _expand_composite_requirements(
#     requirements: List[Dict[str, Any]],
# ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
#     expanded: List[Dict[str, Any]] = []
#     composite_meta: Dict[str, Dict[str, Any]] = {}

#     for req in requirements:
#         req_type = req.get("requirement_type")
#         req_id = str(req.get("id", "")).strip()

#         if req_type != "composite":
#             expanded.append(req)
#             continue

#         sub_requirement_ids: List[str] = []

#         for idx, sub_req in enumerate(req.get("sub_requirements", [])):
#             if not isinstance(sub_req, dict):
#                 continue

#             sub_id_raw = (
#                 str(sub_req.get("id", f"sub_{idx + 1}")).strip()
#                 or f"sub_{idx + 1}"
#             )
#             sub_id = f"{req_id}::{sub_id_raw}"

#             sub_req_copy = dict(sub_req)
#             sub_req_copy["id"] = sub_id
#             sub_req_copy["is_subrequirement"] = True

#             expanded.append(sub_req_copy)
#             sub_requirement_ids.append(sub_id)

#         composite_meta[req_id] = {
#             "sub_requirement_ids": sub_requirement_ids,
#             "min_count": int(
#                 req.get("min_count", len(sub_requirement_ids))
#             ),
#             "constraints": req.get("constraints", {}),
#             "sub_requirements": req.get("sub_requirements", []),
#         }

#     return expanded, composite_meta



# def build_schedule(
#     catalog: Dict[str, Any],
#     current_term: str,
#     year: str,
#     completed_courses: List[str],
#     preferred_courses: List[str],
#     avoid_courses: List[str],
#     scheduled_courses: Optional[Dict[str, int]],
#     chosen_degree: List[str],
#     optimization: Literal["balanced", "graduate early"],
#     deterministic: bool = False,
# ) -> Dict[str, Any]:

#     # ==================================================
#     # Initializing CP-SAT model
#     # ==================================================

#     model = cp_model.CpModel()

#     # ==================================================
#     # Creating necessary variables
#     # ==================================================

#     all_courses: Set[str] = set(catalog.keys())
#     completed: Set[str] = set(completed_courses)

#     # Create fall_spring_to_courses mapping based on course catalog

#     # A course cannot be both completed and scheduled again.
#     scheduled_completed_conflicts = completed.intersection(
#         scheduled_courses or {}
#     )

#     if scheduled_completed_conflicts:
#         return {
#             "status": "infeasible",
#             "schedule": {},
#             "requirements": {},
#             "message": (
#                 "Courses cannot be both completed and scheduled: "
#                 + ", ".join(sorted(scheduled_completed_conflicts))
#             ),
#         }

#     distribution_courses: Dict[str, List[str]] = {
#         dist: sorted(
#             [
#                 code
#                 for code, course in catalog.items()
#                 if getattr(course, "distribution", None) == dist
#             ]
#         )
#         for dist in DISTRIBUTION_REQUIREMENTS.keys()
#     }

#     diversity_courses: List[str] = sorted(
#         [
#             code
#             for code, course in catalog.items()
#             if bool(getattr(course, "analyzing_diversity", False))
#         ]
#     )

#     fwis_courses: List[str] = sorted(
#         [
#             code
#             for code in all_courses
#             if code.startswith("FWIS")
#         ]
#     )

#     lpap_courses: List[str] = sorted(
#         [
#             code
#             for code in all_courses
#             if code.startswith("LPAP")
#         ]
#     )

#     # Get remaining semesters.
#     semester_range, base_semester_number = (
#         svc._remaining_semester_indices(current_term, year)
#     )

#     # Build [fall_courses, spring_courses] from catalog offering terms.
#     fall_courses: List[str] = []
#     spring_courses: List[str] = []
#     for course in sorted(all_courses):
#         offered_terms = {
#             str(term).strip().title()
#             for term in (getattr(catalog[course], "offered_terms", None) or set())
#         }
#         if "Fall" in offered_terms:
#             fall_courses.append(course)
#         if "Spring" in offered_terms:
#             spring_courses.append(course)

#     fall_spring_to_courses: List[List[str]] = [fall_courses, spring_courses]

#     course_to_credits = {
#         course: _credit_hours_to_units(catalog[course].credit_hours)
#         for course in all_courses
#         if catalog[course].credit_hours is not None
#     }

#     degree_requirements = svc._selected_degree_requirements(
#         chosen_degree
#     )

#     expanded_requirements, composite_meta = (
#         _expand_composite_requirements(degree_requirements)
#     )

#     # ==================================================
#     # Creating optimization variables
#     # ==================================================

#     # take[(course, semester)] is 1 if the course is taken
#     # in that semester and 0 otherwise.
#     take = _create_take_variables(
#         model,
#         fall_spring_to_courses,
#         semester_range,
#         base_semester_number,
#     )
#     print(f"Take variables created: {len(take):,}")
#     req_available, use_for_req = (
#         _build_requirement_usage_variables(
#             model=model,
#             expanded_requirements=expanded_requirements,
#             all_courses=all_courses,
#             completed=completed,
#             catalog=catalog,
#             take=take,
#             semester_range=semester_range,
#         )
#     )

#     subgroup_satisfied = _build_sub_requirement_variables(
#         model,
#         composite_meta,
#         req_available,
#         use_for_req,
#     )

#     # ==================================================
#     # Adding constraints
#     # ==================================================

#     _add_cross_list_constraints(
#         model,
#         catalog,
#         all_courses,
#         completed,
#         take,
#         semester_range,
#     )

#     _add_single_take_constraints(
#         model,
#         all_courses,
#         completed,
#         take,
#         semester_range,
#     )

#     _add_scheduled_course_constraints(
#         model,
#         scheduled_courses,
#         completed,
#         take,
#         base_semester_number,
#         semester_range,
#     )

#     _add_requirement_overlap_constraints(
#         model,
#         req_available,
#         use_for_req,
#     )

#     _add_course_requirement_constraints(
#         model=model,
#         expanded_requirements=expanded_requirements,
#         req_available=req_available,
#         use_for_req=use_for_req,
#         composite_meta=composite_meta,
#         subgroup_satisfied=subgroup_satisfied,
#     )

#     _add_general_graduation_constraints(
#         model=model,
#         take=take,
#         semester_range=semester_range,
#         base_semester_number=base_semester_number,
#         all_courses=all_courses,
#         completed=completed,
#         distribution_courses=distribution_courses,
#         diversity_courses=diversity_courses,
#         fwis_courses=fwis_courses,
#         lpap_courses=lpap_courses,
#     )

#     _add_prerequisite_constraints(
#         model,
#         catalog,
#         all_courses,
#         take,
#         completed,
#         semester_range,
#     )

#     _add_term_offering_constraints(
#         model,
#         catalog,
#         all_courses,
#         take,
#         semester_range,
#         base_semester_number,
#     )

#     (
#         total_credits,
#         completed_credits,
#         semester_credit_vars,
#     ) = _add_credit_constraints(
#         model=model,
#         catalog=catalog,
#         all_courses=all_courses,
#         completed=completed,
#         take=take,
#         semester_range=semester_range,
#         course_to_credits=course_to_credits,
#     )

#     _add_preference_constraints(
#         model,
#         preferred_courses,
#         avoid_courses,
#         all_courses,
#         completed_courses,
#         take,
#         semester_range,
#     )

#     semester_used = _add_compact_semester_constraints(
#         model,
#         all_courses,
#         take,
#         semester_range,
#     )

#     required_or_choice = svc._collect_required_or_choice_courses(
#         expanded_requirements
#     )

   

    

#     # ==================================================
#     # Setting optimization objective
#     # ==================================================

#     _set_schedule_objective(
#         model=model,
#         optimization=optimization,
#         semester_range=semester_range,
#         semester_used=semester_used,
#         total_credits=total_credits,
#         required_or_choice=required_or_choice,
#         all_courses=all_courses,
#         take=take,
#         semester_credit_vars=semester_credit_vars,
#     )

#     # ==================================================
#     # Solving the model
#     # ==================================================

#     solver = cp_model.CpSolver()
#     solver.parameters.random_seed = 0
#     solver.parameters.num_search_workers = (
#         1 if deterministic else 8
#     )

#     status = solver.solve(model)

#     if status not in (
#         cp_model.OPTIMAL,
#         cp_model.FEASIBLE,
#     ):
#         return {
#             "status": "infeasible",
#             "schedule": {},
#             "requirements": {},
#             "message": (
#                 "No feasible schedule found with the given constraints."
#             ),
#         }

#     # ==================================================
#     # Building schedule results
#     # ==================================================

#     return _build_schedule_result(
#         solver=solver,
#         take=take,
#         semester_range=semester_range,
#         all_courses=all_courses,
#         base_semester_number=base_semester_number,
#         preferred=preferred_courses,
#         expanded_requirements=expanded_requirements,
#         use_for_req=use_for_req,
#         distribution_courses=distribution_courses,
#         diversity_courses=diversity_courses,
#         fwis_courses=fwis_courses,
#         lpap_courses=lpap_courses,
#         catalog=catalog,
#         completed=completed,
#         degree_requirements=degree_requirements,
#         req_available=req_available,
#         completed_credits=completed_credits,
#     )


from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

import services.schedule_service as svc

from ortools.sat.python import cp_model

from optimizer.build_schedule import _build_schedule_result
from optimizer.constraints import (
    DISTRIBUTION_REQUIREMENTS,
    _credit_hours_to_units,
    _add_compact_semester_constraints,
    _add_course_requirement_constraints,
    _add_credit_constraints,
    _add_cross_list_constraints,
    _add_general_graduation_constraints,
    _add_preference_constraints,
    _add_prerequisite_constraints,
    _add_requirement_overlap_constraints,
    _add_scheduled_course_constraints,
    _add_single_take_constraints,
    _add_term_offering_constraints,
)
from optimizer.objective import _set_schedule_objective
from optimizer.variables import (
    _build_requirement_usage_variables,
    _build_sub_requirement_variables,
    _create_take_variables,
)



def print_model_size(model: cp_model.CpModel, stage: str) -> None:
    proto = model.Proto()

    print(
        f"{stage}: "
        f"{len(proto.variables):,} variables, "
        f"{len(proto.constraints):,} constraints"
    )


def build_model(*args: Any, **kwargs: Any) -> Any:
    raise NotImplementedError(
        "Model construction will be moved into this module "
        "during optimizer refactoring."
    )


def _expand_composite_requirements(
    requirements: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    expanded: List[Dict[str, Any]] = []
    composite_meta: Dict[str, Dict[str, Any]] = {}

    for req in requirements:
        req_type = req.get("requirement_type")
        req_id = str(req.get("id", "")).strip()

        if req_type != "composite":
            expanded.append(req)
            continue

        sub_requirement_ids: List[str] = []

        for idx, sub_req in enumerate(req.get("sub_requirements", [])):
            if not isinstance(sub_req, dict):
                continue

            sub_id_raw = (
                str(sub_req.get("id", f"sub_{idx + 1}")).strip()
                or f"sub_{idx + 1}"
            )
            sub_id = f"{req_id}::{sub_id_raw}"

            sub_req_copy = dict(sub_req)
            sub_req_copy["id"] = sub_id
            sub_req_copy["is_subrequirement"] = True

            expanded.append(sub_req_copy)
            sub_requirement_ids.append(sub_id)

        composite_meta[req_id] = {
            "sub_requirement_ids": sub_requirement_ids,
            "min_count": int(
                req.get("min_count", len(sub_requirement_ids))
            ),
            "constraints": req.get("constraints", {}),
            "sub_requirements": req.get("sub_requirements", []),
        }

    return expanded, composite_meta


def _normalize_catalog_course_code(
    raw_code: Any,
    catalog: Dict[str, Any],
) -> Optional[str]:
    code = str(raw_code).strip()
    if code in catalog:
        return code

    upper_code = code.upper()
    if upper_code in catalog:
        return upper_code

    return None


def _prerequisite_course_codes(
    prerequisite_tree: Any,
    catalog: Dict[str, Any],
) -> Set[str]:
    """Collect every catalog course mentioned anywhere in a prerequisite tree."""
    prerequisite_courses: Set[str] = set()
    stack: List[Any] = [prerequisite_tree]

    while stack:
        node = stack.pop()

        if isinstance(node, dict):
            raw_course = node.get("course")
            raw_courses = (
                raw_course
                if isinstance(raw_course, (list, tuple, set))
                else [raw_course]
            )

            for raw_code in raw_courses:
                if raw_code is None:
                    continue
                code = _normalize_catalog_course_code(raw_code, catalog)
                if code is not None:
                    prerequisite_courses.add(code)

            stack.extend(node.get("conditions", []) or [])

        elif isinstance(node, (list, tuple, set)):
            stack.extend(node)

    return prerequisite_courses


def _collect_prerequisite_closure(
    initial_courses: Set[str],
    catalog: Dict[str, Any],
    completed: Set[str],
) -> Set[str]:
    """Return initial courses plus every recursive course prerequisite."""
    closure = {
        course
        for course in initial_courses
        if course in catalog and course not in completed
    }
    stack = list(closure)

    while stack:
        course = stack.pop()
        prerequisite_tree = getattr(catalog[course], "prereq_tree", None)

        for prerequisite in _prerequisite_course_codes(
            prerequisite_tree,
            catalog,
        ):
            if prerequisite in completed or prerequisite in closure:
                continue

            closure.add(prerequisite)
            stack.append(prerequisite)

    return closure


def _collect_hard_required_courses(
    expanded_requirements: List[Dict[str, Any]],
    catalog: Dict[str, Any],
) -> Set[str]:
    """Collect courses that are individually required, excluding choice options."""
    required_courses: Set[str] = set()

    for requirement in expanded_requirements:
        if requirement.get("requirement_type") != "required_courses":
            continue

        for raw_code in requirement.get("courses", []) or []:
            code = _normalize_catalog_course_code(raw_code, catalog)
            if code is not None:
                required_courses.add(code)

    return required_courses


def _offered_term_count(course: Any) -> int:
    offered_terms = {
        str(term).strip().title()
        for term in (getattr(course, "offered_terms", None) or set())
    }
    return len(offered_terms.intersection({"Fall", "Spring"}))


def _course_subject(course_code: str, course: Any) -> str:
    subject = str(getattr(course, "subject", "") or "").strip().upper()
    return subject or course_code.split()[0]


def _select_category_candidates(
    course_codes: List[str],
    *,
    limit: int,
    catalog: Dict[str, Any],
    completed: Set[str],
    avoid_courses: Set[str],
    diversify_subjects: bool = False,
) -> Set[str]:
    """Select stable, broadly offered candidates for a graduation category."""
    if limit <= 0:
        return set()

    eligible = {
        course_code
        for course_code in course_codes
        if course_code in catalog
        and course_code not in completed
        and _offered_term_count(catalog[course_code]) > 0
    }

    def sort_key(course_code: str) -> Tuple[bool, bool, int, str]:
        course = catalog[course_code]
        return (
            course_code in avoid_courses,
            bool(getattr(course, "prereq_tree", None)),
            -_offered_term_count(course),
            course_code,
        )

    if not diversify_subjects:
        return set(sorted(eligible, key=sort_key)[:limit])

    by_subject: Dict[str, List[str]] = {}
    for course_code in eligible:
        subject = _course_subject(course_code, catalog[course_code])
        by_subject.setdefault(subject, []).append(course_code)

    for subject_courses in by_subject.values():
        subject_courses.sort(key=sort_key)

    selected: List[str] = []
    subjects = sorted(by_subject)
    index = 0

    while len(selected) < limit:
        added_this_round = False

        for subject in subjects:
            subject_courses = by_subject[subject]
            if index >= len(subject_courses):
                continue

            selected.append(subject_courses[index])
            added_this_round = True

            if len(selected) >= limit:
                break

        if not added_this_round:
            break

        index += 1

    return set(selected)


def _has_cross_list_or_corequisite(course: Any) -> bool:
    return any(
        bool(getattr(course, attribute, None))
        for attribute in (
            "cross_list",
            "coreq_tree",
            "corequisites",
            "co_requisites",
        )
    )


def _select_general_elective_fillers(
    *,
    catalog: Dict[str, Any],
    all_courses: Set[str],
    existing_candidates: Set[str],
    completed: Set[str],
    avoid_courses: Set[str],
    course_to_credits: Dict[str, int],
    guaranteed_future_courses: Set[str],
    filler_slack: int = 10,
) -> Set[str]:
    """
    Select only three-credit, prerequisite-free, non-cross-listed fillers.

    Only credits from completed courses and courses that are guaranteed to be
    taken are deducted. Choice candidates are deliberately not counted because
    the solver will not necessarily select them.
    """
    three_credit_units = _credit_hours_to_units(3)
    graduation_credit_units = _credit_hours_to_units(120)

    completed_credit_units = sum(
        course_to_credits.get(course, 0)
        for course in completed
    )
    guaranteed_future_credit_units = sum(
        course_to_credits.get(course, 0)
        for course in guaranteed_future_courses - completed
    )

    remaining_credit_units = max(
        0,
        graduation_credit_units
        - completed_credit_units
        - guaranteed_future_credit_units,
    )
    fillers_needed = (
        math.ceil(remaining_credit_units / three_credit_units)
        + max(0, filler_slack)
    )

    excluded = existing_candidates | completed | avoid_courses
    eligible_fillers = [
        course_code
        for course_code in all_courses
        if course_code not in excluded
        and course_to_credits.get(course_code, 0) == three_credit_units
        and not bool(getattr(catalog[course_code], "prereq_tree", None))
        and not _has_cross_list_or_corequisite(catalog[course_code])
        and _offered_term_count(catalog[course_code]) > 0
    ]

    eligible_fillers.sort(
        key=lambda course_code: (
            -_offered_term_count(catalog[course_code]),
            _course_subject(course_code, catalog[course_code]),
            course_code,
        )
    )

    return set(eligible_fillers[:fillers_needed])


def build_schedule(
    catalog: Dict[str, Any],
    current_term: str,
    year: str,
    completed_courses: List[str],
    preferred_courses: List[str],
    avoid_courses: List[str],
    scheduled_courses: Optional[Dict[str, int]],
    chosen_degree: List[str],
    optimization: Literal["balanced", "graduate early"],
    deterministic: bool = False,
) -> Dict[str, Any]:

    # ==================================================
    # Initializing CP-SAT model
    # ==================================================

    model = cp_model.CpModel()

    # ==================================================
    # Creating necessary variables
    # ==================================================

    all_courses: Set[str] = set(catalog.keys())
    completed: Set[str] = set(completed_courses)

    # Create fall_spring_to_courses mapping based on course catalog

    # A course cannot be both completed and scheduled again.
    scheduled_completed_conflicts = completed.intersection(
        scheduled_courses or {}
    )

    if scheduled_completed_conflicts:
        return {
            "status": "infeasible",
            "schedule": {},
            "requirements": {},
            "message": (
                "Courses cannot be both completed and scheduled: "
                + ", ".join(sorted(scheduled_completed_conflicts))
            ),
        }

    full_distribution_courses: Dict[str, List[str]] = {
        dist: sorted(
            [
                code
                for code, course in catalog.items()
                if getattr(course, "distribution", None) == dist
            ]
        )
        for dist in DISTRIBUTION_REQUIREMENTS.keys()
    }

    full_diversity_courses: List[str] = sorted(
        [
            code
            for code, course in catalog.items()
            if bool(getattr(course, "analyzing_diversity", False))
        ]
    )

    full_fwis_courses: List[str] = sorted(
        [
            code
            for code in all_courses
            if code.startswith("FWIS")
        ]
    )

    full_lpap_courses: List[str] = sorted(
        [
            code
            for code in all_courses
            if code.startswith("LPAP")
        ]
    )

    course_to_credits = {
        course: _credit_hours_to_units(catalog[course].credit_hours)
        for course in all_courses
        if catalog[course].credit_hours is not None
    }

    degree_requirements = svc._selected_degree_requirements(
        chosen_degree
    )

    expanded_requirements, composite_meta = (
        _expand_composite_requirements(degree_requirements)
    )

    # ==================================================
    # Building the reduced candidate-course pool
    # ==================================================

    avoid_set: Set[str] = set()
    for raw_code in avoid_courses:
        code = _normalize_catalog_course_code(raw_code, catalog)
        if code is not None:
            avoid_set.add(code)

    preferred_set: Set[str] = set()
    for raw_code in preferred_courses:
        code = _normalize_catalog_course_code(raw_code, catalog)
        if code is not None:
            preferred_set.add(code)

    scheduled_set: Set[str] = set()
    for raw_code in (scheduled_courses or {}):
        code = _normalize_catalog_course_code(raw_code, catalog)
        if code is not None:
            scheduled_set.add(code)

    # 1. Required and degree-choice candidates.
    required_or_choice = {
        code
        for raw_code in svc._collect_required_or_choice_courses(
            expanded_requirements
        )
        if (
            code := _normalize_catalog_course_code(raw_code, catalog)
        ) is not None
    }
    hard_required_courses = _collect_hard_required_courses(
        expanded_requirements,
        catalog,
    )
    candidate_courses: Set[str] = set(required_or_choice)
    candidate_courses.update(hard_required_courses)

    # 2. Preferred and manually scheduled courses.
    candidate_courses.update(preferred_set)
    candidate_courses.update(scheduled_set)

    # 3. Recursive prerequisite closure for the initial candidates.
    candidate_courses = _collect_prerequisite_closure(
        candidate_courses,
        catalog,
        completed,
    )

    # 4. General graduation candidates. Distribution pools are selected in a
    # subject-diverse order because at most two courses from one subject may
    # count toward a distribution group.
    for dist, dist_courses in full_distribution_courses.items():
        completed_in_distribution = len(
            completed.intersection(dist_courses)
        )
        distribution_courses_needed = max(
            0,
            3 - completed_in_distribution,
        )
        distribution_pool_size = (
            max(8, distribution_courses_needed * 4)
            if distribution_courses_needed
            else 0
        )

        candidate_courses.update(
            _select_category_candidates(
                dist_courses,
                limit=distribution_pool_size,
                catalog=catalog,
                completed=completed,
                avoid_courses=avoid_set,
                diversify_subjects=True,
            )
        )

    if not completed.intersection(full_diversity_courses):
        candidate_courses.update(
            _select_category_candidates(
                full_diversity_courses,
                limit=8,
                catalog=catalog,
                completed=completed,
                avoid_courses=avoid_set,
            )
        )

    if not any(course.startswith("FWIS") for course in completed):
        candidate_courses.update(
            _select_category_candidates(
                full_fwis_courses,
                limit=8,
                catalog=catalog,
                completed=completed,
                avoid_courses=avoid_set,
            )
        )

    if not any(course.startswith("LPAP") for course in completed):
        candidate_courses.update(
            _select_category_candidates(
                full_lpap_courses,
                limit=8,
                catalog=catalog,
                completed=completed,
                avoid_courses=avoid_set,
            )
        )

    # 5. General elective fillers. These alone are restricted to exactly
    # three credits, no prerequisites, and no cross-list/corequisite relation.
    guaranteed_future_courses = hard_required_courses | scheduled_set
    general_fillers = _select_general_elective_fillers(
        catalog=catalog,
        all_courses=all_courses,
        existing_candidates=candidate_courses,
        completed=completed,
        avoid_courses=avoid_set,
        course_to_credits=course_to_credits,
        guaranteed_future_courses=guaranteed_future_courses,
        filler_slack=10,
    )
    candidate_courses.update(general_fillers)

    # 6. A second closure includes prerequisites introduced by distribution,
    # Diversity, FWIS, and LPAP candidates. General fillers add none by design.
    candidate_courses = _collect_prerequisite_closure(
        candidate_courses,
        catalog,
        completed,
    )

    # 7. Completed courses count toward requirements and credits but do not
    # need take variables.
    decision_courses = candidate_courses - completed
    all_courses = decision_courses | completed.intersection(catalog)

    # Restrict general-requirement lookup lists to courses represented by the
    # reduced model plus completed courses.
    distribution_courses: Dict[str, List[str]] = {
        dist: [
            course
            for course in dist_courses
            if course in all_courses
        ]
        for dist, dist_courses in full_distribution_courses.items()
    }
    diversity_courses: List[str] = [
        course
        for course in full_diversity_courses
        if course in all_courses
    ]
    fwis_courses: List[str] = [
        course
        for course in full_fwis_courses
        if course in all_courses
    ]
    lpap_courses: List[str] = [
        course
        for course in full_lpap_courses
        if course in all_courses
    ]

    # Get remaining semesters.
    semester_range, base_semester_number = (
        svc._remaining_semester_indices(current_term, year)
    )

    # Only decision courses receive take variables, and only in terms when the
    # catalog says they are offered.
    fall_courses: List[str] = []
    spring_courses: List[str] = []
    for course in sorted(decision_courses):
        offered_terms = {
            str(term).strip().title()
            for term in (
                getattr(catalog[course], "offered_terms", None) or set()
            )
        }
        if "Fall" in offered_terms:
            fall_courses.append(course)
        if "Spring" in offered_terms:
            spring_courses.append(course)

    fall_spring_to_courses: List[List[str]] = [
        fall_courses,
        spring_courses,
    ]

    print(f"Candidate courses: {len(candidate_courses):,}")
    print(f"General fillers selected: {len(general_fillers):,}")

    # ==================================================
    # Creating optimization variables
    # ==================================================

    # take[(course, semester)] is 1 if the course is taken
    # in that semester and 0 otherwise.
    take = _create_take_variables(
        model,
        fall_spring_to_courses,
        semester_range,
        base_semester_number,
    )
    print(f"Take variables created: {len(take):,}")
    req_available, use_for_req = (
        _build_requirement_usage_variables(
            model=model,
            expanded_requirements=expanded_requirements,
            all_courses=all_courses,
            completed=completed,
            catalog=catalog,
            take=take,
            semester_range=semester_range,
        )
    )

    subgroup_satisfied = _build_sub_requirement_variables(
        model,
        composite_meta,
        req_available,
        use_for_req,
    )

    # ==================================================
    # Adding constraints
    # ==================================================

    _add_cross_list_constraints(
        model,
        catalog,
        all_courses,
        completed,
        take,
        semester_range,
    )

    _add_single_take_constraints(
        model,
        all_courses,
        completed,
        take,
        semester_range,
    )

    _add_scheduled_course_constraints(
        model,
        scheduled_courses,
        completed,
        take,
        base_semester_number,
        semester_range,
    )

    _add_requirement_overlap_constraints(
        model,
        req_available,
        use_for_req,
    )

    _add_course_requirement_constraints(
        model=model,
        expanded_requirements=expanded_requirements,
        req_available=req_available,
        use_for_req=use_for_req,
        composite_meta=composite_meta,
        subgroup_satisfied=subgroup_satisfied,
    )

    _add_general_graduation_constraints(
        model=model,
        take=take,
        semester_range=semester_range,
        base_semester_number=base_semester_number,
        all_courses=all_courses,
        completed=completed,
        distribution_courses=distribution_courses,
        diversity_courses=diversity_courses,
        fwis_courses=fwis_courses,
        lpap_courses=lpap_courses,
    )

    _add_prerequisite_constraints(
        model,
        catalog,
        all_courses,
        take,
        completed,
        semester_range,
    )

    _add_term_offering_constraints(
        model,
        catalog,
        all_courses,
        take,
        semester_range,
        base_semester_number,
    )

    (
        total_credits,
        completed_credits,
        semester_credit_vars,
    ) = _add_credit_constraints(
        model=model,
        catalog=catalog,
        all_courses=all_courses,
        completed=completed,
        take=take,
        semester_range=semester_range,
        course_to_credits=course_to_credits,
    )

    _add_preference_constraints(
        model,
        preferred_courses,
        avoid_courses,
        all_courses,
        completed_courses,
        take,
        semester_range,
    )

    semester_used = _add_compact_semester_constraints(
        model,
        all_courses,
        take,
        semester_range,
    )

    # ==================================================
    # Setting optimization objective
    # ==================================================

    _set_schedule_objective(
        model=model,
        optimization=optimization,
        semester_range=semester_range,
        semester_used=semester_used,
        total_credits=total_credits,
        required_or_choice=required_or_choice,
        all_courses=all_courses,
        take=take,
        semester_credit_vars=semester_credit_vars,
    )

    # ==================================================
    # Solving the model
    # ==================================================

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = 0
    solver.parameters.num_search_workers = (
        1 if deterministic else 8
    )

    status = solver.solve(model)

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):
        return {
            "status": "infeasible",
            "schedule": {},
            "requirements": {},
            "message": (
                "No feasible schedule found with the given constraints."
            ),
        }

    # ==================================================
    # Building schedule results
    # ==================================================

    return _build_schedule_result(
        solver=solver,
        take=take,
        semester_range=semester_range,
        all_courses=all_courses,
        base_semester_number=base_semester_number,
        preferred=preferred_courses,
        expanded_requirements=expanded_requirements,
        use_for_req=use_for_req,
        distribution_courses=distribution_courses,
        diversity_courses=diversity_courses,
        fwis_courses=fwis_courses,
        lpap_courses=lpap_courses,
        catalog=catalog,
        completed=completed,
        degree_requirements=degree_requirements,
        req_available=req_available,
        completed_credits=completed_credits,
    )