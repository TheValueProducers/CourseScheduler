import React from "react";

function RequirementProgressSection({
  progressOptions,
  selectedProgressStatus,
  onSelectProgressStatus,
  onCheckRequirement,
  requirementsLoading,
  requirementsError,
  requirementRows,
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Requirement Progress</h2>
        <button onClick={onCheckRequirement} disabled={requirementsLoading}>
          {requirementsLoading ? "Checking..." : "Check Requirements"}
        </button>
      </div>

      <div className="toggle-row">
        {progressOptions.map((status) => (
          <button
            key={status}
            className={selectedProgressStatus === status ? "toggle active" : "toggle"}
            onClick={() => onSelectProgressStatus(status)}
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
              {requirementRows.length === 0 ? (
                <tr>
                  <td colSpan={3} className="empty-row">
                    No requirements in this mode.
                  </td>
                </tr>
              ) : (
                requirementRows.map((row) => (
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
      </div>
    </section>
  );
}

export default RequirementProgressSection;
