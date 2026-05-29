import React, { useState } from "react";
import MainSchedulingPage from "./pages/MainSchedulingPage";
import CourseEvaluationInputPage from "./pages/CourseEvaluationInputPage";
import CourseRecommenderRankingPage from "./pages/CourseRecommenderRankingPage";

const PAGE_OPTIONS = [
  { key: "schedule", label: "Main Scheduling Page" },
  { key: "evaluation", label: "Course Evaluation Input Page" },
  { key: "recommender", label: "Course Recommender Ranking Page" }
];

function App() {
  const [activePage, setActivePage] = useState("schedule");

  return (
    <div className="app-frame">
      <nav className="top-nav" aria-label="Page navigation">
        <div className="top-nav-brand">
          <span className="eyebrow">Rice CS Planner</span>
          <strong>Course Tools</strong>
        </div>

        <div className="top-nav-links">
          {PAGE_OPTIONS.map((page) => (
            <button
              key={page.key}
              type="button"
              className={activePage === page.key ? "nav-tab active" : "nav-tab"}
              onClick={() => setActivePage(page.key)}
            >
              {page.label}
            </button>
          ))}
        </div>
      </nav>

      {activePage === "schedule" ? (
        <MainSchedulingPage />
      ) : activePage === "evaluation" ? (
        <CourseEvaluationInputPage />
      ) : (
        <CourseRecommenderRankingPage />
      )}
    </div>
  );
}

export default App;
