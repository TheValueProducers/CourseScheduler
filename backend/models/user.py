from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: Optional[int] = None
    name: str = ""
    email: str = ""
