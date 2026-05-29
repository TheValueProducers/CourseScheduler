from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict

from db.database import get_course_catalog_path
from scheduler_engine import load_course_catalog


@lru_cache(maxsize=1)
def get_course_catalog() -> Dict[str, Any]:
    data_path = get_course_catalog_path()
    if not data_path.exists():
        raise FileNotFoundError(f"Course catalog data file not found: {data_path}")
    return load_course_catalog(data_path)
