# Read Jira

Read the current Jira Cloud board for the sprint health report. Return board, sprint, issue, field, and assignee data. Leave filtering, totals, and the workbook to the report step.

## Input format

- Read configuration before any HTTP call. Use `load_config` in `sprint_health/config.py`, then `JiraClient`. Do not run `python -m sprint_health` for this read. That command writes the workbook and, when no sprint is active, skips field ids and column order.
- Required values:
  + `JIRA_BASE_URL` — Jira Cloud origin only, `https://<site>.atlassian.net`, no trailing path.
  + `JIRA_EMAIL` — Atlassian account email.
  + `JIRA_API_TOKEN` — API token for that account.
  + `JIRA_BOARD_ID` — numeric board id.
  + `JIRA_ASSIGNEE_ACCOUNT_IDS` — comma-separated list of exactly five non-blank, unique account ids. Keep that order.
- Load a project-root `.env` without overriding variables already set in the process environment. `load_config` removes one trailing `/` from `JIRA_BASE_URL` and does not otherwise rewrite the origin.
- When a required value is missing or blank, stop before calling Jira. Print each missing name on its own stderr line, then exit 1 once. Print no other text.
- Validate the assignee list only after those five values are present. When it is not exactly five non-blank unique ids, print `JIRA_ASSIGNEE_ACCOUNT_IDS` and exit 1.
- An invalid `REPORT_TIMEZONE` or `REPORT_HOUR_LOCAL` also exits 1 before Jira and prints that name. Unset values default to `Asia/Kolkata` and `8`.

## Processing steps

- Authenticate every request with HTTP Basic. Username is `JIRA_EMAIL`. Password is `JIRA_API_TOKEN`. Send `Accept: application/json`. Use a 30 second timeout.
- `GET /rest/agile/1.0/board/{boardId}`. Keep `id`, `name`, and `location.projectKey`. The board payload has no site field. The origin used later is `JIRA_BASE_URL` after the trailing slash is removed.
- `GET /rest/agile/1.0/board/{boardId}/sprint?state=active`. Page with `startAt` and `maxResults` of 50. Stop when `isLast` is true, the page is empty, `startAt` does not advance, or `startAt + page length >= total`. When `isLast` is absent, stop. When `total` is absent, do not use it as a stop.
- When several sprints are active, keep the one with the latest `startDate`. Set `selectionNote` to every active sprint name, including the one kept, and state that the latest start date won. A sprint with a missing or unparseable `startDate` loses to every sprint that has one.
- When no sprint is active, skip the issue fetch. That is not an error. Still read field ids, board column order, and the five assignee names.
- `GET /rest/api/3/field` once per run.
  + Story Points is the first field named `Story Points`. When it is missing, omit it from later requests.
  + Sprint is the first field whose schema custom type is `com.pyxis.greenhopper.jira:gh-sprint`. When that type is missing, use the first field named `Sprint`. When both are missing, omit the field.
- `GET /rest/agile/1.0/sprint/{sprintId}/issue`. Page with `maxResults` of 50. Stop when the page is empty, `total` is absent, or the running count reaches `total`. Request `summary`, `status`, `assignee`, `parent`, then the Sprint field id, then the Story Points field id, and only when that id exists.
- Leave `fields.parent` as Jira returned it. The report treats it as the phase epic when `parent.fields.issuetype.name` is Epic, ignoring case. This read does not rewrite the parent.
- When the immediate parent is not an epic and has a key, `GET /rest/api/3/issue/{parentKey}?fields=summary,issuetype,parent` once per parent key. Cache that key for the run. Copy `summary` and `issuetype` onto the immediate parent only when those are missing. When the fetched issue has a parent, store it at `fields.parent.fields.parent`. Do not hop again. Do not replace the immediate parent with that epic.
- `GET /rest/agile/1.0/board/{boardId}/configuration`. Read status names in column order, left to right. When a column status has an id and no name, resolve it with `GET /rest/api/3/status`. Drop duplicate names.
- `GET /rest/api/3/user?accountId=` for each of the five account ids, in configured order. Keep the display name, or the account id when Jira returns none.
- On a network error or HTTP 5xx, retry that request up to 3 times. Wait 0.5s, then 1s, then 2s. Then exit 1. A network error prints `Jira request failed for {path}` and does not print the exception text. HTTP 5xx prints `HTTP <status>`.

## Output format

- Board: `id`, `name`, `project_key`.
- Active sprint, or none. Include `id`, `name`, `state`, `startDate`, `endDate`, and `selectionNote` when more than one sprint was active.
- Sprint issues after the one parent hop. Each issue keeps `key` and `fields` for summary, status, assignee, parent, sprint, and story points. The extra parent, when fetched, stays at `fields.parent.fields.parent`.
- Return this data in the reply. Do not write `sprint-health-YYYY-MM-DD.xlsx`. Do not print `sprint_id`, an issue total, or an output path.
- Story Points field id, or none.
- Sprint field id, or none. When it is none, the report treats every in-scope issue as not spillover.
- Status names in board column order. Empty when Jira omits the configuration.
- Assignee display names keyed by account id, in the configured order.

## Constraints

- Jira Cloud only. GET only. Do not create, edit, transition, or comment on issues.
- One site, one board, the five configured accounts.
- Do not print the API token, the Authorization header, or issue descriptions.
- HTTP 401 or 403: exit 1 and print only `HTTP <status>`.
- HTTP 404 on the board: exit 1 and print `HTTP 404 for board {boardId}`. A 404 on a user, a parent issue, the board configuration, or the status catalog returns empty for that call and the read continues. Any other 404 prints `HTTP 404` and exits 1.
- Any other HTTP 4xx: exit 1 and print `HTTP <status>`.
- A response that is not JSON, and a network error after retries: exit 1 and print `Jira request failed for {path}`. Do not print the body or the exception text. The exception text can contain the API token.
- No active sprint is a successful read with an empty issue list.
- Page size is 50. Do not request a Story Points or Sprint field the site does not have.
- Follow at most one parent hop. Leave an unresolved epic unresolved so the report can count the issue as `No phase`.
