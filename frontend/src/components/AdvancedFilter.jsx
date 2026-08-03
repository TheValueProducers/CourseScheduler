import React from "react";

const LEVEL_OPTIONS = [100, 200, 300, 400, 500, 600, 700, 800];
const MIN_LEVEL = LEVEL_OPTIONS[0];
const MAX_LEVEL = LEVEL_OPTIONS[LEVEL_OPTIONS.length - 1];

function clampLevel(value) {
  const numeric = Number(value);
  return LEVEL_OPTIONS.includes(numeric) ? numeric : 100;
}

function sliderPercent(level) {
  return ((level - MIN_LEVEL) / (MAX_LEVEL - MIN_LEVEL)) * 100;
}

function AdvancedFilter({ value, onChange, onSave, onReset }) {
  const minLevel = clampLevel(value?.courseLevel?.[0] ?? 100);
  const maxLevel = clampLevel(value?.courseLevel?.[1] ?? 800);
  const distribution = value?.distribution ?? "";
  const subject = value?.subject ?? "";
  const analyzingDiversity = Boolean(value?.analyzingDiversity);

  function update(nextPatch) {
    onChange({
      courseLevel: [minLevel, maxLevel],
      distribution,
      subject,
      analyzingDiversity,
      ...nextPatch,
    });
  }

  function handleMinChange(event) {
    const nextMin = clampLevel(event.target.value);
    update({ courseLevel: [Math.min(nextMin, maxLevel), maxLevel] });
  }

  function handleMaxChange(event) {
    const nextMax = clampLevel(event.target.value);
    update({ courseLevel: [minLevel, Math.max(nextMax, minLevel)] });
  }

  return (
    <section className="panel advanced-filter-panel">
      <div className="panel-head">
        <h2>Advanced Filter</h2>
        <span className="subtle">Refine ranking results by course attributes.</span>
      </div>

      <div className="advanced-filter-grid">
        <label className="advanced-filter-field advanced-filter-range-field">
          <span>Course Level Range</span>
          <div className="advanced-filter-range-values">
            <strong>{minLevel}</strong>
            <span>to</span>
            <strong>{maxLevel}</strong>
          </div>
          <div className="advanced-filter-slider" aria-label="Course level range slider">
            <div className="advanced-filter-slider-track" />
            <div
              className="advanced-filter-slider-active"
              style={{
                left: `${sliderPercent(minLevel)}%`,
                width: `${sliderPercent(maxLevel) - sliderPercent(minLevel)}%`,
              }}
            />
            <input
              className="advanced-filter-slider-input"
              type="range"
              min="100"
              max="800"
              step="100"
              value={minLevel}
              onChange={handleMinChange}
            />
            <input
              className="advanced-filter-slider-input"
              type="range"
              min="100"
              max="800"
              step="100"
              value={maxLevel}
              onChange={handleMaxChange}
            />
          </div>
        </label>

        <label className="advanced-filter-field">
          <span>Distribution</span>
          <select value={distribution} onChange={(event) => update({ distribution: event.target.value })}>
            <option value="">None</option>
            <option value="1">Distribution 1</option>
            <option value="2">Distribution 2</option>
            <option value="3">Distribution 3</option>
          </select>
        </label>

        <label className="advanced-filter-field">
          <span>Subject</span>
          <input
            value={subject}
            onChange={(event) => update({ subject: event.target.value.toUpperCase() })}
            placeholder="COMP or STAT"
          />
        </label>

        <label className="advanced-filter-checkbox">
          <input
            type="checkbox"
            checked={analyzingDiversity}
            onChange={(event) => update({ analyzingDiversity: event.target.checked })}
          />
          <span>Analyzing Diversity only</span>
        </label>

        <div className="advanced-filter-actions">
          <button type="button" onClick={onSave}>Save Filter</button>
          <button type="button" className="secondary-button" onClick={onReset}>Reset Filter</button>
        </div>
      </div>
    </section>
  );
}

export default AdvancedFilter;