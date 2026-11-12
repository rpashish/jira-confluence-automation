/** Turn sprint issues into health, phase, and workload rows. */

const OVERLOADED = "Overloaded";
const WITHIN_RANGE = "Within range";
const NO_PHASE = "No phase";
const REPORT_TITLE = "Sprint health — database migration";

export function buildReport({
  issues,
  config,
  sprint,
  board = null,
  storyPointsField = null,
  sprintField = null,
  statusOrder = [],
  assigneeNames = null,
  now = new Date(),
}) {
  const generatedAt = inTimezone(now, config.timezone);
  const boardInfo = board || {};
  let inScope = [];
  let excluded = 0;
  if (sprint) {
    [inScope, excluded] = splitAssignees(issues, config);
  }

  const rows = inScope.map((issue) => view(issue, sprint, storyPointsField, sprintField));
  const people = listPeople(inScope, config, assigneeNames);
  return {
    title: REPORT_TITLE,
    site: config.jiraBaseUrl,
    projectKey: boardInfo.project_key || boardInfo.projectKey || "",
    boardName: boardInfo.name || "",
    boardId: config.jiraBoardId,
    sprint: sprint ? sprintInfo(sprint, generatedAt, config.timezone) : null,
    noActiveSprint: sprint == null,
    generatedAt: generatedAt.toISOString(),
    generatedAtDisplay: formatDateTime(generatedAt, config.timezone),
    timezone: config.timezone,
    assignees: people,
    health: health(rows),
    statuses: statuses(rows, statusOrder),
    phases: phases(rows),
    workload: workload(rows, people),
    excludedCount: excluded,
    issueCount: rows.length,
  };
}

function splitAssignees(issues, config) {
  const allowed = new Set(config.assigneeAccountIds);
  const inScope = [];
  let excluded = 0;
  for (const issue of issues) {
    const accountId = accountOf(issue);
    if (allowed.has(accountId)) {
      inScope.push(issue);
    } else {
      excluded += 1;
    }
  }
  return [inScope, excluded];
}

function view(issue, sprint, storyPointsField, sprintField) {
  const fields = issue.fields || {};
  const status = fields.status || {};
  const category = (status.statusCategory?.key || "").toLowerCase();
  const sprints = sprintValues(fields, sprintField);
  const [epicKey, epicSummary] = epicOf(fields);
  return {
    statusName: status.name || "Unknown",
    done: category === "done",
    accountId: accountOf(issue),
    points: pointsOf(fields, storyPointsField),
    spillover: Boolean(sprint) && isSpillover(sprints, sprint),
    epicKey,
    epicSummary,
  };
}

function accountOf(issue) {
  const assignee = issue.fields?.assignee;
  if (!assignee || typeof assignee !== "object") {
    return null;
  }
  return assignee.accountId ?? null;
}

function pointsOf(fields, storyPointsField) {
  if (!storyPointsField) {
    return null;
  }
  const value = fields[storyPointsField];
  if (typeof value === "boolean" || value == null || value === "") {
    return null;
  }
  if (typeof value === "number") {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function sumPoints(values) {
  const numbers = values.filter((value) => value != null);
  if (!numbers.length) {
    return null;
  }
  return numbers.reduce((total, value) => total + value, 0);
}

function sprintValues(fields, sprintField) {
  const raw = sprintField ? fields[sprintField] : fields.sprint;
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw.filter((item) => item && typeof item === "object");
}

function isSpillover(sprints, active) {
  if (sprints.length < 2) {
    return false;
  }
  if (!sprints.some((item) => sameId(item.id, active.id))) {
    return false;
  }
  return sprints.some((item) => isEarlier(item, active));
}

function isEarlier(other, active) {
  if (sameId(other.id, active.id)) {
    return false;
  }
  const activeStart = parseDate(active.startDate);
  const otherStart = parseDate(other.startDate);
  if (activeStart && otherStart) {
    return otherStart.getTime() < activeStart.getTime();
  }
  return ["closed", "completed"].includes(String(other.state || "").toLowerCase());
}

function sameId(left, right) {
  if (left == null || right == null) {
    return false;
  }
  return String(left) === String(right);
}

function epicOf(fields) {
  const parent = fields.parent;
  if (!parent || typeof parent !== "object") {
    return [null, null];
  }
  if (isEpic(parent)) {
    return epicIdentity(parent);
  }
  const grandparent = parent.fields?.parent;
  if (grandparent && typeof grandparent === "object" && isEpic(grandparent)) {
    return epicIdentity(grandparent);
  }
  return [null, null];
}

function isEpic(node) {
  return String(node.fields?.issuetype?.name || "").toLowerCase() === "epic";
}

function epicIdentity(node) {
  if (!node.key) {
    return [null, null];
  }
  return [node.key, node.fields?.summary || ""];
}

function health(rows) {
  const scope = rows.length;
  const doneRows = rows.filter((row) => row.done);
  const openRows = rows.filter((row) => !row.done);
  const done = doneRows.length;
  return {
    scope,
    scopePoints: sumPoints(rows.map((row) => row.points)),
    done,
    donePoints: sumPoints(doneRows.map((row) => row.points)),
    remaining: scope - done,
    remainingPoints: sumPoints(openRows.map((row) => row.points)),
    spillover: rows.filter((row) => row.spillover).length,
    completion: scope === 0 ? 0 : (done / scope) * 100,
  };
}

function statuses(rows, statusOrder) {
  const counts = new Map();
  for (const row of rows) {
    counts.set(row.statusName, (counts.get(row.statusName) || 0) + 1);
  }
  const rank = new Map(statusOrder.map((name, index) => [name, index]));
  const names = [...counts.keys()].sort((left, right) => {
    const leftRank = rank.has(left) ? [0, rank.get(left)] : [1, left];
    const rightRank = rank.has(right) ? [0, rank.get(right)] : [1, right];
    if (leftRank[0] !== rightRank[0]) {
      return leftRank[0] - rightRank[0];
    }
    if (typeof leftRank[1] === "number" && typeof rightRank[1] === "number") {
      return leftRank[1] - rightRank[1];
    }
    return String(leftRank[1]).localeCompare(String(rightRank[1]));
  });
  return names.map((name) => ({ name, count: counts.get(name) }));
}

function phases(rows) {
  const grouped = new Map();
  const summaries = new Map();
  for (const row of rows) {
    const key = row.epicKey || "";
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key).push(row);
    if (key && !summaries.has(key)) {
      summaries.set(key, row.epicSummary || "");
    }
  }
  const epicKeys = [...grouped.keys()].filter(Boolean).sort();
  const ordered = grouped.has("") ? [...epicKeys, ""] : epicKeys;
  return ordered.map((key) => {
    const members = grouped.get(key);
    const scope = members.length;
    const done = members.filter((member) => member.done).length;
    return {
      key,
      summary: key === "" ? NO_PHASE : summaries.get(key) || "",
      scope,
      done,
      remaining: scope - done,
      spillover: members.filter((member) => member.spillover).length,
      completion: scope === 0 ? 0 : (done / scope) * 100,
    };
  });
}

function listPeople(issues, config, assigneeNames) {
  const found = new Map();
  for (const issue of issues) {
    const assignee = issue.fields?.assignee;
    if (assignee && typeof assignee === "object" && assignee.accountId && assignee.displayName) {
      found.set(assignee.accountId, assignee.displayName);
    }
  }
  const overrides = assigneeNames || {};
  return config.assigneeAccountIds.map((accountId) => ({
    accountId,
    displayName: overrides[accountId] || found.get(accountId) || accountId,
  }));
}

function workload(rows, people) {
  const openByAccount = new Map();
  for (const row of rows) {
    if (row.done) {
      continue;
    }
    if (!openByAccount.has(row.accountId)) {
      openByAccount.set(row.accountId, []);
    }
    openByAccount.get(row.accountId).push(row);
  }
  const counts = people.map((person) => (openByAccount.get(person.accountId) || []).length);
  const totalOpen = counts.reduce((total, count) => total + count, 0);
  const mean = people.length ? totalOpen / people.length : 0;
  const threshold = 1.5 * mean;
  return people.map((person, index) => {
    const count = counts[index];
    const openRows = openByAccount.get(person.accountId) || [];
    const balance = totalOpen === 0 || count <= threshold ? WITHIN_RANGE : OVERLOADED;
    return {
      accountId: person.accountId,
      displayName: person.displayName,
      openIssues: count,
      remainingPoints: sumPoints(openRows.map((row) => row.points)),
      share: totalOpen === 0 ? 0 : count / totalOpen,
      balance,
    };
  });
}

function sprintInfo(sprint, now, timeZone) {
  return {
    id: sprint.id,
    name: sprint.name || "",
    state: sprint.state || "",
    startDate: formatDate(sprint.startDate, timeZone),
    endDate: formatDate(sprint.endDate, timeZone),
    daysRemaining: daysRemaining(sprint.endDate, now, timeZone),
    selectionNote: sprint.selectionNote || null,
  };
}

function daysRemaining(endDate, now, timeZone) {
  const end = calendarDay(endDate, timeZone);
  if (!end) {
    return null;
  }
  const today = calendarDay(now, timeZone);
  const diff = (Date.parse(`${end}T00:00:00Z`) - Date.parse(`${today}T00:00:00Z`)) / 86400000;
  return Math.max(0, diff);
}

function formatDate(value, timeZone) {
  return calendarDay(value, timeZone);
}

function formatDateTime(value, timeZone) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(value);
  const get = (type) => parts.find((part) => part.type === type)?.value;
  return `${get("year")}-${get("month")}-${get("day")} ${get("hour")}:${get("minute")}`;
}

function calendarDay(value, timeZone) {
  const parsed = value instanceof Date ? value : parseDate(value);
  if (!parsed) {
    return null;
  }
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(parsed);
  const get = (type) => parts.find((part) => part.type === type)?.value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}

function parseDate(value) {
  if (!value || typeof value !== "string") {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function inTimezone(moment, timeZone) {
  const parsed = moment instanceof Date ? moment : new Date(moment);
  if (Number.isNaN(parsed.getTime())) {
    throw new Error("Invalid report time");
  }
  new Intl.DateTimeFormat("en-US", { timeZone }).format(parsed);
  return parsed;
}
