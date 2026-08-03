from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from ortools.sat.python import cp_model
from parsers.parse_schedule import (
    normalize_course_code,
)

from data.degree_requirement import get_supported_program_options, get_supported_program_requirements

if TYPE_CHECKING:
    from services.schedule_service import CourseRecord

_normalize_course_code = normalize_course_code

YEAR_ORDER = ["Freshman", "Sophomore", "Junior", "Senior"]
TERM_ORDER = ["Fall", "Spring"]
TOTAL_SEMESTERS = 8

DISTRIBUTION_REQUIREMENTS = {
    "Distribution Group I": 3,
    "Distribution Group II": 3,
    "Distribution Group III": 3,
}

CREDIT_UNIT_SCALE = 2
MAX_SEMESTER_CREDITS = 18 * CREDIT_UNIT_SCALE
MIN_GRADUATION_CREDITS = 120 * CREDIT_UNIT_SCALE
COMFORT_MIN_CREDITS = 0
COMFORT_MAX_CREDITS = 16 * CREDIT_UNIT_SCALE


def _credit_hours_to_units(credit_hours: Optional[float]) -> int:
    if credit_hours is None:
        return 0

    units = int(round(float(credit_hours) * CREDIT_UNIT_SCALE))
    if abs(units / CREDIT_UNIT_SCALE - float(credit_hours)) > 1e-9:
        raise ValueError(f"Unsupported credit hour value: {credit_hours}")
    return units


def _take_var_or_zero(
    take: Dict[Tuple[str, int], cp_model.IntVar],
    course: str,
    sem: int,
) -> cp_model.IntVar | int:
    return take.get((course, sem), 0)

def _prereq_satisfied_bool(
    tree: Optional[Dict[str, Any]],
    sem: int,
    model: cp_model.CpModel,
    take: Dict[Tuple[str, int], cp_model.IntVar],
    completed: Set[str],
    semester_range: List[int],
) -> cp_model.IntVar:
    
    """
    Checks whether a course with prerequisites of the form tree can be taken in semester sem
    Input:
    - tree: a dict representing prerequisite tree
    - sem: an integer that represents the semester
    - model: cp_sat model
    - take: a dict that maps key [class, semester] to int (either 0 or 1)
    - completed: a set of classes that the student has completed before
    - semester_range: the list of all semesters that the model can use

    Output: 
    - A cp_model integer variable


    For example:
    - take[('COMP 182', 1)] is 0 because its prereq is COMP 140
    - so model.new_bool_var(f"prereq_satisfied_{1}_{id(["COMP 140"])}") is false
    
    """
    
    #Creates a new satisfied variable based on semester and tree
    satisfied = model.new_bool_var(f"prereq_satisfied_{sem}_{id(tree)}")


    # If tree is not a dictionary returns satisfied equals to zero
    if not isinstance(tree, dict):
        model.add(satisfied == 0)
        return satisfied
    

    
    if "course" in tree:
        prereq_course = _normalize_course_code(tree["course"])

        # If a course is completed set satisfied equals 1
        if prereq_course in completed:
            model.add(satisfied == 1)
            return satisfied

        # If no variable exists for this prerequisite before sem, it cannot
        # satisfy this dependency in time.
        has_prior_take_var = any(
            (prereq_course, p) in take
            for p in semester_range
            if p < sem
        )
        if not has_prior_take_var:
            model.add(satisfied == 0)
            return satisfied
        
        # Checks if a course has been taken before
        taken_before = sum(
            _take_var_or_zero(take, prereq_course, p)
            for p in semester_range
            if p < sem
        )
        model.add(taken_before >= 1).only_enforce_if(satisfied)
        model.add(taken_before == 0).only_enforce_if(satisfied.Not())
        return satisfied

    # Recursively call is there is not a single course as prereq
    child = [_prereq_satisfied_bool(c, sem, model, take, completed, semester_range) for c in tree.get("conditions", [])]
    
    if not child:
        model.add(satisfied == 0)
        return satisfied

    node_type = tree.get("type")

    
    if node_type == "AND":
        model.add(sum(child) == len(child)).only_enforce_if(satisfied)
        model.add(sum(child) <= len(child) - 1).only_enforce_if(satisfied.Not())

    elif node_type == "OR":
        model.add(sum(child) >= 1).only_enforce_if(satisfied)
        model.add(sum(child) == 0).only_enforce_if(satisfied.Not())
    else:
        model.add(satisfied == 0)

    return satisfied

# ==================================================

# Course Requirements Constraints

# ==================================================


def _add_course_requirement_constraints(
    model: cp_model.CpModel,
    expanded_requirements: List[Dict[str, Any]],
    req_available: Dict[str, List[str]],
    use_for_req: Dict[Tuple[str, str], cp_model.IntVar],
    composite_meta: Dict[str, Dict[str, Any]],
    subgroup_satisfied: Dict[Tuple[str, str], cp_model.IntVar]

) -> None:
    # Course-level requirements
    for req in expanded_requirements:
        if req.get("is_subrequirement") is True:
            continue

        req_id = req["id"]
        available = req_available[req_id]

        # Required Courses
        if req["requirement_type"] == "required_courses":
            for course in available:
                model.add(use_for_req[(course, req_id)] == 1)
        
        # Courses with a minimum number and maximum number chosen
        elif req["requirement_type"] == "choose_n":
            model.add(sum(use_for_req[(course, req_id)] for course in available) >= req["min_count"])
            if "max_count" in req:
                model.add(sum(use_for_req[(course, req_id)] for course in available) <= req["max_count"])
        
        # Courses with groups chosen like ("MATH 212") OR ("MATH 222" AND "MATH 232")
        elif req["requirement_type"] == "choose_group":
            available_set = set(available)
            group_met_vars: List[cp_model.IntVar] = []

            for idx, raw_group in enumerate(req.get("options", [])):

                # Check if the group is a list
                if not isinstance(raw_group, list):
                    continue
            
                group_courses = [_normalize_course_code(c) for c in raw_group]
                if not group_courses:
                    continue

                group_met = model.new_bool_var(f"group_met_{req_id}_{idx}")
                group_met_vars.append(group_met)

                if not all(c in available_set for c in group_courses):
                    model.add(group_met == 0)
                    continue

                group_sum = sum(use_for_req[(course, req_id)] for course in group_courses)
                model.add(group_sum == len(group_courses)).only_enforce_if(group_met)
                model.add(group_sum <= len(group_courses) - 1).only_enforce_if(group_met.Not())

            min_count = int(req.get("min_count", 1))
            max_count = int(req.get("max_count", min_count))
            if not group_met_vars:
                if min_count > 0:
                    model.add(0 == 1)
            else:
                model.add(sum(group_met_vars) >= min_count)
                model.add(sum(group_met_vars) <= max_count)

        constraints = req.get("constraints", {})
        for group in constraints.get("max_from_group", []):
            group_courses = [_normalize_course_code(c) for c in group.get("courses", []) if _normalize_course_code(c) in available]
            model.add(sum(use_for_req[(course, req_id)] for course in group_courses) <= group["max_count"])

    # Composite-level constraints spanning multiple sub-requirements
    for parent_req_id, meta in composite_meta.items():
        sub_req_ids = meta.get("sub_requirement_ids", [])
        constraints = meta.get("constraints", {})
        for rule in constraints.get("min_from_subject", []):
            subject = str(rule.get("subject", "")).upper()
            min_count = int(rule.get("min_count", 0))
            if not subject or min_count <= 0:
                continue

            subject_vars: List[cp_model.IntVar] = []
            for sub_req_id in sub_req_ids:
                for course in req_available.get(sub_req_id, []):
                    if course.split(" ")[0] == subject and (course, sub_req_id) in use_for_req:
                        subject_vars.append(use_for_req[(course, sub_req_id)])

            if subject_vars:
                model.add(sum(subject_vars) >= min_count)
            else:
                model.add(0 == 1)
        
        min_count = int(meta.get("min_count", 0))
        if min_count > 0:
            subgroup_vars: List[cp_model.IntVar] = []
            for sub_req_id in sub_req_ids:
                key = (parent_req_id, sub_req_id)
                if key in subgroup_satisfied:
                    subgroup_vars.append(subgroup_satisfied[key])

            if subgroup_vars:
                model.add(sum(subgroup_vars) >= min_count)
            else:
                model.add(0 == 1)




# ==================================================

# General Graduation Requirements Constraints

# ==================================================

def _add_distribution_constraints(
    model: cp_model.CpModel,
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
    all_courses: Set[str],
    completed: Set[str],
    distribution_courses: Dict[str, List[str]],
) -> None:
    
    # A dictionary that maps (course, dist) to optimization variable
    satisfy_dist: Dict[Tuple[str, str], cp_model.IntVar] = {}

    #Looping through each distribution
    for dist, min_courses in DISTRIBUTION_REQUIREMENTS.items():

        # Looping through each course in each distribution
        valid_courses = [c for c in distribution_courses[dist] if c in all_courses]
        for course in valid_courses:
            if course not in completed:
                satisfy_dist[(course, dist)] = model.new_bool_var(
                    f"dist_{dist.replace(' ', '_')}_{course.replace(' ', '_')}"
                )
                # Only count a future distribution course if it is actually taken.
                # This conditions mean a course can be used to satisfy dist or not
                # If a course is not taken, it can not be used to satisfy dist
                # If it is taken, it can be either used to satisfy dist or not
                model.add(
                    satisfy_dist[(course, dist)]
                    <= sum(_take_var_or_zero(take, course, s) for s in semester_range)
                )

        #The number of completed courses and future courses must be larger than 3
        completed_satisfying = [c for c in valid_courses if c in completed]
        future_satisfying = sum(satisfy_dist[(c, dist)] for c in valid_courses if c not in completed)
        model.add(len(completed_satisfying) + future_satisfying >= min_courses)

        # Getting the course code
        subjects = {c.split(" ")[0] for c in valid_courses}

        # The number of courses from the same subject that counts towards distribution must be 2 or less
        for subject in subjects:
            completed_from_subject = min(2, sum(1 for c in completed_satisfying if c.split(" ")[0] == subject))
            future_from_subject = sum(
                satisfy_dist[(c, dist)]
                for c in valid_courses
                if c not in completed and c.split(" ")[0] == subject
            )
            model.add(completed_from_subject + future_from_subject <= 2)



def _add_diversity_constraints(
    model: cp_model.CpModel,
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
    all_courses: Set[str],
    completed: Set[str],
    diversity_courses: List[str],
) -> None:
    valid_diversity = [c for c in diversity_courses if c in all_courses]
    if not any(c in completed for c in valid_diversity):
        model.add(
            sum(
                _take_var_or_zero(take, c, s)
                for c in valid_diversity
                if c not in completed
                for s in semester_range
            )
            >= 1
        )


def _add_fwis_constraints(
    model: cp_model.CpModel,
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
    base_semester_number: int,
    all_courses: Set[str],
    completed: Set[str],
    fwis_courses: List[str],
) -> None:
    valid_fwis = [
        c for c in fwis_courses
        if c in all_courses and c not in completed
    ]

    freshman_semesters = [
        s for s in semester_range
        if (base_semester_number + s) in (0, 1)
    ]

    # FWIS courses may only be taken during freshman semesters.
    for c in valid_fwis:
        for s in semester_range:
            if s not in freshman_semesters:
                if (c, s) in take:
                    model.add(take[(c, s)] == 0)

    # If FWIS has not already been completed, exactly one FWIS must be taken.
    if fwis_courses and not any(c in completed for c in fwis_courses):
        model.add(
            sum(
                take[(c, s)]
                for c in valid_fwis
                for s in semester_range
                if (c, s) in take
            ) == 1
        )


def _add_lpap_constraints(
    model: cp_model.CpModel,
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
    all_courses: Set[str],
    completed: Set[str],
    lpap_courses: List[str],
) -> None:
    valid_lpap = [c for c in lpap_courses if c in all_courses and c not in completed]
    if lpap_courses and not any(c in completed for c in lpap_courses):
        model.add(
            sum(
                _take_var_or_zero(take, c, s)
                for c in valid_lpap
                for s in semester_range
            )
            == 1
        )


def _add_general_graduation_constraints(
    model: cp_model.CpModel,
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
    base_semester_number: int,
    all_courses: Set[str],
    completed: Set[str],
    distribution_courses: Dict[str, List[str]],
    diversity_courses: List[str],
    fwis_courses: List[str],
    lpap_courses: List[str],
) -> None:
    _add_distribution_constraints(model, take, semester_range, all_courses, completed, distribution_courses)
    _add_diversity_constraints(model, take, semester_range, all_courses, completed, diversity_courses)
    _add_fwis_constraints(model, take, semester_range, base_semester_number, all_courses, completed, fwis_courses)
    _add_lpap_constraints(model, take, semester_range, all_courses, completed, lpap_courses)



def _add_cross_list_constraints(
    model: cp_model.CpModel,
    catalog: Dict[str, CourseRecord],
    all_courses: Set[str],
    completed: Set[str],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
) -> None:
    cross_groups: Set[frozenset[str]] = set()

    # Create set of frozenset of cross-listed courses
    for course in all_courses:
        group = {course}
        for cross in catalog[course].cross_list:
            cross_norm = _normalize_course_code(cross)
            if cross_norm in all_courses:
                group.add(cross_norm)
        if len(group) > 1:
            cross_groups.add(frozenset(group))

    # Only one of each group can be taken
    for group in cross_groups:
        completed_count = sum(1 for c in group if c in completed)
        planned_count = sum(
            _take_var_or_zero(take, c, s)
            for c in group
            if c not in completed
            for s in semester_range
        )
        model.add(completed_count + planned_count <= 1)


def _add_single_take_constraints(
    model: cp_model.CpModel,
    all_courses: Set[str],
    completed: Set[str],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
) -> None:
    for course in all_courses:

        # A course can only be taken once
        model.add(
            sum(_take_var_or_zero(take, course, s) for s in semester_range)
            <= 1
        )

        #If a course is completed, it can not be taken anymore
        if course in completed:
            model.add(
                sum(_take_var_or_zero(take, course, s) for s in semester_range)
                == 0
            )


def _add_scheduled_course_constraints(
    model: cp_model.CpModel,
    scheduled: Dict[str, int],
    completed: Set[str],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    base_semester_number: int,
    semester_range: List[int],
) -> None:
    
    # If a course is scheduled in a semester, take is set to 1
    for course, absolute_sem in scheduled.items():
        if course in completed:
            continue

        local_sem = absolute_sem - base_semester_number
        if local_sem not in semester_range:
            raise ValueError(
                f"Scheduled semester index {absolute_sem} for {course} is outside the remaining planning horizon."
            )

        if (course, local_sem) not in take:
            raise ValueError(
                f"Scheduled course {course} is not offered in semester index {absolute_sem}."
            )

        model.add(take[(course, local_sem)] == 1)




def _add_requirement_overlap_constraints(
    model: cp_model.CpModel,
    req_available: Dict[str, List[str]],
    use_for_req: Dict[Tuple[str, str], cp_model.IntVar],
) -> None:
    """
    A course can not satisfy two requirements in a single degree but can be used to satisfy multiple requirements
    across many degrees

    """

    # Map degree to requirements
    # For Example
    # req_ids_by_degree = {

    #     "CS": [

    #         "CS:core",

    #         "CS:theory",

    #         "CS:systems"

    #     ],

    #     "MATH": [

    #         "MATH:linear_algebra",

    #         "MATH:statistics"

    #     ]

    # }
    req_ids_by_degree: Dict[str, List[str]] = {}
    for req_id in req_available:
        degree_key = req_id.split(":", 1)[0] if ":" in req_id else "__single_degree__"
        req_ids_by_degree.setdefault(degree_key, []).append(req_id)

    for course in {c for c, _ in use_for_req}: # Iterate through every course
        for req_ids in req_ids_by_degree.values(): # For each requirement groups in a degree

            # Each course can be used for requirement once
            model.add(
                sum(use_for_req[(course, req_id)] for req_id in req_ids if (course, req_id) in use_for_req) <= 1
            )


def _add_prerequisite_constraints(
    model: cp_model.CpModel,
    catalog: Dict[str, CourseRecord],
    all_courses: Set[str],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    completed: Set[str],
    semester_range: List[int],
) -> None:
    
    """
    Sets the variable that is represented by take[(course, sem)] in model to 1 if pre req can be satisfied
    in semester sem, 0 if otherwise

    """

    # For every semester in every course, check if taking it in that semester is feasible
    for course in all_courses:
        prereq_tree = catalog[course].prereq_tree
        if prereq_tree is None:
            continue
        for sem in semester_range:
            prereq_ok = _prereq_satisfied_bool(prereq_tree, sem, model, take, completed, semester_range) 

            #Take must equal 0 if prereq_ok is 0, else it can be in {0,1}
            if (course, sem) in take:
                model.add(take[(course, sem)] <= prereq_ok)


def _add_term_offering_constraints(
    model: cp_model.CpModel,
    catalog: Dict[str, CourseRecord],
    all_courses: Set[str],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
    base_semester_number: int,
) -> None:
    for course in all_courses:
        offered = catalog[course].offered_terms

        #If not offered, set take variable to 0 for a course in all semesters
        if not offered:
            for sem in semester_range:
                if (course, sem) in take:
                    model.add(take[(course, sem)] == 0)
            continue

        # From base semester, set take[(course, sem)] to 0 based on whether it's not offered in fall or spring
        for sem in semester_range:
            absolute_sem = base_semester_number + sem
            sem_term = TERM_ORDER[absolute_sem % 2]
            if sem_term not in offered:
                if (course, sem) in take:
                    model.add(take[(course, sem)] == 0)


def _add_credit_constraints(
    model: cp_model.CpModel,
    catalog: Dict[str, CourseRecord],
    all_courses: Set[str],
    completed: Set[str],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
    course_to_credits: Dict[str, int],
) -> Tuple[Any, int, Dict[int, cp_model.IntVar]]:
    
    total_credits = sum(
        course_to_credits[c] * _take_var_or_zero(take, c, s)
        for c in all_courses
        if c in course_to_credits
        for s in semester_range
    )
    completed_credits = sum(_credit_hours_to_units(catalog[c].credit_hours) for c in completed if c in catalog)

    #All total and completed credits should be 120 or above to graduate
    model.add(total_credits + completed_credits >= MIN_GRADUATION_CREDITS)

    # Creates a mapping of semester (as integers) to sem_credits_{sem} variable
    semester_credit_vars: Dict[int, cp_model.IntVar] = {}

    for sem in semester_range:
        sem_credits_expr = sum(
            course_to_credits[c] * _take_var_or_zero(take, c, sem)
            for c in all_courses
            if c in course_to_credits
        )
        sem_credits = model.new_int_var(0, MAX_SEMESTER_CREDITS, f"sem_credits_{sem}")

        #If scheduled, then sem_credits must equal sem_credits_expr
        model.add(sem_credits == sem_credits_expr)

        #Total semester credits must be less than 19
        model.add(sem_credits <= MAX_SEMESTER_CREDITS)
        semester_credit_vars[sem] = sem_credits

    return total_credits, completed_credits, semester_credit_vars


def _add_preference_constraints(
    model: cp_model.CpModel,
    preferred: Set[str],
    avoid: Set[str],
    all_courses: Set[str],
    completed: Set[str],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
) -> None:
    # If a course is preferred, set sum of takes to 1
    for course in preferred:
        if course in all_courses and course not in completed:
            model.add(
                sum(_take_var_or_zero(take, course, s) for s in semester_range)
                == 1
            )

    # If a course is not preferred, set sum of takes to 0
    for course in avoid:
        if course in all_courses and course not in completed:
            model.add(
                sum(_take_var_or_zero(take, course, s) for s in semester_range)
                == 0
            )


def _add_compact_semester_constraints(
    model: cp_model.CpModel,
    all_courses: Set[str],
    take: Dict[Tuple[str, int], cp_model.IntVar],
    semester_range: List[int],
) -> Dict[int, cp_model.IntVar]:
    
    # There should be no gaps within semesters
    semester_used = {s: model.new_bool_var(f"semester_used_{s}") for s in semester_range}
    for course in all_courses:
        for sem in semester_range:
            if (course, sem) in take:
                model.add(take[(course, sem)] <= semester_used[sem])
    for i in range(len(semester_range) - 1):
        model.add(semester_used[semester_range[i]] >= semester_used[semester_range[i + 1]])
    return semester_used



