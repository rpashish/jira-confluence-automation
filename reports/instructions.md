# How to fill out the status report

Use `template.md` as the starting point. Copy it, rename the copy for the period (for example `2026-11-12-status.md`), and replace every placeholder. Delete the HTML comments before you share the report.

## Header

| Field | What to write |
| --- | --- |
| **Project** | The product or initiative this report covers. Use the same name every period. |
| **Author** | Your name. |
| **Period** | The date range the report covers, such as `Nov 3–Nov 12, 2026`. |
| **Date** | The day you wrote the report. |
| **Status** | One of `On track`, `At risk`, or `Blocked`. Pick the worst condition that is still true for the project as a whole. |

Use **On track** when planned work is moving and nothing material is stuck. Use **At risk** when a date, scope, or quality goal may slip unless something changes. Use **Blocked** when progress has stopped and you need a decision or an external dependency to move again.

## Summary

Write two to four sentences. Lead with the overall status, then the most important progress, then the single biggest concern if there is one. A reader who stops here should know whether the project is healthy.

## Completed

List work that finished during this period. Each bullet should name the outcome, not the activity. Prefer “Shipped login error states” over “Worked on login.” Leave the section with a single “None” bullet if nothing finished.

## In progress

List work that started and is still open. Include a short note on where it stands, such as “API review in progress” or “waiting on design sign-off.” Do not repeat items already listed under Completed.

## Planned next

List the work you expect to start or finish in the next period. Keep it to what you can actually commit to. If a planned item depends on a decision in **Decisions needed**, say so on that bullet.

## Risks and blockers

Add one row per real risk or blocker. Leave a single empty-looking row out of the published report; if there are none, write “None” in the Item cell and leave the other cells blank.

- **Item** is the risk or blocker in one line.
- **Impact** is what slips or breaks if it is not handled (date, scope, quality, or cost).
- **Owner** is the person who is driving the next step.
- **Mitigation** is the concrete next action, not a general hope.

## Decisions needed

List choices that someone other than you must make before work can continue or before a date can be trusted. Name the decision, who should make it, and the date you need it by. If none are open, write “None.”
