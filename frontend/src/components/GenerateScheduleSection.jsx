import React from "react";

function GenerateScheduleSection({
  degreeSearch,
  filteredDegreeOptions,
  selectedDegrees,
  degreeOptions,
  preferredInput,
  avoidInput,
  currentTerm,
  year,
  optimization,
  generatedSchedule,
  generateStatus,
  generateError,
  generateLoading,
  onGenerateSchedule,
  onApplyGeneratedScheduleToTables,
  onSetDegreeSearch,
  onAddDegree,
  onRemoveDegree,
  onSetPreferredInput,
  onSetAvoidInput,
  onSetCurrentTerm,
  onSetYear,
  onSetOptimization,
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Generate Schedule</h2>
        <button type="button" onClick={onGenerateSchedule} disabled={generateLoading} aria-busy={generateLoading}>
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
              onChange={(event) => onSetDegreeSearch(event.target.value)}
              placeholder="Search degree programs"
            />

            {degreeSearch.trim().length > 0 && (
              <ul className="search-results">
                {filteredDegreeOptions.length === 0 ? (
                  <li className="empty-result">No matching degree options</li>
                ) : (
                  filteredDegreeOptions.slice(0, 8).map((degree) => (
                    <li key={degree.value}>
                      <button type="button" onClick={() => onAddDegree(degree.value)}>
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
                      onClick={() => onRemoveDegree(degreeValue)}
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
          <input value={preferredInput} onChange={(event) => onSetPreferredInput(event.target.value)} placeholder="COMP 341, COMP 449" />
        </label>

        <label>
          Avoid Courses (comma separated)
          <input value={avoidInput} onChange={(event) => onSetAvoidInput(event.target.value)} placeholder="COMP 414" />
        </label>

        <label>
          Current Term
          <select value={currentTerm} onChange={(event) => onSetCurrentTerm(event.target.value)}>
            <option value="Fall">Fall</option>
            <option value="Spring">Spring</option>
          </select>
        </label>

        <label>
          Year
          <select value={year} onChange={(event) => onSetYear(event.target.value)}>
            <option value="Freshman">Freshman</option>
            <option value="Sophomore">Sophomore</option>
            <option value="Junior">Junior</option>
            <option value="Senior">Senior</option>
          </select>
        </label>

        <label>
          Optimization
          <select value={optimization} onChange={(event) => onSetOptimization(event.target.value)}>
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
          <button type="button" onClick={onApplyGeneratedScheduleToTables}>
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
                  <li key={`${semester}-${typeof entry === "string" ? entry : entry?.class || `entry-${idx}`}-${idx}`}>
                    <strong>{typeof entry === "string" ? entry : entry?.class}</strong>
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export default GenerateScheduleSection;
