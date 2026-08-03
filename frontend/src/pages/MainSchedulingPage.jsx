import React, { useEffect, useMemo, useState } from "react";
import GenerateScheduleSection from "../components/GenerateScheduleSection";
import RequirementProgressSection from "../components/RequirementProgressSection";
import ScheduleFlowDiagram from "../components/ScheduleFlowDiagram";
import SemesterTablesSection from "../components/SemesterTablesSection";

const API_URL = "http://localhost:8000"//"https://coursescheduler-production.up.railway.app";

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

function MainSchedulingPage() {
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
        for (const entry of generated) {
          const code = typeof entry === "string" ? entry : entry?.class;
          if (!code) {
            continue;
          }
          if (existingCodes.has(code)) {
            continue;
          }
          additions.push({
            id: `${semester}-${code}-generated`,
            code,
            longTitle: "Generated schedule course",
            status: "planned"
          });
          existingCodes.add(code);
        }

        merged[semester] = [...existingForSemester, ...additions];
      }

      return merged;
    });
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

        <RequirementProgressSection
          progressOptions={PROGRESS_OPTIONS}
          selectedProgressStatus={selectedProgressStatus}
          onSelectProgressStatus={selectProgressStatus}
          onCheckRequirement={checkRequirement}
          requirementsLoading={requirementsLoading}
          requirementsError={requirementsError}
          requirementRows={requirementRows}
        />

        <SemesterTablesSection
          allCourses={allCourses}
          semesters={SEMESTERS}
          highSchool={HIGH_SCHOOL}
          statusOptions={STATUS_OPTIONS}
          coursesLoading={coursesLoading}
          coursesError={coursesError}
          highSchoolCourses={highSchoolCourses}
          highSchoolAddState={highSchoolAddState}
          semesterCourses={semesterCourses}
          addState={addState}
          normalizeCode={normalizeCode}
          onSetHighSchoolOpen={setHighSchoolOpen}
          onSetHighSchoolQuery={setHighSchoolQuery}
          onAddCourseToHighSchool={addCourseToHighSchool}
          onSetHighSchoolCourseStatus={setHighSchoolCourseStatus}
          onRemoveHighSchoolCourse={removeHighSchoolCourse}
          onSetAddOpen={setAddOpen}
          onSetAddQuery={setAddQuery}
          onAddCourseToSemester={addCourseToSemester}
          onSetCourseStatus={setCourseStatus}
          onRemoveCourse={removeCourse}
        />

        <GenerateScheduleSection
          degreeSearch={degreeSearch}
          filteredDegreeOptions={filteredDegreeOptions}
          selectedDegrees={selectedDegrees}
          degreeOptions={degreeOptions}
          preferredInput={preferredInput}
          avoidInput={avoidInput}
          currentTerm={currentTerm}
          year={year}
          optimization={optimization}
          generatedSchedule={generatedSchedule}
          generateStatus={generateStatus}
          generateError={generateError}
          generateLoading={generateLoading}
          onGenerateSchedule={generateSchedule}
          onApplyGeneratedScheduleToTables={applyGeneratedScheduleToTables}
          onSetDegreeSearch={setDegreeSearch}
          onAddDegree={addDegree}
          onRemoveDegree={removeDegree}
          onSetPreferredInput={setPreferredInput}
          onSetAvoidInput={setAvoidInput}
          onSetCurrentTerm={setCurrentTerm}
          onSetYear={setYear}
          onSetOptimization={setOptimization}
        />

        <section className="panel">
          <div className="panel-head">
            <h2>Schedule Flow Diagram</h2>
            <span className="subtle">Prereqs flow into courses from left to right by semester.</span>
          </div>
          <ScheduleFlowDiagram generatedSchedule={generatedSchedule} semesterOrder={SEMESTERS} />
        </section>
      </main>
    </div>
  );
}

export default MainSchedulingPage;
