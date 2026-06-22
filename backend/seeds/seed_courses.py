from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import Boolean as SA_Boolean
from sqlalchemy import Column, Integer as SA_Integer, MetaData, String as SA_String, Table, Text as SA_Text, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.types import JSON, Boolean, Integer, String, Text

# Allow running this script directly via: python seeds/seed_courses.py
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db.database import SessionLocal, engine, get_course_catalog_path
from parsers.parse_schedule import (
    parse_credit_hours,
    parse_cross_list,
    parse_distribution,
    parse_diversity,
    parse_long_title,
    parse_prereq_expr,
)
from services.schedule_service import CourseRecord


def _stage(message: str) -> None:
    print(f"[seed_courses] {message}", flush=True)


def _load_course_catalog_from_json(data_path: Path) -> Dict[str, CourseRecord]:
    with data_path.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    catalog: Dict[str, CourseRecord] = {}
    for row in rows:
        subject = str(row.get("subject", "")).strip().upper()
        course_num_raw = str(row.get("course_number", "")).strip()
        if not subject or not course_num_raw.isdigit():
            continue

        course_number = int(course_num_raw)
        code = f"{subject} {course_number:03d}"
        raw_text = row.get("raw_text") or ""
        term = str(row.get("term", "")).strip().lower()
        prereq = str(row.get("prerequisites") or "")

        if code not in catalog:
            catalog[code] = CourseRecord(
                code=code,
                subject=subject,
                course_number=course_number,
                long_title=parse_long_title(raw_text),
                offered_terms=set(),
                credit_hours=parse_credit_hours(raw_text),
                distribution=parse_distribution(raw_text),
                analyzing_diversity=parse_diversity(raw_text),
                cross_list=parse_cross_list(raw_text),
                prereq_tree=parse_prereq_expr(prereq),
            )

        if "fall" in term:
            catalog[code].offered_terms.add("Fall")
        if "spring" in term:
            catalog[code].offered_terms.add("Spring")

    return catalog


def _format_value_for_column(value: Any, column_type: TypeEngine[Any]) -> Any:
    """Coerce Python values into a shape compatible with the reflected DB column type."""
    if value is None:
        return None

    if isinstance(column_type, Boolean):
        return bool(value)

    if isinstance(column_type, Integer):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    if isinstance(column_type, JSON):
        return value

    if isinstance(column_type, (String, Text)):
        if isinstance(value, (dict, list, set, tuple)):
            if isinstance(value, set):
                value = sorted(value)
            return json.dumps(value, sort_keys=True)
        return str(value)

    if isinstance(value, set):
        return sorted(value)

    return value


def _build_row(record: CourseRecord, table: Table) -> Dict[str, Any]:
    """Build one insert/update payload constrained to reflected table columns."""
    source: Dict[str, Any] = {
        "code": record.code,
        "subject": record.subject,
        "course_number": record.course_number,
        "long_title": record.long_title,
        "offered_terms": sorted(record.offered_terms),
        "credit_hours": record.credit_hours,
        "distribution": record.distribution,
        "analyzing_diversity": record.analyzing_diversity,
        "cross_list": sorted(record.cross_list),
        "prereq_tree": record.prereq_tree,
    }

    row: Dict[str, Any] = {}
    for col in table.columns:
        if col.name not in source:
            continue
        row[col.name] = _format_value_for_column(source[col.name], col.type)

    return row


def _dedupe_catalog_by_code(catalog: Dict[str, CourseRecord]) -> Dict[str, CourseRecord]:
    """Keep one record per normalized course code before seeding."""
    deduped: Dict[str, CourseRecord] = {}
    duplicate_count = 0

    for code, record in catalog.items():
        normalized = " ".join(str(code).upper().split())
        if normalized in deduped:
            duplicate_count += 1
            continue
        deduped[normalized] = record

    _stage(
        f"deduplicated catalog by code: kept={len(deduped)}, duplicates_skipped={duplicate_count}"
    )
    return deduped


def _load_courses_table(db_engine: Engine) -> Table:
    inspector = inspect(db_engine)
    metadata = MetaData()
    _stage("checking whether 'courses' table exists")

    if not inspector.has_table("courses"):
        _stage("'courses' table not found; creating table")
        courses_table = Table(
            "courses",
            metadata,
            Column("code", SA_String(16), primary_key=True),
            Column("subject", SA_String(8), nullable=False),
            Column("course_number", SA_Integer, nullable=False),
            Column("long_title", SA_Text, nullable=True),
            Column("offered_terms", JSON, nullable=True),
            Column("credit_hours", SA_Integer, nullable=True),
            Column("distribution", SA_String(64), nullable=True),
            Column("analyzing_diversity", SA_Boolean, nullable=False, default=False),
            Column("cross_list", JSON, nullable=True),
            Column("prereq_tree", JSON, nullable=True),
        )
        metadata.create_all(db_engine, tables=[courses_table])
        _stage("created 'courses' table")
        return courses_table

    _stage("found existing 'courses' table")
    return Table("courses", metadata, autoload_with=db_engine)


def seed_courses() -> Dict[str, int]:
    _stage("starting course seed")
    data_path = get_course_catalog_path()
    _stage(f"loading course catalog from {data_path}")
    catalog = _load_course_catalog_from_json(data_path)
    _stage(f"loaded {len(catalog)} courses from catalog")
    catalog = _dedupe_catalog_by_code(catalog)

    courses_table = _load_courses_table(engine)
    _stage("courses table is ready")

    if "code" not in courses_table.columns:
        raise RuntimeError("Table 'courses' must have a 'code' column for idempotent seeding.")

    inserted = 0
    updated = 0

    with SessionLocal() as db:
        assert isinstance(db, Session)
        _stage("reading existing course codes from database")

        existing_codes = {
            row[0]
            for row in db.execute(select(courses_table.c.code)).all()
            if row and row[0] is not None
        }
        _stage(f"found {len(existing_codes)} existing courses in database")

        _stage("starting insert/update pass")

        total = len(catalog)
        for index, (code, record) in enumerate(catalog.items(), start=1):
            row_payload = _build_row(record, courses_table)
            if not row_payload:
                continue

            if code in existing_codes:
                db.execute(
                    courses_table.update()
                    .where(courses_table.c.code == code)
                    .values(**row_payload)
                )
                updated += 1
            else:
                db.execute(courses_table.insert().values(**row_payload))
                inserted += 1

            if index % 200 == 0 or index == total:
                _stage(
                    f"processed {index}/{total} courses "
                    f"(inserted={inserted}, updated={updated})"
                )

        _stage("writing changes to database")
        db.commit()
        _stage("database commit complete")

    _stage(
        "seed finished "
        f"(inserted={inserted}, updated={updated}, total_catalog={len(catalog)})"
    )
    return {"inserted": inserted, "updated": updated, "total_catalog": len(catalog)}


if __name__ == "__main__":
    result = seed_courses()
    print(
        "Seed complete: "
        f"inserted={result['inserted']}, "
        f"updated={result['updated']}, "
        f"total_catalog={result['total_catalog']}"
    )