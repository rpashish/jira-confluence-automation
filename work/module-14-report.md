# Module 14 Completion Report

## Backlog Contents
# Sprint health implementation backlog

Version 1 from `project_spec.md`: a weekday Python command, `python -m sprint_health`, that writes `sprint-health-YYYY-MM-DD.xlsx` for the database-migration steering committee.

This is a greenfield plan. Every task starts open, including work that may already exist in the tree.

## Decisions

- Finish one happy-path run that writes a complete workbook before retries, authentication failures, and the atomic file replace.
- The Integration phase installs a launchd agent on this Mac. It stays unloaded until the live board comparison in Testing matches Jira.
- Documentation is a README, a `.env.example` with placeholders, and the section 10 failure behavior.

Build in phase order. Inside Core Features, finish the happy path before the hardening tasks.

## Setup

- [ ] Add `pyproject.toml` for the `sprint-health` package, `requires-python >= 3.11`, dependencies `requests`, `openpyxl`, and `python-dotenv`, and a `pytest` dev extra — custom skill (#1)
- [ ] Point setuptools at the `sprint_health` package, and set pytest `pythonpath = ["."]` and `testpaths = ["tests"]` so `python -m pytest` runs from a fresh checkout — custom skill (#2)
- [ ] Create the package modules `sprint_health/__init__.py`, `__main__.py`, `config.py`, `jira_client.py`, `report.py`, and `excel_writer.py`, each with a docstring that states the responsibility in the spec — custom skill (#3)
- [ ] Create `tests/test_report.py` for fixture-only tests that never call the network — custom skill (#4)
- [ ] Create `.venv` with Python 3.11 or newer and install the project with the dev extra — custom skill (#5)
- [ ] Gitignore `.env`, `.venv/`, and `out/` so the API token and generated workbooks stay out of git — custom skill (#6)
- [ ] Add `tests/fixtures/` for the recorded Jira payload used later by the sheet-row test — custom skill (#7)

## Module 19 — GitHub coding agent

The coding agent takes a repository issue, edits files, and opens a pull request. It has no access to this Mac, the gitignored `.env`, or the live Jira board, and it must not receive `JIRA_API_TOKEN`.

Delegate these open Setup issues. Each one is a committed file change whose acceptance criteria are already written above:

- #2 — setuptools package discovery and pytest `pythonpath` / `testpaths`
- #3 — `sprint_health` module files, each with a docstring that states its spec responsibility
- #4 — `tests/test_report.py` for fixture-only tests that never call the network
- #6 — `.gitignore` entries for `.env`, `.venv/`, and `out/`
- #7 — add `tests/fixtures/` and a sanitized fixture skeleton. Record the real Jira payload in a later local step so the fixture does not invent board data.

Keep these in the local session:

- #1 is already closed.
- #5 creates `.venv` on this machine and installs the dev extra.
- Integration: the launchd plist may be committed only as a template with no secret. Confirming the Mac timezone, loading `.env` from this working directory, and `launchctl bootstrap` / `kickstart` stay here.
- Testing items marked MCP: the two blocking comparisons against the live board.
- Any task that needs the API token, a real account id, or a check that the real token is absent from the tree.

## Core Features

### Happy path

One successful run, with valid credentials and Jira responding, writes the full workbook. Do these tasks before the hardening list.

#### Config

- [ ] Implement `load_config` to read `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_BOARD_ID`, and `JIRA_ASSIGNEE_ACCOUNT_IDS` — custom skill
- [ ] Load a project-root `.env` through python-dotenv without overriding variables that are already set in the process environment — custom skill
- [ ] Default `REPORT_OUTPUT_DIR` to `./out`, `REPORT_TIMEZONE` to `Asia/Kolkata`, and `REPORT_HOUR_LOCAL` to `8` — custom skill
- [ ] Split `JIRA_ASSIGNEE_ACCOUNT_IDS` on commas, strip whitespace, and keep that order for the cover and the workload rows — custom skill

#### Jira read

- [ ] Implement `JiraClient` with HTTP Basic auth: username is `JIRA_EMAIL`, password is `JIRA_API_TOKEN`, base URL is `JIRA_BASE_URL` with no trailing path — custom skill
- [ ] `GET /rest/agile/1.0/board/{boardId}` and keep `name` plus `location.projectKey` for the cover. The site shown on the cover is the host of `JIRA_BASE_URL` — custom skill
- [ ] `GET /rest/agile/1.0/board/{boardId}/sprint?state=active`, page with `startAt` until `startAt + page length >= total`, and select the sprint with the latest `startDate` — custom skill
- [ ] When more than one sprint is active, keep the discarded sprint names so the cover can record which sprint was chosen and why — custom skill
- [ ] `GET /rest/api/3/field` once per run. Resolve the field whose name is `Story Points` and the field whose name is `Sprint` — custom skill
- [ ] `GET /rest/agile/1.0/sprint/{sprintId}/issue` and page until `total` is exhausted. Request `summary`, `status`, `assignee`, `parent`, the Sprint field id, and the Story Points field id — custom skill
- [ ] When `Story Points` is absent, leave it out of the request. Points stay blank and issue counts are still computed — custom skill
- [ ] When `Sprint` is absent, treat every in-scope issue as not spillover and include that fact in the stdout log — custom skill
- [ ] `GET /rest/agile/1.0/board/{boardId}/configuration` and read status names in column order — custom skill
- [ ] Resolve a display name for each of the five account ids with `GET /rest/api/3/user?accountId=`, so a person with no sprint issues still appears by name — custom skill
- [ ] Treat `parent` as the phase epic when `parent.fields.issuetype` is Epic — custom skill
- [ ] When the parent is a story under an epic, `GET /rest/api/3/issue/{parentKey}` once and follow one more parent hop. When that hop still does not reach an epic, the issue is `No phase` — custom skill

#### Report rows

- [ ] Keep an issue only when `assignee.accountId` is one of the five configured ids — custom skill
- [ ] Count active-sprint issues assigned to anyone else as the excluded count. Leave those issues out of scope, phase, and workload totals — custom skill
- [ ] Scope is the in-scope issue count. When the Story Points field exists, also sum points on those issues. Issues with no points add nothing to the sum. When no in-scope issue has points, leave the points figure blank — custom skill
- [ ] Done is the in-scope issues whose status category key is `done` — custom skill
- [ ] Remaining is Scope minus Done — custom skill
- [ ] Spillover is an in-scope issue that is on the active sprint and on at least one earlier sprint. Earlier means another sprint on the issue whose `startDate` is before the active sprint `startDate` — custom skill
- [ ] Completion is Done divided by Scope, as a percentage. Scope of 0 yields 0% — custom skill
- [ ] Count in-scope issues by status name in board column order. Append statuses that are not on the board after the columns, in the order they first appear — custom skill
- [ ] Build one phase row for each epic that parents at least one in-scope issue: epic key, epic summary, scope, done, remaining, spillover, completion — custom skill
- [ ] Put in-scope issues with no resolved epic in a final row named `No phase`. Omit that row when every in-scope issue has an epic — custom skill
- [ ] Build one workload row per configured assignee, in configured order, including people with no sprint issues — custom skill
- [ ] Open issues are that person's remaining issues. Remaining points are the sum of Story Points on those open issues, and blank when none of those issues have points — custom skill
- [ ] Share of open work is that person's open issues divided by all open issues in the report. When the report has no open issues, the share is 0% — custom skill
- [ ] Mark `Overloaded` when the person's open-issue count is greater than 1.5 times the mean open-issue count of the five people. The mean includes people on zero. A count equal to 1.5 times the mean is `Within range`. When nobody has open work, every person is `Within range` — custom skill
- [ ] When no sprint is active, still build the report: zero health totals, no phase rows, five workload rows at zero and `Within range`, excluded count 0, and cover text that there is no active sprint — custom skill
- [ ] Days remaining is the number of calendar days from the run date to the sprint end date in `REPORT_TIMEZONE`. A sprint that ends on the run date has 0 days remaining — custom skill

#### Workbook and command

- [ ] Write four sheets named `Cover`, `Sprint health`, `Migration phases`, and `Workload` — custom skill
- [ ] Cover sheet: title `Sprint health — database migration`; Jira site, project key, and board name; sprint name, state, start date, end date, and days remaining; generated-at timestamp and timezone; the five assignees by display name; the active-sprint choice when several were active; one line for the excluded-issue count — custom skill
- [ ] Sprint health sheet: scope (issues and points), done, remaining, spillover, completion, and the status counts — custom skill
- [ ] Migration phases sheet: epic key, epic summary, scope, done, remaining, spillover, completion, with `No phase` last when it exists — custom skill
- [ ] Workload sheet: Assignee, Open issues, Remaining points, Share of open work, Balance, one row for each of the five people — custom skill
- [ ] Name the file `sprint-health-YYYY-MM-DD.xlsx`, using the run date in `REPORT_TIMEZONE`, and write it under `REPORT_OUTPUT_DIR` — custom skill
- [ ] Create the output directory when it is missing — custom skill
- [ ] Wire `python -m sprint_health` to load config, read Jira, build the four sections, write the workbook, and return 0 — custom skill
- [ ] Log the sprint id (`none` when there is no active sprint), the in-scope issue count, and the output path. Leave the API token and issue descriptions out of stdout and stderr — custom skill
- [ ] A second run on the same local date replaces that day's workbook — custom skill
- [ ] A run with no active sprint writes the zeroed workbook and exits 0 — custom skill

Happy-path gate: with valid credentials, or with a stub that returns one active sprint, the command produces `sprint-health-<date>.xlsx` containing all four sheets.

### Hardening

Start these only after the happy-path gate. They cover bad configuration, retries, authentication and board errors, and the atomic replace.

- [ ] When a required variable is missing or blank, exit 1 before any Jira call and print that variable's name on stderr — custom skill
- [ ] When the assignee list is not exactly five non-blank, unique account ids, exit 1 and print `JIRA_ASSIGNEE_ACCOUNT_IDS` — custom skill
- [ ] When `REPORT_TIMEZONE` is not a valid IANA zone, or `REPORT_HOUR_LOCAL` is not an integer from 0 through 23, exit 1 and print that variable's name — custom skill
- [ ] On HTTP 401 or 403, exit 1, print the status code, and keep the token and the Authorization header out of the message — custom skill
- [ ] On HTTP 404 for the board, exit 1 and include the board id in the message — custom skill
- [ ] On a network error or HTTP 5xx, retry that request up to 3 times with backoffs of about 1s, 2s, and 4s, then exit 1 — custom skill
- [ ] Write the workbook to a temporary file in the output directory. Replace `sprint-health-YYYY-MM-DD.xlsx` only after openpyxl has saved the complete file — custom skill
- [ ] When a run fails, leave any existing workbook for that date in place, and remove the temporary file — custom skill
- [ ] Confirm an authentication failure exits non-zero and does not replace a previously finished workbook for that date — custom skill

## Integration

Schedule the same command with launchd on this Mac. Author the agent here. Leave it unloaded until the blocking live comparison in Testing passes.

- [ ] Add a launchd plist at `~/Library/LaunchAgents/com.sprint-health.report.plist`. Keep it out of git if it would embed a secret; the committed artifact, if any, is a template with no token — custom skill
- [ ] Set `StartCalendarInterval` to Monday–Friday (`Weekday` 1 through 5), `Minute` 0, and `Hour` from `REPORT_HOUR_LOCAL` (default 8) — custom skill
- [ ] Confirm the Mac system timezone is `Asia/Kolkata`, matching `REPORT_TIMEZONE`. launchd fires on the system clock. The report timezone still controls the filename date and the generated-at timestamp — custom skill
- [ ] Set `ProgramArguments` to `<project>/.venv/bin/python` and `-m` `sprint_health`, and set `WorkingDirectory` to the project root so the process loads the gitignored `.env` — custom skill
- [ ] Keep `JIRA_EMAIL`, `JIRA_API_TOKEN`, and the account ids out of the plist. The command reads them from the environment or `.env` — custom skill
- [ ] Send `StandardOutPath` and `StandardErrorPath` to log files under the project that are gitignored. A failed morning run must be readable from those logs, and the logs must not contain the token — custom skill
- [ ] Use one command for the agent and for a manual run. Version 1 adds no second interface — custom skill
- [ ] Leave the agent unloaded. Do not `launchctl bootstrap` it in this phase — custom skill

## Testing

Unit tests use fixture issues and no network. The last items are the live board gate. The launchd agent stays unloaded until that gate passes.

- [ ] Test spillover: an issue on the active sprint and an earlier sprint counts; an issue only on the active sprint does not; an issue that also sits on a later sprint does not count unless an earlier sprint is present — custom skill
- [ ] Test epic grouping: a direct epic parent, one extra hop through a story, and `No phase` when the hop does not reach an epic — custom skill
- [ ] Test completion for a normal done/scope ratio, and 0% when scope is 0 — custom skill
- [ ] Test the overload rule: open issues greater than 1.5 times the five-person mean (zeros included) is `Overloaded`; a count equal to 1.5 times the mean is `Within range`; when every person has zero open issues, each is `Within range` — custom skill
- [ ] Test that all five assignees appear, including people with no issues, and that other assignees affect only the excluded count — custom skill
- [ ] Test that a missing Story Points field leaves points blank and the issue counts still match — custom skill
- [ ] Check in one recorded Jira sprint payload under `tests/fixtures/` and assert the cover, health, phase, workload, and excluded-count rows against expected values — custom skill
- [ ] Test the filename date in `REPORT_TIMEZONE`, including a UTC time that is already the next calendar day in `Asia/Kolkata` — custom skill
- [ ] Test no active sprint: the workbook has zero totals, the cover says there is no active sprint, and the process exits 0 — custom skill
- [ ] Test sprint and issue pagination until `total` is exhausted, and that several active sprints resolve to the latest `startDate` — custom skill
- [ ] Test one parent hop: a story parent is fetched, and the epic above it becomes the phase — custom skill
- [ ] Test HTTP 401 and 403: exit 1, the status is printed, and the token is absent from stdout and stderr — custom skill
- [ ] Test a board HTTP 404: exit 1 and the message names the board id — custom skill
- [ ] Test retries: a 5xx or network error succeeds on a later attempt within the three retries, and a persistent failure exits 1 after the third retry — custom skill
- [ ] Test the atomic replace: an authentication failure leaves an existing `sprint-health-<date>.xlsx` byte-for-byte unchanged and does not leave the temporary file in its place — custom skill
- [ ] Search the repo and confirm the real API token is absent from source, tests, fixtures, the plist template, and `.env.example` — custom skill
- [ ] Blocking: run `python -m sprint_health` against the real board. Compare scope, done, remaining, spillover, phase rows, and the five workload rows with the Jira sprint filtered to those five account ids. Done uses the Done status category — MCP
- [ ] Blocking: confirm issues assigned outside the five match the excluded count and are absent from scope, phase, and workload totals — MCP
- [ ] Only after both comparisons match, `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.sprint-health.report.plist` and `launchctl kickstart` the agent once. Confirm today's workbook is written. If either comparison disagrees, leave the agent unloaded and fix the report first — custom skill

## Documentation

- [ ] Write `README.md`: who the workbook is for, what a weekday run produces, the required Python version, and how to create `.venv` and install the package with the dev extra — custom skill
- [ ] Document every variable. Required: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_BOARD_ID`, `JIRA_ASSIGNEE_ACCOUNT_IDS` (exactly five account ids). Optional, with defaults: `REPORT_OUTPUT_DIR` (`./out`), `REPORT_TIMEZONE` (`Asia/Kolkata`), `REPORT_HOUR_LOCAL` (`8`) — custom skill
- [ ] Document `python -m sprint_health`, the filename `sprint-health-YYYY-MM-DD.xlsx`, the output directory, and that a second run on the same local date overwrites that file — custom skill
- [ ] Document the four sheets and the metric definitions: scope, done (status category `done`), remaining, spillover (active sprint plus an earlier sprint), completion with 0% at zero scope, phase rows, the `No phase` row, workload columns, and `Overloaded` as greater than 1.5 times the five-person mean of open issues — custom skill
- [ ] Document the launchd agent: plist path, Monday–Friday at the configured local hour, the requirement that the Mac timezone match `REPORT_TIMEZONE`, that secrets stay in `.env`, the log paths, and that the agent stays unloaded until the live board comparison passes — custom skill
- [ ] Add `.env.example` with a blank placeholder for each variable and a comment for each default. Use no real email, token, board id, or account id — custom skill
- [ ] Document the section 10 failure behavior in the README: missing or blank required variable (exit 1, print the name, no Jira call); assignee list not exactly five (exit 1); HTTP 401 or 403 (exit 1, print the status, omit the token); board HTTP 404 (exit 1, name the board id); network or HTTP 5xx (three retries with backoff, then exit 1); no active sprint (write zero totals, exit 0); missing output directory (create it, then write); logs include sprint id, issue count, and output path and omit the token and issue descriptions; a failed run does not replace a finished workbook — custom skill

## GitHub Issues
| Issue URL | Title | Created via MCP? |
|-----------|-------|-----------------|
| https://github.com/rpashish/jira-confluence-automation/issues/8 | Module 14 GitHub MCP issue | Yes |

## MCP Tools Used
- get_me
- search_repositories
- issue_write
