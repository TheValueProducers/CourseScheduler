import React, { useEffect, useState } from "react";

const API_URL = "http://localhost:8000";

const RANKING_METRICS = [
  { key: "workload", label: "Least Workload" },
  { key: "overall_diff", label: "Easiest Classes" },
  { key: "instructor", label: "Best Teaching" },
  { key: "usefulness", label: "Most Useful" },
  { key: "interest", label: "Most Interesting" }
];

const RANKING_GROUPS = [
  {
    key: "d1",
    title: "Distribution Classes (D1)"
  },
  {
    key: "d2",
    title: "Distribution Classes (D2)"
  },
  {
    key: "d3",
    title: "Distribution Classes (D3)"
  },
  {
    key: "diversity",
    title: "Analyzing Diversity Classes"
  },
  {
    key: "lpap",
    title: "Lifetime Physical Activity Program (LPAP)"
  }
];

const EMPTY_RANKINGS = {
  d1: {},
  d2: {},
  d3: {},
  diversity: {},
  lpap: {}
};

function formatScore(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toFixed(2);
}

function renderScoreStars(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "☆☆☆☆☆";
  }

  const rounded = Math.max(0, Math.min(5, Math.round(Number(value))));
  return `${"★".repeat(rounded)}${"☆".repeat(5 - rounded)}`;
}

function CourseRecommenderRankingPage() {
  const [rankings, setRankings] = useState(EMPTY_RANKINGS);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    async function loadRankings() {
      setIsLoading(true);
      setLoadError("");

      try {
        const response = await fetch(`${API_URL}/api/rankings`);
        if (!response.ok) {
          throw new Error(`Unable to load rankings: ${response.status}`);
        }

        const data = await response.json();
        setRankings({
          d1: data.d1 && typeof data.d1 === "object" ? data.d1 : {},
          d2: data.d2 && typeof data.d2 === "object" ? data.d2 : {},
          d3: data.d3 && typeof data.d3 === "object" ? data.d3 : {},
          diversity: data.diversity && typeof data.diversity === "object" ? data.diversity : {},
          lpap: data.lpap && typeof data.lpap === "object" ? data.lpap : {}
        });
      } catch (error) {
        setLoadError(String(error.message || error));
      } finally {
        setIsLoading(false);
      }
    }

    loadRankings();
  }, []);

  return (
    <div className="page-shell recommender-shell">
      <div className="hero-glow" />
      <main className="layout recommender-layout">
        <header className="hero">
          <p className="eyebrow">Rice CS Course Reviews</p>
          <h1>Course Recommender Ranking Page</h1>
          <p>
            Browse Bayesian-ranked courses for D1, D2, D3, diversity, and LPAP based on submitted course reviews.
          </p>
        </header>

        <section className="panel">
          <div className="panel-head">
            <h2>Ranking overview</h2>
            <span className="subtle">Sorted by Bayesian score (descending)</span>
          </div>

          {isLoading && <p className="subtle">Loading rankings...</p>}
          {loadError && <p className="error">{loadError}</p>}

          <div className="ranking-group-grid">
            {RANKING_GROUPS.map((group) => (
              <article className="ranking-group-card" key={group.title}>
                <div className="ranking-group-head">
                  <h3>{group.title}</h3>
                  <p>Metric-level ranking cards</p>
                </div>

                <div className="ranking-metric-grid">
                  {RANKING_METRICS.map((metric) => {
                    const rows = rankings[group.key]?.[metric.key] || [];

                    return (
                      <section className="ranking-metric-card" key={`${group.key}-${metric.key}`}>
                        <div className="ranking-metric-head">
                          <h4>{metric.label}</h4>
                        </div>

                        {!isLoading && rows.length === 0 ? (
                          <p className="ranking-empty-state">No courses ranked yet.</p>
                        ) : (
                          <div className="ranking-course-grid">
                            {rows.map((row, index) => (
                              <article className="ranking-course-block" key={`${group.key}-${metric.key}-${row.course}`}>
                                <div className="ranking-course-top">
                                  <span className="ranking-course-rank">#{index + 1}</span>
                                  <strong className="ranking-course-name">{row.course}</strong>
                                </div>
                                <div className="ranking-stars" aria-label={`${formatScore(row.numerical_score)} out of 5 stars`}>
                                  {renderScoreStars(row.numerical_score)}
                                </div>
                                <div className="ranking-course-meta">
                                  <span>Numerical score: {formatScore(row.numerical_score)}</span>
                                  <span>Reviews: {row.num_reviews}</span>
                                </div>
                              </article>
                            ))}
                          </div>
                        )}
                      </section>
                    );
                  })}
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default CourseRecommenderRankingPage;