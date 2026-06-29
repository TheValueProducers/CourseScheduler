import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import services.schedule_service as svc
from optimizer.build_model import _expand_composite_requirements

# chosen_degree = ["bs_comp", "statistics_bs"]
# expanded_requirements = svc._selected_degree_requirements(chosen_degree)

# print("----Degree------")
# print(expanded_requirements)


bs_artificial_intelligence_degree_requirement: List[Dict[str, Any]] = [
    {
        "id": "calculus_1",
        "is_subrequirement": False,
        "requirement_type": "choose_n",
        "courses": ["MATH 101", "MATH 105"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "calculus_2",
        "is_subrequirement": False,
        "requirement_type": "choose_n",
        "courses": ["MATH 102", "MATH 106"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "linear_algebra",
        "is_subrequirement": False,
        "requirement_type": "choose_n",
        "courses": ["CMOR 302", "CMOR 303", "MATH 221", "MATH 354", "MATH 355"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "statistics",
        "is_subrequirement": False,
        "requirement_type": "choose_n",
        "courses": ["STAT 315", "DSCI 301"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "core_cs",
        "is_subrequirement": False,
        "requirement_type": "required_courses",
        "courses": ["COMP 140", "COMP 182", "COMP 215", "COMP 222", "COMP 282"],
        "min_count": 5,
        "max_count": 5,
    },
    {
        "id": "core_ai",
        "is_subrequirement": False,
        "requirement_type": "required_courses",
        "courses": ["COMP 329", "COMP 345", "COMP 346", "COMP 348", "COMP 456", "COMP 457", "PHIL 108", "PSYC 203"],
        "min_count": 8,
        "max_count": 8,
    },
    {
        "id": "ai_electives",
        "is_subrequirement": False,
        "requirement_type": "composite",
        "min_count": 3,

      "sub_requirements": [
        {
            "id": "ai_electives_theory",
            "is_subrequirement": True,
            "requirement_type": "choose_n",
            "courses": ["COMP 409", "COMP 414", "COMP 480", "COMP 585"],
            "min_count": 1,
            "max_count": 1,
        },
        {
            "id": "ai_electives_cognitive",
            "is_subrequirement": True,
            "requirement_type": "choose_n",
            "courses": ["PSYC 430", "PSYC 468"],
            "min_count": 1,
            "max_count": 1,
        },
        {
            "id": "ai_electives_knowledge",
            "is_subrequirement": True,
            "requirement_type": "choose_n",
            "courses": ["COMP 459", "COMP 631"],
            "min_count": 1,
            "max_count": 1,
        },
        {
            "id": "ai_electives_perception",
            "is_subrequirement": True,
            "requirement_type": "choose_n",
            "courses": ["COMP 447", "ELEC 447", "COMP 484"],
            "min_count": 1,
            "max_count": 1,
        },
        {
            "id": "ai_electives_robotics",
            "is_subrequirement": True,
            "requirement_type": "choose_n",
            "courses": ["COMP 442", "COMP 450", "ELEC 450", "MECH 450", "COMP 462"],
            "min_count": 1,
            "max_count": 1,
        },
      ]  
    }

]

expanded, composite_meta = _expand_composite_requirements(bs_artificial_intelligence_degree_requirement)

print("-----Expanded------")
print(expanded)

print("-----Composite Meta-------")
print(composite_meta)


# degree_requirements = svc._selected_degree_requirements(["bs_comp", "statistics_bs"])
# print(degree_requirements)



