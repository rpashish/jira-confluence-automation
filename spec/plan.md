# Implementation Plan: Sprint Health Report

**Branch**: `001-sprint-health` | **Date**: 2026-11-13 | **Spec**: [spec/specification.md](specification.md)

**Input**: Feature specification in `spec/specification.md`, reviewed in `spec/clarify.md`. Constitution `spec/constitution.md` 1.0.0.

## Summary

Version 1 is a weekday command that reads one Jira Cloud board and writes one Excel workbook for the database-migration steering committee. The workbook shows sprint scope, done, remaining, spillover, and completion for five configured accounts, then the same issues by parent epic, then workload balance across those five people.

The technical approach is the Python 3.11 package `sprint_health`: validate the environment, read Jira with HTTP Basic, build the report in memory, and replace that day's workbook only after the file is complete. There is no web UI, database, or Confluence write in this feature.

## Milestones

| Milestone | Phase | Done when |
| --- | --- | --- |
| M0 Gate | 0 | The constitution allows this batch report, and the planning decisions below are copied into `spec/specification.md`. |
| M1 Config | 1 | A missing or invalid setting exits 1 before any Jira call and prints that setting's name. |
| M2 Jira read | 2 | Fixture tests cover sprint choice, pagination, retries, and token-free errors with no network. |
| M3 Report math | 3 | User stories P1, P2, and P3 pass from fixture issues with no network. |
| M4 Workbook | 4 | A recorded payload produces the four sheets, and a failed write leaves the previous file in place. |
| M5 Command | 5 | `python -m sprint_health` returns 0 with the log line on success, including no active sprint, and returns 1 on auth or board failure. |
| M6 Live schedule | 6 | One live-board comparison matches the five-account filter, and only then is the weekday scheduler enabled. |

## Technical Context

**Language/Version**: Python 3.11 or newer

**Primary Dependencies**: `requests` (Jira Cloud REST), `openpyxl` (`.xlsx`), `python-dotenv` (local `.env` only). Tests use `pytest`.

**Storage**: One workbook per run date under `REPORT_OUTPUT_DIR` (default `./out`). No database. Generated workbooks and `.env` stay out of git.

**Testing**: `pytest` for config, the Jira client, and report math, using fixtures and no network. One recorded sprint payload is checked against sheet rows. One manual comparison against the live board is the last gate before scheduling.

**Target Platform**: The operator's machine, weekday morning, via cron or a launchd agent. The command itself does not install or start the scheduler.

**Project Type**: Command-line batch job (`python -m sprint_health`).

**Performance Goals**: One board and one sprint per run. The sprint issue list is paged until `total` is exhausted. A few hundred issues is the expected size.

**Constraints**: HTTP Basic uses `JIRA_EMAIL` and `JIRA_API_TOKEN`. Logs and error text omit the token and issue descriptions. Exit 1 happens before Jira when configuration is invalid. A finished workbook is replaced only by `os.replace` after a complete temporary file is saved. Network errors and HTTP 5xx retry up to three times (waits of 0.5s, 1s, and 2s) and then exit 1.

**Scale/Scope**: One Jira Cloud site, one board, five assignee account ids, four workbook sheets. Version 1 has one interface: this command.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result | Evidence |
| --- | --- | --- |
| I. Spec before code | Pass, after M0 | This plan implements `spec/specification.md`. Decisions that `spec/clarify.md` left open are listed below and must be written back into the spec before M1 is accepted. |
| II. Locked stack | Fail | The feature requires a Python batch job. React 18, Vite, Express, and PostgreSQL 15 are not part of version 1. |
| III. One API boundary | Fail | There is no Vite application and no `/api` for this feature. Jira is called by the command. |
| IV. Official Atlassian APIs | Pass for Jira | Jira Cloud REST only, credentials from the environment. Confluence is not called. |
| V. Idempotent sync | Fail as written | Version 1 does not create or update Jira issues or Confluence pages. A second run on the same local date replaces that day's workbook after the new file is complete. A failed run leaves the previous file. |

The gate does not pass on 1.0.0. M0 amends the constitution so a read-only sprint workbook is an allowed batch feature, with Python 3.11, `requests`, and `openpyxl` as its stack. Until that amendment is ratified, implementation is not accepted. `sprint-health-web/` is outside this plan: the spec excludes a web dashboard, and that app is React 19 and Express 5 rather than the constitution's React 18 and PostgreSQL 15.

## Planning Decisions

These close the items in `spec/clarify.md` for this feature. M0 copies them into the specification.

| Topic | Decision |
| --- | --- |
| Population | The active sprint of the configured board is the population. Unassigned issues and issues assigned outside the five account ids increment the excluded count and stay out of scope, phases, and workload. |
| Project key and board name | Taken from the board resource (`location.projectKey` and board name). The cover shows the configured site origin as the Jira site. |
| Several active sprints | The latest `startDate` wins. A sprint with no parseable start date loses to any dated sprint. Equal start timestamps keep the first sprint returned. The cover records the names considered and the sprint used. |
| No active sprint | Exit 0. Cover sprint name is `No active sprint`. Dates and days remaining are blank. Health counts are zero and point cells are blank. Phase sheet has headers only. Workload lists the five people with zero open issues, blank points, share 0%, and `Within range`. Excluded count is 0. |
| Days remaining | Calendar-day difference from the run's local date to the sprint end date in `REPORT_TIMEZONE`. Missing end date is blank. A date in the past is shown as 0. |
| Spillover | The issue lists the active sprint and another sprint whose start is earlier. When either start date is missing, the other sprint counts as earlier only when its state is `closed` or `completed`. |
| Done and completion | Status category key `done`, case-insensitive. Completion is done issues divided by scope issues, displayed as a percentage. Scope 0 yields 0%. Points are not the completion denominator. |
| Story points | The first field named `Story Points`. A numeric value, including 0, is summed. Blank, empty, and non-numeric values are ignored. A total cell is blank only when every contributing issue has no usable points. |
| Workload | Open issues are in-scope issues that are not done. Share is that person's open issues divided by all five people's open issues, displayed as a percentage, and 0% when the total is 0. `Overloaded` means the open-issue count is greater than 1.5 times the mean of the five counts, with no rounding of the mean. Several people may be overloaded. |
| Order | Assignees stay in configured list order. Phase rows are epic key ascending, with `No phase` last. Status rows follow board column order, then any remaining status name. Zero-count statuses are omitted. |
| Hierarchy | Parent issue type `Epic`, ignoring case, or one hop through a story parent. Anything else is `No phase`, including an epic that is itself on the sprint. Subtasks on the sprint count as their own issues. |
| Display names | `GET /rest/api/3/user?accountId=` for each configured id. A missing name or a 404 for that user shows the account id. HTTP 5xx still retries and can fail the run. |
| Settings | Required: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_BOARD_ID`, `JIRA_ASSIGNEE_ACCOUNT_IDS` (comma-separated, exactly five non-blank ids). Optional: `REPORT_OUTPUT_DIR` (`./out`), `REPORT_TIMEZONE` (`Asia/Kolkata`), `REPORT_HOUR_LOCAL` (`8`, integer 0–23, used by the operator's scheduler). An invalid timezone or hour exits 1 before Jira. |
| Secrets in git | The real token, the real email, and the real five account ids are not committed. Fixtures use fake ids. `.env.example` lists the names with empty values. |
| Process signal | Exit 0 on a complete workbook, including no active sprint. Exit 1 otherwise. Success log: `sprint_id=<id or none> issues=<in-scope count> output=<path>`. |
| Scheduler | Monday–Friday at `REPORT_HOUR_LOCAL` in `REPORT_TIMEZONE`, owned by cron or launchd on the machine that holds `.env`. A manual run on any day uses the same command. The schedule stays unloaded until M6. |
| Leadership handoff | The project manager takes the file from the output directory. Version 1 does not mail or publish it. |

## Project Structure

### Documentation (this feature)

```text
spec/
├── constitution.md
├── specification.md
├── clarify.md
└── plan.md                 # this file
```

### Source Code (repository root)

```text
sprint_health/
├── __init__.py
├── __main__.py             # wire the steps and return the exit code
├── config.py               # environment validation
├── jira_client.py          # Jira Cloud reads, pagination, retries
├── report.py               # health, phases, workload
└── excel_writer.py         # four sheets and atomic replace

tests/
├── test_config.py
├── test_jira_client.py
└── test_report.py

pyproject.toml              # Python >=3.11, requests, openpyxl, python-dotenv, pytest
```

**Structure Decision**: One Python package and one test directory. `config` validates the environment. `jira_client` performs authenticated GETs. `report` is pure and receives already fetched payloads. `excel_writer` only renders a finished report. `__main__` calls them in that order. The web app under `sprint-health-web/` is not a version 1 deliverable.

### Workbook contract

| Sheet | Contents |
| --- | --- |
| Cover | Title `Sprint health — database migration`; site, project key, board; sprint name, state, start, end, days remaining, selection note; generated-at `YYYY-MM-DD HH:MM` and timezone; the five display names in configured order; one excluded-issue count. |
| Sprint health | Scope, scope points, done, remaining, spillover, completion; then one row per observed status. |
| Migration phases | Epic key, epic summary, scope, done, remaining, spillover, completion. |
| Workload balance | Display name, open issues, remaining points, share, balance. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Python batch job instead of React 18, Express, and PostgreSQL 15 | **FR-001** and **FR-023** require one Excel file and a Jira read, with no second interface. | A web app and a database would add a product the specification excludes, and they would still have to write this same workbook. |
| No Confluence write and no sync key | **FR-023** forbids Confluence and Jira edits. Idempotency is the atomic workbook replace in **FR-019**. | Creating a page or issue on each run would change Jira or Confluence, which version 1 does not do. |
| Command calls Jira directly | There is no browser in version 1, so the "frontend never sees the token" rule has no client to protect. The token stays in the environment and out of logs. | Adding Express only to hide a token from a UI this feature does not have. |

## Phases

### Phase 0 — Open the gate

Amend `spec/constitution.md` so this read-only workbook is a permitted feature with the Python stack above. Raise the constitution version and set **Last Amended**. Copy the Planning Decisions table into `spec/specification.md` so the spec states sheet names, the closed environment list, exit codes, and the formulas that `spec/clarify.md` marked unclear.

**M0**: A reader can implement from the specification without choosing between the constitution and the feature spec.

### Phase 1 — Configuration

Implement `load_config`. Read `.env` for local development. Reject a blank required variable, a base URL with a path, an assignee list that is not exactly five non-blank ids, an unknown timezone, and an hour outside 0–23. Defaults apply only to the three optional variables. Print each failing name on stderr and exit 1. Do not open a socket in this phase.

**M1**: `tests/test_config.py` covers each rejection and the defaults. **FR-017**, **FR-018**, and **FR-020** are satisfied for settings.

### Phase 2 — Jira read

Implement `JiraClient` with HTTP Basic. Read the board, page active sprints, choose one, page that sprint's issues until `total` is exhausted, resolve `Story Points` once per run, and load the five display names. Retry network errors and HTTP 5xx up to three times. HTTP 401 and 403 exit 1 with the status and without the token. HTTP 404 on the board exits 1 and names the board id. Other HTTP 4xx exit 1 with the status. Parent epics that arrive as a key only are resolved with one extra read so **FR-011** can see the issue type.

Tests inject a fake session. No test uses the network or a real token.

**M2**: Sprint selection, pagination, retries, and error text are covered. **FR-008**, **FR-015**, **FR-021**, and **FR-024** are satisfied.

### Phase 3 — Report math

Implement `build_report` as a pure function. It splits excluded issues, computes health, status counts, phase rows, and workload, and builds the no-sprint report. Completion, share, spillover, and the overload threshold follow the Planning Decisions table.

**M3**: `tests/test_report.py` passes for spillover, one-hop epic grouping, `No phase`, zero scope, missing points, the 1.5 threshold including people on zero, several people overloaded, and the excluded count. **SC-003**, **SC-004**, and **SC-005** are satisfied without a network. This milestone delivers user stories P1, P2, and P3 at the data layer.

### Phase 4 — Workbook

Implement `excel_writer.write_workbook` for the four sheets in the workbook contract. Create the output directory when it is missing. Save to a temporary file in that directory and `os.replace` it onto `sprint-health-YYYY-MM-DD.xlsx` only after the save returns. On failure, delete the temporary file and leave any existing workbook in place. The date uses the configured timezone.

**M4**: A fixture report matches the expected cover, health, phase, and workload rows. A writer failure leaves the previous file byte-for-byte. **FR-003**, **FR-004**, **FR-005**, **FR-009**, **FR-010**, **FR-012**, **FR-016**, and **FR-019** are satisfied. **SC-007**'s sheet-row check passes.

### Phase 5 — Command

Wire `python -m sprint_health` through config, client, report, and writer. On success, print `sprint_id`, the in-scope issue count, and the output path, then return 0. On no active sprint, `sprint_id` is `none` and the count is 0. Exceptions that already exited 1 stay 1. The log omits the token, the email, account ids, and issue descriptions.

**M5**: A dry run with a fake client writes a workbook and returns 0. An authentication failure returns 1 and does not replace an existing file. **FR-022**, **SC-001**'s file creation, and **SC-006** are satisfied. **SC-007**'s repository search finds no real API token.

### Phase 6 — Live comparison and schedule

Run the command against the real board with the operator's `.env`. Compare scope, done, remaining, spillover, phase rows, and the five workload rows with the Jira sprint filtered to those five account ids. Done uses the Done status category. Fix any mapping mismatch before scheduling.

Add a cron line or a launchd template with no secret in the plist. The agent stays unloaded until the comparison matches. Weekdays and the local hour come from `REPORT_TIMEZONE` and `REPORT_HOUR_LOCAL`.

**M6**: The live comparison record matches, and the next weekday run produces the file before standup. **SC-001** and **SC-002** are satisfied. The scheduler is the last step, not the first.

## Out of this plan

Email, Slack, Teams, Confluence, PDF, a browser dashboard, a second board, editing Jira, and PostgreSQL. Those remain excluded by **FR-023**. Turning them into a product starts with a constitution amendment and a new specification.
