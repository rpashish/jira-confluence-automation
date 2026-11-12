/** Recorded sprint used when the page asks for the sample report. */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { buildReport } from "./report.js";

const FIXTURE = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../../tests/fixtures/sprint_payload.json",
);

const SAMPLE_NOW = new Date("2026-11-12T02:30:00.000Z");

const SAMPLE_CONFIG = {
  jiraBaseUrl: "https://example.atlassian.net",
  jiraBoardId: "1",
  assigneeAccountIds: ["a1", "a2", "a3", "a4", "a5"],
  timezone: "Asia/Kolkata",
};

const SAMPLE_NAMES = {
  a1: "Ada",
  a2: "Ben",
  a3: "Cy",
  a4: "Dee",
  a5: "Ed",
};

export function loadFixtureReport() {
  const payload = JSON.parse(readFileSync(FIXTURE, "utf8"));
  const report = buildReport({
    issues: payload.issues,
    config: SAMPLE_CONFIG,
    sprint: payload.sprint,
    board: payload.board,
    storyPointsField: payload.story_points_field,
    sprintField: payload.sprint_field,
    statusOrder: payload.status_order,
    assigneeNames: SAMPLE_NAMES,
    now: SAMPLE_NOW,
  });
  return { source: "fixture", report };
}
