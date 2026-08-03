from __future__ import annotations

from typing import Any, Dict, List

from .degree_requirements import (
    ba_comp_degree_requirement,
    bs_artificial_intelligence_degree_requirement,
    bs_comp_degree_requirement,
    cmor_ba_breadth_requirement,
    cmor_ba_data_science_requirement,
    cmor_ba_financial_engineering_requirement,
    cmor_ba_supply_chain_requirement,
    cmor_bs_algorithms_requirement,
    cmor_bs_breadth_requirement,
    cmor_bs_data_science_requirement,
    cmor_bs_financial_engineering_requirement,
    cmor_bs_foundations_requirement,
    cmor_bs_supply_chain_requirement,
    data_science_minor_requirement,
    economics_ba_degree_requirement,
    statistics_ba_degree_requirement,
    statistics_bs_degree_requirement,
    statistics_minor_track_a_requirement,
    statistics_minor_track_b_requirement,
    mathematical_economic_analysis_ba_degree_requirement,
    managerial_economics_organizational_sciences_ba_degree_requirement
)


PROGRAM_LABEL_OVERRIDES: Dict[str, str] = {
    "ba_comp": "Bachelor of Arts in Computer Science",
    "bs_comp": "Bachelor of Science in Computer Science",
    "data_science_minor": "Data Science Minor",
    "statistics_ba": "Bachelor of Arts in Statistics",
    "statistics_bs": "Bachelor of Science in Statistics",
    "statistics_minor_track_a": "Statistics Minor Track A",
    "statistics_minor_track_b": "Statistics Minor Track B",
    "economics_ba": "Bachelor of Arts in Economics",
    "cmor_bs_algorithms": "Bachelor of Science (BS) Degree with a Major in Operations Research - Algorithms",
    "cmor_bs_data_science": "Bachelor of Science (BS) Degree with a Major in Operations Research - Data Science",
    "cmor_bs_financial_engineering": "Bachelor of Science (BS) Degree with a Major in Operations Research - Financial Engineering",
    "cmor_bs_foundations": "Bachelor of Science (BS) Degree with a Major in Operations Research - Foundations",
    "cmor_bs_supply_chain": "Bachelor of Science (BS) Degree with a Major in Operations Research - Supply Chain",
    "cmor_bs_breadth": "Bachelor of Science (BS) Degree with a Major in Operations Research - Breadth",
    "cmor_ba_data_science": "Bachelor of Arts (BA) Degree with a Major in Computational and Applied Mathematics - Data Science",
    "cmor_ba_financial_engineering": "Bachelor of Arts (BA) Degree with a Major in Computational and Applied Mathematics - Financial Engineering",
    "cmor_ba_supply_chain": "Bachelor of Arts (BA) Degree with a Major in Computational and Applied Mathematics - Supply Chain",
    "cmor_ba_breadth": "Bachelor of Arts (BA) Degree with a Major in Computational and Applied Mathematics - Breadth",
    "bs_artificial_intelligence": "Bachelor of Science in Artificial Intelligence",
    "mathematical_economic_analysis_ba_degree_requirement": "Bachelor of Arts (BA) Degree with a Major in Managerial Economics and Organizational Sciences",
    "managerial_economics_organizational_sciences_ba_degree_requirement": "Bachelor of Arts (BA) Degree with a Major in Managerial Economics and Organizational Sciences"

    
}


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
