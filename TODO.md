# TODO

Implementation checklist for the Jira sprint health report in `project_spec.md`. Version 1 is a weekday Python command that writes `sprint-health-YYYY-MM-DD.xlsx`.

## Project setup

- [x] Add `sprint_health/` with `config`, `jira_client`, `report`, `excel_writer`, and `__main__`
- [x] Add `tests/test_report.py`
- [x] Declare Python 3.11+ and dependencies: `requests`, `openpyxl`, `python-dotenv`
- [x] Confirm `.env` stays gitignored and the API token never lands in source

## Config

- [ ] Load `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_BOARD_ID`, and `JIRA_ASSIGNEE_ACCOUNT_IDS`
- [ ] Default `REPORT_OUTPUT_DIR` to `./out`, `REPORT_TIMEZONE` to `Asia/Kolkata`, and `REPORT_HOUR_LOCAL` to `8`
- [ ] Exit 1 before calling Jira when a required variable is missing or blank, and print the variable name
- [ ] Exit 1 when the assignee list is not exactly five account ids

## Jira client

- [ ] Authenticate to Jira Cloud with HTTP Basic (email + API token)
- [ ] Read the active sprint from `GET /rest/agile/1.0/board/{boardId}/sprint?state=active`
- [ ] When several sprints are active, use the one with the latest start date and record that choice
- [ ] Page `GET /rest/agile/1.0/sprint/{sprintId}/issue` until `total` is exhausted
- [ ] Request summary, status, assignee, parent, sprint, and Story Points
- [ ] Resolve the Story Points field by name once per run; leave points blank if it is missing
- [ ] Retry network errors and HTTP 5xx up to 3 times, then exit 1
- [ ] Exit 1 on HTTP 401 or 403 without printing the token, and on HTTP 404 naming the board id

## Report

- [ ] Keep issues whose `assignee.accountId` is one of the five configured accounts
- [ ] Compute scope, done (status category `done`), remaining, spillover, and completion
- [ ] Treat zero scope as 0% completion
- [ ] Count spillover when the issue is on the active sprint and at least one earlier sprint
- [ ] Group by parent epic, follow one extra parent hop when the parent is a story, and use a `No phase` row otherwise
- [ ] Build one workload row per assignee, including people with no sprint issues
- [ ] Mark `Overloaded` when open issues exceed 1.5 times the five-person mean; otherwise `Within range`
- [ ] Count active-sprint issues assigned outside the five accounts, and keep them out of the other totals

## Excel

- [ ] Write cover, sprint health, migration phases, workload balance, and the excluded-issue count
- [ ] Name the file `sprint-health-YYYY-MM-DD.xlsx` using the run date in the configured timezone
- [ ] Create the output directory when it is missing
- [ ] Write to a temporary file and replace the day's workbook only after it is complete
- [ ] When no sprint is active, write zero totals, say so on the cover, and exit 0

## Verification and schedule

- [ ] Unit test spillover, epic grouping, zero-scope completion, and the overload threshold with fixtures and no network
- [ ] Check one recorded Jira sprint payload against the expected sheet rows
- [ ] Run once against the real board and compare with the Jira sprint report for the five assignees
- [ ] Add a weekday cron or launchd job at the configured local hour
