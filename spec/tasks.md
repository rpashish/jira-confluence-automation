# Tasks: Sprint Health Report

**Input**: `spec/plan.md`, `spec/specification.md`, `spec/constitution.md`

**Prerequisites**: `spec/plan.md` (required). Planning decisions in that file are the source for every formula below.

**Tests**: Required by **SC-007** and the plan. Write the test for a task first and confirm it fails before the implementation task that follows it.

**Organization**: Tasks follow the plan's phases and milestones. `[P]` means a different file with no dependency on an unfinished task in the same phase. `[US1]`, `[US2]`, and `[US3]` map to the three user stories.

## Format: `[ID] [P?] [Story] Description`

## Milestone map

| Milestone | Tasks | Accepted when |
| --- | --- | --- |
| M0 Gate | T001, T002 | Constitution and specification agree, and implementation no longer has to choose between them. |
| M1 Config | T003–T007 | Invalid settings exit 1 before any Jira call. |
| M2 Jira read | T008, T009 | Sprint choice, pagination, retries, and token-free errors pass with a fake session. |
| M3 Report math | T010, T011, T015–T018 | P1, P2, and P3 pass from fixture issues with no network. |
| M4 Workbook | T012, T013, T016, T018, T021 | The four sheets match the fixture, and a failed write leaves the previous file. |
| M5 Command | T014, T019, T020 | The command returns 0 with the log line, or 1 without replacing a finished workbook. |
| M6 Live schedule | T022, T023, T024 | The live five-account comparison matches, and only then is the weekday scheduler enabled. |

---

## Phase 0: Open the gate (M0)

**Purpose**: Remove the contradiction between `spec/constitution.md` 1.0.0 and the feature spec before any code is accepted.

- [ ] T001 Amend `spec/constitution.md` so a read-only sprint workbook is a permitted feature on Python 3.11 with `requests` and `openpyxl`. Raise the version above 1.0.0 and set **Last Amended** to the amendment date.

  **Acceptance criteria**
  - The constitution names this batch command as allowed: it reads Jira Cloud and writes one Excel file.
  - Confluence writes, a Vite UI, Express, and PostgreSQL are not required for this feature.
  - The version line is greater than 1.0.0 and **Last Amended** is the amendment date.

- [ ] T002 [P] Copy the Planning Decisions table from `spec/plan.md` into `spec/specification.md`: four sheet names, the environment-variable list, exit codes, and the formulas for completion, share, spillover, days remaining, story points, and overload.

  **Acceptance criteria**
  - `spec/specification.md` names sheets Cover, Sprint health, Migration phases, and Workload balance.
  - It lists `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_BOARD_ID`, `JIRA_ASSIGNEE_ACCOUNT_IDS`, `REPORT_OUTPUT_DIR`, `REPORT_TIMEZONE`, and `REPORT_HOUR_LOCAL` with the defaults from the plan.
  - Exit 0 and exit 1 match the plan's process signal. An implementer can build without reading `spec/clarify.md`.

**Checkpoint M0**: T001 and T002 are both done.

---

## Phase 1: Setup

**Purpose**: Package metadata and secret hygiene. Depends on M0.

- [ ] T003 Declare the `sprint_health` package in `pyproject.toml` with Python `>=3.11`, dependencies `requests`, `openpyxl`, and `python-dotenv`, and a `pytest` dev extra.

  **Acceptance criteria**
  - `pip install -e ".[dev]"` installs those packages.
  - `python -m sprint_health` is importable from a clean environment created from `pyproject.toml`.
  - `pytest` collects `tests/` without a network connection.

- [ ] T004 [P] Add `.env.example` with the eight variable names and empty values. Ignore `.env`, `.env.*`, and `out/` in `.gitignore`, and do not ignore `.env.example`.

  **Acceptance criteria**
  - `.env.example` contains every name from T002 and no token, email, or account id.
  - A generated workbook under `out/` and a filled `.env` are untracked.

- [ ] T005 [P] Add the package files from `spec/plan.md`: `sprint_health/__init__.py`, `sprint_health/__main__.py`, `sprint_health/config.py`, `sprint_health/jira_client.py`, `sprint_health/report.py`, and `sprint_health/excel_writer.py`. Each docstring states that file's responsibility from the plan.

  **Acceptance criteria**
  - Those six files exist.
  - Each docstring names one responsibility: wiring, configuration, Jira reads, report math, or workbook writing.

---

## Phase 2: Configuration (M1)

**Purpose**: Blocking prerequisite. No Jira call exists in this phase.

- [ ] T006 [P] Write `tests/test_config.py` for `sprint_health.config.load_config`. Cover each missing or blank required variable, a base URL that contains a path, an assignee list that is not exactly five non-blank ids, an unknown timezone, an hour outside 0–23, and the three defaults.

  **Acceptance criteria**
  - The tests fail before T007 and pass after it.
  - No test opens a socket or reads a real `.env` secret.
  - Expected failures name `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_BOARD_ID`, `JIRA_ASSIGNEE_ACCOUNT_IDS`, `REPORT_TIMEZONE`, or `REPORT_HOUR_LOCAL`.

- [ ] T007 Implement `load_config` in `sprint_health/config.py`. Load a local `.env` for development. Apply defaults only for `REPORT_OUTPUT_DIR` (`./out`), `REPORT_TIMEZONE` (`Asia/Kolkata`), and `REPORT_HOUR_LOCAL` (`8`).

  **Acceptance criteria**
  - Each invalid setting prints that variable's name on stderr and exits 1 before any Jira call (**FR-020**).
  - The assignee value is a comma-separated list of exactly five non-blank ids.
  - `REPORT_HOUR_LOCAL` accepts only integers 0 through 23. An unknown timezone exits 1.
  - Valid input returns the site, email, token, board id, five ids, output directory, timezone, and hour (**FR-017**, **FR-018**).

**Checkpoint M1**: `pytest tests/test_config.py` passes with no network.

---

## Phase 3: Jira read (M2)

**Purpose**: Blocking prerequisite for every user story. Tests inject a fake session.

- [ ] T008 Write `tests/test_jira_client.py` against a fake session for `sprint_health/jira_client.py`. Cover latest-start selection, an undated sprint losing to a dated one, an equal-timestamp tie keeping the first sprint returned, pagination until `total` is exhausted, one lookup of the field named `Story Points`, HTTP 401 and 403, board HTTP 404, three retries then failure for network errors and HTTP 5xx, a user HTTP 404, and one extra read when a parent arrives as a key only.

  **Acceptance criteria**
  - The tests fail before T009 and pass after it.
  - The fake token value never appears in captured stderr.
  - Board 404 output includes the configured board id.
  - Retry waits asserted through the injected sleeper are 0.5s, 1s, and 2s.

- [ ] T009 Implement `JiraClient` in `sprint_health/jira_client.py` with HTTP Basic (`JIRA_EMAIL`, `JIRA_API_TOKEN`). Provide the board (`location.projectKey` and name), the chosen active sprint, paged sprint issues, the Story Points field id, board status order, and display names from `GET /rest/api/3/user?accountId=`.

  **Acceptance criteria**
  - Several active sprints select the latest `startDate`. A sprint with no parseable start loses. Equal starts keep the first sprint returned. The selection note names the sprints considered and the sprint used (**FR-008**).
  - Sprint issues follow pagination until `total` is exhausted.
  - The first field named `Story Points` is resolved once per run. A missing field returns no id (**FR-015**).
  - HTTP 401 and 403 exit 1, print the status, and omit the token. Board HTTP 404 exits 1 and names the board id. Other HTTP 4xx exit 1 with the status. Network errors and HTTP 5xx retry three times, then exit 1 (**FR-021**).
  - A missing display name or a user HTTP 404 leaves that account id for the report to show. User HTTP 5xx uses the same retry rule (**FR-024**).
  - A parent that contains only a key is fetched once so the report can see its issue type (**FR-011**).

**Checkpoint M2**: `pytest tests/test_jira_client.py` passes with no network.

---

## Phase 4: User Story 1 — Weekday sprint health workbook (P1) (M3, M4, M5)

**Goal**: Leadership can open one workbook and read scope, done, remaining, spillover, and completion for the five accounts.

**Independent test**: Run once against a fixture sprint and open `sprint-health-<date>.xlsx`. Scope, done, and remaining match a filter of that sprint to the five account ids. Done uses the Done status category.

- [ ] T010 [US1] Add health cases to `tests/test_report.py` for `sprint_health.report.build_report`: five-account scope, status category `done`, remaining, completion 0% at scope 0, spillover by earlier start, spillover by `closed` or `completed` when a start date is missing, story-point sums that ignore blanks and keep a numeric 0, status rows in board order, and unassigned issues counted as excluded.

  **Acceptance criteria**
  - The tests fail before T011 and pass after it.
  - Fixtures use fake account ids and no network.
  - A status whose category is not `done` stays in remaining even when its name looks finished.

- [ ] T011 [US1] Implement the in-scope split, health totals, spillover, story points, status counts, and the no-sprint health result in `sprint_health/report.py`.

  **Acceptance criteria**
  - Scope, done, remaining, spillover, and completion follow the plan. Completion is `done / scope` as a percentage of issues, and 0% when scope is 0 (**FR-005**, **FR-006**, **FR-007**).
  - Points sum numeric values, including 0. The total is blank only when every contributing issue has no usable points.
  - Unassigned issues and other assignees increment the excluded count and stay out of scope (**FR-002**, **FR-016**).
  - Days remaining are calendar days in `REPORT_TIMEZONE`, blank when the end date is missing, and 0 when the end date is in the past.
  - No active sprint yields zero counts and blank point totals (**FR-009**).

- [ ] T012 [P] [US1] Add `tests/test_excel_writer.py` for the Cover and Sprint health sheets, the output filename, a missing output directory, and a failed save.

  **Acceptance criteria**
  - The tests fail before T013 and pass after it.
  - The filename asserted is `sprint-health-YYYY-MM-DD.xlsx` for the configured timezone (**FR-003**).
  - A failed save leaves the previous workbook byte-for-byte unchanged (**FR-019**, **SC-006**).

- [ ] T013 [US1] Implement Cover and Sprint health in `sprint_health/excel_writer.py`, including atomic replace. Create the output directory when it is missing. Write the excluded-count line from the report value.

  **Acceptance criteria**
  - Cover shows the title `Sprint health — database migration`, site, project key, board name, sprint name, state, start, end, days remaining, selection note, generated-at `YYYY-MM-DD HH:MM`, timezone, the five names in configured order, and the excluded count (**FR-004**).
  - No active sprint writes the sprint name `No active sprint` and blank dates.
  - Sprint health shows scope, scope points, done, remaining, spillover, completion, then one row per observed status. Zero-count statuses are omitted.
  - The writer saves a temporary file in the output directory and calls `os.replace` only after the save returns. On failure it deletes the temporary file.

- [ ] T014 [US1] Wire `sprint_health/__main__.py` so `python -m sprint_health` loads config, reads Jira, builds the report, writes the workbook, prints the log line, and returns 0.

  **Acceptance criteria**
  - A fake client that returns an active sprint produces a workbook and exit 0.
  - The log line is `sprint_id=<id> issues=<in-scope count> output=<path>` (**FR-022**).
  - No active sprint still returns 0 and logs `sprint_id=none issues=0 output=<path>` (**FR-009**).
  - The log omits the token and issue descriptions.

**Checkpoint US1**: Cover and Sprint health are independently testable. M3 is not complete until Phase 6. M5 is not complete until Phase 7.

---

## Phase 5: User Story 2 — Progress by migration phase (P2)

**Goal**: The same in-scope issues appear as one row per parent epic, with `No phase` last.

**Independent test**: Phase rows match the parent epics of the five-account issues. Every issue with no resolvable epic is on the final `No phase` row.

- [ ] T015 [US2] Add phase cases to `tests/test_report.py`: a parent epic, one hop from a story to an epic, `No phase` for a missing epic and for an epic that is itself on the sprint, epic-key order, and a subtask counted as its own issue.

  **Acceptance criteria**
  - The tests fail before T016 and pass after it.
  - `No phase` is the last row when any unresolved issue exists, and it is absent when every issue resolves to an epic.

- [ ] T016 [US2] Implement phase grouping in `sprint_health/report.py` and the Migration phases sheet in `sprint_health/excel_writer.py`.

  **Acceptance criteria**
  - Columns are epic key, epic summary, scope, done, remaining, spillover, and completion (**FR-010**).
  - Issue type `Epic` matches ignoring case. One parent hop is followed. Anything else is `No phase` (**FR-011**).
  - Rows sort by epic key ascending, with `No phase` last.
  - A no-sprint workbook writes the header row only.

**Checkpoint US2**: Phase rows can be checked from fixtures without opening Jira (**SC-003**).

---

## Phase 6: User Story 3 — Workload balance (P3) (M3)

**Goal**: One row per configured person, including people with no issues, and an `Overloaded` flag from the 1.5 rule.

**Independent test**: A fixture where one person's open issues exceed 1.5 times the five-person mean marks that person `Overloaded`. People on zero remain in the list.

- [ ] T017 [US3] Add workload cases to `tests/test_report.py`: all five people, a person with no issues, overload above 1.5 times the mean including zeros, two people overloaded at once, share 0% when nobody has open work, remaining points blank only when every open issue lacks points, configured list order, and excluded issues absent from the totals.

  **Acceptance criteria**
  - The tests fail before T018 and pass after it.
  - The mean is not rounded before the comparison. A count equal to 1.5 times the mean is `Within range`.

- [ ] T018 [US3] Implement workload rows in `sprint_health/report.py` and the Workload balance sheet in `sprint_health/excel_writer.py`. Show the excluded count already produced in T011 on the Cover sheet.

  **Acceptance criteria**
  - Columns are display name, open issues, remaining points, share, and balance (**FR-012**, **FR-013**, **FR-014**).
  - Open issues are in-scope issues whose status category is not `done`. Share is that count divided by all five people's open issues, and 0% when the total is 0.
  - `Overloaded` means the open-issue count is greater than 1.5 times the mean of the five counts. Several people may be overloaded.
  - Issues outside the five accounts appear only as the excluded count (**FR-016**, **SC-004**, **SC-005**).
  - No active sprint lists the five people with zero open issues, blank points, share 0%, and `Within range`.

**Checkpoint M3**: `pytest tests/test_report.py` passes with no network. P1, P2, and P3 are all proven at the data layer.

---

## Phase 7: Command failure and secrets (M5)

**Purpose**: A failed run must not destroy the previous workbook, and the repository must not contain the real secret.

- [ ] T019 Add a command test that an HTTP 401 from the fake client exits 1 and leaves an existing `sprint-health-YYYY-MM-DD.xlsx` byte-for-byte unchanged. Assert stderr contains the status and does not contain the fixture token.

  **Acceptance criteria**
  - The test fails before the `__main__.py` error path is complete, then passes.
  - The same assertion holds for HTTP 403 (**FR-021**, **SC-006**).
  - The log and stderr omit the token, the email, account ids, and issue descriptions (**FR-022**).

- [ ] T020 [P] Add a test that scans the repository for the fixture's stand-in only inside tests, and fails if `.env.example` or `sprint_health/` contains a value assigned to `JIRA_API_TOKEN`.

  **Acceptance criteria**
  - `pytest` passes when `.env.example` values are empty.
  - The test does not require the real token and does not print one (**FR-017**, **SC-007**).

**Checkpoint M5**: `python -m sprint_health` returns 0 with the log line on a fake success, and returns 1 on auth failure without replacing a finished file.

---

## Phase 8: Live comparison and schedule (M4 sheet fixture, M6)

**Purpose**: Prove the workbook against a recorded payload, then against the live board, and only then enable the weekday run.

- [ ] T021 Add one recorded sprint payload under `tests/fixtures/` with fake account ids and secrets removed. Assert Cover, Sprint health, Migration phases, and Workload balance rows in `tests/test_excel_writer.py`.

  **Acceptance criteria**
  - The fixture file contains no real email, token, or production account id.
  - Expected rows cover scope, done, remaining, spillover, one epic, `No phase`, all five people, and the excluded count (**SC-007**).
  - `pytest` passes with no network. This closes M4 together with T012 and T013.

- [ ] T022 Run `python -m sprint_health` against the live board using the operator's `.env`. Compare scope, done, remaining, spillover, phase rows, and the five workload rows with the Jira sprint filtered to those five account ids. Record the comparison in `spec/live-check.md` with sprint id, date, and match or mismatch. Do not copy issue descriptions or the token into that file.

  **Acceptance criteria**
  - Done in both the file and the manual filter uses the Done status category (**SC-002**).
  - A mismatch is fixed in `sprint_health/` and the comparison is repeated before T024.
  - The real token and the real account ids are absent from the committed record.

- [ ] T023 [P] Document the weekday schedule in the project README: Monday–Friday at `REPORT_HOUR_LOCAL` in `REPORT_TIMEZONE`, command `python -m sprint_health`, and the rule that a manual run uses the same command.

  **Acceptance criteria**
  - The README states the default 08:00 `Asia/Kolkata` slot and that the project manager takes the file from the output directory.
  - The documented command does not contain a secret.

- [ ] T024 Add a launchd plist template or a cron example under `sprint_health/scheduler/` with the working directory and the command, and with no email, token, or account id. Leave the agent unloaded.

  **Acceptance criteria**
  - The template uses `REPORT_HOUR_LOCAL` and weekdays Monday–Friday.
  - Searching the template finds no `JIRA_API_TOKEN` value.
  - The scheduler is enabled only after T022 matches. Until then the agent is not bootstrapped (**FR-018**, **SC-001**).

**Checkpoint M6**: The live comparison matches, and the next weekday run is the first scheduled run.

---

## Dependencies

- T001 and T002 block every code task.
- T006 before T007. T008 before T009. T010 before T011. T012 before T013. T015 before T016. T017 before T018. T019 before the M5 checkpoint.
- T007 and T009 block T014.
- T011 blocks T013, T016, and T018 because those sheets render `build_report` output.
- T013 blocks T014.
- T016 and T018 both edit `sprint_health/report.py` and `sprint_health/excel_writer.py`, so they stay sequential.
- T021 depends on T013, T016, and T018.
- T024 depends on a matching T022. T023 may proceed once T014 exists.

## Parallel opportunities

- T001 and T002 edit different files.
- T004 and T005 can proceed with T003.
- T006 and T008 can be written at the same time.
- T012 can be written while T010 is being written.
- T020 and T023 touch different files from the command test.

User stories stay in order P1, then P2, then P3. P2 and P3 share `report.py` and `excel_writer.py`, so they are not split across people at the same time.

## MVP

1. Finish Phase 0 through Phase 4 (T001–T014).
2. Stop and open the fixture workbook. Cover and Sprint health must satisfy the User Story 1 independent test.
3. Add Phase 5 and Phase 6 before calling the report leadership-ready.
4. Enable the scheduler only in T024, after T022 matches.
