from __future__ import annotations

import json
import os
import re
from pathlib import Path
from functools import lru_cache
from typing import Dict, List

import numpy as np
import voyageai


def _read_env_file(path: Path) -> dict[str, str]:
	values: dict[str, str] = {}
	if not path.exists():
		return values

	for line in path.read_text(encoding="utf-8").splitlines():
		stripped = line.strip()
		if not stripped or stripped.startswith("#") or "=" not in stripped:
			continue
		key, value = stripped.split("=", 1)
		values[key.strip()] = value.strip().strip('"').strip("'")

	return values


def resolve_voyage_api_key() -> str:
	env_key = os.getenv("VOYAGE_API_KEY", "").strip()
	if env_key:
		return env_key

	backend_dir = Path(__file__).resolve().parent.parent
	candidate_env_files = [
		backend_dir.parent / ".env",
		backend_dir / ".env",
		backend_dir / "data" / ".env",
	]

	for env_path in candidate_env_files:
		values = _read_env_file(env_path)
		key = values.get("VOYAGE_API_KEY", "").strip()
		if key:
			return key

	raise RuntimeError("VOYAGE_API_KEY not found in environment or .env files.")


STOP_TOKENS = {
	"General Announcements",
	"Building Codes",
	"Classroom Photos & Technology",
	"Spring 2026 Courses with Required or Recommended Only Open Education Resources",
}

LABELS = {
	"Long Title": "long_title",
	"Department": "department",
	"Part of Term": "part_of_term",
	"Grade Mode": "grade_mode",
	"Course Type": "course_type",
	"Language of Instruction": "language_of_instruction",
	"Method of Instruction": "method_of_instruction",
	"Credit Hours": "credit_hours",
	"Distribution Group": "distribution_group",
	"Restrictions": "restrictions",
	"Prerequisites": "prerequisites",
	"Recommended Prerequisite(s)": "recommended_prerequisites",
	"Recommended Prerequisites": "recommended_prerequisites",
	"Description": "description",
	"Additional Fees": "additional_fees",
	"Final Exam": "final_exam",
	"Final Exam Time": "final_exam_time",
	"Final Exam Times": "final_exam_time",
}


def _clean_line(line: str) -> str:
	return " ".join(line.replace("\xa0", " ").split()).strip()


def _is_label_line(line: str) -> bool:
	normalized = _clean_line(line)
	if not normalized.endswith(":"):
		return False
	label = normalized[:-1]
	return label in LABELS


def _extract_block(lines: List[str], start_idx: int) -> tuple[str, int]:
	values: List[str] = []
	i = start_idx

	while i < len(lines):
		cur = _clean_line(lines[i])
		if not cur:
			i += 1
			continue
		if cur in STOP_TOKENS or _is_label_line(cur):
			break
		values.append(cur)
		i += 1

	return "\n".join(values).strip(), i


def _extract_metadata_from_description(description: str) -> Dict[str, object]:
	cross_lists = re.findall(r"Cross-list:\s*([A-Z]{2,5}\s+\d{3})", description, flags=re.IGNORECASE)
	mutually_exclusive = re.findall(
		r"Mutually Exclusive:\s*([^\.]+)\.",
		description,
		flags=re.IGNORECASE,
	)
	return {
		"cross_list": [" ".join(item.upper().split()) for item in cross_lists],
		"mutually_exclusive": [item.strip() for item in mutually_exclusive],
		"repeatable_for_credit": bool(re.search(r"Repeatable for Credit", description, flags=re.IGNORECASE)),
	}


def parse_raw_text(raw_text: str) -> Dict[str, object]:
	"""Parse a raw Rice course page blob into a structured dictionary."""
	lines = [line.rstrip() for line in raw_text.splitlines()]
	output: Dict[str, object] = {
		"subject": None,
		"course_number": None,
		"section": None,
		"course_code": None,
		"crn": None,
		"short_title": None,
		"long_title": None,
		"department": None,
		"part_of_term": None,
		"grade_mode": None,
		"course_type": None,
		"language_of_instruction": None,
		"method_of_instruction": None,
		"credit_hours": None,
		"distribution_group": None,
		"restrictions": None,
		"prerequisites": None,
		"recommended_prerequisites": None,
		"description": None,
		"additional_fees": None,
		"final_exam": None,
		"final_exam_time": None,
		"cross_list": [],
		"mutually_exclusive": [],
		"repeatable_for_credit": False,
	}

	for i, line in enumerate(lines):
		cleaned = _clean_line(line)
		match = re.match(r"^([A-Z]{2,5})\s+(\d{3})(?:\s+([A-Z0-9]{1,4}))?$", cleaned)
		if match:
			output["subject"] = match.group(1)
			output["course_number"] = match.group(2)
			output["section"] = match.group(3)
			output["course_code"] = f"{match.group(1)} {match.group(2)}"
			# The line after CRN block is usually the short title.
			for j in range(i + 1, min(i + 10, len(lines))):
				candidate = _clean_line(lines[j])
				if not candidate:
					continue
				if "(CRN:" in candidate:
					continue
				if candidate.endswith(":"):
					continue
				output["short_title"] = candidate
				break
			break

	if output["course_code"] is None:
		code_match = re.search(r"\b([A-Z]{2,5})\s+(\d{3})\b", raw_text)
		if code_match:
			output["subject"] = code_match.group(1)
			output["course_number"] = code_match.group(2)
			output["course_code"] = f"{code_match.group(1)} {code_match.group(2)}"

	crn_match = re.search(r"\(CRN:\s*(\d+)\)", raw_text)
	if crn_match:
		output["crn"] = int(crn_match.group(1))

	i = 0
	while i < len(lines):
		cleaned = _clean_line(lines[i])
		if cleaned.endswith(":"):
			label = cleaned[:-1]
			field_name = LABELS.get(label)
			if field_name:
				block, next_i = _extract_block(lines, i + 1)
				if block:
					output[field_name] = block
				i = next_i
				continue
		i += 1

	description_text = str(output.get("description") or "")
	output.update(_extract_metadata_from_description(description_text))

	return output


def build_texts_from_rows(rows: List[Dict[str, object]]) -> List[str]:
	return [record["text"] for record in build_recommendation_records(rows)]


def build_recommendation_records(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
	records: List[Dict[str, object]] = []
	seen_offerings: set[tuple[str, str | None, int | None]] = set()

	for row in rows:
		raw_text = str(row.get("raw_text") or "")
		if not raw_text:
			continue
		parsed = parse_raw_text(raw_text)
		course_code = str(parsed.get("course_code") or "UNKNOWN 000")
		term_value = row.get("term")
		term = str(term_value).strip() if term_value not in (None, "") else None
		crn_value = row.get("crn")
		if crn_value in (None, ""):
			crn_value = parsed.get("crn")
		crn = int(crn_value) if crn_value not in (None, "") else None
		offering_key = (course_code, term, crn)
		if offering_key in seen_offerings:
			continue
		seen_offerings.add(offering_key)
		long_title = str(parsed.get("long_title") or "No title")
		description = str(parsed.get("description") or "No description")
		prereqs = str(parsed.get("prerequisites") or "None")
		recommended = str(parsed.get("recommended_prerequisites") or "None")

		records.append(
			{
				"course": course_code,
				"term": term,
				"crn": crn,
				"text": (
					f"{course_code}: {long_title}. Description: {description}. "
					f"Prerequisites: {prereqs}. Recommended prerequisites: {recommended}."
				),
			}
		)

	return records


def _embed_texts(
	texts: List[str],
	client: voyageai.Client,
	model: str = "voyage-4-large",
	batch_size: int = 128,
) -> np.ndarray:
	all_embeddings: List[List[float]] = []

	for i in range(0, len(texts), batch_size):
		batch = texts[i : i + batch_size]
		result = client.embed(batch, model=model, input_type="document")
		all_embeddings.extend(result.embeddings)
		print(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} courses...")

	return np.asarray(all_embeddings, dtype=np.float32)


def load_or_generate_embeddings(
	texts: List[str],
	client: voyageai.Client,
	embeddings_path: Path,
	model: str = "voyage-4-large",
	batch_size: int = 128,
) -> np.ndarray:
	if embeddings_path.exists():
		matrix = np.load(embeddings_path)
		if matrix.ndim == 2 and matrix.shape[0] == len(texts):
			print(f"Loaded embeddings from {embeddings_path} with shape {matrix.shape}")
			return matrix.astype(np.float32, copy=False)
		print(
			f"Embedding file shape {matrix.shape} does not match texts length {len(texts)}. Regenerating..."
		)

	matrix = _embed_texts(texts=texts, client=client, model=model, batch_size=batch_size)
	np.save(embeddings_path, matrix)
	print(f"Saved embeddings to {embeddings_path} with shape {matrix.shape}")
	return matrix


@lru_cache(maxsize=1)
def _load_recommendation_records() -> tuple[Dict[str, object], ...]:
	backend_dir = Path(__file__).resolve().parent.parent
	json_path = backend_dir / "data" / "rice_course_pages.json"

	with json_path.open("r", encoding="utf-8") as f:
		rows = json.load(f)

	return tuple(build_recommendation_records(rows))


@lru_cache(maxsize=1)
def _load_recommendation_embeddings(embeddings_path_str: str) -> np.ndarray:
	records = list(_load_recommendation_records())
	backend_dir = Path(__file__).resolve().parent.parent
	embeddings_path = Path(embeddings_path_str)
	api_key = "pa-b3OJUu7aOQTJuZGBWvv3KoSiupw332No-LO0PeTPzfN"
	vo = voyageai.Client(api_key=api_key)
	texts = [record["text"] for record in records]
	return load_or_generate_embeddings(texts=texts, client=vo, embeddings_path=embeddings_path)


def run_voyage_model(
	records: List[Dict[str, object]],
	query: str,
	embeddings_path: Path,
	top_k: int = 10,
	shortlist_k: int = 50,
) -> List[Dict[str, object]]:
	api_key = "pa-b3OJUu7aOQTJuZGBWvv3KoSiupw332No-LO0PeTPzfN"
	vo = voyageai.Client(api_key=api_key)

	doc_embeddings = _load_recommendation_embeddings(str(embeddings_path))
	query_embedding = np.asarray(
		vo.embed([query], model="voyage-4-large", input_type="query").embeddings[0],
		dtype=np.float32,
	)

	texts = [record["text"] for record in records]
	scores = np.dot(doc_embeddings, query_embedding)
	top_indices = np.argsort(scores)[::-1][: max(1, min(shortlist_k, len(texts)))]
	top_candidates = [records[i] for i in top_indices]

	rerank_result = vo.rerank(
		query,
		[record["text"] for record in top_candidates],
		model="rerank-2.5",
		top_k=max(1, len(top_candidates)),
	)

	recommendations: List[Dict[str, object]] = []
	seen_courses: set[str] = set()

	for item in rerank_result.results:
		candidate_index = getattr(item, "index", None)
		if isinstance(candidate_index, int) and 0 <= candidate_index < len(top_candidates):
			record = top_candidates[candidate_index]
		else:
			document_text = str(getattr(item, "document", ""))
			record = next(
				(record for record in top_candidates if str(record.get("text")) == document_text),
				top_candidates[0],
			)

		course_code = str(record.get("course") or "")
		if not course_code or course_code in seen_courses:
			continue

		seen_courses.add(course_code)
		recommendations.append(
			{
				"course": course_code,
				"term": record.get("term"),
				"crn": record.get("crn"),
			}
		)
		if len(recommendations) >= max(1, min(top_k, len(records))):
			break

	return recommendations


def get_course_recommendations(query: str, top_k: int = 10) -> List[Dict[str, object]]:
	backend_dir = Path(__file__).resolve().parent.parent
	embeddings_path = backend_dir / "data" / "course_embeddings.npy"
	records = list(_load_recommendation_records())
	if not records:
		return []

	return run_voyage_model(records=records, query=query, embeddings_path=embeddings_path, top_k=top_k)


if __name__ == "__main__":
	backend_dir = Path(__file__).resolve().parent.parent
	embeddings_path = backend_dir / "data" / "course_embeddings.npy"
	records = list(_load_recommendation_records())
	print(f"Total parsed course offerings in records: {len(records)}")

	query = "a course that teaches me about computational linear algebra"
	courses = run_voyage_model(records=records, query=query, embeddings_path=embeddings_path)
	print(f"\nTop courses for query: {query}")
	print("-" * 80)
	for course in courses:
		print(course)