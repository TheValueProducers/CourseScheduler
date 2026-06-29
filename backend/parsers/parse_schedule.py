from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def normalize_course_code(course: str) -> str:
    """Normalize course codes like 'comp  140' -> 'COMP 140'."""
    course = " ".join(course.strip().upper().split())
    match = re.match(r"^([A-Z]{2,5})\s*(\d{3})$", course)
    if not match:
        return course
    return f"{match.group(1)} {match.group(2)}"


def parse_cross_list(raw_text: str) -> List[str]:
    if not raw_text:
        return []
    return [normalize_course_code(c) for c in re.findall(r"Cross-list:\s*([A-Z]{2,5}\s+\d{3})", raw_text)]


def parse_long_title(raw_text: str) -> Optional[str]:
    if not isinstance(raw_text, str):
        return None

    match = re.search(
        r"Long Title:\s*\n(.+)",
        raw_text,
    )

    if match:
        return match.group(1).strip()

    return None


def parse_distribution(raw_text: str) -> Optional[str]:
    if not raw_text:
        return None
    match = re.search(r"Distribution Group:\s*\n(.+)", raw_text)
    return match.group(1).strip() if match else None


def parse_diversity(raw_text: str) -> bool:
    if not raw_text:
        return False
    match = re.search(r"Analyzing Diversity:\s*\n(.+)", raw_text)
    return bool(match and match.group(1).strip().lower() == "yes")


def parse_credit_hours(raw_text: str) -> Optional[float]:
    if not raw_text:
        return None
    match = re.search(r"Credit Hours:\s*\n(.+)", raw_text)
    if not match:
        return None
    text = match.group(1).strip()

    number_pattern = r"\d+(?:\.\d+)?"

    if re.fullmatch(number_pattern, text):
        return float(text)

    range_match = re.fullmatch(fr"({number_pattern})\s+TO\s+({number_pattern})", text)
    if range_match:
        lower = range_match.group(1)
        upper = range_match.group(2)
        if "." in lower or "." in upper:
            return None
        return float(upper)

    or_match = re.fullmatch(fr"({number_pattern})\s+OR\s+({number_pattern})", text)
    if or_match:
        return max(float(or_match.group(1)), float(or_match.group(2)))

    return None


def tokenize_prereq(expr: str) -> List[str]:
    return re.findall(r"[A-Z]{2,5}\s+\d{3}|AND|OR|\(|\)", expr.upper())


def parse_prereq_expr(expr: str) -> Optional[Dict[str, Any]]:
    if not expr or not expr.strip():
        return None

    tokens = tokenize_prereq(expr)
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
        return {"course": normalize_course_code(token)}

    try:
        parsed = parse_expression()
        if pos != len(tokens):
            return None
        return parsed
    except Exception:
        return None
