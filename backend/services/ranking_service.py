from __future__ import annotations

from statistics import fmean
from typing import Any, Dict, List

from repositories.course_repository import get_course_catalog
from repositories.review_repository import list_reviews
from schemas.rank_schema import CourseRankRow, GroupedCourseRankings, MetricRankings


GROUPS: List[str] = ["d1", "d2", "d3", "diversity", "lpap"]

METRICS: List[str] = [
    "workload",
    "content_diff",
    "exam_diff",
    "assignment_diff",
    "overall_diff",
    "instructor",
    "usefulness",
    "interest",
]

MINIMUM_REVIEW_THRESHOLD = 10

GROUP_TO_DISTRIBUTION: Dict[str, str] = {
    "d1": "Distribution Group I",
    "d2": "Distribution Group II",
    "d3": "Distribution Group III",
}

REVIEW_SCORE_FIELDS: Dict[str, str] = {
    "workload": "overall_workload",
    "content_diff": "content_difficulty",
    "exam_diff": "exam_difficulty",
    "assignment_diff": "project_assignment_difficulty",
    "instructor": "instructor",
    "usefulness": "practical_usefulness",
    "interest": "interest_enjoyment",
}

RANKING_GROUPS: List[Dict[str, Any]] = [
    {
        "title": "Distribution Classes (D1, D2, D3)",
        "categories": ["Easiest", "Least Workload", "Most Useful", "Best Teaching", "Best Overall Courses"],
    },
    {
        "title": "Analyzing Diversity Classes",
        "categories": ["Easiest", "Least Workload", "Most Useful", "Best Teaching", "Best Overall Courses"],
    },
    {
        "title": "Lifetime Physical Activity Program (LPAP)",
        "categories": ["Easiest", "Least Workload", "Most Useful", "Best Teaching", "Best Overall Courses"],
    },
]


def get_ranking_groups() -> List[Dict[str, Any]]:
    return RANKING_GROUPS


def _get_all_courses_in_group_from_catalog(group: str, catalog: Dict[str, Any]) -> List[str]:
    key = group.strip().lower()
    output: List[str] = []

    for code, course in catalog.items():
        if key in GROUP_TO_DISTRIBUTION and course.distribution == GROUP_TO_DISTRIBUTION[key]:
            output.append(code)
        elif key == "diversity" and course.analyzing_diversity:
            output.append(code)
        elif key == "lpap" and code.startswith("LPAP"):
            output.append(code)

    return sorted(output)


def get_all_courses_in_group(group: str) -> List[str]:
    return _get_all_courses_in_group_from_catalog(group, get_course_catalog())


def _normalize_course_code(subject: str, course_number: Any) -> str | None:
    subject_value = str(subject).strip().upper()
    course_number_value = str(course_number).strip()

    if not subject_value or not course_number_value:
        return None

    if course_number_value.isdigit():
        return f"{subject_value} {int(course_number_value):03d}"

    return f"{subject_value} {course_number_value}"


def _get_review_course(review: Dict[str, Any]) -> str | None:
    return _normalize_course_code(review.get("subject", ""), review.get("course_number", ""))


def _compute_metric_average(review: Dict[str, Any], metric: str) -> float:
    if metric == "overall_diff":
        return (
            0.4 * _compute_metric_average(review, "content_diff")
            + 0.35 * _compute_metric_average(review, "exam_diff")
            + 0.25 * _compute_metric_average(review, "assignment_diff")
        )

    field_name = REVIEW_SCORE_FIELDS[metric]
    value = review.get(field_name)
    return float(value) if value is not None else 0.0


def get_all_reviews_for_group(group: str) -> List[Dict[str, Any]]:
    group_courses = set(get_all_courses_in_group(group))
    reviews = list_reviews()
    filtered_reviews: List[Dict[str, Any]] = []

    for review in reviews:
        course_code = _get_review_course(review)
        if course_code in group_courses:
            filtered_reviews.append(review)

    return filtered_reviews


def get_global_average(metric: str) -> float:
    reviews = list_reviews()
    if not reviews:
        return 0.0

    return fmean(_compute_metric_average(review, metric) for review in reviews)


def get_bayesian_score(v: int, m: int, c: float, r: float) -> float:
    return (v / (v + m)) * r + (m / (v + m)) * c


def _build_ranking_context(catalog: Dict[str, Any]) -> Dict[str, Any]:
    all_reviews = list_reviews()
    reviews_by_course: Dict[str, List[Dict[str, Any]]] = {}

    for review in all_reviews:
        course = _get_review_course(review)
        if course is None:
            continue
        reviews_by_course.setdefault(course, []).append(review)

    global_averages = {
        metric: fmean(_compute_metric_average(review, metric) for review in all_reviews) if all_reviews else 0.0
        for metric in METRICS
    }

    group_courses = {
        group: set(_get_all_courses_in_group_from_catalog(group, catalog))
        for group in GROUPS
    }

    return {
        "reviews_by_course": reviews_by_course,
        "global_averages": global_averages,
        "group_courses": group_courses,
    }


def _rank_group(group: str, reviews_by_course: Dict[str, List[Dict[str, Any]]], global_averages: Dict[str, float], group_courses: set[str]) -> MetricRankings:
    course_dict: Dict[str, Dict[str, Any]] = {}
    ranking_rows: Dict[str, List[CourseRankRow]] = {metric: [] for metric in METRICS}

    for course in sorted(group_courses):
        reviews = reviews_by_course.get(course, [])
        if not reviews:
            continue

        course_dict[course] = {
            "total_reviews": len(reviews),
            "totals": {metric: 0.0 for metric in METRICS},
        }

        for review in reviews:
            for metric in METRICS:
                course_dict[course]["totals"][metric] += _compute_metric_average(review, metric)

    for course, stats in course_dict.items():
        v = stats["total_reviews"]

        for metric in METRICS:
            r = stats["totals"][metric] / v
            c = global_averages[metric]
            bayesian_score = get_bayesian_score(v, MINIMUM_REVIEW_THRESHOLD, c, r)

            ranking_rows[metric].append(
                CourseRankRow(
                    course=course,
                    bayesian_score=float(bayesian_score),
                    numerical_score=float(r),
                    num_reviews=v,
                )
            )

    for metric in METRICS:
        ranking_rows[metric].sort(
            key=lambda row: row.bayesian_score,
            reverse=True,
        )

    return MetricRankings(**ranking_rows)


def get_rankings_for_group(group: str) -> MetricRankings:
    catalog = get_course_catalog()
    context = _build_ranking_context(catalog)
    return _rank_group(
        group=group,
        reviews_by_course=context["reviews_by_course"],
        global_averages=context["global_averages"],
        group_courses=context["group_courses"][group.strip().lower()],
    )


def get_all_rankings_by_group() -> GroupedCourseRankings:
    catalog = get_course_catalog()
    context = _build_ranking_context(catalog)

    rankings: Dict[str, MetricRankings] = {}
    for group in GROUPS:
        rankings[group] = _rank_group(
            group=group,
            reviews_by_course=context["reviews_by_course"],
            global_averages=context["global_averages"],
            group_courses=context["group_courses"][group],
        )

    return GroupedCourseRankings(**rankings)
