from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List

import numpy as np
import voyageai


STOP_TOKENS = {
	"General Announcements",
	"Building Codes",
	"Classroom Photos & Technology",
	"Spring 2026 Courses with Required or Recommended Only Open Education Resources",
}

LABELS = {
	"Long Title": "long_title",
	"Department": "department",
	"Instructor": "instructors",
	"Instructors": "instructors",
	"Meeting": "meeting",
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
		"instructors": [],
		"meeting": None,
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
				if field_name == "instructors":
					output["instructors"] = [x for x in block.split("\n") if x]
				elif block:
					output[field_name] = block
				i = next_i
				continue
		i += 1

	description_text = str(output.get("description") or "")
	output.update(_extract_metadata_from_description(description_text))

	return output


def build_texts_from_rows(rows: List[Dict[str, object]]) -> List[str]:
	texts: List[str] = []

	for row in rows:
		raw_text = str(row.get("raw_text") or "")
		if not raw_text:
			continue
		parsed = parse_raw_text(raw_text)
		course_code = str(parsed.get("course_code") or "UNKNOWN 000")
		long_title = str(parsed.get("long_title") or "No title")
		description = str(parsed.get("description") or "No description")
		prereqs = str(parsed.get("prerequisites") or "None")
		recommended = str(parsed.get("recommended_prerequisites") or "None")

		texts.append(
			f"{course_code}: {long_title}. Description: {description}. "
			f"Prerequisites: {prereqs}. Recommended prerequisites: {recommended}."
		)

	return texts


def run_voyage_model(texts: List[str], query: str) -> None:
	api_key = "pa-b30JUu7a0QTJuZGBWvv3KoSiupw332No-L00PeTPzfN"

	vo = voyageai.Client(api_key=api_key)
	batch_size = 128
	all_embeddings: List[List[float]] = []

	for i in range(0, len(texts), batch_size):
		batch = texts[i : i + batch_size]
		result = vo.embed(batch, model="voyage-4-large", input_type="document")
		all_embeddings.extend(result.embeddings)
		print(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} courses...")

	doc_embeddings = np.array(all_embeddings)
	query_embedding = np.array(vo.embed([query], model="voyage-4-large", input_type="query").embeddings[0])

	scores = np.dot(doc_embeddings, query_embedding)
	top_indices = np.argsort(scores)[::-1][:50]
	top_candidates = [texts[i] for i in top_indices]

	rerank_result = vo.rerank(query, top_candidates, model="rerank-2.5", top_k=10)

	print(f"\nTop courses for query: {query}")
	print("-" * 80)
	for item in rerank_result.results:
		course_code = item.document.split(":", 1)[0]
		print(f"{course_code}: {item.relevance_score:.4f}")


if __name__ == "__main__":
	base_dir = Path(__file__).resolve().parent
	json_path = base_dir / "rice_course_pages.json"
	if not json_path.exists():
		json_path = base_dir / "data" / "rice_course_pages.json"

	with json_path.open("r", encoding="utf-8") as f:
		rows = json.load(f)

	texts = build_texts_from_rows(rows)
	print(f"Total parsed courses in texts: {len(texts)}")

	query = "a course that teaches me linear algebra"
	run_voyage_model(texts=texts, query=query)