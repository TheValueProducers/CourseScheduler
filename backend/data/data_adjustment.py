from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
	sys.path.insert(0, str(BACKEND_ROOT))

from db.database import get_course_catalog_path
from seeds.seed_courses import _load_course_catalog_from_json
from services.schedule_service import CourseRecord


def get_mgmt_612() -> CourseRecord | None:
	catalog = _load_course_catalog_from_json(get_course_catalog_path())
	return catalog.get("MATH 212")


if __name__ == "__main__":
	print(get_mgmt_612())
