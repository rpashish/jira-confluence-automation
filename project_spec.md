# Jira Sprint Health Report — Technical Specification

**Version:** 1.0
**Status:** Ready for implementation
**Audience of this document:** The person building the automation

## 1. Purpose

Produce a weekday-morning sprint health report for the steering committee of a database migration. The report covers the current sprint on one Jira board, limited to the five people on the migration team. It shows committed scope, work done, work remaining, spillover, progress by migration phase, and whether any of the five people is overloaded.

The project manager runs this for leadership. Version 1 is a scheduled Python command that writes an Excel workbook. That is the smallest build that still delivers a leadership-ready file every weekday morning.

## 2. Users and decisions

| User | Decision the report supports |
| --- | --- |
| Steering committee / leadership | Is this sprint on track, which migration phase is moving, and is the five-person team unbalanced? |

The five team members are the subjects of the workload section. They are not a separate audience in version 1.

## 3. Version 1 scope

### In scope

- Jira Cloud, one site, one project, one board.
- Issues on the active sprint assigned to a configured list of five accounts.
- Sprint health: scope, done, remaining, spillover.
- Rollup by parent epic. Each epic represents one migration phase or workstream.
- Workload balance across the five assignees.
- Excel workbook (`.xlsx`) written to a configured folder.
- Run every weekday morning, before standup.
- Authentication with a Jira Cloud API token supplied by environment variables.

### Out of scope

- Daily standup digests, weekly narrative status, blocker lists, and per-person performance rankings.
- Email, Slack, Teams, Confluence, PDF, and a web dashboard.
- More than one project or board.
- Issues assigned to anyone outside the five accounts, except a single excluded-count so leadership can see that filter.
- Descriptions, comments, and rankings of people against each other.
- Historical sprints other than the spillover signal defined below.
- Editing Jira issues.

## 4. Requirements from the interview

| Topic | Decision |
| --- | --- |
| Who uses the report | Leadership or a steering committee |
| Report | Sprint or board health |
| Delivery | Excel file |
| When it runs | Each weekday morning |
| Jira and sign-in | Jira Cloud, API token |
| Data in scope | One project, one board, five assignees |
| How migration progress is stored | Epics or parent issues, one per phase or workstream |
| What to show about the five people | Workload balance |
| Build shape | Simplest option that still produces the report |
| Time window | Current sprint only |

Excel is the version 1 file because it is the simpler of the accepted formats (PDF or Excel) and holds the sprint and workload tables without a document renderer.

## 5. Report contents

One workbook per run. File name: `sprint-health-YYYY-MM-DD.xlsx`, using the run date in the configured timezone.

### 5.1 Cover

- Report title: Sprint health — database migration
- Jira site, project key, board name
- Sprint name, state, start date, end date, days remaining
- Generated-at timestamp and timezone
- The five assignees the report includes

### 5.2 Sprint health

Counts use issues on the active sprint assigned to the five accounts.

| Metric | Definition |
| --- | --- |
| Scope | Issues on the active sprint. Also show story points when the Story Points field is populated. |
| Done | Issues whose status category is Done. |
| Remaining | Scope minus Done. |
| Spillover | Issues on the active sprint that also belong to at least one earlier sprint. |
| Completion | Done divided by Scope, as a percentage. Zero scope yields 0%. |

Also list issue counts by status, in board column order when Jira provides it.

### 5.3 Migration phases

Group the same sprint issues by parent epic.

- One row per epic that parents at least one in-scope sprint issue.
- Columns: epic key, epic summary (the phase or workstream name), scope, done, remaining, spillover, completion.
- Issues with no parent epic go in a final row named `No phase`.

### 5.4 Workload balance

One row per configured assignee, including people with no sprint issues.

| Column | Definition |
| --- | --- |
| Assignee | Display name |
| Open issues | Remaining issues assigned to that person |
| Remaining points | Sum of Story Points on those open issues. Blank when the issue has no points. |
| Share of open work | That person's open issues divided by all open issues in the report |
| Balance | `Overloaded` or `Within range` |

`Overloaded` means the person's open-issue count is greater than 1.5 times the mean open-issue count of the five people. The mean includes people on zero. When nobody has open work, every person is `Within range`.

Story points are shown so leadership can see size. The overload flag uses issue count so a missing points field cannot hide an unbalanced board.

### 5.5 Excluded issues

One line: the number of active-sprint issues on the board whose assignee is not one of the five. Those issues are not included in scope, phase, or workload totals.

## 6. Jira data rules

- Host: Jira Cloud only. Base URL looks like `https://<site>.atlassian.net`.
- Auth: HTTP Basic, username = Atlassian account email, password = API token.
- Board: Agile REST API, `GET /rest/agile/1.0/board/{boardId}/sprint?state=active`.
- If several sprints are active, use the one with the latest start date and record that choice on the cover.
- If no sprint is active, still write the workbook. Health totals are zero and the cover states that there is no active sprint.
- Issues: `GET /rest/agile/1.0/sprint/{sprintId}/issue` with pagination until `total` is exhausted. Request fields: summary, status, assignee, parent, sprint (the sprint custom field), and Story Points.
- Keep an issue when `assignee.accountId` is in the configured five.
- Parent epic: use `parent` when `parent.fields.issuetype` is Epic. If the parent is a story under an epic, follow one more parent hop. If the epic is still unresolved, count the issue under `No phase`.
- Spillover: the sprint field lists more than one sprint, and one of them is the active sprint.
- Done: status category key `done`.
- Story Points field id differs by site. Resolve the field whose name is `Story Points` once per run. If it does not exist, leave points blank and still compute issue counts.

## 7. System design

```
weekday 08:00 local
        |
        v
  scheduler (cron or launchd)
        |
        v
  Python command: python -m sprint_health
        |
        +--> read environment / .env
        +--> Jira Cloud REST (board, active sprint, issues, fields)
        +--> build the four sections in memory
        +--> write ./out/sprint-health-YYYY-MM-DD.xlsx
```

### Modules

| Module | Responsibility |
| --- | --- |
| `config` | Load and validate environment variables |
| `jira_client` | Authenticated GET, pagination, field lookup |
| `report` | Turn issues into sprint, phase, and workload rows |
| `excel_writer` | Write the workbook |
| `__main__` | Wire the steps and return a non-zero exit code on failure |

No web server, database, or queue.

### Dependencies

- Python 3.11 or newer
- `requests` for Jira
- `openpyxl` for Excel
- `python-dotenv` to load a local `.env` during development

## 8. Configuration

Secrets and site-specific ids stay in the environment. `.env` is already gitignored. The workbook output directory is gitignored when it contains generated files; do not commit reports.

| Variable | Required | Meaning |
| --- | --- | --- |
| `JIRA_BASE_URL` | Yes | Cloud site origin, no trailing path |
| `JIRA_EMAIL` | Yes | Account email for the API token |
| `JIRA_API_TOKEN` | Yes | API token for that account |
| `JIRA_BOARD_ID` | Yes | Numeric board id |
| `JIRA_ASSIGNEE_ACCOUNT_IDS` | Yes | Comma-separated list of exactly five account ids |
| `REPORT_OUTPUT_DIR` | No | Default `./out` |
| `REPORT_TIMEZONE` | No | Default `Asia/Kolkata` |
| `REPORT_HOUR_LOCAL` | No | Default `8`. The scheduler uses this hour on weekdays. |

The token needs permission to browse the project and read the board. The spec does not store the token, the email, or the account ids in source.

## 9. Schedule

- Cadence: Monday through Friday.
- Default time: 08:00 `Asia/Kolkata`, so the file exists before standup. Change `REPORT_TIMEZONE` and `REPORT_HOUR_LOCAL` if standup is at another time.
- Mechanism: one cron entry or a launchd agent on the machine that holds the environment variables.
- The command is safe to run again the same day. A second run overwrites that day's workbook.
- A manual run uses the same command. Version 1 does not add a second interface.

Example weekday cron, hour taken from the default:

```cron
0 8 * * 1-5 cd /path/to/project && .venv/bin/python -m sprint_health
```

## 10. Errors

| Condition | Behavior |
| --- | --- |
| Missing or blank required variable | Exit 1 before calling Jira. Print the variable name. |
| Assignee list length is not five | Exit 1. |
| Jira HTTP 401 or 403 | Exit 1. Print the status. Do not print the token. |
| Jira HTTP 404 for the board | Exit 1. Name the board id. |
| Network or HTTP 5xx | Retry up to 3 times with a short backoff, then exit 1. |
| No active sprint | Write the workbook with zero totals and exit 0. |
| Output directory missing | Create it, then write the file. |

Logs go to stdout and stderr. They include sprint id, issue count, and output path. They omit the API token and issue descriptions.

## 11. Acceptance criteria

1. With valid Cloud credentials, a weekday run creates `sprint-health-<date>.xlsx` in the output directory.
2. Scope, done, and remaining match a manual filter of the active sprint limited to the five account ids. Done uses the Done status category.
3. An issue that sits on the active sprint and an earlier sprint appears in the spillover count.
4. Phase rows match parent epics. Issues without an epic appear as `No phase`.
5. The workload sheet lists all five people. A person whose open issues exceed 1.5 times the five-person mean is marked `Overloaded`.
6. Issues assigned to other accounts are excluded from those totals and appear only as the excluded count.
7. Secrets are read from the environment. A search of the repo does not find the API token.
8. An authentication failure exits non-zero and does not write a partial workbook over a previous good file. Write to a temporary file in the output directory and replace the day's file only after the workbook is complete.

## 12. Verification

- Unit tests for spillover detection, epic grouping, completion with zero scope, and the overload threshold, using fixture issues and no network.
- One recorded fixture of a Jira sprint payload checked against expected sheet rows.
- A manual run against the real board, compared with the Jira sprint report for the five assignees, before the weekday schedule is turned on.

## 13. Implementation notes

Suggested layout after implementation begins:

```
sprint_health/
  __init__.py
  __main__.py
  config.py
  jira_client.py
  report.py
  excel_writer.py
tests/
  test_report.py
```

This specification does not include that code. Implementation starts from the acceptance criteria in section 11.
