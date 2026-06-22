from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from ortools.sat.python import cp_model

from optimizer.build_schedule import _build_schedule_result
from optimizer.constraints import (
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
from optimizer.variables import _create_take_variables, _build_requirement_usage_variables, _build_sub_requirement_variables


def build_model(*args: Any, **kwargs: Any) -> Any:
    raise NotImplementedError("Model construction will be moved into this module during optimizer refactoring.")

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
            sub_id_raw = str(sub_req.get("id", f"sub_{idx + 1}")).strip() or f"sub_{idx + 1}"
            sub_id = f"{req_id}::{sub_id_raw}"
            sub_req_copy = dict(sub_req)
            sub_req_copy["id"] = sub_id
            expanded.append(sub_req_copy)
            sub_requirement_ids.append(sub_id)

        composite_meta[req_id] = {
            "sub_requirement_ids": sub_requirement_ids,
            "min_count": int(req.get("min_count", len(sub_requirement_ids))),
            "constraints": req.get("constraints", {}),
            "sub_requirements": req.get("sub_requirements", []),
        }

    return expanded, composite_meta

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
) -> Dict[str, Any]:
    
    # ==================================================

    # Getting Every 

    # ==================================================


    from services import schedule_service as svc

    completed = {svc._normalize_course_code(course) for course in completed_courses}
    preferred = {svc._normalize_course_code(course) for course in preferred_courses}
    avoid = {svc._normalize_course_code(course) for course in avoid_courses}
    scheduled = {
        svc._normalize_course_code(course): int(sem)
        for course, sem in (scheduled_courses or {}).items()
        if isinstance(course, str) and course.strip()
    }

    chosen_degree_normalized = [str(degree).strip().lower() for degree in chosen_degree if str(degree).strip()]
    degree_requirements = svc._selected_degree_requirements(chosen_degree_normalized)
    if not degree_requirements:
        raise ValueError(svc._supported_program_message())
    expanded_requirements, composite_meta = _expand_composite_requirements(degree_requirements)

    semester_range, base_semester_number = svc._remaining_semester_indices(current_term, year)
    model = cp_model.CpModel()

    distribution_courses, diversity_courses, fwis_courses, lpap_courses = svc._collect_special_course_buckets(catalog)

    # Returns a set of string of all possible candidate courses
    all_courses = svc._build_candidate_course_pool(
        expanded_requirements=expanded_requirements,
        distribution_courses=distribution_courses,
        diversity_courses=diversity_courses,
        fwis_courses=fwis_courses,
        lpap_courses=lpap_courses,
        preferred=preferred,
        avoid=avoid,
        scheduled=scheduled,
        catalog=catalog,
    )
    

    svc._validate_scheduled_course_indices(scheduled, catalog)

    course_to_credits = {
        course: catalog[course].credit_hours for course in all_courses if catalog[course].credit_hours is not None
    }

    take = _create_take_variables(model, all_courses, semester_range)

    



    req_available, use_for_req = _build_requirement_usage_variables(
        model=model,
        expanded_requirements=expanded_requirements,
        all_courses=all_courses,
        completed=completed,
        catalog=catalog,
        take=take,
        semester_range=semester_range,
    )

    subgroup_satisfied = _build_sub_requirement_variables(model, composite_meta, req_available, use_for_req)


    _add_cross_list_constraints(model, catalog, all_courses, completed, take, semester_range)
    _add_single_take_constraints(model, all_courses, completed, take, semester_range)
    _add_scheduled_course_constraints(model, scheduled, completed, take, base_semester_number, semester_range)

    _add_requirement_overlap_constraints(model, req_available, use_for_req)

    _add_course_requirement_constraints(
        model=model,
        expanded_requirements=expanded_requirements,
        req_available=req_available,
        use_for_req=use_for_req,
        composite_meta=composite_meta,
        subgroup_satisfied=subgroup_satisfied
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

    _add_prerequisite_constraints(model, catalog, all_courses, take, completed, semester_range)
    _add_term_offering_constraints(model, catalog, all_courses, take, semester_range, base_semester_number)

    total_credits, completed_credits, semester_credit_vars = _add_credit_constraints(
        model=model,
        catalog=catalog,
        all_courses=all_courses,
        completed=completed,
        take=take,
        semester_range=semester_range,
        course_to_credits=course_to_credits,
    )

    _add_preference_constraints(model, preferred, avoid, all_courses, completed, take, semester_range)
    semester_used = _add_compact_semester_constraints(model, all_courses, take, semester_range)
    required_or_choice = svc._collect_required_or_choice_courses(expanded_requirements)
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

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "status": "infeasible",
            "schedule": {},
            "requirements": {},
            "message": "No feasible schedule found with the given constraints.",
        }

    return _build_schedule_result(
        solver=solver,
        take=take,
        semester_range=semester_range,
        all_courses=all_courses,
        base_semester_number=base_semester_number,
        preferred=preferred,
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
