# Read Jira

Read the current Jira Cloud board for the sprint health report. Return board, sprint, issue, field, and assignee data. Leave filtering, totals, and the workbook to the report step.

## Input format

- Read configuration before any HTTP call.
- Required values:
  + `JIRA_BASE_URL` — Jira Cloud origin only, `https://<site>.atlassian.net`, no trailing path.
  + `JIRA_EMAIL` — Atlassian account email.
  + `JIRA_API_TOKEN` — API token for that account.
  + `JIRA_BOARD_ID` — numeric board id.
  + `JIRA_ASSIGNEE_ACCOUNT_IDS` — comma-separated list of exactly five non-blank, unique account ids. Keep that order.
- Load a project-root `.env` without overriding variables already set in the process environment.
- When a required value is missing or blank, or the assignee list is not exactly five unique ids, stop before calling Jira. Exit 1 and print that variable's name on stderr.

## Processing steps

- Authenticate every request with HTTP Basic. Username is `JIRA_EMAIL`. Password is `JIRA_API_TOKEN`. Send `Accept: application/json`. Use a 30 second timeout.
- `GET /rest/agile/1.0/board/{boardId}`. Keep `id`, `name`, and `location.projectKey`. The site is the host of `JIRA_BASE_URL`.
- `GET /rest/agile/1.0/board/{boardId}/sprint?state=active`. Page with `startAt` and `maxResults` of 50 until `isLast` is true or `startAt + page length >= total`.
- When several sprints are active, keep the one with the latest `startDate`. Record the other sprint names and that the latest start date won.
- When no sprint is active, skip the issue fetch. That is not an error.
- `GET /rest/api/3/field` once per run.
  + Story Points is the field named `Story Points`. When it is missing, omit it from later requests.
  + Sprint is the field whose schema custom type is `com.pyxis.greenhopper.jira:gh-sprint`. When that type is missing, use the field named `Sprint`. When both are missing, omit the field.
- `GET /rest/agile/1.0/sprint/{sprintId}/issue`. Page until `total` is exhausted. Request `summary`, `status`, `assignee`, `parent`, plus the Sprint and Story Points field ids when they exist.
- Treat `parent` as the phase epic when `parent.fields.issuetype.name` is Epic, ignoring case.
- When the parent is not an epic, `GET /rest/api/3/issue/{parentKey}?fields=summary,issuetype,parent` once per parent key and follow one more parent hop. Cache that key for the run. Do not hop again.
- `GET /rest/agile/1.0/board/{boardId}/configuration`. Read status names in column order, left to right. When a column status has an id and no name, resolve it with `GET /rest/api/3/status`. Drop duplicate names.
- `GET /rest/api/3/user?accountId=` for each of the five account ids, in configured order. Keep the display name, or the account id when Jira returns none.
- On a network error or HTTP 5xx, retry that request up to 3 times. Wait about 0.5s, then 1s, then 2s. Then exit 1.

## Output format

- Board: `id`, `name`, `project_key`.
- Active sprint, or none. Include `id`, `name`, `state`, `startDate`, `endDate`, and `selectionNote` when more than one sprint was active.
- Sprint issues after the one parent hop. Each issue keeps `key` and `fields` for summary, status, assignee, parent, sprint, and story points.
- Story Points field id, or none.
- Sprint field id, or none. When it is none, the report treats every in-scope issue as not spillover.
- Status names in board column order. Empty when Jira omits the configuration.
- Assignee display names keyed by account id, in the configured order.

## Constraints

- Jira Cloud only. GET only. Do not create, edit, transition, or comment on issues.
- One site, one board, the five configured accounts.
- Do not print the API token, the Authorization header, or issue descriptions.
- HTTP 401 or 403: exit 1 and print only `HTTP <status>`.
- HTTP 404 on the board: exit 1 and include the board id. A 404 on a user, a parent issue, the board configuration, or the status catalog returns empty for that call and the read continues.
- Any other HTTP 4xx: exit 1 and print `HTTP <status>`.
- A response that is not JSON: exit 1 and name the path. Do not print the body.
- No active sprint is a successful read with an empty issue list.
- Page size is 50. Do not request a Story Points or Sprint field the site does not have.
- Follow at most one parent hop. Leave an unresolved epic unresolved so the report can count the issue as `No phase`.
