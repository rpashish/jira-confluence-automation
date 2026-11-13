# QA Report: Sprint Health

**Application:** Sprint health web client and API  
**Date:** 2026-11-13  
**Environment:** Local. Frontend `http://127.0.0.1:5173/`, API `http://127.0.0.1:3001`, Postgres `localhost:5432`.  
**Browser:** Google Chrome 157.0.8103.51, plus a Chromium session for navigation and full-page capture.

## Pages visited

| Page | URL | Result |
|---|---|---|
| Starting page | `http://127.0.0.1:5173/` | Loaded. Live report did not render. The page showed the missing Jira configuration panel. |
| Recorded sample | `http://127.0.0.1:5173/?source=fixture` | Loaded. Cover, sprint health, migration phases, and workload balance all rendered. |

The client has no other routes. Both screens share the title **Sprint health — database migration**.

## Elements tested

### Starting page

- Heading **Sprint health** and the weekday-report introduction.
- Heading **Jira configuration is missing**.
- Instruction to set environment variables and reload.
- List items: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_BOARD_ID`, `JIRA_ASSIGNEE_ACCOUNT_IDS`.
- Link **Open the recorded sample** (`/?source=fixture`). Clicked. Navigation succeeded.

No form fields, buttons, or submit control are present.

### Recorded sample

- Banner: sample data from the recorded sprint fixture, not the live board.
- Cover fields: Jira site `https://example.atlassian.net`, project key `MIG`, board Migration board, sprint Sprint 12, state active, start `2026-11-02`, end `2026-11-13`, 1 day remaining, generated at `2026-11-12 08:00`, timezone `Asia/Kolkata`.
- Assignees: Ada, Ben, Cy, Dee, Ed.
- Excluded-issue note: 2 issues outside the five accounts.
- Metric cards: Scope 5 (11 points), Done 2 (7 points), Remaining 3 (4 points), Spillover 1, Completion 40%.
- Issues-by-status table: To Do 1, In Progress 2, Done 2.
- Migration phases table: MIG-100 Schema cutover, MIG-200 Data move, and No phase.
- Workload table: Ada, Ben, and Dee Overloaded; Cy and Ed Within range. Ben's remaining points are blank.

No links, forms, or buttons are present on this page.

## User flow

1. Open the starting page.
2. Look for a required form and a submit button. Neither exists.
3. Use the only control, **Open the recorded sample**.
4. Confirm the sample report renders the cover, health metrics, status counts, phase rows, and workload rows.

The sample path completed. The live path stops on the starting page.

## Bugs found

| ID | Severity | What happened | Expected |
|---|---|---|---|
| QA-1 | Blocker for the live report | `GET /api/report` returns HTTP 400 `missing_config`. The starting page lists the five unset variables and does not show sprint data. | A configured environment would return the live sprint report. The missing-config panel itself matches the current client. |

No layout break, failed sample request, or broken link was observed. The sample request `GET /api/report?source=fixture` succeeded, and the page content matched that response.

## Fixes applied

None. This session did not change application code. Docker Compose (`hello-genai-db-1` healthy, `hello-genai-api-1` up), the local API on port 3001, and the Vite client on port 5173 were already running and were left running.

## Current status

The recorded-sample flow is working. The live Jira report is blocked until `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_BOARD_ID`, and `JIRA_ASSIGNEE_ACCOUNT_IDS` are set and the starting page is reloaded.
