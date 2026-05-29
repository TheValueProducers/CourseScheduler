from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Set, Dict, Any, List


@dataclass
class Course:
    code: str
    subject: str
    course_number: int
    long_title: Optional[str] = None
    offered_terms: Set[str] = field(default_factory=set)
    credit_hours: Optional[int] = None
    distribution: Optional[str] = None
    analyzing_diversity: bool = False
    cross_list: List[str] = field(default_factory=list)
    prereq_tree: Optional[Dict[str, Any]] = None
