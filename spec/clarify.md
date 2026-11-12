# Spec Review: Gaps, Contradictions, and Unclear Requirements

**Reviewed:** `spec/constitution.md` 1.0.0 (ratified 2026-11-13) and `spec/specification.md` (Draft, created 2026-11-13, branch `001-sprint-health`)

**Reviewer role:** Senior developer, before planning

**Verdict:** These two files cannot be implemented together. The constitution describes a React, Express, and PostgreSQL application that writes Jira issues and Confluence pages. The specification describes a read-only weekday Excel report. The constitution says it outranks the specification, so planning is blocked until one file is amended.

## Contradictions

### C-1. Two different products

The constitution is titled "Jira/Confluence Automation" and Principle V requires each run to create or update a Jira issue or a Confluence page, using a stable key stored in PostgreSQL. Governance rejects a change that can duplicate either record.

The specification's audience is a steering committee reading a sprint health workbook. **FR-023** says version 1 reads Jira only, does not edit Jira issues, and does not send Confluence. The assumptions repeat that exclusion and also exclude a web dashboard.

No user story, entity, or success criterion describes a Confluence page, a Jira write, a browser screen, or a stored sync key.

### C-2. The constitution locks a stack the specification never uses

Principle II and the technology section require React 18 with Vite, Node.js with Express, a JSON API under `/api`, and PostgreSQL 15 in Docker Compose, including ordered migrations.

**FR-001** requires one Excel workbook per run. The entities are a sprint, an issue, a phase, an assignee, a workbook, and an excluded count. Nothing is stored in PostgreSQL. Nothing is served to a browser. Delivery Rules require Express API tests, sync-rule tests, and migration tests. **SC-007** requires fixture tests for spillover, epic grouping, zero-scope completion, and the overload threshold.

A plan that follows the specification introduces a stack outside Principle II. A plan that follows the constitution drops the workbook the specification requires.

### C-3. Idempotency is defined twice, for different side effects

Principle V: a second run updates the existing Jira or Confluence record, and a failed run leaves the previous successful state and reports which step stopped.

**FR-019**: a second run on the same day overwrites that day's workbook only after the new file is complete, and a failed run must not replace a finished workbook.

The failure rule is similar. The successful second run is not. The specification has no step names, so "which step stopped" cannot be reported.

### C-4. Logging requirements disagree

Delivery Rules: logs name the operation, the Jira or Confluence object id, and the outcome, and they omit issue bodies that are not required to diagnose the failure.

**FR-022**: logs include the sprint id, the issue count, and the output path, and they omit issue descriptions. There is no Confluence object id in this feature. "Issue count" is not defined as in-scope issues, fetched issues, or excluded issues. A run with no active sprint has no sprint id, and **FR-022** still requires one.

### C-5. Secret-handling rules disagree inside the specification, and with the constitution

**FR-017** says a search of the repository must not find the token, the email, or the account ids.

**SC-007** says a repository search finds no API token. It does not mention the email or the account ids. The assumptions require a recorded sprint payload checked against sheet rows. A realistic payload contains account ids. That payload satisfies **SC-007** and fails **FR-017**.

The constitution requires an example environment file with names and empty values. **FR-017** does not say whether a placeholder email or a fixture account id counts as "the email" or "the account ids".

### C-6. Principle I is already broken

Principle I says the specification states the user-facing behavior, and the constitution outranks specs only when they conflict. The write-sync behavior, the browser, and the database live in the constitution and have no specification. The workbook behavior lives in the specification and conflicts with the constitution. Neither document is the single source of behavior.

### C-7. "Four health figures" versus the metrics actually required

User Story 1 says the workbook's value is "those four health figures" after naming committed scope, work done, work remaining, spillover, and completion.

**FR-005** and **FR-006** require five figures: Scope, Done, Remaining, Spillover, and Completion. Completion is also a phase column in **FR-010**.

### C-8. One project is required, and the filters do not enforce it

**FR-001** says the workbook covers one project and one board. **FR-002** keeps every active-sprint issue assigned to one of the five accounts. **FR-016** counts every other active-sprint issue on the board.

A Jira board can contain issues from more than one project. Nothing drops those issues. Scope and the excluded count can include a second project while the cover still claims one project. The assumptions say a second project is out of scope, and the filters still accept it.

## Gaps

### G-1. Workbook layout is missing, so the success criteria cannot be tested

The stories say "cover sheet", "health section", "phase section", and "workload section". **SC-007** expects sheet rows. No sheet names, header row, column order, number formats, or placement of the excluded count are specified. An implementation can satisfy the field lists in **FR-004**, **FR-005**, **FR-010**, and **FR-012** with a different arrangement than the fixture test expects.

### G-2. The no-sprint workbook is only partly specified

**FR-009** says health totals are zero and the cover states that there is no active sprint. It does not say what sprint name, state, start date, end date, or days remaining contain, even though **FR-004** requires all of them. It does not say whether the phase section is empty, whether a `No phase` row is absent, whether the five workload rows are still written as zeros, or whether the excluded count is zero. Status counts in board column order are also unspecified for this run.

### G-3. How the file reaches the steering committee

The purpose of the report is a leadership decision. The assumptions exclude email, Slack, Teams, and Confluence. The only output is a file in the output folder, default `./out`. No requirement says who copies that file to the committee, or what "before standup" means if the file stays on the machine that ran the job.

### G-4. The scheduler is required and not specified

**FR-018** says the run must occur each weekday morning at the configured local hour. The assumptions name `REPORT_TIMEZONE` and `REPORT_HOUR_LOCAL`. Nothing says whether version 1 includes the scheduler or only a command an operator schedules. Weekday is not tied explicitly to the configured timezone versus the machine clock. A manual weekend run is allowed by the "same report behavior" sentence, and the software's response to a weekend invocation is otherwise unstated.

There is no behavior for an invalid timezone, an hour outside 0–23, or a local time that does not exist when the configured zone changes clocks.

### G-5. Required settings are not a closed list

**FR-017** and **FR-020** talk about the site, the account email, the API token, the board id, and five account ids. Only the optional names appear as identifiers: `REPORT_TIMEZONE`, `REPORT_HOUR_LOCAL`, and `./out`. The failing "name" in **FR-020** has no canonical spelling. The list separator, whitespace, and duplicate account ids are unspecified. Five identical ids have length five and make the workload rows and the mean meaningless.

### G-6. Cover fields have no source

**FR-004** requires project key, board name, and Jira site. No setting supplies the project key or the board name, and no read is required to derive them from the board. "Jira site" might be the hostname or the configured base URL. The sprint id is logged and is not on the cover, so two sprints with the same name cannot be told apart from the workbook.

### G-7. Jira read completeness

Nothing requires the run to follow pagination until every sprint issue is read. **SC-002** still requires the totals to match a manual filter of the whole sprint. A single page of issues can produce a workbook that looks complete.

Nothing states the auth scheme. **FR-021** defines 401 and 403, and the specification never says the email and token are HTTP Basic credentials.

User lookup is required by **FR-024** only for a missing display name. A failed lookup, a 404 for one account, or a 404 for a sprint or field request has no behavior. **FR-021** names 404 only for the board.

HTTP 400, 429, and other 4xx responses are unspecified. Retry applies to "a network error or HTTP 5xx" with no backoff, and "up to 3 times" does not say whether the failed attempt is included. A retried page in the middle of a sprint does not say whether earlier pages are kept.

### G-8. Issue hierarchy beyond one parent hop

**FR-011** covers a parent epic, or one hop from a story to an epic. It does not cover:

- an epic that is itself on the sprint
- a subtask whose parent story's parent is the epic, beyond the one hop already stated
- company-managed projects that store the epic on an epic-link field rather than `parent`
- a parent payload that contains only a key, with no issue type, so "unresolved" has no test

Those issues fall through to `No phase` or are grouped differently depending on the reader's guess.

### G-9. Subtasks and points can inflate scope

Scope is an issue count. A story and its subtask can both sit on the sprint and both be assigned to the five. Both count. Story points on both can be summed. The specification does not say whether subtasks are excluded, counted, or rolled up.

### G-10. Unassigned issues

**FR-002** and **FR-016** talk about an assignee account id that is, or is not, one of the five. An issue with no assignee matches neither sentence cleanly. It is unclear whether it increments the excluded count, is dropped, or fails the run.

### G-11. Delivery of generated files

The specification does not say the workbook stays out of git. **FR-017** covers the token, the email, and the account ids. The workbook contains display names, the project key, and sprint data.

### G-12. Constitution behavior that has no specification

If the constitution remains in force, these requirements are missing rather than merely in conflict:

- screens, routes, and who is allowed to open the Vite application
- the `/api` resources, status codes, and how the browser authenticates to Express
- the PostgreSQL tables, the stable external key, and the migration list
- which Confluence page is created or updated, and what Jira issue is written
- which environment names exist, and which site, product, and account each environment uses
- the example environment file's variable names
- pinned Node.js, Vite, and Express versions. "Active LTS" and "current official REST APIs" change without an amendment, which fights the locked-stack rule

### G-13. Process gap

The specification status is Draft. The constitution is ratified and claims precedence. There is no record of which constitution version the specification claims to satisfy.

## Unclear requirements

### U-1. Days remaining

**FR-004** requires days remaining. It does not say calendar days or weekdays, whether the end date is compared in the report timezone, what happens when the end date is missing, or what is shown when the sprint is already past its end date. A sprint that ends today could be 0 or 1.

### U-2. Which sprint wins a tie

**FR-008** selects the active sprint with the latest start date. Two active sprints can share that start date, and an active sprint can have no start date. The cover "records that choice" with no required wording. The no-sprint sentence on the cover is also unfixed, unlike the report title.

### U-3. What "earlier sprint" means

**FR-007** counts spillover when the sprint field lists the active sprint and at least one earlier sprint. "Earlier" has no sort key: start date, end date, or creation order. A second sprint with no dates, or a future sprint also listed on the issue, is unclassified. Closed and active previous sprints are treated as the same if they are earlier, and that should be confirmed.

### U-4. Completion formula

**FR-006** says Done divided by Scope. Scope is an issue count, and Scope also shows story points. It is unclear whether completion uses issues or points. Rounding is unspecified: a ratio of 1/3 could be 33%, 33.3%, or 0.33. The same gap applies to every phase row.

### U-5. Where story points appear, and how partial sums work

**FR-005** adds story points on Scope only. Done, Remaining, and Spillover do not get a point total. Phase rows in **FR-010** have no point columns. Workload remaining points do.

**FR-014** says an issue with no points contributes a blank. A person with a mix of pointed and unpointed open issues has one remaining-points cell. It is unclear whether that cell is the sum of the known points or blank because any issue is blank. **FR-005** implies the opposite for Scope: sum the populated points, and still count the unpointed issues. The two sections need one rule.

A value of 0 is not distinguished from missing. Two fields named `Story Points` are not disambiguated. Team-managed projects often use `Story point estimate` instead, and this specification would then show blank points while still looking successful.

### U-6. Share of open work

**FR-012** names the column and does not give the formula. The denominator is not stated. When nobody has open work, **FR-013** sets every balance to `Within range` and leaves the share, which would divide by zero, unspecified. Rounding is unspecified.

### U-7. Overload threshold arithmetic

**FR-013** says greater than 1.5 times the mean of the five open-issue counts, including zeros. Equal to 1.5 times the mean is `Within range`. The mean can be fractional. Nothing says the comparison is exact, or that the mean is rounded first.

User Story 3's independent test says the overloaded person is flagged "and the others are Within range". That describes one fixture. **FR-013** allows several people to be `Overloaded` at once. The test sentence can be read as a product rule that only one person may be flagged.

### U-8. Status counts and board columns

**FR-005** lists issue counts by status in board column order when Jira provides that order. A column can hold more than one status. It is unclear whether the row is one count per status or one count per column. Statuses with zero issues, statuses not on the board, and the order to use when Jira provides no column configuration are all unspecified.

### U-9. Phase and assignee order

`No phase` is the final phase row. The order of the epic rows is unspecified. The order of the five people on the cover and in the workload section is unspecified. **FR-024** does not say the configured list order is preserved.

### U-10. Failure signaling

The edge cases say the run fails or succeeds. They never define the signal a scheduler sees: exit code, a specific log line, or both. **FR-021** says "report the status" and "name the board id" without the message text. Retry timing is unspecified, so a test cannot tell a retry from a single slow call.

Network failures can include the request URL in the exception text. **FR-021** forbids printing the token on 401 and 403, and it does not say the same for a network error.

### U-11. Overlapping runs

**FR-019** covers a second run after the first finishes. Two runs at the same time can write the same day's file. Locking or a single-writer rule is absent.

### U-12. "Issue count" and descriptions in logs

**FR-022** omits issue descriptions. It does not say whether issue summaries, account ids, or the base URL may be logged. The constitution allows issue bodies when they are required to diagnose a failure. The specification's ban on descriptions is absolute. A planner cannot tell which rule wins, because of **C-6**.

## Questions to settle before a plan

1. Which document is amended: the constitution, so version 1 is the Excel sprint report, or the specification, so version 1 is the React, Express, PostgreSQL, and Confluence product?
2. If the workbook remains the product, which sheet names, columns, formats, and row orders are the fixture in **SC-007** asserting?
3. Are unassigned issues, subtasks, and issues from another project on the same board in scope, in the excluded count, or dropped?
4. Do completion and share use issue counts, how are they rounded, and how is a mixed story-point total displayed?
5. What is the closed list of environment variable names, the assignee-list format, the exit codes, and the scheduler's owner?
