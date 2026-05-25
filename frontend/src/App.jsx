import React, { useEffect, useMemo, useState } from "react";

const API_URL = "https://course-scheduler-nu.vercel.app";

const SEMESTERS = [
  "Freshman Fall",
  "Freshman Spring",
  "Sophomore Fall",
  "Sophomore Spring",
  "Junior Fall",
  "Junior Spring",
  "Senior Fall",
  "Senior Spring"
];
const HIGH_SCHOOL = "High School";

const STATUS_OPTIONS = ["planned", "attended"];
const PROGRESS_OPTIONS = ["planned", "attended"];
const YEAR_ORDER = ["Freshman", "Sophomore", "Junior", "Senior"];
const TERM_ORDER = ["Fall", "Spring"];

function normalizeCode(course) {
  return `${course.subject} ${String(course.course_number).padStart(3, "0")}`;
}

function parseListInput(value) {
  return value
    .split(",")
    .map((v) => v.trim().toUpperCase())
    .filter(Boolean);
}

function blankSemesterMap() {
  return Object.fromEntries(SEMESTERS.map((semester) => [semester, []]));
}

function App() {
  const [allCourses, setAllCourses] = useState([]);
  const [coursesLoading, setCoursesLoading] = useState(true);
  const [coursesError, setCoursesError] = useState("");

  const [highSchoolCourses, setHighSchoolCourses] = useState([]);
  const [highSchoolAddState, setHighSchoolAddState] = useState({ open: false, query: "" });
  const [semesterCourses, setSemesterCourses] = useState(blankSemesterMap);
  const [addState, setAddState] = useState(() => Object.fromEntries(SEMESTERS.map((s) => [s, { open: false, query: "" }])));

  const [currentTerm, setCurrentTerm] = useState("Fall");
  const [year, setYear] = useState("Freshman");
  const [optimization, setOptimization] = useState("balanced");
  const [degreeOptions, setDegreeOptions] = useState([]);
  const [degreeSearch, setDegreeSearch] = useState("");
  const [selectedDegrees, setSelectedDegrees] = useState(["bs_comp"]);
  const [preferredInput, setPreferredInput] = useState("");
  const [avoidInput, setAvoidInput] = useState("");

  const [selectedProgressStatus, setSelectedProgressStatus] = useState("planned");
  const [requirementsByType, setRequirementsByType] = useState({ planned: [], attended: [] });
  const [requirementsLoading, setRequirementsLoading] = useState(false);
  const [requirementsError, setRequirementsError] = useState("");

  const [generatedSchedule, setGeneratedSchedule] = useState({});
  const [generateStatus, setGenerateStatus] = useState("");
  const [generateError, setGenerateError] = useState("");
  const [generateLoading, setGenerateLoading] = useState(false);

  useEffect(() => {
    async function loadInitialData() {
      setCoursesLoading(true);
      setCoursesError("");
      try {
        const [coursesRes, programsRes] = await Promise.all([fetch(`${API_URL}/api/courses`), fetch(`${API_URL}/api/programs`)]);

        if (!coursesRes.ok) {
          throw new Error(`Unable to load courses: ${coursesRes.status}`);
        }

        const coursesData = await coursesRes.json();
        setAllCourses(coursesData);

        if (!programsRes.ok) {
          throw new Error(`Unable to load programs: ${programsRes.status}`);
        }

        const programsData = await programsRes.json();
        const normalizedPrograms = Array.isArray(programsData)
          ? programsData.filter((row) => typeof row?.value === "string" && typeof row?.label === "string")
          : [];

        setDegreeOptions(normalizedPrograms);
        setSelectedDegrees((prev) => {
          const availableKeys = new Set(normalizedPrograms.map((row) => row.value));
          const validPrevious = prev.filter((value) => availableKeys.has(value));
          if (validPrevious.length > 0) {
            return validPrevious;
          }
          if (availableKeys.has("bs_comp")) {
            return ["bs_comp"];
          }
          if (normalizedPrograms.length > 0) {
            return [normalizedPrograms[0].value];
          }
          return [];
        });
      } catch (error) {
        setCoursesError(String(error.message || error));
      } finally {
        setCoursesLoading(false);
      }
    }

    loadInitialData();
  }, []);

  const allEntries = useMemo(() => {
    return [...highSchoolCourses, ...Object.values(semesterCourses).flat()];
  }, [highSchoolCourses, semesterCourses]);

  const scheduleInputs = useMemo(() => {
    const currentYearIdx = YEAR_ORDER.indexOf(year);
    const currentTermIdx = TERM_ORDER.indexOf(currentTerm);
    const currentSemesterIndex = currentYearIdx * 2 + currentTermIdx;

    const completedSet = new Set(highSchoolCourses.map((entry) => entry.code));
    const scheduledMap = new Map();

    for (const [semester, entries] of Object.entries(semesterCourses)) {
      const semesterIndex = SEMESTERS.indexOf(semester);
      if (semesterIndex < 0) {
        continue;
      }

      for (const entry of entries || []) {
        if (semesterIndex < currentSemesterIndex) {
          completedSet.add(entry.code);
          continue;
        }

        const existing = scheduledMap.get(entry.code);
        if (existing === undefined || semesterIndex < existing) {
          scheduledMap.set(entry.code, semesterIndex);
        }
      }
    }

    return {
      completedCourses: Array.from(completedSet).sort(),
      scheduledCourses: Object.fromEntries(
        Array.from(scheduledMap.entries()).sort((a, b) => a[1] - b[1] || a[0].localeCompare(b[0]))
      )
    };
  }, [currentTerm, year, highSchoolCourses, semesterCourses]);

  const preferredCourses = useMemo(() => parseListInput(preferredInput), [preferredInput]);
  const avoidCourses = useMemo(() => parseListInput(avoidInput), [avoidInput]);
  const filteredDegreeOptions = useMemo(() => {
    const query = degreeSearch.trim().toLowerCase();
    return degreeOptions.filter((degree) => {
      if (selectedDegrees.includes(degree.value)) {
        return false;
      }
      if (query.length === 0) {
        return true;
      }
      return degree.label.toLowerCase().includes(query) || degree.value.toLowerCase().includes(query);
    });
  }, [degreeOptions, degreeSearch, selectedDegrees]);

  const requirementRows = useMemo(() => {
    return requirementsByType[selectedProgressStatus] || [];
  }, [requirementsByType, selectedProgressStatus]);

  async function checkRequirement() {
    setRequirementsLoading(true);
    setRequirementsError("");

    try {
      const plannedSet = new Set();
      const attendedSet = new Set();

      for (const entry of allEntries) {
        if (entry.status === "planned") {
          plannedSet.add(entry.code);
        }
        if (entry.status === "attended") {
          plannedSet.add(entry.code);
          attendedSet.add(entry.code);
        }
      }

      const payload = [
        { type: "planned", classes: Array.from(plannedSet).sort(), chosen_degree: selectedDegrees },
        { type: "attended", classes: Array.from(attendedSet).sort(), chosen_degree: selectedDegrees }
      ];

      const res = await fetch(`${API_URL}/api/check-requirements`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `Request failed: ${res.status}`);
      }

      const next = { planned: [], attended: [] };
      for (const bucket of Array.isArray(data) ? data : []) {
        if (bucket?.type === "planned" || bucket?.type === "attended") {
          next[bucket.type] = (bucket.requirements || []).map((row) => ({
            requirement: row.type,
            satisfied: Boolean(row.satisfied),
            progress: Array.isArray(row.progress) ? row.progress : [0, 0]
          }));
        }
      }
      setRequirementsByType(next);
    } catch (error) {
      setRequirementsError(String(error.message || error));
      setRequirementsByType({ planned: [], attended: [] });
    } finally {
      setRequirementsLoading(false);
    }
  }

  function selectProgressStatus(status) {
    setSelectedProgressStatus(status);
  }

  function addDegree(degreeValue) {
    setSelectedDegrees((prev) => {
      if (prev.includes(degreeValue)) {
        return prev;
      }
      return [...prev, degreeValue];
    });
    setDegreeSearch("");
  }

  function removeDegree(degreeValue) {
    setSelectedDegrees((prev) => prev.filter((value) => value !== degreeValue));
  }

  function setAddOpen(semester, open) {
    setAddState((prev) => ({
      ...prev,
      [semester]: {
        ...prev[semester],
        open,
        query: open ? prev[semester].query : ""
      }
    }));
  }

  function setAddQuery(semester, query) {
    setAddState((prev) => ({
      ...prev,
      [semester]: {
        ...prev[semester],
        query
      }
    }));
  }

  function addCourseToSemester(semester, course) {
    const code = normalizeCode(course);
    const longTitle = course.long_title || "Untitled course";

    setSemesterCourses((prev) => {
      const current = prev[semester] || [];
      if (current.some((entry) => entry.code === code)) {
        return prev;
      }

      return {
        ...prev,
        [semester]: [...current, { id: `${semester}-${code}`, code, longTitle, status: "planned" }]
      };
    });

    setAddState((prev) => ({
      ...prev,
      [semester]: {
        open: false,
        query: ""
      }
    }));
  }

  function setHighSchoolOpen(open) {
    setHighSchoolAddState((prev) => ({
      ...prev,
      open,
      query: open ? prev.query : ""
    }));
  }

  function setHighSchoolQuery(query) {
    setHighSchoolAddState((prev) => ({
      ...prev,
      query
    }));
  }

  function addCourseToHighSchool(course) {
    const code = normalizeCode(course);
    const longTitle = course.long_title || "Untitled course";

    setHighSchoolCourses((prev) => {
      if (prev.some((entry) => entry.code === code)) {
        return prev;
      }
      return [...prev, { id: `high-school-${code}`, code, longTitle, status: "planned" }];
    });

    setHighSchoolAddState({ open: false, query: "" });
  }

  function removeHighSchoolCourse(id) {
    setHighSchoolCourses((prev) => prev.filter((entry) => entry.id !== id));
  }

  function setHighSchoolCourseStatus(id, status) {
    setHighSchoolCourses((prev) => prev.map((entry) => (entry.id === id ? { ...entry, status } : entry)));
  }

  function removeCourse(semester, id) {
    setSemesterCourses((prev) => ({
      ...prev,
      [semester]: prev[semester].filter((entry) => entry.id !== id)
    }));
  }

  function setCourseStatus(semester, id, status) {
    setSemesterCourses((prev) => ({
      ...prev,
      [semester]: prev[semester].map((entry) => (entry.id === id ? { ...entry, status } : entry))
    }));
  }

  async function generateSchedule() {
    setGenerateStatus("");
    setGenerateError("");
    setGenerateLoading(true);

    try {
      const payload = {
        current_term: currentTerm,
        year,
        completed_courses: scheduleInputs.completedCourses,
        preferred_courses: preferredCourses,
        avoid_courses: avoidCourses,
        scheduled_courses: scheduleInputs.scheduledCourses,
        chosen_degree: selectedDegrees,
        optimization
      };

      const res = await fetch(`${API_URL}/api/schedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `Request failed: ${res.status}`);
      }

      setGeneratedSchedule(data.schedule || {});
      setGenerateStatus(data.status || "done");
    } catch (error) {
      setGenerateError(String(error.message || error));
      setGeneratedSchedule({});
    } finally {
      setGenerateLoading(false);
    }
  }

  function applyGeneratedScheduleToTables() {
    if (!generatedSchedule || Object.keys(generatedSchedule).length === 0) {
      return;
    }

    setSemesterCourses((prev) => {
      const merged = { ...prev };

      const existingCodes = new Set(
        Object.values(prev)
          .flat()
          .map((entry) => entry.code)
      );

      for (const semester of SEMESTERS) {
        const existingForSemester = prev[semester] || [];
        const generated = generatedSchedule[semester] || [];

        const additions = [];
        for (const [code, reason] of generated) {
          if (existingCodes.has(code)) {
            continue;
          }
          additions.push({
            id: `${semester}-${code}-generated`,
            code,
            longTitle: reason,
            status: "planned"
          });
          existingCodes.add(code);
        }

        merged[semester] = [...existingForSemester, ...additions];
      }

      return merged;
    });
  }

  function renderRequirementTable(rows) {
    return (
      <div className="req-card">
        <table>
          <thead>
            <tr>
              <th>Requirement</th>
              <th>Satisfied</th>
              <th>Progress</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={3} className="empty-row">
                  No requirements in this mode.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.requirement}>
                  <td>{row.requirement}</td>
                  <td>{row.satisfied ? "Yes" : "No"}</td>
                  <td>
                    {row.progress[0]}/{row.progress[1]}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="hero-glow" />
      <main className="layout">
        <header className="hero">
          <p className="eyebrow">Rice CS Degree Planner</p>
          <h1>Main Scheduling Page</h1>
          <p>
            Track progress, classify your courses, and generate a semester-by-semester plan from your current
            term and year.
          </p>
        </header>

        <section className="panel">
          <div className="panel-head">
            <h2>How to schedule your classes?</h2>
          </div>

          <ol className="instruction-list">
            <li>Add any completed courses to the <strong>Semester Table</strong> section.</li>
            <li>
              If you want a course to be taken in a specific semester, add it directly to the appropriate semester
              in the <strong>Semester Table</strong>.
            </li>
            <li>
              In the <strong>Generate Schedule</strong> section:
              <ul>
                <li>
                  Add courses you want to take sometime during your undergraduate studies to
                  <strong> Preferred Courses</strong>.
                </li>
                <li>Add courses you want to avoid to <strong>Avoid Courses</strong>.</li>
                <li>This is especially useful for courses with long or complicated prerequisite chains.</li>
              </ul>
            </li>
            <li>
              Select your degree programs accordingly.
              <ul>
                <li>You may select multiple majors and/or minors.</li>
                <li>Do <strong>not</strong> select both the BA and BS version of the same major.</li>
              </ul>
            </li>
            <li>
              Select:
              <ul>
                <li>your current year (for example, Freshman),</li>
                <li>current term (for example, Spring),</li>
                <li>
                  and optimization preference:
                  <ul>
                    <li><strong>Balanced</strong>{" -> "}more even workload across semesters</li>
                    <li><strong>Graduate Early</strong>{" -> "}finish requirements as quickly as possible</li>
                  </ul>
                </li>
              </ul>
            </li>
            <li>Click <strong>Run Scheduler</strong> to generate a schedule.</li>
            <li>Click <strong>Apply to Semester Tables</strong> to save the generated schedule into the planner.</li>
            <li>Click <strong>Check Requirements</strong> to see your progress toward degree requirements.</li>
          </ol>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>Requirement Progress</h2>
            <button onClick={checkRequirement} disabled={requirementsLoading}>
              {requirementsLoading ? "Checking..." : "Check Requirements"}
            </button>
          </div>

          <div className="toggle-row">
            {PROGRESS_OPTIONS.map((status) => (
              <button
                key={status}
                className={selectedProgressStatus === status ? "toggle active" : "toggle"}
                onClick={() => selectProgressStatus(status)}
                type="button"
              >
                {status}
              </button>
            ))}
          </div>

          <p className="warning">
            Warning: Courses may vary each semester. The following courses are planned based on their
            availability in Fall/Spring 2026. Courses that are offered during the same semester may not be taken
            concurrently due to conflicting schedules. Courses are balanced by credit hours but might not be in
            terms of workload.
          </p>

          {requirementsError && <p className="error">{requirementsError}</p>}

          <div className="req-grid">
            {renderRequirementTable(requirementRows)}
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>Semester Tables</h2>
            <span className="subtle">Please fill in the courses you have taken, plan to take, or passed.</span>
          </div>

          {coursesLoading && <p>Loading course catalog...</p>}
          {coursesError && <p className="error">{coursesError}</p>}

          <div className="semester-grid">
            <article className="semester-card" key={HIGH_SCHOOL}>
              <div className="semester-head">
                <h3>{HIGH_SCHOOL}</h3>
                <button type="button" onClick={() => setHighSchoolOpen(!highSchoolAddState.open)}>
                  {highSchoolAddState.open ? "Cancel" : "Add Class"}
                </button>
              </div>

              {highSchoolAddState.open && (
                <div className="add-box">
                  <input
                    value={highSchoolAddState.query}
                    onChange={(e) => setHighSchoolQuery(e.target.value)}
                    placeholder="Search any course by code or title"
                  />
                  {highSchoolAddState.query.trim().length > 0 && (
                    <ul className="search-results">
                      {allCourses
                        .filter((course) => {
                          const query = highSchoolAddState.query.trim().toLowerCase();
                          const code = normalizeCode(course).toLowerCase();
                          const title = (course.long_title || "").toLowerCase();
                          return code.includes(query) || title.includes(query);
                        })
                        .slice(0, 8)
                        .map((course) => (
                          <li key={`${HIGH_SCHOOL}-${normalizeCode(course)}`}>
                            <button type="button" onClick={() => addCourseToHighSchool(course)}>
                              <span>{normalizeCode(course)}</span>
                              <small>{course.long_title || "Untitled course"}</small>
                            </button>
                          </li>
                        ))}
                    </ul>
                  )}
                </div>
              )}

              <table>
                <thead>
                  <tr>
                    <th>Course</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {highSchoolCourses.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="empty-row">
                        No courses added yet.
                      </td>
                    </tr>
                  ) : (
                    highSchoolCourses.map((entry) => (
                      <tr key={entry.id}>
                        <td>
                          <div className="course-code">{entry.code}</div>
                          <div className="course-title">{entry.longTitle}</div>
                        </td>
                        <td>
                          <select value={entry.status} onChange={(e) => setHighSchoolCourseStatus(entry.id, e.target.value)}>
                            {STATUS_OPTIONS.map((option) => (
                              <option key={option} value={option}>
                                {option}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td>
                          <button type="button" className="danger" onClick={() => removeHighSchoolCourse(entry.id)}>
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </article>

            {SEMESTERS.map((semester) => {
              const localAddState = addState[semester];
              const query = (localAddState?.query || "").trim().toLowerCase();

              const candidates =
                query.length === 0
                  ? []
                  : allCourses
                      .filter((course) => {
                        const code = normalizeCode(course).toLowerCase();
                        const title = (course.long_title || "").toLowerCase();
                        return code.includes(query) || title.includes(query);
                      })
                      .slice(0, 8);

              return (
                <article className="semester-card" key={semester}>
                  <div className="semester-head">
                    <h3>{semester}</h3>
                    <button type="button" onClick={() => setAddOpen(semester, !localAddState.open)}>
                      {localAddState.open ? "Cancel" : "Add Class"}
                    </button>
                  </div>

                  {localAddState.open && (
                    <div className="add-box">
                      <input
                        value={localAddState.query}
                        onChange={(e) => setAddQuery(semester, e.target.value)}
                        placeholder="Search by COMP 140 or course title"
                      />
                      {query.length > 0 && (
                        <ul className="search-results">
                          {candidates.length === 0 ? (
                            <li className="empty-result">No matches</li>
                          ) : (
                            candidates.map((course) => (
                              <li key={`${semester}-${normalizeCode(course)}`}>
                                <button type="button" onClick={() => addCourseToSemester(semester, course)}>
                                  <span>{normalizeCode(course)}</span>
                                  <small>{course.long_title || "Untitled course"}</small>
                                </button>
                              </li>
                            ))
                          )}
                        </ul>
                      )}
                    </div>
                  )}

                  <table>
                    <thead>
                      <tr>
                        <th>Course</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(semesterCourses[semester] || []).length === 0 ? (
                        <tr>
                          <td colSpan={3} className="empty-row">
                            No courses added yet.
                          </td>
                        </tr>
                      ) : (
                        semesterCourses[semester].map((entry) => (
                          <tr key={entry.id}>
                            <td>
                              <div className="course-code">{entry.code}</div>
                              <div className="course-title">{entry.longTitle}</div>
                            </td>
                            <td>
                              <select
                                value={entry.status}
                                onChange={(e) => setCourseStatus(semester, entry.id, e.target.value)}
                              >
                                {STATUS_OPTIONS.map((option) => (
                                  <option key={option} value={option}>
                                    {option}
                                  </option>
                                ))}
                              </select>
                            </td>
                            <td>
                              <button type="button" className="danger" onClick={() => removeCourse(semester, entry.id)}>
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </article>
              );
            })}
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>Generate Schedule</h2>
            <button type="button" onClick={generateSchedule} disabled={generateLoading} aria-busy={generateLoading}>
              {generateLoading ? (
                <span className="loading-inline">
                  <span className="loading-dot" aria-hidden="true" />
                  Running...
                </span>
              ) : (
                "Run Scheduler"
              )}
            </button>
          </div>

          <div className="controls-grid">
            <label className="degree-picker-field">
              Degree Programs
              <div className="degree-picker">
                <input
                  value={degreeSearch}
                  onChange={(e) => setDegreeSearch(e.target.value)}
                  placeholder="Search degree programs"
                />

                {degreeSearch.trim().length > 0 && (
                  <ul className="search-results">
                    {filteredDegreeOptions.length === 0 ? (
                      <li className="empty-result">No matching degree options</li>
                    ) : (
                      filteredDegreeOptions.slice(0, 8).map((degree) => (
                        <li key={degree.value}>
                          <button type="button" onClick={() => addDegree(degree.value)}>
                            <span>{degree.label}</span>
                            <small>{degree.value}</small>
                          </button>
                        </li>
                      ))
                    )}
                  </ul>
                )}

                <div className="degree-chip-row">
                  {selectedDegrees.length === 0 ? (
                    <span className="subtle">No degree selected.</span>
                  ) : (
                    selectedDegrees.map((degreeValue) => {
                      const matched = degreeOptions.find((degree) => degree.value === degreeValue);
                      const label = matched ? matched.label : degreeValue;

                      return (
                        <button
                          key={degreeValue}
                          type="button"
                          className="degree-chip"
                          onClick={() => removeDegree(degreeValue)}
                          title="Click to remove"
                        >
                          {label} x
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            </label>

            <label>
              Preferred Courses (comma separated)
              <input
                value={preferredInput}
                onChange={(e) => setPreferredInput(e.target.value)}
                placeholder="COMP 341, COMP 449"
              />
            </label>

            <label>
              Avoid Courses (comma separated)
              <input
                value={avoidInput}
                onChange={(e) => setAvoidInput(e.target.value)}
                placeholder="COMP 414"
              />
            </label>

            <label>
              Current Term
              <select value={currentTerm} onChange={(e) => setCurrentTerm(e.target.value)}>
                <option value="Fall">Fall</option>
                <option value="Spring">Spring</option>
              </select>
            </label>

            <label>
              Year
              <select value={year} onChange={(e) => setYear(e.target.value)}>
                <option value="Freshman">Freshman</option>
                <option value="Sophomore">Sophomore</option>
                <option value="Junior">Junior</option>
                <option value="Senior">Senior</option>
              </select>
            </label>

            <label>
              Optimization
              <select value={optimization} onChange={(e) => setOptimization(e.target.value)}>
                <option value="balanced">Balanced</option>
                <option value="graduate early">Graduate Early</option>
              </select>
            </label>
          </div>

          {generateStatus && <p className="success">Scheduler status: {generateStatus}</p>}
          {generateError && <p className="error">{generateError}</p>}

          <div className="generated-box">
            <div className="panel-head compact">
              <h3>Generated Semesters</h3>
              <button type="button" onClick={applyGeneratedScheduleToTables}>
                Apply to Semester Tables
              </button>
            </div>

            {Object.keys(generatedSchedule).length === 0 ? (
              <p className="subtle">No generated schedule yet.</p>
            ) : (
              Object.entries(generatedSchedule).map(([semester, entries]) => (
                <div key={semester} className="generated-semester">
                  <h4>{semester}</h4>
                  <ul>
                    {entries.map((entry, idx) => (
                      <li key={`${semester}-${entry[0]}-${idx}`}>
                        <strong>{entry[0]}</strong>
                        <span>{entry[1]}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
