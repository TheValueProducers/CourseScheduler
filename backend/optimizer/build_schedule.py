from __future__ import annotations

from typing import Any

from parsers.parse_schedule import (
    normalize_course_code,
)

from optimizer.constraints import YEAR_ORDER, TERM_ORDER, TOTAL_SEMESTERS, DISTRIBUTION_REQUIREMENTS


_normalize_course_code = normalize_course_code

def _course_matches_filter(course: CourseRecord, filters: Dict[str, Any], constraints: Dict[str, Any]) -> bool:

    """
    Returns True if the course matches the filters and constraints. False if otherwise
    
    """
    if "subject" in filters and course.subject != str(filters["subject"]).upper():
        return False

    if "min_level" in filters and course.course_number < int(filters["min_level"]):
        return False

    excluded_courses = {_normalize_course_code(c) for c in constraints.get("excluded_courses", [])}
    if course.code in excluded_courses:
        return False

    if 500 <= course.course_number < 600 and constraints.get("allow_500_level", True) is False:
        return False

    if course.course_number >= 600:
        allowed_600 = {_normalize_course_code(c) for c in constraints.get("allowed_600_level_courses", [])}
        if course.code not in allowed_600:
            return False

    return True



def _evaluate_requirement_from_taken(
    req: Dict[str, Any],
    taken: Set[str],
    catalog: Dict[str, CourseRecord],
) -> Tuple[bool, List[int]]:
    req_type = req.get("requirement_type")

    if req_type == "required_courses":
        courses = [_normalize_course_code(c) for c in req.get("courses", [])]
        total = len(courses)
        count = len([c for c in courses if c in taken])
        return count >= total, [count, total]

    if req_type == "choose_group":
        satisfied_groups = 0
        for raw_group in req.get("options", []):
            if not isinstance(raw_group, list):
                continue
            group_courses = [_normalize_course_code(c) for c in raw_group]
            if group_courses and all(course in taken for course in group_courses):
                satisfied_groups += 1

        target = int(req.get("min_count", 1))
        return satisfied_groups >= target, [min(satisfied_groups, target), target]

    satisfying_courses: List[str] = []
    if "courses" in req:
        satisfying_courses = sorted(
            _normalize_course_code(c)
            for c in req.get("courses", [])
            if _normalize_course_code(c) in catalog
        )
    elif "filters" in req:
        filters = req.get("filters", {})
        constraints = req.get("constraints", {})
        satisfying_courses = sorted(
            code
            for code, rec in catalog.items()
            if _course_matches_filter(rec, filters, constraints)
        )
    elif "options" in req:
        option_courses: List[str] = []
        for option in req.get("options", []):
            if isinstance(option, list):
                option_courses.extend(_normalize_course_code(c) for c in option)
        satisfying_courses = sorted({c for c in option_courses if c in catalog})

    target = int(req.get("min_count", 0))
    count = len([c for c in satisfying_courses if c in taken])
    return count >= target, [min(count, target), target]



def _semester_label(base_semester_number: int, local_semester_index: int) -> str:

    """
    Returns a resulting semester when the semester represented by base_semester_number is looked ahead by local_semester_index

    For example, _semester_label(1, 2), where 1 is "Freshman Spring". Looking ahead 2 semesters would return "Sophomore Spring"

    Input: 
    - base_semester_number: An integer that represents current term and year
    - local_semester_index: An integer that represents the number of semesters that is being looked ahead
    Output: 
    - A string that represents a formal representation of year and current term e.g. Freshman Fall
    
    """
    absolute = base_semester_number + local_semester_index
    year = YEAR_ORDER[min(absolute // 2, len(YEAR_ORDER) - 1)]
    term = TERM_ORDER[absolute % 2]
    return f"{year} {term}"

def _build_schedule_result(
    solver: cp_model.CpSolver,
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
    all_courses: Set[str],
    base_semester_number: int,
    preferred: Set[str],
    expanded_requirements: List[Dict[str, Any]],
    use_for_req: Dict[Tuple[str, str], cp_model.IntVar],
    distribution_courses: Dict[str, List[str]],
    diversity_courses: List[str],
    fwis_courses: List[str],
    lpap_courses: List[str],
    catalog: Dict[str, CourseRecord],
    completed: Set[str],
    degree_requirements: List[Dict[str, Any]],
    req_available: Dict[str, List[str]],
    completed_credits: int,
) -> Dict[str, Any]:
    def course_reason(course: str, sem: int) -> str:
        reasons: List[str] = []

        if course in preferred:
            reasons.append("student prefers this course")

        for req in expanded_requirements:
            req_id = req["id"]
            if (course, req_id) in use_for_req and solver.value(use_for_req[(course, req_id)]) == 1:
                reasons.append(f"satisfies {req_id}")

        for dist, courses in distribution_courses.items():
            if course in courses:
                reasons.append(f"can satisfy {dist}")

        if course in diversity_courses:
            reasons.append("can satisfy analyzing_diversity")

        if course in fwis_courses:
            reasons.append("satisfies FWIS requirement")

        if catalog[course].prereq_tree is not None:
            reasons.append("prerequisites are satisfied by this semester")

        absolute_sem = base_semester_number + sem
        reasons.append(f"offered in {TERM_ORDER[absolute_sem % 2]}")

        if not reasons:
            reasons.append("supports graduation credit and requirement progress")

        return "; ".join(reasons)

    schedule: Dict[str, List[List[str]]] = {}
    planned_courses: Set[str] = set()

    for sem in semester_range:
        sem_courses = [course for course in sorted(all_courses) if solver.value(take[(course, sem)]) == 1]
        if not sem_courses:
            continue

        label = _semester_label(base_semester_number, sem)
        schedule[label] = []
        for course in sem_courses:
            planned_courses.add(course)
            schedule[label].append([course, course_reason(course, sem)])

    completed_and_planned = completed | planned_courses

    requirement_progress: Dict[str, Dict[str, Any]] = {}

    for req in degree_requirements:
        req_id = req["id"]
        if req.get("requirement_type") == "composite":
            sub_requirements = [sub for sub in req.get("sub_requirements", []) if isinstance(sub, dict)]
            sub_satisfied_count = 0
            for sub_req in sub_requirements:
                sub_satisfied, _ = _evaluate_requirement_from_taken(sub_req, completed_and_planned, catalog)
                if sub_satisfied:
                    sub_satisfied_count += 1

            min_subject_ok = True
            for rule in req.get("constraints", {}).get("min_from_subject", []):
                subject = str(rule.get("subject", "")).upper()
                min_count = int(rule.get("min_count", 0))
                if not subject or min_count <= 0:
                    continue
                eligible_subject_courses: Set[str] = set()
                for sub_req in sub_requirements:
                    if "courses" in sub_req:
                        eligible_subject_courses.update(_normalize_course_code(c) for c in sub_req.get("courses", []))
                    elif "options" in sub_req:
                        for option in sub_req.get("options", []):
                            if isinstance(option, list):
                                eligible_subject_courses.update(_normalize_course_code(c) for c in option)
                    elif "filters" in sub_req:
                        filters = sub_req.get("filters", {})
                        constraints = sub_req.get("constraints", {})
                        eligible_subject_courses.update(
                            code for code, rec in catalog.items() if _course_matches_filter(rec, filters, constraints)
                        )

                subject_count = sum(
                    1 for c in completed_and_planned if c in eligible_subject_courses and c.split(" ")[0] == subject
                )
                if subject_count < min_count:
                    min_subject_ok = False
                    break

            total_needed = int(req.get("min_count", len(sub_requirements)))
            requirement_progress[req_id] = {
                "satisfied": sub_satisfied_count >= total_needed and min_subject_ok,
                "progress": [min(sub_satisfied_count, total_needed), total_needed],
            }
            continue

        available = req_available[req_id]

        if req["requirement_type"] == "required_courses":
            total_needed = len(req.get("courses", []))
            taken_count = len([c for c in req.get("courses", []) if _normalize_course_code(c) in completed_and_planned])
            satisfied = taken_count >= total_needed
            requirement_progress[req_id] = {
                "satisfied": satisfied,
                "progress": [taken_count, total_needed],
            }
            continue

        if req["requirement_type"] == "choose_group":
            satisfied_groups = 0
            for raw_group in req.get("options", []):
                if not isinstance(raw_group, list):
                    continue
                group_courses = [_normalize_course_code(c) for c in raw_group]
                if group_courses and all(course in completed_and_planned for course in group_courses):
                    satisfied_groups += 1

            min_count = int(req.get("min_count", 1))
            requirement_progress[req_id] = {
                "satisfied": satisfied_groups >= min_count,
                "progress": [min(satisfied_groups, min_count), min_count],
            }
            continue

        min_count = int(req.get("min_count", 0))
        satisfied_count = len([c for c in available if c in completed_and_planned])
        requirement_progress[req_id] = {
            "satisfied": satisfied_count >= min_count,
            "progress": [min(satisfied_count, min_count), min_count],
        }

    for dist, min_courses in DISTRIBUTION_REQUIREMENTS.items():
        completed_dist = [c for c in distribution_courses[dist] if c in completed_and_planned]
        requirement_progress[dist] = {
            "satisfied": len(completed_dist) >= min_courses,
            "progress": [min(len(completed_dist), min_courses), min_courses],
        }

    diversity_ok = any(c in completed_and_planned for c in diversity_courses)
    requirement_progress["analyzing_diversity"] = {
        "satisfied": diversity_ok,
        "progress": [1 if diversity_ok else 0, 1],
    }

    fwis_ok = any(c in completed_and_planned for c in fwis_courses)
    requirement_progress["FWIS"] = {
        "satisfied": fwis_ok,
        "progress": [1 if fwis_ok else 0, 1],
    }

    lpap_ok = any(c in completed_and_planned for c in lpap_courses)
    requirement_progress["LPAP"] = {
        "satisfied": lpap_ok,
        "progress": [1 if lpap_ok else 0, 1],
    }

    planned_credits = sum(catalog[c].credit_hours or 0 for c in planned_courses)
    total_credit_value = completed_credits + planned_credits
    requirement_progress["total_credits"] = {
        "satisfied": total_credit_value >= 120,
        "progress": [min(total_credit_value, 120), 120],
    }

    return {
        "status": "feasible",
        "schedule": schedule,
        "requirements": requirement_progress,
    }


