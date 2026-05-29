from __future__ import annotations

from typing import Any


def build_objective(*args: Any, **kwargs: Any) -> Any:
    raise NotImplementedError("Objective construction will be moved into this module during optimizer refactoring.")
