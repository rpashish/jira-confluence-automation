# Feature Specification: Sprint Health Report for the Database Migration

**Feature Branch**: `001-sprint-health`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "Produce a weekday-morning sprint health report for the steering committee of a database migration. The report covers the current sprint on one Jira board, limited to the five people on the migration team. It shows committed scope, work done, work remaining, spillover, progress by migration phase, and whether any of the five people is overloaded. Version 1 writes one Excel workbook each weekday morning."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Weekday sprint health workbook (Priority: P1)

The project manager runs the report before standup. Leadership opens one Excel workbook and sees whether the current sprint on the migration board is on track: committed scope, work done, work remaining, spillover, and completion, limited to the five migration-team accounts.

**Why this priority**: The steering committee's decision is whether this sprint is on track. A workbook with those four health figures is the smallest result that still supports that decision every weekday morning.

**Independent Test**: With valid Jira Cloud credentials and an active sprint, run the report once and open `sprint-health-<date>.xlsx`. Scope, done, and remaining match a manual filter of that sprint limited to the five account ids. Done uses the Done status category.

**Acceptance Scenarios**:

1. **Given** valid Cloud credentials, one board, and an active sprint, **When** the weekday run finishes, **Then** `sprint-health-YYYY-MM-DD.xlsx` exists in the configured output folder, named with the run date in the configured timezone.
2. **Given** issues on the active sprint assigned to the five accounts, **When** the health section is read, **Then** Scope is that issue count, Done is the count whose status category is Done, Remaining is Scope minus Done, and Completion is Done divided by Scope.
3. **Given** the Story Points field is populated on some of those issues, **When** the health section is read, **Then** Scope also shows the sum of those points, and issues with no points still count toward the issue totals.
4. **Given** an issue on the active sprint that also belongs to at least one earlier sprint, **When** the health section is read, **Then** that issue is included in Spillover.
5. **Given** the cover sheet, **When** leadership opens the workbook, **Then** it shows the title "Sprint health — database migration", the Jira site, project key, board name, sprint name, state, start date, end date, days remaining, the generated-at timestamp and timezone, and the five assignees.
6. **Given** Jira provides board column order, **When** the health section is read, **Then** issue counts are listed by status in that column order.
7. **Given** the same day's workbook already exists, **When** the report runs again, **Then** that day's file is replaced only after the new workbook is complete.

---

### User Story 2 - Progress by migration phase (Priority: P2)

Leadership sees the same in-scope sprint issues grouped by parent epic, so each migration phase or workstream has its own scope, done, remaining, spillover, and completion.

**Why this priority**: After the sprint-level totals, the committee needs to see which phase is moving. The phase rollup uses the epic already stored in Jira and adds no new Jira fields.

**Independent Test**: Compare phase rows with the parent epics of the five-account sprint issues. Every issue with no resolvable epic appears on a final row named `No phase`.

**Acceptance Scenarios**:

1. **Given** in-scope issues whose parent is an epic, **When** the phase section is read, **Then** there is one row per such epic with epic key, epic summary, scope, done, remaining, spillover, and completion.
2. **Given** an in-scope issue whose parent is a story under an epic, **When** phases are grouped, **Then** the issue is counted under that epic.
3. **Given** an in-scope issue with no parent epic, or a parent that is still unresolved after one hop, **When** phases are grouped, **Then** the issue is counted on the final row named `No phase`.

---

### User Story 3 - Workload balance across the five people (Priority: P3)

Leadership sees one row per configured assignee, including people with no sprint issues, and a flag when one person's open issues exceed 1.5 times the five-person mean.

**Why this priority**: The committee also decides whether the five-person team is unbalanced. The five people are the subjects of this section. Version 1 does not treat them as a separate audience and does not rank them.

**Independent Test**: Load a fixture sprint in which one of the five accounts holds more than 1.5 times the mean open-issue count, including people on zero. That person is `Overloaded` and the others are `Within range`.

**Acceptance Scenarios**:

1. **Given** the five configured accounts, **When** the workload section is read, **Then** each person has a row with display name, open issues, remaining points, share of open work, and balance, including a person with no sprint issues.
2. **Given** a person's open-issue count is greater than 1.5 times the mean open-issue count of the five people, **When** balance is calculated, **Then** that person is `Overloaded`. The mean includes people on zero.
3. **Given** nobody has open work, **When** balance is calculated, **Then** every person is `Within range`.
4. **Given** an open issue has no Story Points, **When** remaining points are shown, **Then** that issue contributes a blank point value, and the overload flag still uses the open-issue count.
5. **Given** active-sprint issues assigned to anyone outside the five accounts, **When** the workbook is read, **Then** those issues are absent from scope, phase, and workload totals and appear only as a single excluded-issue count.

---

### Edge Cases

- No sprint is active. The workbook is still written. Health totals are zero. The cover states that there is no active sprint. The run succeeds.
- Several sprints are active. The sprint with the latest start date is used, and the cover records that choice.
- Scope is zero. Completion is 0%.
- The site has no field named `Story Points`. Point columns stay blank and issue counts are still computed.
- A required setting is missing or blank. The run stops before any Jira call and reports that setting's name. A previous good workbook is left in place.
- The assignee list does not contain exactly five account ids. The run stops before any Jira call.
- Jira returns HTTP 401 or 403. The run fails, reports the status, and leaves the token out of the message. A partial workbook does not replace a previous good file.
- Jira returns HTTP 404 for the board. The run fails and names the board id.
- The network fails or Jira returns HTTP 5xx. The run retries that request up to 3 times, then fails.
- The output folder does not exist. It is created, then the workbook is written.
- A run fails after a successful file from an earlier day. The earlier file remains. The day's file is replaced only after the new workbook is complete.
- An issue's sprint field lists the active sprint plus an earlier sprint. It counts as spillover.
- Status category key `done` is the only Done signal. A status name that looks finished and is not in that category stays in Remaining.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST produce one Excel workbook per run for the steering committee, covering the current sprint of one Jira Cloud site, one project, and one board.
- **FR-002**: The system MUST include only issues on the active sprint whose assignee account id is one of a configured list of exactly five accounts.
- **FR-003**: The system MUST name the file `sprint-health-YYYY-MM-DD.xlsx`, using the run date in the configured timezone.
- **FR-004**: The cover MUST show the title "Sprint health — database migration", the Jira site, project key, board name, sprint name, state, start date, end date, days remaining, the generated-at timestamp and timezone, and the five assignees by display name.
- **FR-005**: The health section MUST report Scope, Done, Remaining, Spillover, and Completion for the in-scope issues, plus story points on Scope when the Story Points field is populated, plus issue counts by status in board column order when Jira provides that order.
- **FR-006**: Done MUST mean the issue status category key is `done`. Remaining MUST be Scope minus Done. Completion MUST be Done divided by Scope, and MUST be 0% when Scope is zero.
- **FR-007**: Spillover MUST mean the issue is on the active sprint and its sprint field also lists at least one earlier sprint.
- **FR-008**: When several sprints are active, the system MUST use the one with the latest start date and MUST record that choice on the cover.
- **FR-009**: When no sprint is active, the system MUST still write the workbook with zero health totals and a cover statement that there is no active sprint, and the run MUST succeed.
- **FR-010**: The phase section MUST group the same in-scope issues by parent epic, with one row per epic that parents at least one in-scope issue, and columns for epic key, epic summary, scope, done, remaining, spillover, and completion.
- **FR-011**: The system MUST treat `parent` as the phase epic when its issue type is Epic, ignoring case. When the parent is a story under an epic, the system MUST follow one more parent hop. When the epic is still unresolved, the issue MUST count under `No phase`.
- **FR-012**: The workload section MUST list every configured assignee, including people with no sprint issues, with display name, open issues (remaining issues assigned to that person), remaining story points, share of open work, and balance.
- **FR-013**: Balance MUST be `Overloaded` when that person's open-issue count is greater than 1.5 times the mean open-issue count of the five people, including people on zero. Otherwise it MUST be `Within range`. When nobody has open work, every person MUST be `Within range`.
- **FR-014**: The overload flag MUST use open-issue count. Remaining points MUST be shown and MUST stay blank for an issue that has no Story Points value.
- **FR-015**: The system MUST resolve the field whose name is `Story Points` once per run. When that field does not exist, point values stay blank and issue counts are still computed.
- **FR-016**: The workbook MUST include one excluded-issue count: active-sprint issues on the board whose assignee is not one of the five. Those issues MUST be absent from scope, phase, and workload totals.
- **FR-017**: The system MUST read the Jira site, account email, API token, board id, and five account ids from the environment. A search of the repository MUST NOT find the token, the email, or the account ids.
- **FR-018**: The run MUST occur each weekday morning, before standup, at the configured local hour. The default timezone is `Asia/Kolkata` and the default hour is 8. A manual run MUST use the same report behavior.
- **FR-019**: A second run on the same day MUST be safe and MUST overwrite that day's workbook only after the new workbook is complete. A failed run MUST NOT replace a finished workbook with a partial file.
- **FR-020**: When a required setting is missing or blank, or the assignee list length is not five, the system MUST stop before calling Jira and MUST report the failing name.
- **FR-021**: On HTTP 401 or 403 the system MUST fail, report the status, and omit the token. On HTTP 404 for the board the system MUST fail and name the board id. On a network error or HTTP 5xx the system MUST retry that request up to 3 times and then fail.
- **FR-022**: Logs MUST include the sprint id, the issue count, and the output path. Logs MUST omit the API token and issue descriptions.
- **FR-023**: The system MUST read Jira only. Version 1 does not edit Jira issues, and it does not send email, Slack, Teams, Confluence, PDF, or a second interface.
- **FR-024**: Display names MUST come from Jira for each of the five account ids. When Jira returns no display name, the account id MUST be shown instead.

### Key Entities *(include if feature involves data)*

- **Sprint**: The active sprint chosen for the run, with name, state, start date, end date, and days remaining. When several are active, the one with the latest start date is the sprint of record.
- **Issue**: An active-sprint work item assigned to one of the five accounts, with summary, status, status category, assignee, parent, the sprints it belongs to, and optional story points.
- **Phase**: A parent epic that represents one migration phase or workstream. Issues that do not resolve to an epic belong to the `No phase` row.
- **Assignee**: One of the five configured accounts, shown by display name, with open issues, remaining points, share of open work, and balance.
- **Workbook**: The single leadership file for a run date, containing the cover, sprint health, migration phases, workload balance, and the excluded-issue count.
- **Excluded count**: The number of active-sprint issues on the board assigned outside the five accounts. It is a count only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A weekday run with valid Cloud credentials creates `sprint-health-<date>.xlsx` in the output directory before standup, at 08:00 in the configured timezone unless that hour was changed.
- **SC-002**: Scope, done, and remaining match a manual filter of the active sprint limited to the five account ids, with Done defined by the Done status category.
- **SC-003**: Every issue that sits on the active sprint and an earlier sprint is included in the spillover count, and phase rows match parent epics, with unresolved issues on the `No phase` row.
- **SC-004**: The workload section lists all five people, and a person whose open issues exceed 1.5 times the five-person mean is marked `Overloaded`.
- **SC-005**: Issues assigned to other accounts are absent from scope, phase, and workload totals and appear only as the excluded count.
- **SC-006**: An authentication failure ends as a failed run, omits the token, and leaves the previous finished workbook unchanged.
- **SC-007**: A repository search finds no API token. Unit checks for spillover, epic grouping, zero-scope completion, and the overload threshold pass using fixture issues and no network.

## Assumptions

- The audience is the steering committee and leadership. The project manager is the person who runs the report. The five team members are subjects of the workload section.
- Version 1 delivers an Excel workbook because that file holds the sprint and workload tables. The accepted alternative of PDF is unused.
- The time window is the current sprint only. Earlier sprints appear only through the spillover signal.
- Jira Cloud is the only work tracker. Sign-in is an API token for one site. The token can browse the project and read the board.
- Migration progress is already stored as epics, one epic per phase or workstream.
- Default schedule is Monday through Friday at 08:00 `Asia/Kolkata`. `REPORT_TIMEZONE` and `REPORT_HOUR_LOCAL` move that slot when standup is at another time. The output folder defaults to `./out`.
- Version 1 leaves these outside the report: standup digests, weekly narrative status, blocker lists, per-person performance rankings, email, Slack, Teams, Confluence, PDF, a web dashboard, a second project or board, descriptions, comments, and editing Jira issues.
- Story points are displayed so leadership can see size. A missing points field does not change the overload flag.
- Verification uses fixture issues with no network, one recorded sprint payload checked against expected sheet rows, and one manual comparison with the live board for the five assignees before the weekday schedule is turned on.
