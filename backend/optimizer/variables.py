from __future__ import annotations

from typing import Any
from ortools.sat.python import cp_model
from parsers.parse_schedule import (
    normalize_course_code,
)
from optimizer.build_schedule import _course_matches_filter

_normalize_course_code = normalize_course_code

def _create_take_variables(
    model: cp_model.CpModel,
    all_courses: Set[str],
    semester_range: List[int],
) -> Dict[Tuple[str, int], cp_model.IntVar]:
    
    """
    Create a mapping of [(course, sem)] to optimization variable for every course in every semester
    """
    take: Dict[Tuple[str, int], cp_model.IntVar] = {}
    for course in all_courses:
        for sem in semester_range:
            take[(course, sem)] = model.new_bool_var(f"take_{course.replace(' ', '_')}_{sem}")
    return take


def _build_requirement_usage_variables(
    model: cp_model.CpModel,
    expanded_requirements: List[Dict[str, Any]],
    all_courses: Set[str],
    completed: Set[str],
    catalog: Dict[str, CourseRecord],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
) -> Tuple[Dict[str, List[str]], Dict[Tuple[str, str], cp_model.IntVar]]:
    
    """
    Returns a mapping of (course, req_id) to list of available courses for it
    """
    req_available: Dict[str, List[str]] = {}
    use_for_req: Dict[Tuple[str, str], cp_model.IntVar] = {}

    for req in expanded_requirements:
        req_id = req["id"]

        #Creates a list that checks whether courses are available to be taken for a specific requirement
        available: List[str] = []

        # If it's a simple requirement like core or application domains
        if "courses" in req:
            available = [
                _normalize_course_code(c)
                for c in req["courses"]
                if _normalize_course_code(c) in all_courses or _normalize_course_code(c) in completed
            ]
        
        # If it's a filter requirement, like having at least 2 comp courses above 300
        elif "filters" in req:
            filters = req.get("filters", {})
            constraints = req.get("constraints", {})
            for course in all_courses:
                if _course_matches_filter(catalog[course], filters, constraints):
                    available.append(course)

        # If it contains "options" like take "COMP 140" OR ("COMP 130" AND "COMP 160")
        elif "options" in req:
            option_courses: List[str] = []
            for option in req.get("options", []):
                if isinstance(option, list):
                    option_courses.extend(_normalize_course_code(c) for c in option)
            available = sorted({c for c in option_courses if c in all_courses or c in completed})

        req_available[req_id] = available

        #Using from req_available mapping, we create optimization variables for use_for_req
        for course in available:
            var = model.new_bool_var(f"use_{course.replace(' ', '_')}_for_{req_id}")
            use_for_req[(course, req_id)] = var
            if course not in completed:

                # You can not use this course in requirement if not taken in any semester
                model.add(var <= sum(take[(course, s)] for s in semester_range))

    return req_available, use_for_req



def _build_sub_requirement_variables(
    model: cp_model.CpModel,
    composite_meta: Dict[str, Dict[str, Any]],
    req_available: Dict[str, List[str]],
    use_for_req: Dict[Tuple[str, str], cp_model.IntVar],
) -> Dict[Tuple[str, str], cp_model.IntVar]:
    # Maps (parent_req_id, sub_req_id) -> bool var that is 1 iff >= 1 course
    # in that subgroup is used to satisfy the subgroup.
    subgroup_satisfied: Dict[Tuple[str, str], cp_model.IntVar] = {}
    for parent_req_id, meta in composite_meta.items():
        for sub_req_id in meta.get("sub_requirement_ids", []):
            var = model.new_bool_var(f"subgroup_satisfied_{parent_req_id}_{sub_req_id}")
            subgroup_satisfied[(parent_req_id, sub_req_id)] = var

            courses_in_sub = [
                c for c in req_available.get(sub_req_id, [])
                if (c, sub_req_id) in use_for_req
            ]
            if not courses_in_sub:
                model.add(var == 0)
                continue

            course_sum = sum(use_for_req[(c, sub_req_id)] for c in courses_in_sub)
            # var == 1  →  at least one course used in this subgroup
            model.add(course_sum >= 1).only_enforce_if(var)
            # var == 0  →  no course used in this subgroup
            model.add(course_sum == 0).only_enforce_if(var.Not())

    return subgroup_satisfied

    
