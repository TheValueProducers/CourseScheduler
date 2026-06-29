from ortools.sat.python import cp_model
from typing import Any, Dict, List, Tuple

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from optimizer import variables as vars_module


def _expand_composite_requirements_for_test(
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


# Lightweight catalog record stub that provides only fields used by variables.
class DummyCourse:
    def __init__(self):
        self.code = "COMP 101"  # normalized code like "COMP 101"
        self.subject = "COMP"  # subject like "COMP", "MATH"
        self.course_number = 101  # numerical part (e.g., 101, 310, 500, etc.)
        self.long_title = None
        self.offered_terms = set()
        self.credit_hours = 3
        self.distribution = None
        self.analyzing_diversity = False
        self.cross_list = []
        self.prereq_tree = None

# ==================================================

# Dummy Courses

# ==================================================


#COMP 215
comp_215 = DummyCourse()
comp_215.code = "COMP 215"
comp_215.subject = "COMP"
comp_215.course_number = 215
comp_215.credit_hours = 4
comp_215.long_title = "INTRODUCTION TO PROGRAM DESIGN"
comp_215.offered_terms = {"Fall", "Spring"}
comp_215.distribution = None
comp_215.analyzing_diversity = False
comp_215.cross_list = []
comp_215.prereq_tree = {
    "course": "COMP 182"
}

#COMP 341

comp_341 = DummyCourse()
comp_341.code = "COMP 341"
comp_341.subject = "COMP"
comp_341.course_number = 341
comp_341.credit_hours = 3
comp_341.long_title = "PRACTICAL MACHINE LEARNING FOR REAL WORLD APPLICATIONS"
comp_341.offered_terms = {"Fall"}
comp_341.distribution = None
comp_341.analyzing_diversity = False
comp_341.cross_list = []
comp_341.prereq_tree = {
    "type": "AND",
    "conditions": [
        {
            "course": "COMP 182"
        },
        {
            "type": "OR",
            "conditions": [
                {
                    "course": "MATH 102"
                },
                {
                    "course": "MATH 106"
                }
            ]
        }
    ]
}

#COMP 568

comp_568 = DummyCourse()
comp_568.code = "COMP 568"
comp_568.subject = "COMP"
comp_568.course_number = 568
comp_568.credit_hours = 3

comp_568.long_title = "DEEP LEARNING SYSTEMS DESIGN AND OPTIMIZATION"

comp_568.offered_terms = {"Spring"}

comp_568.distribution = None

comp_568.analyzing_diversity = False

comp_568.cross_list = []

comp_568.prereq_tree = None

# COMP 646
comp_646 = DummyCourse()
comp_646.code = "COMP 646"
comp_646.subject = "COMP"
comp_646.course_number = 646
comp_646.credit_hours = 3

comp_646.long_title = "DEEP LEARNING FOR VISION AND LANGUAGE"

comp_646.offered_terms = {"Spring"}

comp_646.distribution = None

comp_646.analyzing_diversity = False

comp_646.cross_list = []

comp_646.prereq_tree = None


#STAT 310
stat_310 = DummyCourse()
stat_310.code = "STAT 310"
stat_310.subject = "STAT"
stat_310.course_number = 310
stat_310.credit_hours = 3

stat_310.long_title = "PROBABILITY AND STATISTICS"
stat_310.offered_terms = {"Fall", "Spring"}
stat_310.distribution = "Distribution Group III"
stat_310.analyzing_diversity = False
stat_310.cross_list = ["ECON 307"]
stat_310.prereq_tree = {
    "type": "OR",
    "conditions": [
        {
            "course": "MATH 102"
        },
        {
            "course": "MATH 106"
        }
    ]
}

# MATH 101
math_101 = DummyCourse()
math_101.code = "MATH 101"
math_101.subject = "MATH"
math_101.course_number = 101
math_101.long_title = "SINGLE VARIABLE CALCULUS I"
math_101.offered_terms = {"Fall", "Spring"}
math_101.credit_hours = 3
math_101.distribution = "Distribution Group III"
math_101.analyzing_diversity = False
math_101.cross_list = []
math_101.prereq_tree = None

#MATH 102
math_102 = DummyCourse()
math_102.code = "MATH 102"
math_102.subject = "MATH"
math_102.course_number = 102
math_102.long_title = "SINGLE VARIABLE CALCULUS II"
math_102.offered_terms = {"Fall", "Spring"}
math_102.credit_hours = 3
math_102.distribution = "Distribution Group III"
math_102.analyzing_diversity = False
math_102.cross_list = []
math_102.prereq_tree = None

# STAT 410
stat_410 = DummyCourse()
stat_410.code = "STAT 410"
stat_410.subject = "STAT"
stat_410.course_number = 410
stat_410.long_title = "LINEAR REGRESSION"
stat_410.offered_terms = {"Fall", "Spring"}
stat_410.credit_hours = 4
stat_410.distribution = None
stat_410.analyzing_diversity = False
stat_410.cross_list = []
stat_410.prereq_tree = {
    "type": "OR",
    "conditions": [
        {"course": "STAT 310"},
        {"course": "STAT 311"},
        {"course": "STAT 312"},
        {"course": "ECON 307"},
        {"course": "STAT 315"},
        {"course": "DSCI 301"},
    ],
}

# ==================================================

# Dummy degree

# ==================================================


bs_artificial_intelligence_degree_requirement: List[Dict[str, Any]] = [
    {
        "id": "calculus_1",
        "requirement_type": "choose_n",
        "courses": ["MATH 101", "MATH 105"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "calculus_2",
        "requirement_type": "choose_n",
        "courses": ["MATH 102", "MATH 106"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "linear_algebra",
        "requirement_type": "choose_n",
        "courses": ["CMOR 302", "CMOR 303", "MATH 221", "MATH 354", "MATH 355"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "statistics",
        "requirement_type": "choose_n",
        "courses": ["STAT 315", "DSCI 301"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "core_cs",
        "requirement_type": "required_courses",
        "courses": ["COMP 140", "COMP 182", "COMP 215", "COMP 222", "COMP 282"],
        "min_count": 5,
        "max_count": 5,
    },
    {
        "id": "core_ai",
        "requirement_type": "required_courses",
        "courses": ["COMP 329", "COMP 345", "COMP 346", "COMP 348", "COMP 456", "COMP 457", "PHIL 108", "PSYC 203"],
        "min_count": 8,
        "max_count": 8,
    },
    {
        "id": "ai_electives",
        "requirement_type": "composite",
        "min_count": 3,

      "sub_requirements": [
        {
            "id": "ai_electives_theory",
            "requirement_type": "choose_n",
            "courses": ["COMP 409", "COMP 414", "COMP 480", "COMP 585"],
            "min_count": 0,
            "max_count": 1,
        },
        {
            "id": "ai_electives_cognitive",
            "requirement_type": "choose_n",
            "courses": ["PSYC 430", "PSYC 468"],
            "min_count": 0,
            "max_count": 1,
        },
        {
            "id": "ai_electives_knowledge",
            "requirement_type": "choose_n",
            "courses": ["COMP 459", "COMP 631"],
            "min_count": 0,
            "max_count": 1,
        },
        {
            "id": "ai_electives_perception",
            "requirement_type": "choose_n",
            "courses": ["COMP 447", "ELEC 447", "COMP 484"],
            "min_count": 0,
            "max_count": 1,
        },
        {
            "id": "ai_electives_robotics",
            "requirement_type": "choose_n",
            "courses": ["COMP 442", "COMP 450", "ELEC 450", "MECH 450", "COMP 462"],
            "min_count": 0,
            "max_count": 1,
        },
      ]  
    }

]


# ==================================================

# Tests for _create_take_variables

# ==================================================


# Verifies take variables are created for each (course, semester) pair.
def test_create_take_variables_creates_bool_vars_for_all_courses_and_semesters():
    model = cp_model.CpModel()
    courses = {"COMP 140", "COMP 182", "MATH 212"}
    semester_range = [0, 1, 2]

    take = vars_module._create_take_variables(model, courses, semester_range)

    # Check all (course, sem) pairs exist
    for course in courses:
        for sem in semester_range:
            assert (course, sem) in take
            assert isinstance(take[(course, sem)], cp_model.IntVar)

    # Verify total count is correct
    assert len(take) == len(courses) * len(semester_range)


# Ensures take variables are boolean (0 or 1 only) when solved.
def test_create_take_variables_enforces_bool_semantics():
    model = cp_model.CpModel()
    courses = {"COMP 140"}
    semester_range = [0, 1]

    take = vars_module._create_take_variables(model, courses, semester_range)

    model.add(take[("COMP 140", 0)] >= 0)
    solver = solve(model)

    # Check that values are 0 or 1
    for (course, sem), var in take.items():
        val = solver.Value(var)
        assert val in (0, 1)


# ==================================================

# Tests for _build_requirement_usage_variables

# ==================================================


# Verifies simple requirement with explicit courses creates correct available list and use vars.
# Verifies simple requirement with explicit courses creates correct available list and use vars.
def test_build_requirement_usage_variables_simple_courses_requirement():
    model = cp_model.CpModel()
    semester_range = [0, 1]

    all_courses = {

        "COMP 215",

        "COMP 341",

        "COMP 568",

        "COMP 646",

        "STAT 310",


    }
    completed = set()

    catalog = {

        "COMP 215": comp_215,

        "COMP 341": comp_341,

        "COMP 568": comp_568,

        "COMP 646": comp_646,

        "STAT 310": stat_310,

        "MATH 101": math_101,

        "MATH 102": math_102,

        "STAT 410": stat_410,

    }

    take = {
        (course, sem): model.new_bool_var(f"take_{course.replace(' ', '_')}_{sem}")
        for course in all_courses
        for sem in semester_range
    }

    expanded_requirements = [
        {
            "id": "CS:core",
            "courses": ["COMP 215", "COMP 341"],
        },
        {
            "id": "CS:electives",
            "courses": ["COMP 568", "COMP 646"],
        },
        {
            "id": "stats:core",
            "courses": ["STAT 310", "STAT 410"],
        },
        {
            "id": "CS:math",
            "courses": ["MATH 101", "MATH 102"],
        },
    ]

    req_available, use_for_req = vars_module._build_requirement_usage_variables(
        model,
        expanded_requirements,
        all_courses,
        completed,
        catalog,
        take,
        semester_range,
    )

    assert set(req_available["CS:core"]) == {"COMP 215", "COMP 341"}

    assert set(req_available["CS:electives"]) == {"COMP 568", "COMP 646"}

    assert set(req_available["stats:core"]) == {"STAT 310"}

    assert set(req_available["CS:math"]) == set()

    assert ("COMP 215", "CS:core") in use_for_req
    assert ("COMP 341", "CS:core") in use_for_req

    assert ("COMP 568", "CS:electives") in use_for_req
    assert ("COMP 646", "CS:electives") in use_for_req

    assert ("STAT 310", "stats:core") in use_for_req
    assert ("STAT 410", "stats:core") not in use_for_req

    assert ("MATH 101", "CS:math") not in use_for_req
    assert ("MATH 102", "CS:math") not in use_for_req

    expected_pairs = {
        ("COMP 215", "CS:core"),
        ("COMP 341", "CS:core"),
        ("COMP 568", "CS:electives"),
        ("COMP 646", "CS:electives"),
        ("STAT 310", "stats:core"),
    }

    assert set(use_for_req.keys()) == expected_pairs


# Ensures requirement usage variables for non-completed courses are bounded by take variables.
def test_build_requirement_usage_variables_use_var_bounded_by_take():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"COMP 140"}
    completed = set()
    catalog = {"COMP 140": DummyCourse()}

    take = {
        (course, sem): model.new_bool_var(f"take_{course.replace(' ', '_')}_{sem}")
        for course in all_courses
        for sem in semester_range
    }

    expanded_requirements = [{"id": "CS:core", "courses": ["COMP 140"]}]

    req_available, use_for_req = vars_module._build_requirement_usage_variables(
        model,
        expanded_requirements,
        all_courses,
        completed,
        catalog,
        take,
        semester_range,
    )

    # If use_var is 1, at least one take var must be 1
    model.add(use_for_req[("COMP 140", "CS:core")] == 1)
    model.add(take[("COMP 140", 0)] == 0)
    model.add(take[("COMP 140", 1)] == 0)

    assert solve_status(model) == cp_model.INFEASIBLE


# Verifies completed courses are included in available list without take constraint.
def test_build_requirement_usage_variables_includes_completed_courses():
    model = cp_model.CpModel()
    semester_range = [0, 1]
    all_courses = {"COMP 140"}
    completed = {"COMP 140"}
    catalog = {"COMP 140": DummyCourse()}

    take = {
        (course, sem): model.new_bool_var(f"take_{course.replace(' ', '_')}_{sem}")
        for course in all_courses
        for sem in semester_range
    }

    expanded_requirements = [{"id": "CS:core", "courses": ["COMP 140"]}]

    req_available, use_for_req = vars_module._build_requirement_usage_variables(
        model,
        expanded_requirements,
        all_courses,
        completed,
        catalog,
        take,
        semester_range,
    )

    assert "COMP 140" in req_available["CS:core"]
    assert ("COMP 140", "CS:core") in use_for_req


# ==================================================

# Tests for _build_requirement_usage_variables

# ==================================================

# Ensures filter-based requirements apply _course_matches_filter logic correctly.
def test_build_requirement_usage_variables_filter_requirement():
    model = cp_model.CpModel()
    semester_range = [0]
    all_courses = {"COMP 215", "COMP 341", "COMP 568", "COMP 646", "STAT 310"}
    completed = set()
    catalog = {
        "COMP 215": comp_215,
        "COMP 341": comp_341,
        "COMP 568": comp_568,
        "COMP 646": comp_646,
        "STAT 310": stat_310
    
    }

    take = {
        (course, sem): model.new_bool_var(f"take_{course.replace(' ', '_')}_{sem}")
        for course in all_courses
        for sem in semester_range
    }

    # Simple mock filter for courses with level >= 300
    expanded_requirements = [
        {
            "id": "CS:electives",
            "filters": {"min_level": 300, "subject": "COMP"},
            "constraints": {"allow_500_level": False, "allowed_600_level_courses": ["COMP 646"]},
        }
    ]

    req_available, use_for_req = vars_module._build_requirement_usage_variables(
        model,
        expanded_requirements,
        all_courses,
        completed,
        catalog,
        take,
        semester_range,
    )
    
    # Both courses are >= 300, so both should pass a basic filter check
    assert "CS:electives" in req_available

    # Testing each courses
    assert ("COMP 215", "CS:electives") not in use_for_req
    assert ("COMP 341", "CS:electives") in use_for_req
    assert ("COMP 568", "CS:electives") not in use_for_req
    assert ("COMP 646", "CS:electives") in use_for_req
    assert ("STAT 310", "CS:electives") not in use_for_req


    


# Verifies options-based requirements flatten and normalize course lists.
def test_build_requirement_usage_variables_options_requirement():
    model = cp_model.CpModel()
    semester_range = [0]
    all_courses = {"COMP 215", "COMP 341", "COMP 568", "COMP 646", "STAT 310"}
    completed = set()
    catalog = {
        "COMP 215": comp_215,
        "COMP 341": comp_341,
        "COMP 568": comp_568,
        "COMP 646": comp_646,
        "STAT 310": stat_310
    
    }

    take = {
        (course, sem): model.new_bool_var(f"take_{course.replace(' ', '_')}_{sem}")
        for course in all_courses
        for sem in semester_range
    }

    expanded_requirements = [
        {
            "id": "CS:choice",
            "options": [["COMP 341"], ["COMP 215", "COMP 568"]],
        }
    ]

    req_available, use_for_req = vars_module._build_requirement_usage_variables(
        model,
        expanded_requirements,
        all_courses,
        completed,
        catalog,
        take,
        semester_range,
    )

    assert "CS:choice" in req_available
    available_set = set(req_available["CS:choice"])
    assert available_set == {"COMP 341", "COMP 215", "COMP 568"}


# Ensures use_for_req variables correctly map all available courses to requirement IDs.
def test_build_requirement_usage_variables_use_for_req_coverage():
    model = cp_model.CpModel()
    semester_range = [0]
    all_courses = {"COMP 140", "COMP 182"}
    completed = set()
    catalog = {c: DummyCourse() for c in all_courses}

    take = {
        (course, sem): model.new_bool_var(f"take_{course.replace(' ', '_')}_{sem}")
        for course in all_courses
        for sem in semester_range
    }

    expanded_requirements = [
        {"id": "CS:core", "courses": ["COMP 140", "COMP 182"]}
    ]

    req_available, use_for_req = vars_module._build_requirement_usage_variables(
        model,
        expanded_requirements,
        all_courses,
        completed,
        catalog,
        take,
        semester_range,
    )

    for course in req_available["CS:core"]:
        assert (course, "CS:core") in use_for_req


# ==================================================

# Tests for _build_sub_requirement_variables

# ==================================================


# Verifies subgroup_satisfied variables are created for each (parent, sub) requirement pair.


# composite_meta[req_id] = {
#     "sub_requirement_ids": sub_requirement_ids,
#     "min_count": int(req.get("min_count", len(sub_requirement_ids))),
#     "constraints": req.get("constraints", {}),
#     "sub_requirements": req.get("sub_requirements", []),
# }

def test_build_sub_requirement_variables_creates_satisfaction_vars():
    model = cp_model.CpModel()

    composite_meta = {
        "MAJOR:parent": {
            "sub_requirement_ids": ["MAJOR:core1", "MAJOR:core2"],
        }
    }

    req_available = {
        "MAJOR:core1": ["COMP 409"],
        "MAJOR:core2": ["PSYC 430"],
    }

    use_for_req = {
        ("COMP 409", "MAJOR:core1"): model.new_bool_var("use_comp409_core1"),
        ("PSYC 430", "MAJOR:core2"): model.new_bool_var("use_psyc430_core2"),
    }

    subgroup_satisfied = vars_module._build_sub_requirement_variables(
        model,
        composite_meta,
        req_available,
        use_for_req,
    )

    assert ("MAJOR:parent", "MAJOR:core1") in subgroup_satisfied
    assert ("MAJOR:parent", "MAJOR:core2") in subgroup_satisfied


# Ensures subgroup_satisfied is 1 iff at least one course in that subgroup is used.
def test_build_sub_requirement_variables_satisfaction_iff_course_used():
    model = cp_model.CpModel()

    composite_meta = {
        "MAJOR:parent": {
            "sub_requirement_ids": ["MAJOR:core"],
        }
    }

    req_available = {
        "MAJOR:core": ["COMP 140", "COMP 182"],
    }

    use_for_req = {
        ("COMP 140", "MAJOR:core"): model.new_bool_var("use_comp140"),
        ("COMP 182", "MAJOR:core"): model.new_bool_var("use_comp182"),
    }

    subgroup_satisfied = vars_module._build_sub_requirement_variables(
        model,
        composite_meta,
        req_available,
        use_for_req,
    )

    # If subgroup_satisfied is 1, at least one course must be used
    model.add(subgroup_satisfied[("MAJOR:parent", "MAJOR:core")] == 1)
    model.add(use_for_req[("COMP 140", "MAJOR:core")] == 0)
    model.add(use_for_req[("COMP 182", "MAJOR:core")] == 0)

    assert solve_status(model) == cp_model.INFEASIBLE


# Verifies subgroup_satisfied is 0 iff no courses in that subgroup are used.
def test_build_sub_requirement_variables_unsatisfied_iff_no_courses_used():
    model = cp_model.CpModel()

    composite_meta = {
        "MAJOR:parent": {
            "sub_requirement_ids": ["MAJOR:core"],
        }
    }

    req_available = {
        "MAJOR:core": ["COMP 140"],
    }

    use_for_req = {
        ("COMP 140", "MAJOR:core"): model.new_bool_var("use_comp140"),
    }

    subgroup_satisfied = vars_module._build_sub_requirement_variables(
        model,
        composite_meta,
        req_available,
        use_for_req,
    )

    # If subgroup_satisfied is 0, no courses can be used
    model.add(subgroup_satisfied[("MAJOR:parent", "MAJOR:core")] == 0)
    model.add(use_for_req[("COMP 140", "MAJOR:core")] == 1)

    assert solve_status(model) == cp_model.INFEASIBLE


# Ensures empty subgroup_satisfied is set to 0 when no courses are available in subgroup.
def test_build_sub_requirement_variables_empty_subgroup_unsatisfiable():
    model = cp_model.CpModel()

    composite_meta = {
        "MAJOR:parent": {
            "sub_requirement_ids": ["MAJOR:core"],
        }
    }

    req_available = {
        "MAJOR:core": [],  # Empty subgroup
    }

    use_for_req = {}

    subgroup_satisfied = vars_module._build_sub_requirement_variables(
        model,
        composite_meta,
        req_available,
        use_for_req,
    )

    # Empty subgroup must be unsatisfied
    model.add(subgroup_satisfied[("MAJOR:parent", "MAJOR:core")] == 0)
    solve(model)


# Verifies multiple composite requirements create correct (parent, sub) satisfaction pairs.
def test_build_sub_requirement_variables_multiple_composites():
    model = cp_model.CpModel()

    composite_meta = {
        "CS:major": {
            "sub_requirement_ids": ["CS:core", "CS:electives"],
        },
        "MATH:major": {
            "sub_requirement_ids": ["MATH:algebra", "MATH:analysis"],
        },
    }

    req_available = {
        "CS:core": ["COMP 140"],
        "CS:electives": ["COMP 310"],
        "MATH:algebra": ["MATH 212"],
        "MATH:analysis": ["MATH 231"],
    }

    use_for_req = {
        ("COMP 140", "CS:core"): model.new_bool_var("u1"),
        ("COMP 310", "CS:electives"): model.new_bool_var("u2"),
        ("MATH 212", "MATH:algebra"): model.new_bool_var("u3"),
        ("MATH 231", "MATH:analysis"): model.new_bool_var("u4"),
    }

    subgroup_satisfied = vars_module._build_sub_requirement_variables(
        model,
        composite_meta,
        req_available,
        use_for_req,
    )

    # Verify all 4 pairs exist
    assert len(subgroup_satisfied) == 4
    assert ("CS:major", "CS:core") in subgroup_satisfied
    assert ("CS:major", "CS:electives") in subgroup_satisfied
    assert ("MATH:major", "MATH:algebra") in subgroup_satisfied
    assert ("MATH:major", "MATH:analysis") in subgroup_satisfied
