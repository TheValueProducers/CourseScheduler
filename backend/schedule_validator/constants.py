from typing import Literal

Verdict = Literal["Test Passed", "Test Failed"]
TermName = Literal["Fall", "Spring"]
AcademicYear = Literal["Freshman", "Sophomore", "Junior", "Senior"]

YEAR_NAMES: tuple[AcademicYear, ...] = (
    "Freshman",
    "Sophomore",
    "Junior",
    "Senior",
)

DEFAULT_COURSE_CODE_KEYS = (
    "class",
    "course_code",
    "courseCode",
    "code",
    "id",
)