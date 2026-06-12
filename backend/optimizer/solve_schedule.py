from __future__ import annotations

from typing import Any

from services.schedule_service import build_schedule


def solve_schedule(*args: Any, **kwargs: Any) -> Any:
    return build_schedule(*args, **kwargs)
