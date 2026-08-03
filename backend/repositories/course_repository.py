from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

import re

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
    _READ_ONLY_START = re.compile(
        r"^\s*(SELECT|WITH)\b",
        re.IGNORECASE,
    )

    _FORBIDDEN_SQL = re.compile(
        r"\b("
        r"INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|"
        r"TRUNCATE|GRANT|REVOKE|COPY|CALL|DO|VACUUM|"
        r"ANALYZE|REFRESH|REINDEX|CLUSTER|COMMENT|"
        r"SET|RESET|LOCK|DISCARD"
        r")\b",
        re.IGNORECASE,
    )

    def execute_read_only_sql(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Execute one read-only SELECT/WITH query.

        This method should only be used with a fresh Session connected through
        a database role that has SELECT permission only on approved tables.
        """
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("SQL query must be a nonempty string.")

        if not 1 <= max_rows <= 5000:
            raise ValueError("max_rows must be between 1 and 5000.")

        query = sql.strip()

        # Allow one optional trailing semicolon but reject multiple statements.
        if query.endswith(";"):
            query = query[:-1].rstrip()

        if ";" in query:
            raise ValueError("Only one SQL statement is allowed.")

        if not self._READ_ONLY_START.match(query):
            raise ValueError(
                "Only SELECT or WITH queries are allowed."
            )

        if self._FORBIDDEN_SQL.search(query):
            raise ValueError(
                "The query contains a prohibited SQL operation."
            )

        # SET TRANSACTION must occur before another query in the transaction.
        if self.db.in_transaction():
            raise RuntimeError(
                "execute_read_only_sql requires a fresh database session."
            )

        bound_params = dict(params or {})
        reserved_parameter = "__course_repo_max_rows"

        if reserved_parameter in bound_params:
            raise ValueError(
                f"{reserved_parameter!r} is a reserved parameter name."
            )

        bound_params[reserved_parameter] = max_rows

        # Database-level protections. The regex checks above are only an
        # additional guard and are not a complete SQL security parser.
        self.db.execute(text("SET TRANSACTION READ ONLY"))
        self.db.execute(
            text("SET LOCAL statement_timeout = '5000ms'")
        )

        limited_query = text(
            f"""
            SELECT *
            FROM (
                {query}
            ) AS raw_course_query
            LIMIT :{reserved_parameter}
            """
        )

        result = self.db.execute(
            limited_query,
            bound_params,
        )

        if not result.returns_rows:
            raise ValueError(
                "The SQL statement did not return rows."
            )

        return [
            dict(row)
            for row in result.mappings().all()
        ]
