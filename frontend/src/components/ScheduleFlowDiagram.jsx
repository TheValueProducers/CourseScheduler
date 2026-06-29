import React, { useMemo } from "react";
import { ReactFlow, Background, Controls } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const DEFAULT_SEMESTER_ORDER = [
  "Freshman Fall",
  "Freshman Spring",
  "Sophomore Fall",
  "Sophomore Spring",
  "Junior Fall",
  "Junior Spring",
  "Senior Fall",
  "Senior Spring"
];

function normalizeEntry(entry) {
  if (typeof entry === "string") {
    return { class: entry, prereqs: [] };
  }

  return {
    class: entry?.class || "",
    prereqs: Array.isArray(entry?.prereqs) ? entry.prereqs : []
  };
}

function buildOrderedSemesters(generatedSchedule, semesterOrder) {
  const scheduleKeys = Object.keys(generatedSchedule || {});
  const keySet = new Set(scheduleKeys);

  const orderedKnown = semesterOrder.filter((semester) => keySet.has(semester));
  const unknown = scheduleKeys.filter((semester) => !semesterOrder.includes(semester));

  return [...orderedKnown, ...unknown];
}

export default function ScheduleFlowDiagram({ generatedSchedule, semesterOrder = DEFAULT_SEMESTER_ORDER }) {
  const { nodes, edges } = useMemo(() => {
    const schedule = generatedSchedule || {};
    const semesters = buildOrderedSemesters(schedule, semesterOrder);

    if (semesters.length === 0) {
      return { nodes: [], edges: [] };
    }

    const builtNodes = [];
    const builtEdges = [];

    const courseOccurrences = new Map();
    const scheduleRows = [];

    const prereqColumnX = 40;
    const semesterStartX = 280;
    const semesterXGap = 300;
    const headerY = 20;
    const rowStartY = 100;
    const rowGapY = 95;

    semesters.forEach((semester, semIndex) => {
      const x = semesterStartX + semIndex * semesterXGap;

      builtNodes.push({
        id: `label-${semester}`,
        type: "input",
        position: { x, y: headerY },
        data: { label: semester },
        draggable: false,
        selectable: false,
        style: {
          width: 220,
          fontWeight: 700,
          color: "#000000",
          background: "#fef3c7",
          border: "1px solid #f59e0b"
        }
      });

      const rows = Array.isArray(schedule[semester]) ? schedule[semester] : [];
      rows.forEach((rawEntry, rowIndex) => {
        const entry = normalizeEntry(rawEntry);
        if (!entry.class) {
          return;
        }

        const nodeId = `course-${semester}-${entry.class}`;
        builtNodes.push({
          id: nodeId,
          position: { x, y: rowStartY + rowIndex * rowGapY },
          data: { label: entry.class },
          style: {
            width: 220,
            color: "#000000",
            border: "1px solid #0f766e",
            background: "#f0fdfa"
          }
        });

        const occurrences = courseOccurrences.get(entry.class) || [];
        occurrences.push({ nodeId, semIndex });
        courseOccurrences.set(entry.class, occurrences);

        scheduleRows.push({
          nodeId,
          semIndex,
          classCode: entry.class,
          prereqs: entry.prereqs
        });
      });
    });

    const prereqStubIds = new Map();

    function getOrCreatePrereqStub(prereqCode) {
      if (prereqStubIds.has(prereqCode)) {
        return prereqStubIds.get(prereqCode);
      }

      const stubId = `prereq-${prereqCode}`;
      const stubIndex = prereqStubIds.size;
      prereqStubIds.set(prereqCode, stubId);

      builtNodes.push({
        id: stubId,
        position: { x: prereqColumnX, y: rowStartY + stubIndex * rowGapY },
        data: { label: prereqCode },
        style: {
          width: 180,
          color: "#000000",
          border: "1px dashed #6b7280",
          background: "#f9fafb"
        }
      });

      return stubId;
    }

    for (const row of scheduleRows) {
      const uniquePrereqs = Array.from(new Set(row.prereqs));
      for (const prereqCode of uniquePrereqs) {
        const occurrences = courseOccurrences.get(prereqCode) || [];
        const validSources = occurrences.filter((occ) => occ.semIndex < row.semIndex);

        const sourceId =
          validSources.length > 0
            ? validSources[validSources.length - 1].nodeId
            : getOrCreatePrereqStub(prereqCode);

        builtEdges.push({
          id: `edge-${sourceId}-${row.nodeId}-${prereqCode}`,
          source: sourceId,
          target: row.nodeId,
          animated: false
        });
      }
    }

    return { nodes: builtNodes, edges: builtEdges };
  }, [generatedSchedule, semesterOrder]);

  if (!generatedSchedule || Object.keys(generatedSchedule).length === 0) {
    return <p className="subtle">Run scheduler to generate a flow diagram.</p>;
  }

  return (
    <div style={{ height: 560, width: "100%", border: "1px solid #e5e7eb", borderRadius: 10 }}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background gap={20} size={1} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
