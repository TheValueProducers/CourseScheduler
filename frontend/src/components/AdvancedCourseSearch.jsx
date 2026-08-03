import React, { useState } from "react";

const API_URL = "http://localhost:8000";

const CATALOG_TERM_MAP = {
  "Fall 2026": "202610",
  "Spring 2026": "202620"
};

function buildCatalogUrl(term, crn) {
  const mappedTerm = typeof term === "string" ? CATALOG_TERM_MAP[term] : undefined;
  if (!mappedTerm || crn === null || crn === undefined) {
    return null;
  }

  const normalizedCrn = String(crn).trim();
  if (!normalizedCrn) {
    return null;
  }

  return `https://courses.rice.edu/courses/!SWKSCAT.cat?p_action=COURSE&p_term=${mappedTerm}&p_crn=${encodeURIComponent(normalizedCrn)}`;
}

function AdvancedCourseSearch({ filters }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    const trimmed = query.trim();
    if (!trimmed) {
      setError("Enter a search prompt before submitting.");
      setResults([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/course-recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: trimmed,
          filters: {
            course_level: filters?.courseLevel,
            distribution: filters?.distribution ? Number(filters.distribution) : null,
            analyzing_diversity: Boolean(filters?.analyzingDiversity),
            subject: filters?.subject?.trim() || null,
          },
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Request failed: ${response.status}`);
      }

      setResults(Array.isArray(data.courses) ? data.courses : []);
    } catch (nextError) {
      setError(String(nextError.message || nextError));
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel advanced-search-panel">
      <div className="panel-head">
        <h2>Advanced Search</h2>
      </div>

      <p className="subtle">Search for classes and review relevant matches before adding them to your plan.</p>

      <form className="advanced-search-form" onSubmit={handleSubmit}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="e.g. Give me a class about computational linear algebra"
          aria-label="Advanced class search"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      <div className="advanced-search-results" aria-live="polite">
        {loading ? (
          <p className="subtle">Searching for relevant classes...</p>
        ) : results.length === 0 ? (
          <p className="empty-result">No advanced search results yet.</p>
        ) : (
          <ul className="advanced-search-result-list">
            {results.map((result, idx) => {
              const course = typeof result === "string" ? result : result.course;
              const term = typeof result === "string" ? null : result.term;
              const crn = typeof result === "string" ? null : result.crn;
              const courseUrl = buildCatalogUrl(term, crn);

              return (
                <li key={`${course}-${crn ?? idx}`}>
                  {courseUrl ? (
                    <a className="advanced-search-course advanced-search-course-link" href={courseUrl} target="_blank" rel="noreferrer">
                      {course}
                    </a>
                  ) : (
                    <div className="advanced-search-course">{course}</div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}

export default AdvancedCourseSearch;
