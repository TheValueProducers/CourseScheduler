from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from db.database import get_course_catalog_path
from services.schedule_service import load_course_catalog


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    @lru_cache(maxsize=1)
    def _cached_catalog() -> Dict[str, Any]:
        data_path = get_course_catalog_path()
        if not data_path.exists():
            raise FileNotFoundError(f"Course catalog data file not found: {data_path}")
        return load_course_catalog(data_path)

    def get_course_catalog(self) -> Dict[str, Any]:
        # Kept as an instance method for repository DI consistency.
        _ = self.db
        return self._cached_catalog()

    def get_all_courses(self) -> List[Dict[str, Any]]:
        catalog = self.get_course_catalog()
        return [
            {
                "subject": record.subject,
                "course_number": record.course_number,
                "long_title": record.long_title,
            }
            for record in sorted(catalog.values(), key=lambda c: (c.subject, c.course_number))
        ]
