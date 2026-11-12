# Implementation Checklist: Sprint Health Report

**Spec:** `spec/specification.md` (Draft, 2026-11-13)

**Implementation checked:** `sprint_health/` (`python -m sprint_health`), with `tests/`.

**Run:** `.venv/bin/python -m pytest -q` on 2026-11-13. **27 passed** in 0.38s. The system `python3` is 3.9 and cannot collect these tests. The project virtualenv is Python 3.14.

**Not run:** a live Jira board comparison, and a weekday scheduled run. Those two items stay unverified.

The web app under `sprint-health-web/` is a second interface. The spec's version 1 is the Excel command, so the rows below judge `sprint_health/`.

## Functional requirements

| Id | Implemented | Works | Evidence |
| --- | --- | --- | --- |
| FR-001 | Yes | Partial | `excel_writer.write_workbook` writes one `.xlsx`. `JiraClient.board` reads one board and its project key. Issues are not filtered to that project key, so a multi-project board can include other projects. No live run was compared with Jira. |
| FR-002 | Yes | Yes | `_split_assignees` keeps an issue only when `assignee.accountId` is one of the five. `test_other_assignees_are_excluded_from_the_totals` passed. |
| FR-003 | Yes | Yes | The filename is `sprint-health-YYYY-MM-DD.xlsx` from the configured timezone. `test_file_date_uses_the_configured_timezone` expects `sprint-health-2026-11-13.xlsx` for 20:00 UTC when the zone is `Asia/Kolkata`. |
| FR-004 | Yes | Yes | Cover title is `Sprint health — database migration`. The sheet writes site, project key, board, sprint, state, dates, days remaining, generated-at, timezone, and the five display names. `test_recorded_sprint_payload_matches_sheet_rows` checks each of those cells. |
| FR-005 | Yes | Yes | Sprint health writes Scope, Done, Remaining, Spillover, Completion, story points, and status rows. Status order follows the board column list, then any other status name. The recorded fixture asserts Scope 5 / 11 points, Done 2, Remaining 3, Spillover 1, and statuses To Do, In Progress, Done. |
| FR-006 | Yes | Yes | Done is status category key `done`, case-insensitive. Remaining is scope minus done. Completion is 0 when scope is 0, otherwise done/scope times 100, stored as an Excel percentage. `test_zero_scope_completion_is_zero_percent` passed. |
| FR-007 | Yes | Yes | Spillover requires the active sprint plus another sprint with an earlier start. If either start date is missing, a `closed` or `completed` sprint still counts as earlier. `test_spillover_requires_the_active_sprint_and_an_earlier_one` passed. |
| FR-008 | Yes | Yes | `active_sprint` chooses the latest `startDate` and sets `selectionNote`. The cover writes that note. `test_active_sprint_pages_and_keeps_the_latest_start` and `test_sprint_choice_is_recorded_on_the_cover` passed. |
| FR-009 | Yes | Yes | No active sprint still writes the workbook, uses zero health totals, prints `There is no active sprint. Health totals are zero.`, and `run` returns 0. `test_no_active_sprint_exits_zero_and_logs_without_the_token` passed. |
| FR-010 | Yes | Yes | Migration phases has one row per epic with key, summary, scope, done, remaining, spillover, and completion. The recorded workbook asserts Schema cutover, Data move, and No phase. |
| FR-011 | Yes | Yes | Parent issue type `Epic` matches ignoring case. One hop is fetched when the parent is not an epic. Anything else is `No phase`. `test_epic_grouping_follows_one_parent_hop_and_closes_with_no_phase` and `test_sprint_issues_page_until_total_and_follow_one_parent_hop` passed. |
| FR-012 | Yes | Yes | Workload lists every configured person, including people with no issues, with display name, open issues, remaining points, share, and balance. The recorded sheet lists Ada through Ed, including Cy and Ed on zero open issues. |
| FR-013 | Yes | Yes | `Overloaded` is open issues greater than 1.5 times the mean of the five counts, including zeros. Otherwise `Within range`. Nobody open means every person is `Within range`. `test_overload_threshold_uses_open_issues_and_includes_zeros` passed. The recorded fixture marks three of five people Overloaded, which the 1.5 rule allows. |
| FR-014 | Yes | Yes | The flag uses the open-issue count. A missing point value stays blank and is omitted from the sum. The recorded sheet leaves Ben's remaining points empty while Ben is still Overloaded. `test_missing_story_points_field_leaves_points_blank` passed. |
| FR-015 | Yes | Yes | `_load_fields` runs once per client and takes the first field named `Story Points`. A missing field leaves points blank and issue counts are still computed. `test_missing_story_points_field_is_left_out_of_the_request` passed. |
| FR-016 | Yes | Yes | The cover has one excluded-issue count. Those issues stay out of scope, phases, and workload. The recorded fixture expects excluded count 2. |
| FR-017 | Yes | Yes | `load_config` reads `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_BOARD_ID`, and `JIRA_ASSIGNEE_ACCOUNT_IDS`. A search of the tree found no assigned `JIRA_API_TOKEN`. Tests use a stand-in token and synthetic account ids. |
| FR-018 | Partial | No | Defaults `Asia/Kolkata` and hour 8 are loaded and tested. `python -m sprint_health` is the manual command. Nothing in the package runs it on weekday mornings. `REPORT_HOUR_LOCAL` is stored and never read by the command or a scheduler. |
| FR-019 | Yes | Yes | The writer saves a temporary file and `os.replace`s it onto the day's workbook. The recorded test writes a second complete workbook over the same path and asserts a single file remains. `test_auth_failure_does_not_replace_a_finished_workbook` asserts the previous bytes survive an exit before writing. |
| FR-020 | Yes | Yes | A missing or blank required variable, or an assignee list that is not five distinct non-blank ids, prints the variable name and exits 1 before a client is constructed. `test_missing_variable_exits_with_its_name_and_hides_the_token` and `test_assignee_list_must_be_exactly_five_ids` passed. |
| FR-021 | Yes | Yes | HTTP 401 and 403 print `HTTP <status>` and exit 1 without the token. Board HTTP 404 prints `HTTP 404 for board <id>`. Network errors and HTTP 5xx retry three times (waits 0.5s, 1s, 2s), then exit 1. The 401, 403, 404, 503, and connection-error tests passed. |
| FR-022 | Yes | Yes | Success logs `sprint_id=… issues=… output=…`. The no-sprint test checks `sprint_id=none`, `issues=0`, and that the token is absent. Issue descriptions are not written to that line. |
| FR-023 | Partial | Partial | `JiraClient._get` sends only HTTP GET. The command does not send mail or write Confluence, PDF, or Jira issues. `sprint-health-web/` is a browser interface, which this requirement leaves out of version 1. |
| FR-024 | Yes | Yes | `assignee_names` calls `GET /rest/api/3/user?accountId=` and stores `displayName`, or the account id when the name is missing or the user returns 404. |

## User stories

| Story | Implemented | Works | Evidence |
| --- | --- | --- | --- |
| US1 Weekday workbook | Yes | Partial | Scenarios 2–7 are covered by the report tests and the recorded workbook. Scenario 1's file is produced in tests. A real weekday run with Cloud credentials was not executed. |
| US2 Migration phases | Yes | Yes | All three acceptance scenarios are in `test_epic_grouping_follows_one_parent_hop_and_closes_with_no_phase` and the recorded phase rows. |
| US3 Workload balance | Yes | Yes | Five rows, the 1.5 threshold, zero open work, blank points, and the excluded count are asserted in `tests/test_report.py`. |

## Edge cases

| Case | Implemented | Works | Evidence |
| --- | --- | --- | --- |
| No active sprint | Yes | Yes | Workbook written, totals zero, cover sentence present, exit 0. |
| Several active sprints | Yes | Yes | Latest start date wins and the cover records the choice. |
| Scope zero | Yes | Yes | Completion is 0%. |
| No Story Points field | Yes | Yes | Point cells stay blank. Counts are still computed. |
| Missing or blank required setting | Yes | Yes | Exit 1 with the variable name before any Jira call. |
| Assignee list is not five ids | Yes | Yes | Exit 1 with `JIRA_ASSIGNEE_ACCOUNT_IDS`. Duplicates are also rejected. |
| HTTP 401 or 403 | Yes | Yes | Exit 1, status printed, token omitted, previous file kept when the failure happens before writing. |
| Board HTTP 404 | Yes | Yes | Exit 1 and the message names the board id. |
| Network error or HTTP 5xx | Yes | Yes | Three retries, then exit 1. A 503 that recovers on the fourth attempt returns the board. |
| Output directory missing | Yes | Yes | `mkdir(parents=True)` and the recorded test writes into `nested/out`, which did not exist. |
| Failed run after an earlier good file | Yes | Yes | The earlier file's bytes are unchanged when `run` exits before `write_workbook`. |
| Active sprint plus an earlier sprint | Yes | Yes | Counted as spillover. |
| Done is only status category `done` | Yes | Yes | `_view` sets done from the category key. A finished-looking name in another category stays in Remaining. |

## Success criteria

| Id | Implemented | Works | Evidence |
| --- | --- | --- | --- |
| SC-001 | Partial | No | The command can create the dated workbook. Nothing runs it at 08:00 on weekdays, and no live file was observed before standup. |
| SC-002 | Yes | Not run | The fixture totals match the five-account filter and the Done category. No manual comparison against the live board was done. |
| SC-003 | Yes | Yes | Spillover and `No phase` pass on fixture issues with no network. |
| SC-004 | Yes | Yes | All five people are listed. The overload threshold test passed. |
| SC-005 | Yes | Yes | Other assignees appear only as the excluded count. |
| SC-006 | Yes | Yes | Authentication exits 1, omits the token, and leaves the finished workbook unchanged. |
| SC-007 | Yes | Yes | No assigned API token was found in the tree. The spillover, epic, zero-scope, and overload tests passed with fixtures and no network. |

## Result

Twenty-two of twenty-four functional requirements are implemented and pass their unit tests. **FR-018** is the gap that blocks a weekday report: the hour is configured and unused. **FR-001** and **FR-023** are partial because the board's project key is displayed rather than used as a filter, and a web UI exists beside the Excel command. **SC-001** does not work until a scheduler exists. **SC-002** is implemented and still needs the live board comparison.
