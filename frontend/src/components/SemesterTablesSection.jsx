import React from "react";

function SemesterTablesSection({
  allCourses,
  semesters,
  highSchool,
  statusOptions,
  coursesLoading,
  coursesError,
  highSchoolCourses,
  highSchoolAddState,
  semesterCourses,
  addState,
  normalizeCode,
  onSetHighSchoolOpen,
  onSetHighSchoolQuery,
  onAddCourseToHighSchool,
  onSetHighSchoolCourseStatus,
  onRemoveHighSchoolCourse,
  onSetAddOpen,
  onSetAddQuery,
  onAddCourseToSemester,
  onSetCourseStatus,
  onRemoveCourse,
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Semester Tables</h2>
        <span className="subtle">Please fill in the courses you have taken, plan to take, or passed.</span>
      </div>

      {coursesLoading && <p>Loading course catalog...</p>}
      {coursesError && <p className="error">{coursesError}</p>}

      <div className="semester-grid">
        <article className="semester-card" key={highSchool}>
          <div className="semester-head">
            <h3>{highSchool}</h3>
            <button type="button" onClick={() => onSetHighSchoolOpen(!highSchoolAddState.open)}>
              {highSchoolAddState.open ? "Cancel" : "Add Class"}
            </button>
          </div>

          {highSchoolAddState.open && (
            <div className="add-box">
              <input
                value={highSchoolAddState.query}
                onChange={(event) => onSetHighSchoolQuery(event.target.value)}
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
                      <li key={`${highSchool}-${normalizeCode(course)}`}>
                        <button type="button" onClick={() => onAddCourseToHighSchool(course)}>
                          <span>{normalizeCode(course)}</span>
                          <small>{course.long_title || "Untitled course"}</small>
                        </button>
                      </li>
                    ))}
                </ul>
              )}
            </div>
          )}

          <div className="semester-table-scroll">
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
                        <select value={entry.status} onChange={(event) => onSetHighSchoolCourseStatus(entry.id, event.target.value)}>
                          {statusOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <button type="button" className="danger" onClick={() => onRemoveHighSchoolCourse(entry.id)}>
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>

        {semesters.map((semester) => {
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
                <button type="button" onClick={() => onSetAddOpen(semester, !localAddState.open)}>
                  {localAddState.open ? "Cancel" : "Add Class"}
                </button>
              </div>

              {localAddState.open && (
                <div className="add-box">
                  <input
                    value={localAddState.query}
                    onChange={(event) => onSetAddQuery(semester, event.target.value)}
                    placeholder="Search by COMP 140 or course title"
                  />
                  {query.length > 0 && (
                    <ul className="search-results">
                      {candidates.length === 0 ? (
                        <li className="empty-result">No matches</li>
                      ) : (
                        candidates.map((course) => (
                          <li key={`${semester}-${normalizeCode(course)}`}>
                            <button type="button" onClick={() => onAddCourseToSemester(semester, course)}>
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

              <div className="semester-table-scroll">
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
                            <select value={entry.status} onChange={(event) => onSetCourseStatus(semester, entry.id, event.target.value)}>
                              {statusOptions.map((option) => (
                                <option key={option} value={option}>
                                  {option}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td>
                            <button type="button" className="danger" onClick={() => onRemoveCourse(semester, entry.id)}>
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default SemesterTablesSection;
