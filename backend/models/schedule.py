from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Schedule:
    status: str = "draft"
    schedule: Dict[str, List[List[str]]] = field(default_factory=dict)
