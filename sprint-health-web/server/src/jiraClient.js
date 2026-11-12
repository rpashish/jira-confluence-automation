/** Authenticated Jira Cloud reads for the sprint health report. */

const SPRINT_FIELD_TYPE = "com.pyxis.greenhopper.jira:gh-sprint";
const ATTEMPTS = 4;
const PAGE_SIZE = 50;

export class JiraError extends Error {
  constructor(message, status = 502) {
    super(message);
    this.status = status;
  }
}

export class JiraClient {
  constructor(config, fetchImpl = fetch) {
    this.config = config;
    this.fetchImpl = fetchImpl;
    this.fieldsLoaded = false;
    this.storyPointsField = null;
    this.sprintField = null;
  }

  async board() {
    const payload = await this.get(this.boardPath());
    const location = payload.location || {};
    return {
      id: payload.id,
      name: payload.name || "",
      project_key: location.projectKey || "",
    };
  }

  async activeSprint() {
    const sprints = [];
    let start = 0;
    while (true) {
      const page = await this.get(`${this.boardPath()}/sprint`, {
        state: "active",
        startAt: start,
        maxResults: PAGE_SIZE,
      });
      const values = (page.values || []).filter((item) => item && typeof item === "object");
      sprints.push(...values);
      const nextStart = (page.startAt ?? start) + values.length;
      if (page.isLast !== false || !values.length || nextStart <= start) {
        break;
      }
      if (page.total != null && nextStart >= page.total) {
        break;
      }
      start = nextStart;
    }
    if (!sprints.length) {
      return null;
    }
    const chosen = { ...sprints.reduce((latest, sprint) => (laterStart(sprint, latest) ? sprint : latest)) };
    if (sprints.length > 1) {
      const names = sprints.map((sprint) => sprint.name || String(sprint.id)).join(", ");
      chosen.selectionNote =
        `Several sprints are active (${names}); ` +
        `using ${chosen.name} because it has the latest start date.`;
    }
    return chosen;
  }

  async sprintIssues(sprintId) {
    const issues = [];
    let start = 0;
    while (true) {
      const page = await this.get(`/rest/agile/1.0/sprint/${sprintId}/issue`, {
        startAt: start,
        maxResults: PAGE_SIZE,
        fields: await this.issueFields(),
      });
      const batch = (page.issues || []).filter((item) => item && typeof item === "object");
      issues.push(...batch);
      start += batch.length;
      if (!batch.length || page.total == null || start >= page.total) {
        break;
      }
    }
    return this.attachParentEpics(issues);
  }

  async storyPointsFieldId() {
    await this.loadFields();
    return this.storyPointsField;
  }

  async sprintFieldId() {
    await this.loadFields();
    return this.sprintField;
  }

  async statusOrder() {
    const payload = await this.get(`${this.boardPath()}/configuration`, null, { missingOk: true });
    if (!payload || typeof payload !== "object") {
      return [];
    }
    const columns = payload.columnConfig?.columns || [];
    const ordered = [];
    let needsLookup = false;
    for (const column of columns) {
      for (const status of column.statuses || []) {
        if (status.name) {
          ordered.push(status.name);
        } else if (status.id != null) {
          needsLookup = true;
          ordered.push(["id", String(status.id)]);
        }
      }
    }
    let names = ordered;
    if (needsLookup) {
      const catalog = await this.get("/rest/api/3/status", null, { missingOk: true });
      const byId = new Map(
        (Array.isArray(catalog) ? catalog : [])
          .filter((item) => item && item.name)
          .map((item) => [String(item.id), item.name]),
      );
      names = [];
      for (const item of ordered) {
        if (Array.isArray(item)) {
          const name = byId.get(item[1]);
          if (name) {
            names.push(name);
          }
        } else {
          names.push(item);
        }
      }
    }
    const seen = new Set();
    const unique = [];
    for (const name of names) {
      if (typeof name === "string" && !seen.has(name)) {
        seen.add(name);
        unique.push(name);
      }
    }
    return unique;
  }

  async assigneeNames() {
    const names = {};
    for (const accountId of this.config.assigneeAccountIds) {
      const payload = await this.get("/rest/api/3/user", { accountId }, { missingOk: true });
      names[accountId] = (payload && payload.displayName) || accountId;
    }
    return names;
  }

  async issueFields() {
    await this.loadFields();
    const fields = ["summary", "status", "assignee", "parent"];
    if (this.sprintField) {
      fields.push(this.sprintField);
    }
    if (this.storyPointsField) {
      fields.push(this.storyPointsField);
    }
    return fields.join(",");
  }

  async loadFields() {
    if (this.fieldsLoaded) {
      return;
    }
    const payload = await this.get("/rest/api/3/field");
    const fields = Array.isArray(payload) ? payload : [];
    let sprintId = fields.find((field) => field.schema?.custom === SPRINT_FIELD_TYPE)?.id ?? null;
    if (sprintId == null) {
      sprintId = fields.find((field) => field.name === "Sprint")?.id ?? null;
    }
    this.sprintField = sprintId;
    this.storyPointsField = fields.find((field) => field.name === "Story Points")?.id ?? null;
    this.fieldsLoaded = true;
  }

  async attachParentEpics(issues) {
    const cache = new Map();
    for (const issue of issues) {
      if (!issue.fields || typeof issue.fields !== "object") {
        issue.fields = {};
      }
      const parent = issue.fields.parent;
      if (!parent || typeof parent !== "object" || isEpic(parent) || !parent.key) {
        continue;
      }
      if (!cache.has(parent.key)) {
        cache.set(
          parent.key,
          await this.get(`/rest/api/3/issue/${encodeURIComponent(parent.key)}`, {
            fields: "summary,issuetype,parent",
          }, { missingOk: true }),
        );
      }
      const fetched = cache.get(parent.key);
      const fetchedFields = (fetched && fetched.fields) || {};
      parent.fields = parent.fields || {};
      if (!parent.fields.issuetype && fetchedFields.issuetype) {
        parent.fields.issuetype = fetchedFields.issuetype;
      }
      if (!parent.fields.summary && fetchedFields.summary) {
        parent.fields.summary = fetchedFields.summary;
      }
      if (fetchedFields.parent && typeof fetchedFields.parent === "object") {
        parent.fields.parent = fetchedFields.parent;
      }
    }
    return issues;
  }

  boardPath() {
    return `/rest/agile/1.0/board/${this.config.jiraBoardId}`;
  }

  async get(path, params = null, { missingOk = false } = {}) {
    const url = new URL(`${this.config.jiraBaseUrl}${path}`);
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        url.searchParams.set(key, String(value));
      }
    }
    const authorization = `Basic ${Buffer.from(`${this.config.jiraEmail}:${this.config.jiraApiToken}`).toString("base64")}`;
    for (let attempt = 0; attempt < ATTEMPTS; attempt += 1) {
      let response;
      try {
        response = await this.fetchImpl(url, {
          headers: { Accept: "application/json", Authorization: authorization },
          signal: AbortSignal.timeout(30000),
        });
      } catch {
        if (attempt < ATTEMPTS - 1) {
          await sleep(500 * 2 ** attempt);
          continue;
        }
        throw new JiraError(`Jira request failed for ${path}`, 502);
      }
      const status = response.status;
      if (status === 401 || status === 403) {
        throw new JiraError(`HTTP ${status}`, status);
      }
      if (status === 404) {
        if (missingOk) {
          return null;
        }
        throw new JiraError(missingMessage(path, this.config.jiraBoardId), 404);
      }
      if (status >= 500 && status <= 599) {
        if (attempt < ATTEMPTS - 1) {
          await sleep(500 * 2 ** attempt);
          continue;
        }
        throw new JiraError(`HTTP ${status}`, 502);
      }
      if (status >= 400) {
        throw new JiraError(`HTTP ${status}`, status);
      }
      try {
        return await response.json();
      } catch {
        throw new JiraError(`Jira request failed for ${path}`, 502);
      }
    }
    throw new JiraError(`Jira request failed for ${path}`, 502);
  }
}

function laterStart(candidate, current) {
  const candidateStart = Date.parse(candidate.startDate || "");
  const currentStart = Date.parse(current.startDate || "");
  const candidateKnown = !Number.isNaN(candidateStart);
  const currentKnown = !Number.isNaN(currentStart);
  if (candidateKnown !== currentKnown) {
    return candidateKnown;
  }
  if (!candidateKnown) {
    return false;
  }
  return candidateStart > currentStart;
}

function isEpic(node) {
  return String(node.fields?.issuetype?.name || "").toLowerCase() === "epic";
}

function missingMessage(path, boardId) {
  if (path.startsWith(`/rest/agile/1.0/board/${boardId}`)) {
    return `HTTP 404 for board ${boardId}`;
  }
  return "HTTP 404";
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
