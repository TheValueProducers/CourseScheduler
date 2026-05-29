from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def normalize_course_code(course: str) -> str:
    course = " ".join(course.strip().upper().split())
    match = re.match(r"^([A-Z]{2,5})\s*(\d{3})$", course)
    if not match:
        return course
    return f"{match.group(1)} {match.group(2)}"


def tokenize_prerequisite_expression(expr: str) -> List[str]:
    return re.findall(r"[A-Z]{2,5}\s+\d{3}|AND|OR|\(|\)", expr.upper())


def parse_prerequisites(expr: str) -> Optional[Dict[str, Any]]:
    if not expr or not expr.strip():
        return None

    tokens = tokenize_prerequisite_expression(expr)
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
