from __future__ import annotations

from typing import Any, Dict, List


PROGRAM_LABEL_OVERRIDES: Dict[str, str] = {
    "ba_comp": "Bachelor of Arts in Computer Science",
    "bs_comp": "Bachelor of Science in Computer Science",
    "data_science_minor": "Data Science Minor",
    "statistics_ba": "Bachelor of Arts in Statistics",
    "statistics_bs": "Bachelor of Science in Statistics",
    "statistics_minor_track_a": "Statistics Minor Track A",
    "statistics_minor_track_b": "Statistics Minor Track B",
    "cmor_bs_algorithms": "CMOR BS - Algorithms",
    "cmor_bs_data_science": "CMOR BS - Data Science",
    "cmor_bs_financial_engineering": "CMOR BS - Financial Engineering",
    "cmor_bs_foundations": "CMOR BS - Foundations",
    "cmor_bs_supply_chain": "CMOR BS - Supply Chain",
    "cmor_bs_breadth": "CMOR BS - Breadth",
    "cmor_ba_data_science": "CMOR BA - Data Science",
    "cmor_ba_financial_engineering": "CMOR BA - Financial Engineering",
    "cmor_ba_supply_chain": "CMOR BA - Supply Chain",
    "cmor_ba_breadth": "CMOR BA - Breadth",
}


bs_comp_degree_requirement: List[Dict[str, Any]] = [
	{
		"id": "required_core",
		"requirement_type": "required_courses",
		"courses": [
			"COMP 140",
			"COMP 182",
			"COMP 215",
			"COMP 222",
			"COMP 301",
			"COMP 312",
			"COMP 318",
			"COMP 321",
			"COMP 382",
		],
		"min_count": 9,
        "max_count": 9,
		
	},
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
		"id": "multivariable_calculus",
		"requirement_type": "choose_n",
		"courses": ["MATH 212", "MATH 222", "MATH 232"],
		"min_count": 1,
		"max_count": 1,
	},
	{
		"id": "probability_statistics",
		"requirement_type": "choose_n",
		"courses": ["ELEC 303", "STAT 310", "STAT 311", "STAT 312", "STAT 315", "DSCI 301"],
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
		"id": "design_requirement",
		"requirement_type": "choose_n",
		"courses": ["COMP 402", "COMP 410", "COMP 413", "COMP 416", "COMP 460", "COMP 461"],
		"min_count": 1,
		"max_count": 1,
	},
	{
		"id": "systems",
		"requirement_type": "choose_n",
		"courses": ["COMP 412", "COMP 421", "COMP 422", "COMP 427", "COMP 429", "COMP 432", "COMP 436", "COMP 458"],
		"min_count": 1,
		"max_count": 1,
	},
	{
		"id": "application_domains",
		"requirement_type": "choose_n",
		"courses": ["COMP 418", "COMP 431", "COMP 440", "COMP 442", "COMP 447", "COMP 450", "COMP 459", "COMP 462", "COMP 471", "COMP 484"],
		"min_count": 1,
		"max_count": 1,
	},
	{
		"id": "theory",
		"requirement_type": "choose_n",
		"courses": ["COMP 409", "COMP 411", "COMP 414", "COMP 423", "COMP 448", "COMP 463", "COMP 475", "COMP 480", "COMP 481"],
		"min_count": 1,
		"max_count": 1,
	},
	{
		"id": "comp_electives",
		"requirement_type": "choose_n",
		"filters": {"subject": "COMP", "min_level": 300},
		"min_count": 2,
		"constraints": {
			"max_from_group": [{"courses": ["COMP 390", "COMP 490", "COMP 491"], "max_count": 1}],
			"allowed_600_level_courses": ["COMP 631", "COMP 646"],
			"allow_500_level": True,
		},
	},
]

ba_comp_degree_requirement: List[Dict[str, Any]] = [
	{
		"id": "required_core",
		"requirement_type": "required_courses",
		"courses": [
			"COMP 140",
			"COMP 182",
			"COMP 215",
			"COMP 222",
			"COMP 301",
			"COMP 312",
			"COMP 318",
			"COMP 321",
			"COMP 382",
		],
		"min_count": 9,
		"max_count": 9,
	},
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
		"id": "multivariable_calculus",
		"requirement_type": "choose_n",
		"courses": ["MATH 212", "MATH 222", "MATH 232"],
		"min_count": 1,
		"max_count": 1,
	},
	{
		"id": "probability_statistics",
		"requirement_type": "choose_n",
		"courses": ["ELEC 303", "STAT 310", "STAT 311", "STAT 312", "STAT 315", "DSCI 301"],
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
		"id": "design_requirement",
		"requirement_type": "choose_n",
		"courses": ["COMP 402", "COMP 410", "COMP 413", "COMP 416", "COMP 460", "COMP 461"],
		"min_count": 1,
		"max_count": 1,
	},
	{
		"id": "comp_electives",
		"requirement_type": "choose_n",
		"filters": {"subject": "COMP", "min_level": 300},
		"min_count": 2,
		"constraints": {
			"max_from_group": [{"courses": ["COMP 390", "COMP 490", "COMP 491"], "max_count": 1}],
			"allowed_600_level_courses": ["COMP 631", "COMP 646"],
			"allow_500_level": True,
		},
	},
]

data_science_minor_requirement: List[Dict[str, Any]] = [
    {
        "id": "dsci_minor_prerequisite",
        "requirement_type": "choose_n",
        "courses": ["DSCI 101", "COMP 140"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "dsci_minor_statistics",
        "requirement_type": "choose_n",
        "courses": [
            "BIOE 439",
            "BUSI 395",
            "DSCI 301",
            "STAT 315",
            "ELEC 303",
            "PSYC 339",
            "SOCI 382",
            "SOSC 302",
            "STAT 280",
            "STAT 305",
            "STAT 310",
            "ECON 307",
            "STAT 311",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "dsci_minor_big_data",
        "requirement_type": "choose_n",
        "courses": ["DSCI 302", "COMP 330", "COMP 430"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "dsci_minor_machine_learning",
        "requirement_type": "choose_n",
        "courses": [
            "CMOR 438",
            "COMP 341",
            "COMP 540",
            "DSCI 303",
            "ELEC 378",
            "ELEC 478",
            "STAT 413",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "dsci_minor_ethics",
        "requirement_type": "choose_n",
        "courses": ["DSCI 305", "COMP 301"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "dsci_minor_elective",
        "requirement_type": "choose_n",
        "courses": [
            "ASTR 408",
            "BIOS 338",
            "CEVE 427",
            "MECH 427",
            "CMOR 303",
            "CMOR 442",
            "COMP 340",
            "COMP 447",
            "ELEC 447",
            "COMP 480",
            "DSCI 304",
            "ECON 310",
            "STAT 376",
            "ECON 418",
            "EEPS 450",
            "EEPS 451",
            "ELEC 431",
            "ELEC 439",
            "ELEC 440",
            "COMP 440",
            "ELEC 483",
            "ELEC 498",
            "COMP 498",
            "MECH 498",
            "LING 430",
            "MDHM 359",
            "PSYC 439",
            "SMGT 431",
            "SMGT 440",
            "SOCI 460",
            "SOCI 483",
            "STAT 405",
            "STAT 410",
            "STAT 411",
            "STAT 419",
            "STAT 421",
            "STAT 423",
            "STAT 425",
            "STAT 449",
            "STAT 453",
            "STAT 482",
            "STAT 486",
            "STAT 487",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "dsci_minor_capstone",
        "requirement_type": "choose_n",
        "courses": ["DSCI 435", "COMP 449"],
        "min_count": 1,
        "max_count": 1,
    },
]

statistics_ba_degree_requirement: List[Dict[str, Any]] = [
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

        "id": "multivariable_calculus",

        "requirement_type": "choose_group",

        "options": [

            ["MATH 212"],

            ["MATH 221", "MATH 222"],

            ["MATH 232"],

        ],

        "min_count": 1,

        "max_count": 1,

    },
    {
        "id": "linear_algebra",
        "requirement_type": "choose_n",
        "courses": [
            "CMOR 302",
            "CMOR 303",
            "MATH 355",
            "MATH 354",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "statistical_computation",
        "requirement_type": "required_courses",
        "courses": ["STAT 405"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "basic_computing",
        "requirement_type": "choose_n",
        "courses": [
            "CMOR 220",
            "COMP 140",
            "COMP 182",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "advanced_computing",
        "requirement_type": "choose_n",
        "courses": [
            "CMOR 360",
            "CMOR 422",
            "CMOR 441",
            "CMOR 520",
            "COMP 215",
            "COMP 322",
            "ELEC 323",
            "COMP 330",
            "COMP 382",
            "DSCI 302",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "probability_statistics",
        "requirement_type": "choose_n",
        "courses": [
            "STAT 310",
            "ECON 307",
            "STAT 311",
            "STAT 315",
            "DSCI 301",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "linear_regression",
        "requirement_type": "required_courses",
        "courses": ["STAT 410"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "stat_electives",
        "requirement_type": "choose_n",
        "filters": {
            "subject": "STAT",
            "min_level": 300,
        },
        "min_count": 6,
        "constraints": {
            "excluded_courses": [
                "STAT 305",
                "STAT 310",
                "STAT 311",
                "STAT 315",
                "STAT 385",
            ]
        },
    },
    {
        "id": "methodology_theory_requirement",
        "requirement_type": "choose_n",
        "courses": [
            "STAT 411",
            "STAT 413",
            "STAT 418",
            "STAT 419",
            "STAT 421",
            "STAT 425",
            "STAT 453",
            "STAT 502",
            "COMP 502",
            "ELEC 502",
            "STAT 541",
            "STAT 545",
        ],
        "min_count": 3,
        "max_count": 6,
    },
    {
        "id": "senior_capstone",
        "requirement_type": "choose_n",
        "courses": [
            "DSCI 435",
            "COMP 449",
            "STAT 450",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "approved_outside_elective",
        "requirement_type": "choose_n",
        "courses": [
            "CMOR 350",
            "CMOR 360",
            "CMOR 451",
            "CMOR 455",
            "COMP 322",
            "ELEC 323",
            "COMP 330",
            "COMP 382",
            "COMP 422",
            "COMP 430",
            "COMP 440",
            "ELEC 440",
            "COMP 441",
            "COMP 502",
            "ELEC 502",
            "STAT 502",
            "DSCI 304",
            "DSCI 435",
            "COMP 449",
            "ECON 300",
            "ECON 305",
            "ECON 308",
            "ECON 310",
            "STAT 376",
            "ECON 418",
            "ECON 419",
            "ECON 449",
            "PSYC 439",
            "SOCI 436",
            "SOCI 483",
            "SMGT 430",
            "SMGT 431",
        ],
        "min_count": 0,
        "max_count": 1,
    },
]

statistics_bs_degree_requirement: List[Dict[str, Any]] = [
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

        "id": "multivariable_calculus",

        "requirement_type": "choose_group",

        "options": [

            ["MATH 212"],

            ["MATH 221", "MATH 222"],

            ["MATH 232"],

        ],

        "min_count": 1,

        "max_count": 1,

    },
    {
        "id": "linear_algebra",
        "requirement_type": "choose_n",
        "courses": ["CMOR 302", "CMOR 303", "MATH 355", "MATH 354"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "analysis",
        "requirement_type": "choose_n",
        "courses": ["MATH 302", "MATH 321", "MATH 331", "MATH 427"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "statistical_computation",
        "requirement_type": "required_courses",
        "courses": ["STAT 405"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "basic_computing",
        "requirement_type": "choose_n",
        "courses": ["CMOR 220", "COMP 140", "COMP 182"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "advanced_computing",
        "requirement_type": "choose_n",
        "courses": [
            "CMOR 360", "CMOR 422", "CMOR 441", "CMOR 520",
            "COMP 215", "COMP 322", "ELEC 323",
            "COMP 330", "COMP 382", "DSCI 302",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "probability_statistics",
        "requirement_type": "choose_n",
        "courses": ["STAT 310", "ECON 307", "STAT 311", "STAT 315", "DSCI 301"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "linear_regression",
        "requirement_type": "required_courses",
        "courses": ["STAT 410"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "probability",
        "requirement_type": "required_courses",
        "courses": ["STAT 418"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "statistical_inference",
        "requirement_type": "required_courses",
        "courses": ["STAT 419"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "stat_electives",
        "requirement_type": "choose_n",
        "filters": {"subject": "STAT", "min_level": 300},
        "min_count": 6,
        "constraints": {
            "excluded_courses": ["STAT 305", "STAT 310", "STAT 311", "STAT 315", "STAT 385"]
        },
    },
    {
        "id": "methodology_theory_requirement",
        "requirement_type": "choose_n",
        "courses": [
            "STAT 411", "STAT 413", "STAT 421", "STAT 425", "STAT 453",
            "STAT 502", "COMP 502", "ELEC 502",
            "STAT 525", "STAT 532", "STAT 533", "STAT 541", "STAT 545",
            "STAT 550", "STAT 552", "STAT 581", "CMOR 552",
            "STAT 582", "STAT 650",
        ],
        "min_count": 4,
    },
    {
        "id": "senior_capstone",
        "requirement_type": "choose_n",
        "courses": ["DSCI 435", "COMP 449", "STAT 450"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "approved_outside_elective",
        "requirement_type": "choose_n",
        "courses": [
            "CMOR 350", "CMOR 360", "CMOR 451", "CMOR 455",
            "COMP 322", "ELEC 323", "COMP 330", "COMP 382",
            "COMP 422", "COMP 430", "COMP 440", "ELEC 440",
            "COMP 441", "COMP 502", "ELEC 502", "STAT 502",
            "DSCI 304", "DSCI 435", "COMP 449",
            "ECON 300", "ECON 305", "ECON 308", "ECON 310",
            "STAT 376", "ECON 418", "ECON 419", "ECON 449",
        ],
        "min_count": 0,
        "max_count": 1,
    },
]

statistics_minor_track_a_requirement: List[Dict[str, Any]] = [
    {
        "id": "stat_minor_track_a_probability_statistics",
        "requirement_type": "choose_n",
        "courses": ["STAT 310", "ECON 307", "STAT 311", "STAT 315", "DSCI 301"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "stat_minor_track_a_statistical_computation",
        "requirement_type": "required_courses",
        "courses": ["STAT 405"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "stat_minor_track_a_linear_regression",
        "requirement_type": "required_courses",
        "courses": ["STAT 410"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "stat_minor_track_a_electives",
        "requirement_type": "choose_n",
        "filters": {"subject": "STAT", "min_level": 300},
        "min_count": 3,
        "constraints": {
            "excluded_courses": ["STAT 305", "STAT 310", "STAT 311", "STAT 315", "STAT 385"]
        },
    },
]
statistics_minor_track_b_requirement: List[Dict[str, Any]] = [
    {
        "id": "stat_minor_track_b_intro_statistics",
        "requirement_type": "choose_n",
        "courses": ["STAT 280", "STAT 180", "STAT 305"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "stat_minor_track_b_data_methods",
        "requirement_type": "choose_n",
        "courses": ["STAT 385", "DSCI 101"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "stat_minor_track_b_electives",
        "requirement_type": "choose_n",
        "filters": {"subject": "STAT", "min_level": 300},
        "min_count": 4,
        "constraints": {
            "excluded_courses": ["STAT 305", "STAT 385"]
        },
    },
]

operations_research_ba_base_requirement: List[Dict[str, Any]] = [
    {
        "id": "or_intro_programming",
        "requirement_type": "required_courses",
        "courses": ["COMP 140"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_calculus_1",
        "requirement_type": "choose_n",
        "courses": ["MATH 101", "MATH 105"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_calculus_2",
        "requirement_type": "choose_n",
        "courses": ["MATH 102", "MATH 106"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_multivariable_calculus",
        "requirement_type": "choose_group",
        "options": [
            ["MATH 212"],
            ["MATH 232"],
            ["MATH 221", "MATH 222"],
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_linear_algebra",
        "requirement_type": "choose_n",
        "courses": [
            "CMOR 302",
            "CMOR 303",
            "MATH 354",
            "MATH 355",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_intermediate_core",
        "requirement_type": "required_courses",
        "courses": [
            "CMOR 350",
            "CMOR 360",
        ],
        "min_count": 2,
        "max_count": 2,
    },
    {
        "id": "or_machine_learning",
        "requirement_type": "choose_n",
        "courses": [
            "ELEC 378",
            "CMOR 438",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_probability_statistics",
        "requirement_type": "choose_n",
        "courses": [
            "STAT 310",
            "ECON 307",
            "STAT 311",
            "STAT 315",
            "DSCI 301",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_advanced_requirement",
        "requirement_type": "choose_n",
        "courses": [
            "CMOR 404",
            "CMOR 442",
            "CMOR 444",
            "CMOR 451",
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_senior_design",
        "requirement_type": "choose_group",
        "options": [
            ["DSCI 435"],
            ["COMP 449"],
            ["CMOR 492", "CMOR 493"],
        ],
        "min_count": 1,
        "max_count": 1,
    },
]

operations_research_bs_base_requirement: List[Dict[str, Any]] = [
    {
        "id": "or_intro_comp",
        "requirement_type": "required_courses",
        "courses": ["COMP 140", "COMP 182", "COMP 215"],
        "min_count": 3,
        "max_count": 3,
    },
    {
        "id": "or_calculus_1",
        "requirement_type": "choose_n",
        "courses": ["MATH 101", "MATH 105"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_calculus_2",
        "requirement_type": "choose_n",
        "courses": ["MATH 102", "MATH 106"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_multivariable_calculus",
        "requirement_type": "choose_group",
        "options": [
            ["MATH 212"],
            ["MATH 232"],
            ["MATH 221", "MATH 222"],
        ],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_intermediate_core",
        "requirement_type": "required_courses",
        "courses": ["CMOR 350", "CMOR 360"],
        "min_count": 2,
        "max_count": 2,
    },
    {
        "id": "or_analysis",
        "requirement_type": "choose_n",
        "courses": ["MATH 302", "MATH 321"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_linear_algebra",
        "requirement_type": "choose_n",
        "courses": ["CMOR 302", "CMOR 303", "MATH 354", "MATH 355"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_probability_statistics",
        "requirement_type": "choose_n",
        "courses": ["STAT 310", "ECON 307", "STAT 311", "STAT 315", "DSCI 301"],
        "min_count": 1,
        "max_count": 1,
    },
    {
        "id": "or_advanced_core",
        "requirement_type": "required_courses",
        "courses": ["CMOR 441", "CMOR 442", "CMOR 451"],
        "min_count": 3,
        "max_count": 3,
    },
    {
        "id": "or_senior_design",
        "requirement_type": "choose_group",
        "options": [
            ["CMOR 492", "CMOR 493"],
            ["DSCI 435"],
            ["COMP 449"],
        ],
        "min_count": 1,
        "max_count": 1,
    },
]


or_algorithms_core_courses = [
    "CMOR 444",
    "CMOR 446",
    "CMOR 531",
    "CMOR 533",
    "CMOR 544",
    "COMP 382",
    "COMP 414",
    "COMP 416",
    "COMP 441",
    "COMP 458",
    "COMP 459",
    "COMP 480",
    "ELEC 570",
]

or_data_science_core_courses = [
    "CMOR 437",
    "CMOR 531",
    "CMOR 533",
    "COMP 414",
    "COMP 440",
    "COMP 441",
    "ELEC 478",
    "ELEC 578",
    "STAT 413",
    "COMP 459",
    "ELEC 475",
    "STAT 502",
    "COMP 502",
    "ELEC 502",
    "STAT 602",
    "COMP 602",
    "ELEC 602",
]

or_financial_engineering_core_courses = [
    "CMOR 455",
    "CMOR 462",
    "CMOR 531",
    "CMOR 533",
    "CMOR 544",
    "ECON 443",
    "STAT 449",
    "STAT 482",
]

or_foundations_core_courses = [
    "CMOR 404",
    "CMOR 444",
    "CMOR 446",
    "CMOR 455",
    "CMOR 531",
    "CMOR 533",
    "CMOR 543",
    "CMOR 544",
    "CMOR 552",
    "STAT 581",
    "CMOR 554",
    "STAT 552",
    "CMOR 556",
    "COMP 382",
]

or_supply_chain_core_courses = [
    "CMOR 452",
    "CMOR 461",
    "CMOR 465",
    "CMOR 464",
    "CMOR 467",
]

or_applied_operations_research = [
    "CMOR 437",
    "CMOR 438",
    "CMOR 452",
    "CMOR 461",
    "CMOR 462",
    "CMOR 463",
    "CMOR 465",
    "CMOR 467",
    "COMP 440",
    "ELEC 440",
    "COMP 441",
    "ELEC 478",
    "STAT 413",
    "COMP 459",
    "ECON 437",
    "ENST 437",
    "ECON 443",
    "ECON 449",
    "ECON 470",
    "ECON 481",
    "ELEC 475",
    "ELEC 533",
    "CMOR 553",
    "STAT 583",
    "STAT 449",
    "STAT 482",
    "STAT 502",
    "COMP 502",
    "ELEC 502",
    "STAT 602",
    "COMP 602",
    "ELEC 602",
]

or_theoretical_foundations = [
    "CMOR 404",
    "CMOR 444",
    "CMOR 446",
    "CMOR 455",
    "CMOR 531",
    "CMOR 533",
    "CMOR 543",
    "CMOR 544",
    "CMOR 552",
    "STAT 581",
    "CMOR 554",
    "STAT 552",
    "CMOR 556",
    "COMP 382",
    "COMP 414",
    "COMP 458",
    "COMP 480",
    "ELEC 570",
    "MATH 412",
    "STAT 418",
    "STAT 419",
]

or_algorithms_specialization = {
    "id": "or_algorithms_specialization",
    "requirement_type": "composite",
    "constraints": {
        "min_from_subject": [{"subject": "CMOR", "min_count": 3}]
    },
    "sub_requirements": [
        {
            "id": "core",
            "requirement_type": "choose_n",
            "courses": or_algorithms_core_courses,
            "min_count": 3,
            "max_count": 3,
        },
        {
            "id": "applied_or",
            "requirement_type": "choose_n",
            "courses": or_applied_operations_research,
            "min_count": 1,
            "max_count": 1,
        },
        {
            "id": "theoretical_foundations",
            "requirement_type": "choose_n",
            "courses": or_theoretical_foundations,
            "min_count": 1,
            "max_count": 1,
        },
    ],
}

or_data_science_specialization = {
    "id": "or_data_science_specialization",
    "requirement_type": "composite",
    "constraints": {
        "min_from_subject": [{"subject": "CMOR", "min_count": 3}]
    },
    "sub_requirements": [
        {
            "id": "core",
            "requirement_type": "choose_n",
            "courses": or_data_science_core_courses,
            "min_count": 3,
            "max_count": 3,
        },
        {
            "id": "applied_or",
            "requirement_type": "choose_n",
            "courses": or_applied_operations_research,
            "min_count": 1,
            "max_count": 1,
        },
        {
            "id": "theoretical_foundations",
            "requirement_type": "choose_n",
            "courses": or_theoretical_foundations,
            "min_count": 1,
            "max_count": 1,
        },
    ],
}

or_financial_engineering_specialization = {
    "id": "or_financial_engineering_specialization",
    "requirement_type": "composite",
    "constraints": {
        "min_from_subject": [{"subject": "CMOR", "min_count": 3}]
    },
    "sub_requirements": [
        {
            "id": "core",
            "requirement_type": "choose_n",
            "courses": or_financial_engineering_core_courses,
            "min_count": 3,
            "max_count": 3,
        },
        {
            "id": "theoretical_foundations",
            "requirement_type": "choose_n",
            "courses": or_theoretical_foundations,
            "min_count": 1,
            "max_count": 1,
        },
        {
            "id": "additional_elective",
            "requirement_type": "choose_n",
            "courses": sorted(set(or_theoretical_foundations + or_applied_operations_research)),
            "min_count": 1,
            "max_count": 1,
        },
    ],
}

or_foundations_specialization = {
    "id": "or_foundations_specialization",
    "requirement_type": "composite",
    "constraints": {
        "min_from_subject": [{"subject": "CMOR", "min_count": 3}]
    },
    "sub_requirements": [
        {
            "id": "core",
            "requirement_type": "choose_n",
            "courses": or_foundations_core_courses,
            "min_count": 4,
            "max_count": 4,
        },
        {
            "id": "elective",
            "requirement_type": "choose_n",
            "courses": sorted(set(or_applied_operations_research + or_theoretical_foundations)),
            "min_count": 1,
            "max_count": 1,
        },
    ],
}
or_supply_chain_specialization = {
    "id": "or_supply_chain_specialization",
    "requirement_type": "composite",
    "constraints": {
        "min_from_subject": [{"subject": "CMOR", "min_count": 3}]
    },
    "sub_requirements": [
        {
            "id": "core",
            "requirement_type": "choose_n",
            "courses": or_supply_chain_core_courses,
            "min_count": 3,
            "max_count": 3,
        },
        {
            "id": "theoretical_foundations",
            "requirement_type": "choose_n",
            "courses": or_theoretical_foundations,
            "min_count": 1,
            "max_count": 1,
        },
        {
            "id": "additional_elective",
            "requirement_type": "choose_n",
            "courses": sorted(set(or_theoretical_foundations + or_applied_operations_research)),
            "min_count": 1,
            "max_count": 1,
        },
    ],
}

or_breadth_specialization = {
    "id": "or_breadth_specialization",
    "requirement_type": "composite",
    "constraints": {
        "min_from_subject": [{"subject": "CMOR", "min_count": 3}]
    },
    "sub_requirements": [
        {
            "id": "applied_or",
            "requirement_type": "choose_n",
            "courses": or_applied_operations_research,
            "min_count": 2,
            "max_count": 2,
        },
        {
            "id": "theoretical_foundations",
            "requirement_type": "choose_n",
            "courses": or_theoretical_foundations,
            "min_count": 2,
            "max_count": 2,
        },
        {
            "id": "additional_elective",
            "requirement_type": "choose_n",
            "courses": sorted(set(or_applied_operations_research + or_theoretical_foundations)),
            "min_count": 1,
            "max_count": 1,
        },
    ],
}

cmor_bs_algorithms_requirement = operations_research_bs_base_requirement + [or_algorithms_specialization]
cmor_bs_data_science_requirement = operations_research_bs_base_requirement + [or_data_science_specialization]
cmor_bs_financial_engineering_requirement = operations_research_bs_base_requirement + [or_financial_engineering_specialization]
cmor_bs_foundations_requirement = operations_research_bs_base_requirement + [or_foundations_specialization]
cmor_bs_supply_chain_requirement = operations_research_bs_base_requirement + [or_supply_chain_specialization]
cmor_bs_breadth_requirement = operations_research_bs_base_requirement + [or_breadth_specialization]

cmor_ba_data_science_requirement = (
    operations_research_ba_base_requirement
    + [or_data_science_specialization]
)

cmor_ba_financial_engineering_requirement = (
    operations_research_ba_base_requirement
    + [or_financial_engineering_specialization]
)

cmor_ba_supply_chain_requirement = (
    operations_research_ba_base_requirement
    + [or_supply_chain_specialization]
)

cmor_ba_breadth_requirement = (
    operations_research_ba_base_requirement
    + [or_breadth_specialization]
)


def _program_key_from_var_name(var_name: str) -> str:
    if var_name.endswith("_degree_requirement"):
        return var_name[: -len("_degree_requirement")]
    if var_name.endswith("_major_requirement"):
        return var_name[: -len("_major_requirement")]
    if var_name.endswith("_requirement"):
        return var_name[: -len("_requirement")]
    return var_name


def _program_label_from_key(key: str) -> str:
    if key in PROGRAM_LABEL_OVERRIDES:
        return PROGRAM_LABEL_OVERRIDES[key]

    parts = key.split("_")
    humanized_parts = [p.upper() if len(p) <= 3 else p.capitalize() for p in parts]
    return " ".join(humanized_parts)


def get_supported_program_requirements() -> Dict[str, List[Dict[str, Any]]]:
    programs: Dict[str, List[Dict[str, Any]]] = {}

    for var_name, value in globals().items():
        if not var_name.endswith("_requirement"):
            continue
        if var_name.endswith("_base_requirement"):
            continue
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            continue

        program_key = _program_key_from_var_name(var_name)
        if not program_key:
            continue
        programs[program_key] = value

    return dict(sorted(programs.items()))


def get_supported_program_options() -> List[Dict[str, str]]:
    options = [
        {"value": key, "label": _program_label_from_key(key)}
        for key in get_supported_program_requirements().keys()
    ]
    return sorted(options, key=lambda option: option["label"])
