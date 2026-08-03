from __future__ import annotations

import re
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

# Ensure backend package imports work when running from accuracy_tests/.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db.database import SessionLocal
from mock_quries import COURSE_RELEVANCE_GROUND_TRUTH
from repositories.course_repository import CourseRepository
from services.course_service import (
    get_course_recommendations as get_course_recommendations_service,
)

# Unbound method reference; pass a CourseRepository instance as the first arg.
execute_read_only_sql = CourseRepository.execute_read_only_sql

TOP_K = 10

# Evaluate every query in the ground-truth mapping.
QUERIES = list(COURSE_RELEVANCE_GROUND_TRUTH)


INTENT_PHRASES = re.compile(
    r"\b(?:"
    r"give me|find me|show me|"
    r"i want|i want to learn|"
    r"i am looking for|i['’]m looking for"
    r")\b",
    re.IGNORECASE,
)

GENERIC_WORDS = re.compile(
    r"\b(?:"
    r"a|an|the|course|courses|class|classes|"
    r"about|on|covering|cover|that|teach|teaches|"
    r"exploring|explore"
    r")\b",
    re.IGNORECASE,
)


def postgres_query_terms(query: str) -> tuple[str, str]:
    cleaned = INTENT_PHRASES.sub(" ", query)
    cleaned = GENERIC_WORDS.sub(" ", cleaned)

    # Prevent hyphens from being interpreted as PostgreSQL NOT operators.
    tokens = re.findall(r"[a-zA-Z0-9]+", cleaned.lower())

    and_query = " ".join(tokens)
    or_query = " OR ".join(tokens)

    return and_query, or_query


POSTGRES_SEARCH_SQL = """
WITH search_terms AS (
    SELECT
        websearch_to_tsquery(
            'english',
            :and_query
        ) AS and_query,
        websearch_to_tsquery(
            'english',
            :or_query
        ) AS or_query
),
course_documents AS (
    SELECT
        c.code,
        c.subject,
        c.course_number,
        c.long_title,
        (
            setweight(
                to_tsvector(
                    'english',
                    coalesce(c.code, '')
                ),
                'A'
            )
            ||
            setweight(
                to_tsvector(
                    'english',
                    coalesce(c.long_title, '')
                ),
                'A'
            )
            ||
            setweight(
                to_tsvector(
                    'english',
                    coalesce(c.subject, '')
                ),
                'B'
            )
        ) AS document
    FROM courses AS c
)
SELECT
    c.code,
    c.subject,
    c.course_number,
    c.long_title,
    c.document @@ q.and_query AS matches_all_terms,
    ts_rank_cd(
        c.document,
        q.or_query
    ) AS score
FROM course_documents AS c
CROSS JOIN search_terms AS q
WHERE c.document @@ q.or_query
ORDER BY
    matches_all_terms DESC,
    score DESC,
    c.code ASC
"""


def run_postgres_search(query: str) -> list[dict[str, Any]]:
    and_query, or_query = postgres_query_terms(query)

    with SessionLocal() as db:
        repository = CourseRepository(db)

        return execute_read_only_sql(
            repository,
            POSTGRES_SEARCH_SQL,
            params={
                "and_query": and_query,
                "or_query": or_query,
            },
            max_rows=TOP_K,
        )


def run_voyage_search(query: str) -> Any:
    return get_course_recommendations_service(query=query)


def normalize_service_result(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()

    if isinstance(value, list):
        return [
            normalize_service_result(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: normalize_service_result(item)
            for key, item in value.items()
        }

    return value


def normalize_course_code(code: Any) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(code).strip().upper(),
    )


def extract_course_codes(
    results: Any,
    code_key: str,
) -> list[str]:
    if not isinstance(results, list):
        raise TypeError(
            f"Expected results to be a list, "
            f"received {type(results).__name__}."
        )

    return [
        normalize_course_code(result[code_key])
        for result in results[:TOP_K]
        if isinstance(result, dict) and result.get(code_key)
    ]


def calculate_recall_at_10(
    retrieved_codes: list[str],
    relevant_codes: list[str],
) -> float:
    relevant_set = {
        normalize_course_code(code)
        for code in relevant_codes
    }

    if not relevant_set:
        raise ValueError(
            "Cannot calculate recall without relevant courses."
        )

    retrieved_set = {
        normalize_course_code(code)
        for code in retrieved_codes[:TOP_K]
    }

    relevant_retrieved = retrieved_set & relevant_set

    return len(relevant_retrieved) / len(relevant_set)


def run_evaluation() -> list[dict[str, Any]]:
    recall_results: list[dict[str, Any]] = []

    for index, query in enumerate(QUERIES, start=1):
        relevant_codes = COURSE_RELEVANCE_GROUND_TRUTH[query]

        # Suppress output generated internally by the search services.
        with redirect_stdout(StringIO()):
            postgres_results = run_postgres_search(query)

            voyage_results = normalize_service_result(
                run_voyage_search(query)
            )

        postgres_codes = extract_course_codes(
            results=postgres_results,
            code_key="code",
        )

        voyage_codes = extract_course_codes(
            results=voyage_results,
            code_key="course",
        )

        postgres_recall = calculate_recall_at_10(
            retrieved_codes=postgres_codes,
            relevant_codes=relevant_codes,
        )

        voyage_recall = calculate_recall_at_10(
            retrieved_codes=voyage_codes,
            relevant_codes=relevant_codes,
        )

        recall_results.append(
            {
                "query": query,
                "postgresql_recall_at_10": postgres_recall,
                "voyage_ai_recall_at_10": voyage_recall,
            }
        )

        print(f"{index}. {query}")
        print(f"PostgreSQL Recall@10: {postgres_recall:.1%}")
        print(f"VoyageAI Recall@10:   {voyage_recall:.1%}")
        print()

    if recall_results:
        average_postgres_recall = sum(
            result["postgresql_recall_at_10"]
            for result in recall_results
        ) / len(recall_results)

        average_voyage_recall = sum(
            result["voyage_ai_recall_at_10"]
            for result in recall_results
        ) / len(recall_results)

        print("=" * 80)
        print("AVERAGE RECALL@10")
        print("=" * 80)
        print(
            f"PostgreSQL Average Recall@10: "
            f"{average_postgres_recall:.1%}"
        )
        print(
            f"VoyageAI Average Recall@10:   "
            f"{average_voyage_recall:.1%}"
        )

    return recall_results



if __name__ == "__main__":
    recall_results = run_evaluation()