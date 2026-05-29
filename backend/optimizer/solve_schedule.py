from __future__ import annotations

from typing import Any

from scheduler_engine import build_schedule


def solve_schedule(*args: Any, **kwargs: Any) -> Any:
    return build_schedule(*args, **kwargs)
