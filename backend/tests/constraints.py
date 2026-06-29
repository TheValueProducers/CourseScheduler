from ortools.sat.python import cp_model

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from optimizer import constraints as cons
from optimizer.variables import _build_sub_requirement_variables



# ==================================================

# Testing Framework

# ==================================================


# Solves a model and asserts it is feasible/optimal, returning the solver for value checks.
def solve(model):
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return solver


# Solves a model and returns raw CP-SAT status code for feasible/infeasible assertions.
def solve_status(model):
    solver = cp_model.CpSolver()
    return solver.Solve(model)


# Builds take[(course, semester)] boolean decision variables used across tests.
def make_take(model, courses, semester_range):
    return {
        (course, sem): model.new_bool_var(f"take_{course.replace(' ', '_')}_{sem}")
        for course in courses
        for sem in semester_range
    }


# Lightweight catalog record stub that provides only fields used by constraints.
class DummyCourse:
    def __init__(self, prereq_tree=None, cross_list=None, offered_terms=None, credit_hours=3):
        self.prereq_tree = prereq_tree
        self.cross_list = cross_list or []
        self.offered_terms = offered_terms or []
        self.credit_hours = credit_hours


def _expand_composite_requirements_for_test(requirements):
    expanded = []
    composite_meta = {}

    for req in requirements:
        req_type = req.get("requirement_type")
        req_id = str(req.get("id", "")).strip()

        if req_type != "composite":
            expanded.append(req)
            continue

        sub_requirement_ids = []
        for idx, sub_req in enumerate(req.get("sub_requirements", [])):
            if not isinstance(sub_req, dict):
                continue
            sub_id_raw = str(sub_req.get("id", f"sub_{idx + 1}")).strip() or f"sub_{idx + 1}"
            sub_id = f"{req_id}::{sub_id_raw}"

            sub_req_copy = dict(sub_req)
            sub_req_copy["id"] = sub_id
            sub_req_copy["is_subrequirement"] = True
            expanded.append(sub_req_copy)
            sub_requirement_ids.append(sub_id)

        composite_meta[req_id] = {
            "sub_requirement_ids": sub_requirement_ids,
            "min_count": int(req.get("min_count", len(sub_requirement_ids))),
            "constraints": req.get("constraints", {}),
            "sub_requirements": req.get("sub_requirements", []),
        }

    return expanded, composite_meta


# Verifies a single-course prerequisite is satisfied only when taken in an earlier semester.
def test_prereq_satisfied_bool_single_course_requires_previous_semester_take():
    model = cp_model.CpModel()
    courses = {"COMP 140"}
    semester_range = [0, 1]
    take = make_take(model, courses, semester_range)

    model.add(take[("COMP 140", 0)] == 1)
    satisfied = cons._prereq_satisfied_bool(
        {"course": "COMP 140"},
        1,
        model,
        take,
        set(),
        semester_range,
    )
    model.add(satisfied == 1)

    assert solve_status(model) in (cp_model.OPTIMAL, cp_model.FEASIBLE)

# ==================================================

# Test Course Requirement Constraints

# ==================================================

# composite_meta[req_id] = {
#     "sub_requirement_ids": sub_requirement_ids,
#     "min_count": int(req.get("min_count", len(sub_requirement_ids))),
#     "constraints": req.get("constraints", {}),
#     "sub_requirements": req.get("sub_requirements", []),
# }

# Covers required, choose_n, choose_group, and composite subject/subgroup requirement rules.
def test_add_course_requirement_constraints_required_choose_n_choose_group_and_composite():
    model = cp_model.CpModel()

    requirements = [
        {
            "id": "CS:core",
            "requirement_type": "required_courses",
            "courses": ["COMP 140"],
        },
        {
            "id": "CS:electives",
            "requirement_type": "choose_n",
            "courses": ["COMP 321", "COMP 322"],
            "min_count": 1,
            "max_count": 1,
            "constraints": {"max_from_group": [{"courses": ["COMP 321", "COMP 322"], "max_count": 1}]},
        },
        {
            "id": "CS:track",
            "requirement_type": "choose_group",
            "options": [["MATH 212"], ["MATH 222", "MATH 232"]],
            "min_count": 1,
            "max_count": 1,
        },
        {
            "id": "CS:stats",
            "requirement_type": "choose_n",
            "courses": ["STAT 315", "DSCI 301"],
            "min_count": 1,
            "max_count": 1,
        },
       
        {
            "id": "cs_electives",
            "requirement_type": "composite",
            "min_count": 3,
            "sub_requirements": [
                {
                    "id": "elective_1",
                    "requirement_type": "choose_n",
                    "courses": ["COMP 409", "COMP 414", "COMP 480", "COMP 585"],
                    "min_count": 1,
                    "max_count": 1,
                },
                {
                    "id": "elective_2",
                    "requirement_type": "choose_n",
                    "courses": ["PSYC 430", "PSYC 468"],
                    "min_count": 1,
                    "max_count": 1,
                },
                {
                    "id": "elective_3",
                    "requirement_type": "choose_n",
                    "courses": ["COMP 459", "COMP 631"],
                    "min_count": 1,
                    "max_count": 1,
                },
                {
                    "id": "elective_4",
                    "requirement_type": "choose_n",
                    "courses": ["COMP 447", "ELEC 447", "COMP 484"],
                    "min_count": 1,
                    "max_count": 1,
                },
                {
                    "id": "elective_5",
                    "requirement_type": "choose_n",
                    "courses": ["COMP 442", "COMP 450", "ELEC 450", "MECH 450", "COMP 462"],
                    "min_count": 1,
                    "max_count": 1,
                },
            ],
        },
    ]

    expanded_requirements, composite_meta = _expand_composite_requirements_for_test(requirements)

    req_available = {
        "CS:core": ["COMP 140"],
        "CS:electives": ["COMP 321", "COMP 322"],
        "CS:track": ["MATH 212", "MATH 222", "MATH 232"],
        "CS:stats": ["STAT 315", "DSCI 301"],
        
        "cs_electives::elective_1": ["COMP 409", "COMP 414", "COMP 480", "COMP 585"],
        "cs_electives::elective_2": ["PSYC 430", "PSYC 468"],
        "cs_electives::elective_3": ["COMP 459", "COMP 631"],
        "cs_electives::elective_4": ["COMP 447", "ELEC 447", "COMP 484"],
        "cs_electives::elective_5": ["COMP 442", "COMP 450", "ELEC 450", "MECH 450", "COMP 462"],
    }

    use_for_req = {}
    for req_id, courses in req_available.items():
        for course in courses:
            use_for_req[(course, req_id)] = model.new_bool_var(f"use_{course.replace(' ', '_')}_{req_id.replace(':', '_')}")

    subgroup_satisfied = _build_sub_requirement_variables(model, composite_meta, req_available, use_for_req)

    cons._add_course_requirement_constraints(
        model,
        expanded_requirements,
        req_available,
        use_for_req,
        composite_meta,
        subgroup_satisfied,
    )

   
    model.add(use_for_req[("COMP 409", "cs_electives::elective_1")] == 1)
    model.add(use_for_req[("PSYC 430", "cs_electives::elective_2")] == 1)
    model.add(use_for_req[("COMP 459", "cs_electives::elective_3")] == 0)
    model.add(use_for_req[("COMP 631", "cs_electives::elective_3")] == 0)
    model.add(use_for_req[("COMP 447", "cs_electives::elective_4")] == 1)

    # Current composite modeling enforces each sub-requirement choose_n(min_count=1),
    # so forcing one subgroup to have no selected course makes the model infeasible.
    solve(model)


# Ensures distribution subject-cap logic can make an over-concentrated plan infeasible.
def test_add_distribution_constraints_detects_subject_cap_infeasible():
    model = cp_model.CpModel()
    semester_range = [0]
    all_courses = {"COMP 101", "COMP 102", "COMP 103"}
    take = make_take(model, all_courses, semester_range)

    for course in all_courses:
        model.add(take[(course, 0)] == 1)

    distribution_courses = {
        "Distribution Group I": ["COMP 101", "COMP 102", "COMP 103"],
        "Distribution Group II": [],
        "Distribution Group III": [],
    }

    cons._add_distribution_constraints(
        model,
        take,
        semester_range,
        all_courses,
        set(),
        distribution_courses,
    )

    assert solve_status(model) == cp_model.INFEASIBLE


# Ensures at least one diversity course is required when none is already completed.
def test_add_diversity_constraints_requires_one_when_none_completed():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"ANTH 201"}
    take = make_take(model, all_courses, semester_range)

    for sem in semester_range:
        model.add(take[("ANTH 201", sem)] == 0)

    cons._add_diversity_constraints(
        model,
        take,
        semester_range,
        all_courses,
        set(),
        ["ANTH 201"],
    )

    assert solve_status(model) == cp_model.INFEASIBLE


# Checks FWIS can only be in freshman terms and exactly one FWIS is required when missing.
def test_add_fwis_constraints_blocks_non_freshman_and_requires_exactly_one():
    model = cp_model.CpModel()
    semester_range = [0, 1, 2]
    all_courses = {"FWIS 100"}
    take = make_take(model, all_courses, semester_range)

    model.add(take[("FWIS 100", 0)] == 0)
    model.add(take[("FWIS 100", 1)] == 0)
    model.add(take[("FWIS 100", 2)] == 1)

    cons._add_fwis_constraints(
        model,
        take,
        semester_range,
        0,
        all_courses,
        set(),
        ["FWIS 100"],
    )

    assert solve_status(model) == cp_model.INFEASIBLE


# Ensures LPAP requires exactly one planned course when no LPAP is completed yet.
def test_add_lpap_constraints_requires_exactly_one_when_none_completed():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"LPAP 101"}
    take = make_take(model, all_courses, semester_range)

    model.add(take[("LPAP 101", 0)] == 0)
    model.add(take[("LPAP 101", 1)] == 0)

    cons._add_lpap_constraints(
        model,
        take,
        semester_range,
        all_courses,
        set(),
        ["LPAP 101"],
    )

    assert solve_status(model) == cp_model.INFEASIBLE


# Confirms the wrapper adds all graduation sub-constraints and they jointly affect feasibility.
def test_add_general_graduation_constraints_combines_sub_constraints():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"HIST 101", "FWIS 100", "LPAP 101", "COMP 101", "COMP 102", "COMP 103"}
    take = make_take(model, all_courses, semester_range)

    distribution_courses = {
        "Distribution Group I": ["COMP 101", "COMP 102", "COMP 103"],
        "Distribution Group II": [],
        "Distribution Group III": [],
    }

    for sem in semester_range:
        model.add(take[("HIST 101", sem)] == 0)

    cons._add_general_graduation_constraints(
        model,
        take,
        semester_range,
        0,
        all_courses,
        set(),
        distribution_courses,
        ["HIST 101"],
        ["FWIS 100"],
        ["LPAP 101"],
    )

    assert solve_status(model) == cp_model.INFEASIBLE


# Verifies cross-listed courses are mutually exclusive across the planning horizon.
def test_add_cross_list_constraints_allows_only_one_across_cross_list_group():
    model = cp_model.CpModel()
    semester_range = [0]
    all_courses = {"COMP 310", "ELEC 310"}
    take = make_take(model, all_courses, semester_range)
    catalog = {
        "COMP 310": DummyCourse(cross_list=["ELEC 310"]),
        "ELEC 310": DummyCourse(cross_list=["COMP 310"]),
    }

    model.add(take[("COMP 310", 0)] == 1)
    model.add(take[("ELEC 310", 0)] == 1)

    cons._add_cross_list_constraints(model, catalog, all_courses, set(), take, semester_range)
    assert solve_status(model) == cp_model.INFEASIBLE


# Ensures a course cannot be planned twice and completed courses cannot be retaken.
def test_add_single_take_constraints_prevents_retake_and_completed_replan():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"COMP 140"}
    completed = {"COMP 140"}
    take = make_take(model, all_courses, semester_range)

    model.add(take[("COMP 140", 0)] == 1)

    cons._add_single_take_constraints(model, all_courses, completed, take, semester_range)
    assert solve_status(model) == cp_model.INFEASIBLE


# Verifies a scheduled course is pinned to the requested local semester index.
def test_add_scheduled_course_constraints_sets_exact_semester():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    take = make_take(model, {"COMP 182"}, semester_range)

    cons._add_scheduled_course_constraints(
        model,
        {"COMP 182": 1},
        set(),
        take,
        0,
        semester_range,
    )

    model.add(take[("COMP 182", 1)] == 1)
    solve(model)


# Verifies out-of-horizon scheduled semester indices raise a ValueError.
def test_add_scheduled_course_constraints_raises_on_out_of_range_semester():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    take = make_take(model, {"COMP 182"}, semester_range)

    try:
        cons._add_scheduled_course_constraints(
            model,
            {"COMP 182": 4},
            set(),
            take,
            0,
            semester_range,
        )
        assert False, "Expected ValueError for out-of-range scheduled semester"
    except ValueError:
        pass


# Ensures one course cannot satisfy two requirements inside the same degree namespace.
def test_add_requirement_overlap_constraints_prevents_double_count_within_degree():
    model = cp_model.CpModel()
    req_available = {
        "CS:core": ["COMP 140"],
        "CS:math": ["COMP 140"],
        "MATH:elective": ["COMP 140"],
    }
    use_for_req = {
        ("COMP 140", "CS:core"): model.new_bool_var("use_core"),
        ("COMP 140", "CS:math"): model.new_bool_var("use_math"),
        ("COMP 140", "MATH:elective"): model.new_bool_var("use_math_degree"),
    }

    cons._add_requirement_overlap_constraints(model, req_available, use_for_req)
    model.add(use_for_req[("COMP 140", "CS:core")] == 1)
    model.add(use_for_req[("COMP 140", "CS:math")] == 1)

    assert solve_status(model) == cp_model.INFEASIBLE


# Verifies prerequisite constraints block taking a dependent course before its prerequisite.
def test_add_prerequisite_constraints_blocks_course_before_prereq():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"COMP 182", "COMP 140"}
    take = make_take(model, all_courses, semester_range)
    catalog = {
        "COMP 182": DummyCourse(prereq_tree={"course": "COMP 140"}),
        "COMP 140": DummyCourse(prereq_tree=None),
    }

    model.add(take[("COMP 182", 0)] == 1)
    model.add(take[("COMP 140", 0)] == 0)

    cons._add_prerequisite_constraints(model, catalog, all_courses, take, set(), semester_range)
    assert solve_status(model) == cp_model.INFEASIBLE


# Ensures course offerings by term are enforced (e.g., Fall-only cannot be taken in Spring).
def test_add_term_offering_constraints_respects_offered_terms():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"COMP 310"}
    take = make_take(model, all_courses, semester_range)
    catalog = {"COMP 310": DummyCourse(offered_terms=["Fall"]) }

    model.add(take[("COMP 310", 1)] == 1)

    cons._add_term_offering_constraints(model, catalog, all_courses, take, semester_range, 0)
    assert solve_status(model) == cp_model.INFEASIBLE


# Verifies total-credit floor and per-semester credit cap are both enforced.
def test_add_credit_constraints_enforces_total_and_semester_caps():
    model = cp_model.CpModel()
    semester_range = [0]
    all_courses = {"BIG 500"}
    take = make_take(model, all_courses, semester_range)
    catalog = {"DONE 499": DummyCourse(credit_hours=119)}
    # _add_credit_constraints now works in half-credit units (scale=2).
    # 20 credit hours => 40 units, which exceeds the 18-credit cap (36 units).
    course_to_credits = {"BIG 500": 40}

    model.add(take[("BIG 500", 0)] == 1)

    _, completed_credits, semester_credit_vars = cons._add_credit_constraints(
        model,
        catalog,
        all_courses,
        {"DONE 499"},
        take,
        semester_range,
        course_to_credits,
    )

    assert completed_credits == 238
    assert 0 in semester_credit_vars
    assert solve_status(model) == cp_model.INFEASIBLE


# Ensures preferred courses must be included and avoided courses must be excluded.
def test_add_preference_constraints_enforces_preferred_and_avoid_lists():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"COMP 321", "COMP 322"}
    take = make_take(model, all_courses, semester_range)

    for sem in semester_range:
        model.add(take[("COMP 321", sem)] == 0)
    model.add(take[("COMP 322", 0)] == 1)

    cons._add_preference_constraints(
        model,
        preferred={"COMP 321"},
        avoid={"COMP 322"},
        all_courses=all_courses,
        completed=set(),
        take=take,
        semester_range=semester_range,
    )

    assert solve_status(model) == cp_model.INFEASIBLE


# Verifies compact semester monotonicity: using a later term implies earlier term usage.
def test_add_compact_semester_constraints_disallows_gaps():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"COMP 140"}
    take = make_take(model, all_courses, semester_range)

    model.add(take[("COMP 140", 0)] == 0)
    model.add(take[("COMP 140", 1)] == 1)

    semester_used = cons._add_compact_semester_constraints(model, all_courses, take, semester_range)
    assert 0 in semester_used and 1 in semester_used

    # If a later semester is used, an earlier one cannot be unused.
    model.add(semester_used[0] == 0)
    assert solve_status(model) == cp_model.INFEASIBLE