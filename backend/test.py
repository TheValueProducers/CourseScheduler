from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import voyageai

from services.course_service import build_texts_from_rows


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
	env_key = "pa-b3OJUu7aOQTJuZGBWvv3KoSiupw332No-LO0PeTPzfN"
	if env_key:
		return env_key

	backend_dir = Path(__file__).resolve().parent
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

	raise RuntimeError(
		"VOYAGE_API_KEY not found. Set it in shell or in .env (repo root/backend/data)."
	)


def generate_embeddings() -> None:
	backend_dir = Path(__file__).resolve().parent
	data_dir = backend_dir / "data"
	json_path = data_dir / "rice_course_pages.json"
	output_path = data_dir / "course_embeddings.npy"

	api_key = resolve_voyage_api_key()
	client = voyageai.Client(api_key=api_key)

	with json_path.open("r", encoding="utf-8") as f:
		rows = json.load(f)

	texts = build_texts_from_rows(rows)
	if not texts:
		raise RuntimeError("No course texts generated from rice_course_pages.json")

	all_embeddings: list[list[float]] = []
	batch_size = 128
	for i in range(0, len(texts), batch_size):
		batch = texts[i : i + batch_size]
		result = client.embed(batch, model="voyage-4-large", input_type="document")
		all_embeddings.extend(result.embeddings)
		print(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)}")

	matrix = np.asarray(all_embeddings, dtype=np.float32)
	np.save(output_path, matrix)

	print(f"Saved embeddings to {output_path}")
	print(f"Embedding shape: {matrix.shape}")


if __name__ == "__main__":
	generate_embeddings()
