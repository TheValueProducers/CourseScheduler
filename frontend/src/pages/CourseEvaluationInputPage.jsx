import React, { useEffect, useMemo, useState } from "react";

const API_URL = "http://localhost:8000";

const EVALUATION_SECTIONS = [
  {
    key: "workload",
    title: "Overall workload",
    prompt: "How much time each week outside of class?",
    ratings: [
      { value: 1, description: "Extremely heavy (16+ hrs/week)" },
      { value: 2, description: "Heavy (11-15 hrs/week)" },
      { value: 3, description: "Moderate (7-10 hrs/week)" },
      { value: 4, description: "Light (4-6 hrs/week)" },
      { value: 5, description: "Very light (0-3 hrs/week)" }
    ]
  },
  {
    key: "difficulty",
    title: "Content difficulty",
    prompt: "How intellectually challenging was the course material?",
    ratings: [
      { value: 1, description: "Extremely difficult and highly abstract" },
      { value: 2, description: "Difficult concepts requiring significant effort" },
      { value: 3, description: "Moderately challenging" },
      { value: 4, description: "Mostly straightforward" },
      { value: 5, description: "Very easy concepts" }
    ]
  },
  {
    key: "examDifficulty",
    title: "Exam difficulty",
    prompt: "How difficult were the quizzes/exams in this course?",
    ratings: [
      { value: 1, description: "Extremely difficult/unpredictable" },
      { value: 2, description: "Difficult and time-pressured" },
      { value: 3, description: "Fair difficulty" },
      { value: 4, description: "Easier than expected" },
      { value: 5, description: "Very easy exams" }
    ]
  },
  {
    key: "projectDifficulty",
    title: "Project/assignment difficulty",
    prompt: "How difficult were the projects and assignments?",
    ratings: [
      { value: 1, description: "Extremely demanding projects" },
      { value: 2, description: "Challenging and time-consuming" },
      { value: 3, description: "Moderate effort required" },
      { value: 4, description: "Simple and manageable" },
      { value: 5, description: "Very easy assignments" }
    ]
  },
  {
    key: "instructor",
    title: "Instructor",
    prompt: "How effective was the instructor overall?",
    ratings: [
      { value: 5, description: "Exceptional instructor. Very clear explanations, highly supportive, extremely approachable." },
      { value: 4, description: "Strong instructor. Explains concepts well and is helpful and approachable." },
      { value: 3, description: "Average instructor. Generally understandable but inconsistent at times." },
      { value: 2, description: "Weak instructor. Explanations are often unclear or support is limited." },
      { value: 1, description: "Poor instructor. Difficult to follow and not supportive." }
    ]
  },
  {
    key: "usefulness",
    title: "Practical usefulness",
    prompt: "How useful was this course for your academic or career goals? Please do not consider this for your grades.",
    ratings: [
      { value: 1, description: "Barely useful" },
      { value: 2, description: "Slightly useful" },
      { value: 3, description: "Moderately useful" },
      { value: 4, description: "Very useful" },
      { value: 5, description: "Extremely valuable and applicable" }
    ]
  },
  {
    key: "interestEnjoyment",
    title: "Interest / enjoyment",
    prompt: "How engaging, fun, or intellectually interesting was this course?",
    ratings: [
      { value: 1, description: "Very boring" },
      { value: 2, description: "Slightly uninteresting" },
      { value: 3, description: "Neutral" },
      { value: 4, description: "Interesting" },
      { value: 5, description: "Very interesting / fun" }
    ]
  }
];

const DEFAULT_RATINGS = Object.fromEntries(EVALUATION_SECTIONS.map((section) => [section.key, ""]));

function normalizeCode(course) {
  return `${course.subject} ${String(course.course_number).padStart(3, "0")}`;
}

function CourseEvaluationInputPage() {
  const [allCourses, setAllCourses] = useState([]);
  const [coursesLoading, setCoursesLoading] = useState(true);
  const [coursesError, setCoursesError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [ratings, setRatings] = useState(DEFAULT_RATINGS);
  const [hoveredRatings, setHoveredRatings] = useState(DEFAULT_RATINGS);
  const [likeInput, setLikeInput] = useState("");
  const [dislikeInput, setDislikeInput] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    async function loadCourses() {
      setCoursesLoading(true);
      setCoursesError("");

      try {
        const response = await fetch(`${API_URL}/api/courses`);
        if (!response.ok) {
          throw new Error(`Unable to load courses: ${response.status}`);
        }

        const data = await response.json();
        setAllCourses(Array.isArray(data) ? data : []);
      } catch (error) {
        setCoursesError(String(error.message || error));
      } finally {
        setCoursesLoading(false);
      }
    }

    loadCourses();
  }, []);

  const filteredCourses = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (query.length === 0) {
      return allCourses.slice(0, 10);
    }

    return allCourses
      .filter((course) => {
        const code = normalizeCode(course).toLowerCase();
        const title = (course.long_title || "").toLowerCase();
        return code.includes(query) || title.includes(query);
      })
      .slice(0, 10);
  }, [allCourses, searchQuery]);

  function handleSelectCourse(course) {
    setSelectedCourse(course);
    setSearchQuery("");
    setSubmitError("");
    setSubmitSuccess("");
  }

  function handleRatingChange(key, value) {
    setSubmitError("");
    setSubmitSuccess("");
    setRatings((prev) => ({
      ...prev,
      [key]: value
    }));
  }

  function handleRatingHover(key, value) {
    setHoveredRatings((prev) => ({
      ...prev,
      [key]: value
    }));
  }

  function handleRatingHoverLeave(key) {
    setHoveredRatings((prev) => ({
      ...prev,
      [key]: ""
    }));
  }

  function resetEvaluation() {
    setSelectedCourse(null);
    setSearchQuery("");
    setRatings(DEFAULT_RATINGS);
    setHoveredRatings(DEFAULT_RATINGS);
    setLikeInput("");
    setDislikeInput("");
    setSubmitError("");
  }

  const missingRatings = EVALUATION_SECTIONS.filter((section) => !ratings[section.key]);
  const isCourseMissing = !selectedCourse;
  const canSubmit = !isCourseMissing && missingRatings.length === 0 && !isSubmitting;

  async function handleSubmitReview() {
    setSubmitError("");
    setSubmitSuccess("");

    if (isCourseMissing || missingRatings.length > 0) {
      const missingFieldNames = missingRatings.map((section) => section.title).join(", ");
      const reason = [
        isCourseMissing ? "Please select a course." : "",
        missingFieldNames.length > 0 ? `Please provide ratings for: ${missingFieldNames}.` : ""
      ]
        .filter(Boolean)
        .join(" ");

      setSubmitError(reason || "Please complete all required inputs before submitting.");
      return;
    }

    const payload = {
      overall_workload: Number(ratings.workload),
      content_difficulty: Number(ratings.difficulty),
      exam_difficulty: Number(ratings.examDifficulty),
      project_assignment_difficulty: Number(ratings.projectDifficulty),
      instructor: Number(ratings.instructor),
      practical_usefulness: Number(ratings.usefulness),
      interest_enjoyment: Number(ratings.interestEnjoyment),
      user_like: likeInput.trim(),
      user_dislike: dislikeInput.trim(),
      course_number: String(selectedCourse.course_number).padStart(3, "0"),
      subject: selectedCourse.subject
    };

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/api/reviews`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Unable to submit review: ${response.status}`);
      }

      await response.json();
      setSubmitSuccess("Review submitted successfully.");
      setRatings(DEFAULT_RATINGS);
      setLikeInput("");
      setDislikeInput("");
      setSelectedCourse(null);
    } catch (error) {
      setSubmitError(String(error.message || error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-shell evaluation-shell">
      <div className="hero-glow" />
      <main className="layout evaluation-layout">
        <header className="hero evaluation-hero">
          <p className="eyebrow">Rice CS Course Reviews</p>
          <h1>Course Evaluation Input Page</h1>
          <p>
            Search the course catalog, choose a course, and record a structured evaluation for workload,
            difficulty, exams, projects, instructor quality, and practical usefulness.
          </p>
        </header>

        <section className="panel evaluation-panel">
          <div className="panel-head">
            <h2>Search for a course</h2>
            <span className="subtle">Courses are fetched from the catalog before you search</span>
          </div>

          <div className="evaluation-search-box">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by course code or title"
            />

            {coursesLoading && <p className="subtle evaluation-status">Loading course catalog...</p>}
            {coursesError && <p className="error">{coursesError}</p>}

            {!coursesLoading && searchQuery.trim().length > 0 && (
              <ul className="search-results evaluation-results">
                {filteredCourses.length === 0 ? (
                  <li className="empty-result">No matching courses found.</li>
                ) : (
                  filteredCourses.map((course) => {
                    const code = normalizeCode(course);
                    return (
                      <li key={`${code}-${course.long_title || ""}`}>
                        <button type="button" onClick={() => handleSelectCourse(course)}>
                          <span>{code}</span>
                          <small>{course.long_title || "Untitled course"}</small>
                        </button>
                      </li>
                    );
                  })
                )}
              </ul>
            )}
          </div>
        </section>

        <section className="panel evaluation-panel">
          <div className="panel-head">
            <h2>Selected course</h2>
            <button type="button" onClick={resetEvaluation} disabled={!selectedCourse && Object.values(ratings).every((value) => value === "")}>
              Reset
            </button>
          </div>

          {selectedCourse ? (
            <div className="selected-course-card">
              <div>
                <div className="course-code">{normalizeCode(selectedCourse)}</div>
                <div className="course-title">{selectedCourse.long_title || "Untitled course"}</div>
              </div>
              <button type="button" className="danger" onClick={() => setSelectedCourse(null)}>
                Remove course
              </button>
            </div>
          ) : (
            <p className="subtle">Choose a course from the search results to start an evaluation.</p>
          )}
        </section>

        <section className="panel evaluation-panel">
          <div className="panel-head">
            <h2>Evaluation inputs</h2>
            <span className="subtle">Pick one rating for each category. Comments are optional.</span>
          </div>

          {submitError && <p className="error">{submitError}</p>}
          {submitSuccess && <p className="success">{submitSuccess}</p>}

          <div className="evaluation-grid">
            {EVALUATION_SECTIONS.map((section) => (
              <article
                className={
                  section.key === "usefulness" ? "evaluation-card evaluation-card--usefulness" : "evaluation-card"
                }
                key={section.key}
              >
                <div className="evaluation-card-head">
                  <h3>{section.title}</h3>
                  <p>{section.prompt}</p>
                </div>

                <div className="rating-buttons" role="radiogroup" aria-label={section.title}>
                  {[1, 2, 3, 4, 5].map((value) => {
                    const previewValue = Number(hoveredRatings[section.key] || ratings[section.key] || 0);
                    const isFilled = value <= previewValue;

                    return (
                      <button
                        key={value}
                        type="button"
                        className={isFilled ? "star-button filled" : "star-button"}
                        onMouseEnter={() => handleRatingHover(section.key, value)}
                        onMouseLeave={() => handleRatingHoverLeave(section.key)}
                        onFocus={() => handleRatingHover(section.key, value)}
                        onBlur={() => handleRatingHoverLeave(section.key)}
                        onClick={() => handleRatingChange(section.key, value)}
                        aria-label={`${value} star${value > 1 ? "s" : ""}`}
                        title={`${value} / 5`}
                      >
                        ★
                      </button>
                    );
                  })}
                </div>

                <div className="rating-legend">
                  <table>
                    <thead>
                      <tr>
                        <th>Rating</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {section.ratings.map((rating) => (
                        <tr key={`${section.key}-${rating.value}`}>
                          <td>{rating.value}</td>
                          <td>{rating.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>
            ))}
          </div>

          <div className="evaluation-notes">
            <label className="evaluation-note-field">
              What you like about the class?
              <textarea
                value={likeInput}
                onChange={(e) => setLikeInput(e.target.value)}
                placeholder="Examples: teaching style, projects, real-world applications, organization, exams, collaboration, usefulness, pacing"
                rows={5}
              />
              <span className="evaluation-note-help">Examples: teaching style, projects, real-world applications, organization, exams, collaboration, usefulness, pacing</span>
            </label>

            <label className="evaluation-note-field">
              What you dislike about the class?
              <textarea
                value={dislikeInput}
                onChange={(e) => setDislikeInput(e.target.value)}
                placeholder="Examples: workload, unclear lectures, harsh grading, difficult exams, disorganization, outdated material, poor pacing"
                rows={5}
              />
              <span className="evaluation-note-help">Examples/prompts: workload, unclear lectures, harsh grading, difficult exams, disorganization, outdated material, poor pacing</span>
            </label>
          </div>

          <div className="evaluation-submit-row">
            <button type="button" onClick={handleSubmitReview} disabled={!canSubmit}>
              {isSubmitting ? "Submitting..." : "Submit Review"}
            </button>
            {!canSubmit && (
              <span className="subtle">
                Complete all ratings and choose a course before submitting.
              </span>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default CourseEvaluationInputPage;