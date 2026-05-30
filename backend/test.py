# import os
# import numpy as np
# import voyageai
# from repositories.course_repository import get_course_catalog

# vo = voyageai.Client(api_key="pa-b3OJUu7aOQTJuZGBWvv3KoSiupw332No-LO0PeTPzfN")

# query = "a course that teaches me linear algebra"
# catalog = get_course_catalog()

# # Build candidate list
# courses = sorted(catalog.values(), key=lambda c: (c.subject, c.course_number))
# texts = [
#     f"{course.subject} {course.course_number}: {course.long_title or 'No description'}"
#     for course in courses
# ]

# print(f"Total courses: {len(texts)}")

# # --- Stage 1: Embedding search (handles all 3260 courses) ---
# # Embed in batches (max 120K tokens per request)
# BATCH_SIZE = 128
# all_embeddings = []

# for i in range(0, len(texts), BATCH_SIZE):
#     batch = texts[i:i + BATCH_SIZE]
#     result = vo.embed(batch, model="voyage-4-large", input_type="document")
#     all_embeddings.extend(result.embeddings)
#     print(f"Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} courses...")

# doc_embeddings = np.array(all_embeddings)

# # Embed the query
# query_embedding = np.array(
#     vo.embed([query], model="voyage-4-large", input_type="query").embeddings[0]
# )

# # Get top 50 by cosine similarity
# scores = np.dot(doc_embeddings, query_embedding)
# top_indices = np.argsort(scores)[::-1][:50]
# top_candidates = [texts[i] for i in top_indices]

# print(f"\nTop 50 candidates shortlisted, reranking...")

# # --- Stage 2: Rerank top 50 → final top 5 ---
# rerank_result = vo.rerank(query, top_candidates, model="rerank-2.5", top_k=5)

# print(f"\nTop courses for: '{query}'")
# print("-" * 60)
# for item in rerank_result.results:
#     print(f"{item.relevance_score:.4f}  {item.document}")

from repositories.course_repository import get_course_catalog
courses = get_course_catalog()
print(courses['COMP 140'])