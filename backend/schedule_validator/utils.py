import re
from typing import Any, Iterable, Mapping


def normalize_course_code(code: str) -> str:
    return re.sub(r"\s+", "", str(code)).upper()


def infer_subject(code: str) -> str:
    match = re.match(r"[A-Z]+", normalize_course_code(code))
    return match.group(0) if match else ""


def read_field(value: Any, field_name: str, default: Any) -> Any:
    if isinstance(value, Mapping):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def unique_in_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def format_issues(issues: Iterable[Any], success_message: str) -> str:
    materialized = [str(issue) for issue in issues]
    return "; ".join(materialized) if materialized else success_message