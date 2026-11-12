/** Load and validate the Module 08 environment variables. */

export const REQUIRED_VARIABLES = [
  "JIRA_BASE_URL",
  "JIRA_EMAIL",
  "JIRA_API_TOKEN",
  "JIRA_BOARD_ID",
  "JIRA_ASSIGNEE_ACCOUNT_IDS",
];

const ASSIGNEE_COUNT = 5;

export class ConfigError extends Error {
  constructor(variables) {
    super(variables.join(", "));
    this.variables = variables;
  }
}

export function loadConfig(env) {
  const missing = REQUIRED_VARIABLES.filter((name) => !text(env, name));
  if (missing.length) {
    throw new ConfigError(missing);
  }

  const accountIds = env.JIRA_ASSIGNEE_ACCOUNT_IDS.split(",").map((part) => part.trim());
  const unique = new Set(accountIds);
  if (
    accountIds.length !== ASSIGNEE_COUNT ||
    accountIds.some((accountId) => !accountId) ||
    unique.size !== ASSIGNEE_COUNT
  ) {
    throw new ConfigError(["JIRA_ASSIGNEE_ACCOUNT_IDS"]);
  }

  const timezone = text(env, "REPORT_TIMEZONE") || "Asia/Kolkata";
  try {
    new Intl.DateTimeFormat("en-US", { timeZone: timezone }).format(new Date());
  } catch {
    throw new ConfigError(["REPORT_TIMEZONE"]);
  }

  const hourText = text(env, "REPORT_HOUR_LOCAL") || "8";
  const hour = Number(hourText);
  if (!Number.isInteger(hour) || hour < 0 || hour > 23 || String(hour) !== String(Number(hourText))) {
    throw new ConfigError(["REPORT_HOUR_LOCAL"]);
  }

  return {
    jiraBaseUrl: text(env, "JIRA_BASE_URL").replace(/\/+$/, ""),
    jiraEmail: text(env, "JIRA_EMAIL"),
    jiraApiToken: text(env, "JIRA_API_TOKEN"),
    jiraBoardId: text(env, "JIRA_BOARD_ID"),
    assigneeAccountIds: accountIds,
    timezone,
    reportHourLocal: hour,
  };
}

function text(env, name) {
  return String(env?.[name] ?? "").trim();
}
