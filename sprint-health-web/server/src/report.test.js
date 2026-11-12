import assert from "node:assert/strict";
import test from "node:test";

import { ConfigError, loadConfig } from "./config.js";
import { loadFixtureReport } from "./fixture.js";
import { buildReport } from "./report.js";

const ACCOUNTS = ["a1", "a2", "a3", "a4", "a5"];
const ACTIVE = {
  id: 20,
  name: "Sprint 12",
  state: "active",
  startDate: "2026-11-02T03:30:00.000Z",
  endDate: "2026-11-13T03:30:00.000Z",
};

function sampleConfig() {
  return {
    jiraBaseUrl: "https://example.atlassian.net",
    jiraBoardId: "1",
    assigneeAccountIds: ACCOUNTS,
    timezone: "Asia/Kolkata",
  };
}

function issue(key, { account = "a1", points = null, category = "indeterminate", status = "To Do", parent = null, sprints = [ACTIVE] } = {}) {
  return {
    key,
    fields: {
      summary: key,
      status: { name: status, statusCategory: { key: category } },
      assignee: account ? { accountId: account, displayName: account } : null,
      parent,
      customfield_10016: points,
      customfield_10020: sprints,
    },
  };
}

function build(issues, extra = {}) {
  return buildReport({
    issues,
    config: sampleConfig(),
    sprint: ACTIVE,
    storyPointsField: "customfield_10016",
    sprintField: "customfield_10020",
    ...extra,
  });
}

test("recorded fixture matches the Module 08 sheet totals", () => {
  const { source, report } = loadFixtureReport();
  assert.equal(source, "fixture");
  assert.deepEqual(report.health, {
    scope: 5,
    scopePoints: 11,
    done: 2,
    donePoints: 7,
    remaining: 3,
    remainingPoints: 4,
    spillover: 1,
    completion: 40,
  });
  assert.equal(report.excludedCount, 2);
  assert.deepEqual(
    report.phases.map((phase) => [phase.key, phase.summary]),
    [
      ["MIG-100", "Schema cutover"],
      ["MIG-200", "Data move"],
      ["", "No phase"],
    ],
  );
  assert.deepEqual(
    report.workload.map((row) => [row.displayName, row.openIssues, row.balance]),
    [
      ["Ada", 1, "Overloaded"],
      ["Ben", 1, "Overloaded"],
      ["Cy", 0, "Within range"],
      ["Dee", 1, "Overloaded"],
      ["Ed", 0, "Within range"],
    ],
  );
  assert.equal(report.sprint.daysRemaining, 1);
  assert.equal(report.generatedAtDisplay, "2026-11-12 08:00");
  assert.deepEqual(
    report.statuses.map((status) => [status.name, status.count]),
    [
      ["To Do", 1],
      ["In Progress", 2],
      ["Done", 2],
    ],
  );
});

test("spillover requires the active sprint and an earlier one", () => {
  const activeEntry = { id: 20, name: "Sprint 12", state: "active", startDate: ACTIVE.startDate };
  const report = build([
    issue("EARLIER", {
      sprints: [
        { id: 19, name: "Sprint 11", state: "closed", startDate: "2026-10-19T03:30:00.000Z" },
        activeEntry,
      ],
    }),
    issue("ONLY", { sprints: [activeEntry] }),
    issue("FUTURE", {
      sprints: [
        activeEntry,
        { id: 21, name: "Sprint 13", state: "future", startDate: "2026-11-16T03:30:00.000Z" },
      ],
    }),
    issue("CLOSED", { sprints: [activeEntry, { id: 18, name: "Sprint 10", state: "closed" }] }),
  ]);
  assert.equal(report.health.scope, 4);
  assert.equal(report.health.spillover, 2);
});

test("other assignees stay out of the totals", () => {
  const report = build([
    issue("IN", { account: "a1", points: 2 }),
    issue("OUT", { account: "z9", points: 8 }),
    issue("UNASSIGNED", { account: null, points: 4 }),
  ]);
  assert.equal(report.health.scope, 1);
  assert.equal(report.health.scopePoints, 2);
  assert.equal(report.excludedCount, 2);
});

test("zero scope is within range for every person", () => {
  const report = buildReport({ issues: [], config: sampleConfig(), sprint: null });
  assert.equal(report.health.completion, 0);
  assert.deepEqual(
    report.workload.map((row) => row.balance),
    ["Within range", "Within range", "Within range", "Within range", "Within range"],
  );
});

test("config requires the five Jira variables", () => {
  assert.throws(() => loadConfig({}), ConfigError);
});
