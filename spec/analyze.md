# Analysis: Sprint Health Tasks

**Reviewed:** `spec/tasks.md` (T001–T024), `spec/plan.md` (2026-11-13), `spec/specification.md` (Draft), `spec/constitution.md` 1.0.0

**Date:** 2026-11-13

**Verdict:** The task list is implementable after M0, and the user-story split is sound. Do not treat M0 as done from T002's acceptance bullets alone: they check a subset of the planning decisions. Do not treat "tests fail first" as true for T006–T018: `sprint_health/`, `pyproject.toml`, and `tests/test_config.py`, `tests/test_jira_client.py`, and `tests/test_report.py` are already in the tree. The highest delivery risk is T022, which is manual, credentialed, and the gate for the scheduler.

Complexity: **Low** is one file and a closed rule. **Medium** is a multi-case test or two files. **High** is live Jira, a scheduler, or a client with many failure paths.

## Task assessment

| Task | Complexity | Dependencies | Risks |
| --- | --- | --- | --- |
| T001 | Medium | None. Parallel with T002. | An amendment that only names Python can leave Principles II, III, and V in force, so the gate still fails. Dropping secret and read-only rules would weaken later tasks. |
| T002 | Medium | `spec/plan.md` Planning Decisions. Parallel with T001. Blocks every later task. | Acceptance checks sheet names, eight variables, and exit codes. It does not check unassigned issues, sprint tie-break, the no-sprint workbook, retry waits, or the error matrix. M0 can pass while those rules stay only in the plan. The spec can remain Draft. |
| T003 | Low | M0. | Acceptance says `python -m sprint_health` is importable. That module is created in T005, which is marked parallel. Import fails until T005 lands. Running the module is not the same as importing it, and a run may call Jira. |
| T004 | Low | T002 for the eight names. Parallel with T003 after M0. | `.gitignore` rule `.env.*` also matches `.env.example`. The task requires both that ignore pattern and a tracked example file. Those bullets conflict unless the ignore file adds `!.env.example`. |
| T005 | Low | M0. Parallel with T003 and T004. | The six modules already exist and already contain behavior. "Add the files" does not say what to do with that code. Later "failing test" tasks will pass immediately. |
| T006 | Medium | T005. May be written beside T008. | `tests/test_config.py` already exists. A test-first failure is unlikely. Easy to miss one of: path on the base URL, blank assignee segments, timezone, hour. |
| T007 | Medium | T006. Blocks T014. | Exiting from a library function makes tests depend on `SystemExit`. A trailing slash and a URL with a path need one rule. Loading `.env` must not override variables already set in the test environment. |
| T008 | High | T005. Beside T006. | Pagination (`startAt`, `total`, `isLast`) is easy to fake in a way production will not match. Parent-key fetch has no URL in the task. Retry timing depends on an injected sleeper. Existing client tests may already cover this, so the test will not fail first. |
| T009 | High | T008. Blocks T014. | Some boards omit `location.projectKey`. A request exception can include the URL with the email and token. HTTP 429 is a 4xx and will not retry. `SystemExit` inside the client makes the command test in T019 assert an exit that happened before the writer ran. |
| T010 | Medium | T005. Beside T012. | Spillover fixtures must include start dates, or the `closed` fallback hides a bad comparison. Existing `tests/test_report.py` may already pass these cases. |
| T011 | High | T010. Blocks T013, T014, T016, and T018. The dependency list omits T014. | Days remaining across timezones, and a completion value stored as 0–100 and then formatted again as a percent, will show 10000% in Excel. Subtasks count twice by decision; that is untested until T015. |
| T012 | Medium | T005 for the module. Marked [P] with T010. Blocks T013. | Openpyxl rewrites zip metadata, so a byte compare is stable only when the failed path does not save. The report dict shape is still moving in T011. |
| T013 | Medium | T011, T012. Blocks T014 and T021. | US1 delivery has two sheets. The plan's workbook contract has four. A run at T014 can look finished and still fail T021. Midnight in `REPORT_TIMEZONE` changes the filename. |
| T014 | Medium | T007, T009, T011, T013. The written dependency list names T007, T009, and T013 only. | No-sprint must not request sprint issues. A client that calls `SystemExit` skips the success log. The MVP checkpoint expects a workbook before phase and workload sheets exist. |
| T015 | Medium | T011. Same file as T010, so not parallel with it. | "Epic on the sprint is `No phase`" is a plan decision the current spec does not state until T002. Tests will encode that rule before the spec does if M0 was accepted on the narrow T002 bullets. |
| T016 | Medium | T015. Shares `report.py` and `excel_writer.py` with T018. | A header-only phase sheet on no-sprint can disagree with a sheet T013 already created. Column order must match T021. |
| T017 | Medium | T011. Same test file as T015. | The 1.5 boundary needs a hand-checked fixture. Equal-to-threshold must be `Within range`. Share as a ratio versus a percent will fail the sheet test later. |
| T018 | Medium | T017, and T016 because of the shared files. | T013 and T018 both own the excluded-count cell. One of them can drop it. No-sprint must still list five people. |
| T019 | Medium | T014 and T013. File path is not named. | If the client exits on 401 before `write_workbook`, the "file unchanged" assertion passes without exercising replace. Plan M5 also requires board 404 at the command. This task asserts 401 and 403 only. |
| T020 | Medium | T004. Marked [P]. It also assumes a fixture stand-in that T021 creates later. | The scan does not cover the whole tree, and it cannot see the real token without embedding it. **FR-017** also forbids the real email and the real account ids. **SC-007** can pass this task and still fail a human search. |
| T021 | Medium | T013, T016, T018. | `tests/fixtures/sprint_payload.json` is already present. The task does not say whether to replace it. A synthetic payload will not catch a mapping bug that only the live board has. Sheet assertions are brittle if column labels drift. |
| T022 | High | A working command (T014) and, in practice, T021. Blocks T024. | Needs the real `.env`. The notes file can leak the token or account ids. Jira's UI filter and the API can disagree on subtasks and unassigned issues. There is no numeric tolerance and no separate task for the fix loop. This cannot run in CI. |
| T023 | Low | T014, per the dependency list. Parallel with T020. | There is no project README. The only README in the tree is `work/module03-task/README.md`. "The project README" has no path. |
| T024 | Medium | A matching T022. | launchd and cron will not expand `REPORT_HOUR_LOCAL` by themselves. A template that names the variable will not fire at 08:00. Enabling the agent is not the same as observing the next weekday file, so **SC-001** stays open after this task. The plist must stay free of secrets and of a machine-specific secret path. |

## Contradictions

1. **Constitution versus feature spec, still open.** `spec/constitution.md` 1.0.0 requires React 18, Vite, Express, PostgreSQL 15, and Jira or Confluence writes. `spec/specification.md` **FR-023** requires a read-only Excel command. The plan records this gate as failed. T001 is the fix, and it is not done. Any code accepted before T001 violates the constitution that is in force today.

2. **Phase numbers.** The plan's Phase 1 is configuration (M1). The task list's Phase 1 is setup, and configuration is Phase 2. Plan Phase 3 (all report math) is task Phases 4–6. Plan Phase 6 (live schedule) is task Phase 8. Milestone names match. Phase numbers do not. A reference to "Phase 4" is the workbook in the plan and User Story 1 in the tasks.

3. **M1's task range versus its sentence.** The milestone map assigns T003–T007 to M1. The acceptance sentence is only "invalid settings exit 1". T003–T005 do not prove that sentence.

4. **T003 versus T005.** T003 is done only when the package imports. T005 creates the package and is allowed to run in parallel.

5. **T004 versus itself.** Ignore `.env.*` and keep `.env.example` tracked. The first pattern ignores the second file.

6. **Tests fail first versus the current tree.** T006, T008, T010, T015, and T017 require a red test before implementation. The modules and three test modules are already implemented. Those tasks cannot meet that acceptance criterion without deleting or quarantining the current tests.

7. **T011 is missing from the T014 dependency line.** The narrative says T007 and T009 block T014, and T013 blocks T014. T014 calls `build_report`, which T011 creates.

8. **T020 before T021.** T020 scans for "the fixture's stand-in". T021 is the task that adds the recorded payload. The stand-in is undefined when T020 runs.

9. **Four sheets versus the US1 checkpoint.** The plan's workbook contract has Cover, Sprint health, Migration phases, and Workload balance. T013 requires the first two. The MVP stop after T014 opens a workbook that the plan would still call incomplete. That is a useful checkpoint only if the stop is described as two sheets.

10. **M5 board failure.** The plan's M5 includes board HTTP 404 at the command. T019 checks 401 and 403. Client coverage of 404 is in T008, which exits inside `JiraClient` and may never reach `__main__.py`.

11. **"Before standup" versus 08:00.** **SC-001** and **FR-018** want the file before standup and at 08:00. The plan, T023, and T024 keep 08:00 `Asia/Kolkata` and never define standup. If standup is 08:00, a file written at 08:00 misses "before standup".

12. **Spec wording the plan already replaced.** The specification still says "those four health figures" while requiring five metrics, and **FR-012** names share of open work without the formula the plan locked. That is expected until T002, and T002's acceptance list does not require the "four figures" sentence to change.

## Gaps

- **T002's checklist is smaller than the Planning Decisions table.** Unassigned and other-project issues, tie-break, no-sprint sheet contents, hierarchy including an epic on the sprint, display-name 404, retry waits, other HTTP 4xx, and duplicate account ids are outside the acceptance bullets. Duplicate ids are five non-blank values and still break the workload mean. No document forbids them.
- **Successful same-day replace.** **FR-019** requires a second successful run to overwrite the day's file only after the new file is complete. T012 and T013 test a failed save. No task runs two successful writes and checks the second bytes.
- **No write calls.** **FR-023** says the command reads Jira only. No test asserts the session never receives POST, PUT, or DELETE.
- **Percent formatting.** The plan says completion and share are displayed as percentages. No task states 0–100 versus an Excel percent format, or the number of decimal places. T011 and T017 can lock opposite representations.
- **Retry waits are not in the spec closure.** T008 and T009 lock 0.5s, 1s, and 2s. T002 does not require that timing to be copied into the specification. **FR-021** still says "up to 3 times" with no waits.
- **Command-level board 404, network failure, and HTTP 5xx.** Covered on the client in T008. Not covered through `python -m sprint_health` in T019.
- **SC-001 observation.** T024 enables a template. Nothing records that a later weekday run actually produced the file before standup.
- **Concurrent runs.** The plan accepts last-writer-wins and schedules no task. Two 08:00 invocations can still interleave. That residual risk is undocumented in the task list.
- **Live mismatch loop.** T022 says to fix `sprint_health/` and repeat. There is no task id, no regression test, and no rule that the fixture in T021 gains the case that mismatched.
- **Spec status.** No task moves `spec/specification.md` from Draft to a state that matches a ratified constitution version.
- **Feature branch.** The spec and the plan name `001-sprint-health`. No task creates it. Work is on `main`.
- **Gate re-check.** The plan says to re-check the constitution after design. No task does that after T001.

## Missing artifacts

| Artifact | Expected by | State |
| --- | --- | --- |
| Amended constitution | T001, plan M0 | `spec/constitution.md` is still 1.0.0 and still requires the web stack. |
| Specification with planning decisions | T002, plan M0 | `spec/specification.md` is still the pre-decision draft. |
| `.env.example` | T004, plan secrets decision | File is absent. |
| Project README | T023 | No repository README. `work/module03-task/README.md` is a different document. |
| `tests/test_excel_writer.py` | T012, T021 | Absent. The plan's test list names only `test_config.py`, `test_jira_client.py`, and `test_report.py`. |
| `tests/fixtures/` payload | T021, plan M4 | `tests/fixtures/sprint_payload.json` is already present, ahead of the task, with no sheet-row test. |
| Command test module | T014, T019 | No path is given. The plan's `tests/` tree has no `test_main.py`. |
| `spec/live-check.md` | T022 | Absent, correctly, until the live run. The plan's `spec/` tree does not list it. |
| `sprint_health/scheduler/` template | T024 | Absent. The plan's source tree does not list it. |
| `research.md`, `data-model.md`, `contracts/`, `quickstart.md` | Spec Kit plan template | Not created. The decisions and the workbook contract live inside `spec/plan.md` instead. |
| `project_spec.md` update | — | The older technical spec is not an input of the task list. After T002 it can contradict `spec/specification.md` with no task to reconcile it. |

The plan's documentation tree also omits `spec/tasks.md` and this file. Both exist.

## Requirement coverage

| Id | Tasks | Note |
| --- | --- | --- |
| FR-001–FR-007, FR-009, FR-010, FR-012–FR-016 | T010–T018 | Covered if T002 has copied the formulas. |
| FR-008, FR-015, FR-021, FR-024 | T008, T009 | Client level. Command level is partial (T019). |
| FR-011 | T009, T015, T016 | Parent-key fetch plus grouping. |
| FR-017 | T004, T007, T020 | T020 is narrower than the requirement. |
| FR-018, SC-001 | T023, T024 | Schedule is documented and templated. The observed weekday file is not a task. |
| FR-019 | T012, T013 | Failure path only. Second successful write is untested. |
| FR-020 | T006, T007 | Covered. |
| FR-022, SC-006 | T014, T019 | Covered for the success log and for 401/403. |
| FR-023 | None directly | Excluded products are listed in the plan. No test locks read-only HTTP. |
| SC-002 | T022 | Manual only. |
| SC-003–SC-005, SC-007 unit checks | T010, T015, T017, T021 | Covered offline. |
| SC-007 secret search | T020 | Partial. |

## What to change before implementation

1. Widen T002 so M0 is done only when every Planning Decisions row is in `spec/specification.md`, the "four health figures" sentence is gone, and the spec status records the constitution version it satisfies.
2. Add `!.env.example` to T004, and name `README.md` in T023.
3. Put T011 on the T014 dependency line. Move the fixture stand-in ahead of T020, or point T020 at a sentinel defined in T004.
4. Name `tests/test_command.py` for T014 and T019, and add board 404 plus one successful overwrite to that file.
5. Treat T006–T018 as characterization tests against the existing package, or remove the "must fail first" line for files that already implement the behavior.
6. State that the US1 stop after T014 produces Cover and Sprint health only. Keep M4 closed only when T021's four sheets pass.
7. For T024, put the hour in the template as the integer from `REPORT_HOUR_LOCAL` at install time, and add a follow-up check that the first enabled weekday run created the file. Leave the agent unloaded in the committed tree.
