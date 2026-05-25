from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from ortools.sat.python import cp_model

from degree_requirement import get_supported_program_requirements


# -----------------------------
# Important information
# -----------------------------


YEAR_ORDER = ["Freshman", "Sophomore", "Junior", "Senior"]
TERM_ORDER = ["Fall", "Spring"]
TOTAL_SEMESTERS = 8

DISTRIBUTION_REQUIREMENTS = {
    "Distribution Group I": 3,
    "Distribution Group II": 3,
    "Distribution Group III": 3,
}

SUPPORTED_DEGREE_REQUIREMENTS: Dict[str, List[Dict[str, Any]]] = get_supported_program_requirements()


def _supported_program_message() -> str:
    supported = sorted(SUPPORTED_DEGREE_REQUIREMENTS.keys())
    if not supported:
        return "No supported degree selected. No programs are currently configured."
    listed = ", ".join(f"'{name}'" for name in supported)
    return f"No supported degree selected. Include one or more of: {listed} in chosen_degree."


def _selected_degree_requirements(chosen_degree: List[str]) -> List[Dict[str, Any]]:
    selected_degrees = [d for d in chosen_degree if d in SUPPORTED_DEGREE_REQUIREMENTS]
    is_multi_degree = len(selected_degrees) > 1
    selected: List[Dict[str, Any]] = []
    for degree in selected_degrees:
        requirements = SUPPORTED_DEGREE_REQUIREMENTS.get(degree)
        if requirements:
            for req in requirements:
                req_copy = dict(req)
                if is_multi_degree:
                    req_copy["id"] = f"{degree}:{req['id']}"
                selected.append(req_copy)
    return selected


# -----------------------------
# Class Information
# -----------------------------

@dataclass
class CourseRecord:
    code: str
    subject: str
    course_number: int
    long_title: Optional[str]
    offered_terms: Set[str]
    credit_hours: Optional[int]
    distribution: Optional[str]
    analyzing_diversity: bool
    cross_list: List[str]
    prereq_tree: Optional[Dict[str, Any]]




# -----------------------------
# Defining important information
# -----------------------------


def _normalize_course_code(course: str) -> str:
    """
    Normalizing every course code in the form of [capitalized subject] [course number], like COMP 140

    Input: A potential course code in terms of string, e.g. comp  140
    Output: Normalized course code, e.g. COMP 140
    
    """
    course = " ".join(course.strip().upper().split())
    match = re.match(r"^([A-Z]{2,5})\s*(\d{3})$", course)
    if not match:
        return course
    return f"{match.group(1)} {match.group(2)}"


def _parse_cross_list(raw_text: str) -> List[str]:

    """

    Returns all cross listed courses of a course

    Input: Raw text entry of a course
    Output: A list of cross listed courses


    """

    if not raw_text:
        return []
    return [_normalize_course_code(c) for c in re.findall(r"Cross-list:\s*([A-Z]{2,5}\s+\d{3})", raw_text)]


def parse_long_title(raw_text):

    """

    Returns the long title of a course

    Input: Raw text entry of a course
    Output: The long title of a course 


    """

    if not isinstance(raw_text, str):
        return None

    match = re.search(
        r"Long Title:\s*\n(.+)",
        raw_text,
    )

    if match:
        return match.group(1).strip()

    return None




def _parse_distribution(raw_text: str) -> Optional[str]:

    """

    Returns distribution of a course 

    Input: Raw text entry of a course
    Output: The distribution of a course


    """


    if not raw_text:
        return None
    match = re.search(r"Distribution Group:\s*\n(.+)", raw_text)
    return match.group(1).strip() if match else None


def _parse_diversity(raw_text: str) -> bool:
    if not raw_text:
        return False
    match = re.search(r"Analyzing Diversity:\s*\n(.+)", raw_text)
    return bool(match and match.group(1).strip().lower() == "yes")


def _parse_credit_hours(raw_text: str) -> Optional[int]:
    if not raw_text:
        return None
    match = re.search(r"Credit Hours:\s*\n(.+)", raw_text)
    if not match:
        return None
    text = match.group(1).strip()

    # Single fixed credit, e.g. "3"
    if re.fullmatch(r"\d+", text):
        return int(text)

    # Ranges like "1 TO 3"; use upper bound to avoid undercounting.
    range_match = re.fullmatch(r"(\d+)\s+TO\s+(\d+)", text)
    if range_match:
        return int(range_match.group(2))

    # Alternatives like "3 OR 5"; use upper value conservatively.
    or_match = re.fullmatch(r"(\d+)\s+OR\s+(\d+)", text)
    if or_match:
        return max(int(or_match.group(1)), int(or_match.group(2)))

    return None



def _tokenize_prereq(expr: str) -> List[str]:

    """
    Convert from this form:

    expr = "(COMP 182 AND MATH 101) OR STAT 310"

    Into this form:

    [

    "(",

    "COMP 182",

    "AND",

    "MATH 101",

    ")",

    "OR",

    "STAT 310"

]
    
    """
    return re.findall(r"[A-Z]{2,5}\s+\d{3}|AND|OR|\(|\)", expr.upper())


def _parse_prereq_expr(expr: str) -> Optional[Dict[str, Any]]:

    """

    Convert this:
    "(COMP 182 AND MATH 212) OR STAT 310"

    Into this:
    {
        "type": "OR",
        "conditions": [
            {
                "type": "AND",
                "conditions": [
                    {"course": "COMP 182"},
                    {"course": "MATH 212"}
                ]
            },
            {"course": "STAT 310"}
        ]
    }
    
    """
    if not expr or not expr.strip():
        return None

    tokens = _tokenize_prereq(expr)
    if not tokens:
        return None

    pos = 0

    def parse_expression() -> Dict[str, Any]:
        return parse_or()

    def parse_or() -> Dict[str, Any]:
        nonlocal pos
        left = parse_and()
        conditions = [left]
        while pos < len(tokens) and tokens[pos] == "OR":
            pos += 1
            conditions.append(parse_and())
        if len(conditions) == 1:
            return left
        return {"type": "OR", "conditions": conditions}

    def parse_and() -> Dict[str, Any]:
        nonlocal pos
        left = parse_factor()
        conditions = [left]
        while pos < len(tokens) and tokens[pos] == "AND":
            pos += 1
            conditions.append(parse_factor())
        if len(conditions) == 1:
            return left
        return {"type": "AND", "conditions": conditions}

    def parse_factor() -> Dict[str, Any]:
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError("Unexpected end of prerequisite expression")
        token = tokens[pos]
        if token == "(":
            pos += 1
            node = parse_expression()
            if pos < len(tokens) and tokens[pos] == ")":
                pos += 1
            return node
        pos += 1
        return {"course": _normalize_course_code(token)}

    try:
        parsed = parse_expression()
        if pos != len(tokens):
            return None
        return parsed
    except Exception:
        # Some catalog prerequisite strings are malformed; skip them instead of failing the API.
        return None


def load_course_catalog(json_path: Path) -> Dict[str, CourseRecord]:

    """

    Convert this:
    {
        "subject": "COMP",
        "course_number": "182",
        "term": "Fall 2026",
        "raw_text": "...",
        "prerequisites": "(COMP 140 AND MATH 101)"
    }

    Into this:
    CourseRecord(
        code="COMP 182",
        subject="COMP",
        course_number=182,
        long_title="Algorithmic Thinking",
        offered_terms={"Fall"},
        credit_hours=4,
        distribution=None,
        analyzing_diversity=False,
        cross_list=[],
        prereq_tree={
            "type": "AND",
            ...
        }
    )
    
    """
    with json_path.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    catalog: Dict[str, CourseRecord] = {}

    for row in rows:
        subject = str(row.get("subject", "")).strip().upper()
        course_num_raw = str(row.get("course_number", "")).strip()
        if not subject or not course_num_raw.isdigit():
            continue

        course_number = int(course_num_raw)
        code = f"{subject} {course_number:03d}"

        raw_text = row.get("raw_text") or ""
        term = str(row.get("term", "")).strip()
        prereq = row.get("prerequisites") or ""

        if code not in catalog:
            catalog[code] = CourseRecord(
                code=code,
                subject=subject,
                course_number=course_number,
                long_title=parse_long_title(raw_text),
                offered_terms=set(),
                credit_hours=_parse_credit_hours(raw_text),
                distribution=_parse_distribution(raw_text),
                analyzing_diversity=_parse_diversity(raw_text),
                cross_list=_parse_cross_list(raw_text),
                prereq_tree=_parse_prereq_expr(str(prereq)),
            )

        if "fall" in term.lower():
            catalog[code].offered_terms.add("Fall")
        if "spring" in term.lower():
            catalog[code].offered_terms.add("Spring")

        if catalog[code].credit_hours is None:
            catalog[code].credit_hours = _parse_credit_hours(raw_text)
        if catalog[code].long_title is None:
            catalog[code].long_title = parse_long_title(raw_text)
        if catalog[code].distribution is None:
            catalog[code].distribution = _parse_distribution(raw_text)
        if not catalog[code].analyzing_diversity:
            catalog[code].analyzing_diversity = _parse_diversity(raw_text)
        if not catalog[code].cross_list:
            catalog[code].cross_list = _parse_cross_list(raw_text)
        if catalog[code].prereq_tree is None and prereq:
            catalog[code].prereq_tree = _parse_prereq_expr(str(prereq))

    return catalog


def _remaining_semester_indices(current_term: str, year: str) -> Tuple[List[int], int]:
    """
    Return a list of remaining semesters and the current semester based on year and term

    Input: current_term e.g. Spring, and year e.g. Freshman
    Output:
    - A list of remaining semesters. e.g. Sophomore Spring returns [0,1,2,3,4]
    - An integer representing the semester e.g. Sophomore Spring returns 3
    
    """
    if year not in YEAR_ORDER:
        raise ValueError(f"Invalid year: {year}. Expected one of {YEAR_ORDER}.")
    if current_term not in TERM_ORDER:
        raise ValueError(f"Invalid current_term: {current_term}. Expected one of {TERM_ORDER}.")

    current_year_idx = YEAR_ORDER.index(year)
    current_term_idx = TERM_ORDER.index(current_term)
    current_semester_number = current_year_idx * 2 + current_term_idx
    remaining = TOTAL_SEMESTERS - current_semester_number
    if remaining <= 0:
        raise ValueError("No semesters remain based on current_term and year.")
    return list(range(remaining)), current_semester_number


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
            "constraints": req.get("constraints", {}),
            "sub_requirements": req.get("sub_requirements", []),
        }

    return expanded, composite_meta


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


def _prereq_satisfied_bool(
    tree: Optional[Dict[str, Any]],
    sem: int,
    model: cp_model.CpModel,
    take: Dict[Tuple[str, int], cp_model.IntVar],
    completed: Set[str],
    semester_range: List[int],
) -> cp_model.IntVar:
    satisfied = model.new_bool_var(f"prereq_satisfied_{sem}_{id(tree)}")

    """
    Checks whether a course with prerequisites of the form tree can be taken in semester sem
    Input:
    - tree: a dict representing prerequisite tree
    - sem: an integer that represents the semester
    - model: cp_sat model
    - take: a dict that maps key [class, semester] to int (either 0 or 1)
    - completed: a set of classes that the student has completed before
    - semester_range: the list of all semesters that the model can use
    
    """

    if not isinstance(tree, dict):
        model.add(satisfied == 0)
        return satisfied

    if "course" in tree:
        prereq_course = _normalize_course_code(tree["course"])
        if prereq_course in completed:
            model.add(satisfied == 1)
            return satisfied

        if (prereq_course, 0) not in take:
            model.add(satisfied == 0)
            return satisfied

        taken_before = sum(take[(prereq_course, p)] for p in semester_range if p < sem)
        model.add(taken_before >= 1).only_enforce_if(satisfied)
        model.add(taken_before == 0).only_enforce_if(satisfied.Not())
        return satisfied

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



# -----------------------------
# Main Scheduling Function
# -----------------------------


def build_schedule(
    catalog: Dict[str, CourseRecord],
    current_term: str,
    year: str,
    completed_courses: List[str],
    preferred_courses: List[str],
    avoid_courses: List[str],
    scheduled_courses: Optional[Dict[str, int]],
    chosen_degree: List[str],
    optimization: Literal["balanced", "graduate early"],
) -> Dict[str, Any]:
    
    # Normalized course codes for each category
    completed = {_normalize_course_code(c) for c in completed_courses}
    preferred = {_normalize_course_code(c) for c in preferred_courses}
    avoid = {_normalize_course_code(c) for c in avoid_courses}
    scheduled = {
        _normalize_course_code(c): int(sem)
        for c, sem in (scheduled_courses or {}).items()
        if isinstance(c, str) and c.strip()
    }
    chosen_degree_normalized = [str(d).strip().lower() for d in chosen_degree if str(d).strip()]
    degree_requirements = _selected_degree_requirements(chosen_degree_normalized)
    if not degree_requirements:
        raise ValueError(_supported_program_message())
    expanded_requirements, composite_meta = _expand_composite_requirements(degree_requirements)

    #Getting the remaining semester list and an integer that represents the current semester
    semester_range, base_semester_number = _remaining_semester_indices(current_term, year)


    #Initializing the cp_sat model
    model = cp_model.CpModel()

    #Initializing an empty list that represents the courses that satisfy each category
    distribution_courses: Dict[str, List[str]] = {
        "Distribution Group I": [],
        "Distribution Group II": [],
        "Distribution Group III": [],
    }
    diversity_courses: List[str] = []
    fwis_courses: List[str] = []
    lpap_courses: List[str] = []

    ## Adding all courses from the course catalog in specific categories
    for code, rec in catalog.items():
        if rec.distribution in distribution_courses:
            distribution_courses[rec.distribution].append(code)
        if rec.analyzing_diversity:
            diversity_courses.append(code)
        if code.startswith("FWIS"):
            fwis_courses.append(code)
        if code.startswith("LPAP"):
            lpap_courses.append(code)

    #Adding the courses that need to be taken into all_courses
    all_courses: Set[str] = set()
    for req in expanded_requirements:
        if "courses" in req:
            all_courses.update(_normalize_course_code(c) for c in req["courses"])
        if "options" in req:
            for option in req["options"]:
                if isinstance(option, list):
                    all_courses.update(_normalize_course_code(c) for c in option)

    for dist_list in distribution_courses.values():
        all_courses.update(dist_list)

    all_courses.update(diversity_courses)
    all_courses.update(fwis_courses)
    all_courses.update(lpap_courses)
    all_courses.update(preferred)
    all_courses.update(avoid)
    all_courses.update(scheduled.keys())


    # Adding elective courses into all_courses
    for req in expanded_requirements:
        if "filters" not in req:
            continue
        filters = req.get("filters", {})
        constraints = req.get("constraints", {})
        for code, rec in catalog.items():
            if _course_matches_filter(rec, filters, constraints):
                all_courses.add(code)
    # Filter out courses that do not exist in catalog
    all_courses = {c for c in all_courses if c in catalog}

    # Raise error if scheduled course is not in catalog or semester is out of range
    for course, absolute_sem in scheduled.items():
        if course not in catalog:
            raise ValueError(f"Scheduled course not found in catalog: {course}")
        if absolute_sem < 0 or absolute_sem >= TOTAL_SEMESTERS:
            raise ValueError(
                f"Scheduled semester index for {course} must be between 0 and {TOTAL_SEMESTERS - 1}."
            )

    # Maps each course to its credit hour
    course_to_credits = {c: catalog[c].credit_hours for c in all_courses if catalog[c].credit_hours is not None}

    # Makes decision variables for all courses in every semester
    take: Dict[Tuple[str, int], cp_model.IntVar] = {}
    for course in all_courses:
        for sem in semester_range:
            take[(course, sem)] = model.new_bool_var(f"take_{course.replace(' ', '_')}_{sem}")

    # Build a list of frozen sets of cross listed courses
    cross_groups: Set[frozenset[str]] = set()
    for course in all_courses:
        group = {course}
        for cross in catalog[course].cross_list:
            cross_norm = _normalize_course_code(cross)
            if cross_norm in all_courses:
                group.add(cross_norm)
        if len(group) > 1:
            cross_groups.add(frozenset(group))

    # If a course is already completed, it is in completed_count. Both completed and planned count should not exceed 1
    for group in cross_groups:
        completed_count = sum(1 for c in group if c in completed)
        planned_count = sum(take[(c, s)] for c in group if c not in completed for s in semester_range)
        model.add(completed_count + planned_count <= 1)

    # A course can be taken at most once. Completed courses should not be taken again
    for course in all_courses:
        model.add(sum(take[(course, s)] for s in semester_range) <= 1)
        if course in completed:
            model.add(sum(take[(course, s)] for s in semester_range) == 0)

    # Courses in scheduled are taken in a specific semester
    for course, absolute_sem in scheduled.items():
        if course in completed:
            continue

        local_sem = absolute_sem - base_semester_number
        if local_sem not in semester_range:
            raise ValueError(
                f"Scheduled semester index {absolute_sem} for {course} is outside the remaining planning horizon."
            )

        model.add(take[(course, local_sem)] == 1)

    req_available: Dict[str, List[str]] = {}
    use_for_req: Dict[Tuple[str, str], cp_model.IntVar] = {}

    for req in expanded_requirements:
        req_id = req["id"]
        available: List[str] = []

        # Get available courses in each degree requirements
        if "courses" in req:
            available = [
                _normalize_course_code(c)
                for c in req["courses"]
                if _normalize_course_code(c) in all_courses or _normalize_course_code(c) in completed
            ]
        elif "filters" in req:
            filters = req.get("filters", {})
            constraints = req.get("constraints", {})
            for course in all_courses:
                if _course_matches_filter(catalog[course], filters, constraints):
                    available.append(course)
        elif "options" in req:
            option_courses: List[str] = []
            for option in req.get("options", []):
                if isinstance(option, list):
                    option_courses.extend(_normalize_course_code(c) for c in option)
            available = sorted({c for c in option_courses if c in all_courses or c in completed})

        req_available[req_id] = available

        # Check whether if a course counts towards requirements
        for course in available:

            #Creates new variable [course, requirement]
            var = model.new_bool_var(f"use_{course.replace(' ', '_')}_for_{req_id}")
            use_for_req[(course, req_id)] = var

            # A course counts towards requirement if it is actually taken
            if course not in completed:
                model.add(var <= sum(take[(course, s)] for s in semester_range))

    # Prevent one course being used for multiple requirements within the same degree.
    # Across different selected degrees, overlap is allowed (e.g. COMP 301 for BS CS and DS minor).
    req_ids_by_degree: Dict[str, List[str]] = {}
    for req_id in req_available:
        degree_key = req_id.split(":", 1)[0] if ":" in req_id else "__single_degree__"
        req_ids_by_degree.setdefault(degree_key, []).append(req_id)

    for course in {c for c, _ in use_for_req}:
        for req_ids in req_ids_by_degree.values():
            model.add(sum(use_for_req[(course, req_id)] for req_id in req_ids if (course, req_id) in use_for_req) <= 1)

    # A course must be taken if it is in required course, or the sum of courses in a requirement must be no less than min count and no more than max count
    for req in expanded_requirements:
        req_id = req["id"]
        available = req_available[req_id]

        if req["requirement_type"] == "required_courses":
            for course in available:
                model.add(use_for_req[(course, req_id)] == 1)
        elif req["requirement_type"] == "choose_n":
            model.add(sum(use_for_req[(course, req_id)] for course in available) >= req["min_count"])
            if "max_count" in req:
                model.add(sum(use_for_req[(course, req_id)] for course in available) <= req["max_count"])
        elif req["requirement_type"] == "choose_group":
            available_set = set(available)
            group_met_vars: List[cp_model.IntVar] = []

            for idx, raw_group in enumerate(req.get("options", [])):
                if not isinstance(raw_group, list):
                    continue

                group_courses = [_normalize_course_code(c) for c in raw_group]
                if not group_courses:
                    continue

                group_met = model.new_bool_var(f"group_met_{req_id}_{idx}")
                group_met_vars.append(group_met)

                # A group option is met only if all courses in that option are satisfied.
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

    # Composite-level constraints that span multiple sub-requirements.
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


    #Check whether if a student satisfy their distribution courses
    satisfy_dist: Dict[Tuple[str, str], cp_model.IntVar] = {}
    for dist, min_courses in DISTRIBUTION_REQUIREMENTS.items():
        valid_courses = [c for c in distribution_courses[dist] if c in all_courses]
        for course in valid_courses:
            if course not in completed:
                satisfy_dist[(course, dist)] = model.new_bool_var(f"dist_{dist.replace(' ', '_')}_{course.replace(' ', '_')}")
                
                # Only count a future distribution course if it is actually taken. For example, if HIST 101 is never taken, satisfy_dist[("HIST 101", "Distribution Group I")] = 0
                model.add(satisfy_dist[(course, dist)] <= sum(take[(course, s)] for s in semester_range))

        # Completed courses and future courses should exceed min courses to satisfy distribution
        completed_satisfying = [c for c in valid_courses if c in completed]
        future_satisfying = sum(satisfy_dist[(c, dist)] for c in valid_courses if c not in completed)
        model.add(len(completed_satisfying) + future_satisfying >= min_courses)

        #Only count 2 courses for each subject for distribution
        subjects = {c.split(" ")[0] for c in valid_courses}
        for subject in subjects:
            completed_from_subject = min(2, sum(1 for c in completed_satisfying if c.split(" ")[0] == subject))
            future_from_subject = sum(
                satisfy_dist[(c, dist)]
                for c in valid_courses
                if c not in completed and c.split(" ")[0] == subject
            )
            model.add(completed_from_subject + future_from_subject <= 2)

    # Diversity courses should be 1 or more
    valid_diversity = [c for c in diversity_courses if c in all_courses]
    if not any(c in completed for c in valid_diversity):
        model.add(sum(take[(c, s)] for c in valid_diversity if c not in completed for s in semester_range) >= 1)

    #FWIS courses should be 1 or more
    valid_fwis = [c for c in fwis_courses if c in all_courses and c not in completed]
    freshman_semesters = [s for s in semester_range if (base_semester_number + s) in (0, 1)]

    # FWIS can only be taken in Freshman Fall/Spring.
    for c in valid_fwis:
        for s in semester_range:
            if s not in freshman_semesters:
                model.add(take[(c, s)] == 0)

    # Enforce the FWIS requirement only when freshman semesters are still in horizon.
    if fwis_courses and not any(c in completed for c in fwis_courses) and freshman_semesters:
        model.add(sum(take[(c, s)] for c in valid_fwis for s in freshman_semesters) == 1)

    # LPAP courses must be taken
    valid_lpap = [c for c in lpap_courses if c in all_courses and c not in completed]
    if lpap_courses and not any(c in completed for c in lpap_courses):
        model.add(sum(take[(c, s)] for c in valid_lpap for s in semester_range) == 1)

    #Only take the course if prereq is finished before that semester
    for course in all_courses:
        prereq_tree = catalog[course].prereq_tree
        if prereq_tree is None:
            continue
        for sem in semester_range:
            prereq_ok = _prereq_satisfied_bool(prereq_tree, sem, model, take, completed, semester_range)
            model.add(take[(course, sem)] <= prereq_ok)

    # A course can only can scheduled in the semester if it is actually offered
    for course in all_courses:
        offered = catalog[course].offered_terms
        if not offered:
            for sem in semester_range:
                model.add(take[(course, sem)] == 0)
            continue
        for sem in semester_range:
            absolute_sem = base_semester_number + sem
            sem_term = TERM_ORDER[absolute_sem % 2]
            if sem_term not in offered:
                model.add(take[(course, sem)] == 0)

    #Total and completed credits should be 120 or more
    total_credits = sum(course_to_credits[c] * take[(c, s)] for c in all_courses if c in course_to_credits for s in semester_range)
    completed_credits = sum(catalog[c].credit_hours or 0 for c in completed if c in catalog)
    model.add(total_credits + completed_credits >= 120)

    #Each semester should not exceed more than 18 credits
    semester_credit_vars: Dict[int, cp_model.IntVar] = {}
    for sem in semester_range:
        sem_credits_expr = sum(course_to_credits[c] * take[(c, sem)] for c in all_courses if c in course_to_credits)
        sem_credits = model.new_int_var(0, 18, f"sem_credits_{sem}")
        model.add(sem_credits == sem_credits_expr)
        model.add(sem_credits <= 18)
        semester_credit_vars[sem] = sem_credits

    #Set preffered and avoid courses
    for course in preferred:
        if course in all_courses and course not in completed:
            model.add(sum(take[(course, s)] for s in semester_range) == 1)

    for course in avoid:
        if course in all_courses and course not in completed:
            model.add(sum(take[(course, s)] for s in semester_range) == 0)

    # Check whether each semester is being used and force semesters to stay compact without gaps
    semester_used = {s: model.new_bool_var(f"semester_used_{s}") for s in semester_range}
    for course in all_courses:
        for sem in semester_range:
            model.add(take[(course, sem)] <= semester_used[sem])
    for i in range(len(semester_range) - 1):
        model.add(semester_used[semester_range[i]] >= semester_used[semester_range[i + 1]])

    # Builds a set of courses explicitly required within degree requirement
    required_or_choice: Set[str] = set()
    for req in expanded_requirements:
        if "courses" in req:
            required_or_choice.update(_normalize_course_code(c) for c in req["courses"])
        if "options" in req:
            for option in req["options"]:
                if isinstance(option, list):
                    required_or_choice.update(_normalize_course_code(c) for c in option)

    # Optimize model based on graduate early or balanced
    if optimization == "graduate early":
        model.minimize(
            1000 * sum(semester_used[s] for s in semester_range)
            + total_credits
            + 10 * sum(s * take[(c, s)] for c in required_or_choice if c in all_courses for s in semester_range)
        )
    else:
        min_comfort, max_comfort, max_credits = 0, 16, 18
        comfort_penalties = []
        for sem in semester_range:
            sem_credits = semester_credit_vars[sem]
            penalty = model.new_int_var(0, max_credits, f"penalty_{sem}")
            model.add(penalty >= min_comfort - sem_credits)
            model.add(penalty >= sem_credits - max_comfort)
            model.add(penalty >= 0)
            comfort_penalties.append(penalty)

        # Primary balanced objective: make semester credit loads as equal as possible.
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
            + sum(s * take[(c, s)] for c in required_or_choice if c in all_courses for s in semester_range)
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
        for c in sem_courses:
            planned_courses.add(c)
            schedule[label].append([c, course_reason(c, sem)])

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

            total_needed = len(sub_requirements)
            requirement_progress[req_id] = {
                "satisfied": sub_satisfied_count >= total_needed and min_subject_ok,
                "progress": [sub_satisfied_count, total_needed],
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


def check_requirements_for_courses(
    catalog: Dict[str, CourseRecord],
    course_codes: List[str],
    chosen_degree: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    taken = {_normalize_course_code(c) for c in course_codes if isinstance(c, str) and c.strip()}
    chosen_degree_normalized = [str(d).strip().lower() for d in (chosen_degree or ["bs_comp"]) if str(d).strip()]
    degree_requirements = _selected_degree_requirements(chosen_degree_normalized)
    if not degree_requirements:
        raise ValueError(_supported_program_message())

    rows: List[Dict[str, Any]] = []

    for req in degree_requirements:
        req_type = req["id"]
        if req.get("requirement_type") == "composite":
            sub_requirements = [sub for sub in req.get("sub_requirements", []) if isinstance(sub, dict)]
            sub_satisfied_count = 0
            for sub_req in sub_requirements:
                sub_satisfied, _ = _evaluate_requirement_from_taken(sub_req, taken, catalog)
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

                subject_count = sum(1 for c in taken if c in eligible_subject_courses and c.split(" ")[0] == subject)
                if subject_count < min_count:
                    min_subject_ok = False
                    break

            total_needed = len(sub_requirements)
            rows.append(
                {
                    "type": req_type,
                    "satisfied": sub_satisfied_count >= total_needed and min_subject_ok,
                    "progress": [sub_satisfied_count, total_needed],
                }
            )
            continue

        satisfying_courses: List[str] = []

        if "courses" in req:
            satisfying_courses = sorted(
                _normalize_course_code(c)
                for c in req["courses"]
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

        taken_count = len([c for c in satisfying_courses if c in taken])
        total_count = len(satisfying_courses)

        if req["requirement_type"] == "required_courses":
            satisfied = taken_count >= total_count
        elif req["requirement_type"] == "choose_group":
            satisfied_groups = 0
            for raw_group in req.get("options", []):
                if not isinstance(raw_group, list):
                    continue
                group_courses = [_normalize_course_code(c) for c in raw_group]
                if group_courses and all(course in taken for course in group_courses):
                    satisfied_groups += 1

            target = int(req.get("min_count", 1))
            satisfied = satisfied_groups >= target
            total_count = target
            taken_count = min(satisfied_groups, target)
        else:
            target = int(req.get("min_count", 0))
            satisfied = taken_count >= target
            total_count = target
            taken_count = min(taken_count, target)

        rows.append(
            {
                "type": req_type,
                "satisfied": satisfied,
                "progress": [taken_count, total_count],
            }
        )

    for dist, min_courses in DISTRIBUTION_REQUIREMENTS.items():
        dist_courses = [code for code, rec in catalog.items() if rec.distribution == dist]
        taken_count = len([c for c in dist_courses if c in taken])
        rows.append(
            {
                "type": dist,
                "satisfied": taken_count >= min_courses,
                "progress": [min(taken_count, min_courses), min_courses],
            }
        )

    diversity_courses = [code for code, rec in catalog.items() if rec.analyzing_diversity]
    diversity_taken = len([c for c in diversity_courses if c in taken])
    rows.append(
        {
            "type": "analyzing_diversity",
            "satisfied": diversity_taken >= 1,
            "progress": [1 if diversity_taken >= 1 else 0, 1],
        }
    )

    fwis_courses = [code for code in catalog if code.startswith("FWIS")]
    fwis_taken = len([c for c in fwis_courses if c in taken])
    rows.append(
        {
            "type": "FWIS",
            "satisfied": fwis_taken >= 1,
            "progress": [1 if fwis_taken >= 1 else 0, 1],
        }
    )

    lpap_courses = [code for code in catalog if code.startswith("LPAP")]
    lpap_taken = len([c for c in lpap_courses if c in taken])
    rows.append(
        {
            "type": "LPAP",
            "satisfied": lpap_taken >= 1,
            "progress": [1 if lpap_taken >= 1 else 0, 1],
        }
    )

    total_credits = sum((catalog[c].credit_hours or 0) for c in taken if c in catalog)
    rows.append(
        {
            "type": "total_credits",
            "satisfied": total_credits >= 120,
            "progress": [min(total_credits, 120), 120],
        }
    )

    return rows
