from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.course import Course
from parsers.parse_schedule import normalize_course_code


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _coerce_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, (set, tuple)):
            return list(value)
        if isinstance(value, str):
            text_value = value.strip()
            if not text_value:
                return []
            try:
                parsed = json.loads(text_value)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [text_value]
        return []

    @staticmethod
    def _coerce_dict(value: Any) -> Optional[Dict[str, Any]]:
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            text_value = value.strip()
            if not text_value:
                return None
            try:
                parsed = json.loads(text_value)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return None
        return None

    def get_course_catalog(self) -> Dict[str, Any]:
        rows = self.db.execute(
            text(
                """
                SELECT
                    code,
                    subject,
                    course_number,
                    long_title,
                    offered_terms,
                    credit_hours,
                    distribution,
                    analyzing_diversity,
                    cross_list,
                    prereq_tree
                FROM courses
                """
            )
        ).mappings().all()

        catalog: Dict[str, Course] = {}
        for row in rows:
            code_raw = str(row.get("code", "")).strip()
            if not code_raw:
                continue

            code = normalize_course_code(code_raw)
            subject = str(row.get("subject", "")).strip().upper()

            course_number_raw = row.get("course_number")
            try:
                course_number = int(course_number_raw)
            except (TypeError, ValueError):
                number_text = "".join(ch for ch in code.split(" ")[-1] if ch.isdigit())
                course_number = int(number_text) if number_text.isdigit() else 0

            offered_terms = {
                str(term).strip()
                for term in self._coerce_list(row.get("offered_terms"))
                if str(term).strip()
            }
            cross_list = [
                normalize_course_code(str(c))
                for c in self._coerce_list(row.get("cross_list"))
                if str(c).strip()
            ]

            catalog[code] = Course(
                code=code,
                subject=subject,
                course_number=course_number,
                long_title=row.get("long_title"),
                offered_terms=offered_terms,
                credit_hours=row.get("credit_hours"),
                distribution=row.get("distribution"),
                analyzing_diversity=bool(row.get("analyzing_diversity")),
                cross_list=cross_list,
                prereq_tree=self._coerce_dict(row.get("prereq_tree")),
            )

        return catalog

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
