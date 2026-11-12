# Instructions Catalog

Each entry below is an instruction file with a one-line description. Optional sub-fields after `+`:
- **Keywords** — trigger words/phrases: if user's request matches, load this instruction.
- **Target** — file glob pattern: if current file or context matches, consider this instruction relevant.
- **Exceptions** — edge cases or clarifications that don't fit in the one-liner.
- **Status** — `battle-tested` when the instruction has been run and the output matched it without a further fix.

---

- [`./instructions/creating-instructions.agent.md`](./creating-instructions.agent.md) — Create, organize, and wire instruction files and their IDE wrappers.
  + Keywords: create instruction, update instruction, instruction file, main.agent.md, cursor rules, agent instructions, shortcut-links
  + Target: `instructions/**/*.agent.md`, `.cursor/rules/**/*.mdc`
  + Status: battle-tested
- [`./instructions/create-status-report.agent.md`](./create-status-report.agent.md) — Generate a weekly status report in Markdown with Accomplishments, Blockers, and Next week. Bullet points only, 20 lines maximum, professional tone, no fluff words.
  + Keywords: status report, weekly status, accomplishments, blockers, next week
  + Target: `work/**/*.md`, `reports/**/*.md`
  + Status: battle-tested
- [`./instructions/calculate-compound-interest.agent.md`](./calculate-compound-interest.agent.md) — Calculate compound interest with `tools/compound_interest.py` and present the final amount and interest earned.
  + Keywords: compound interest, final amount, interest earned, compound_interest.py
  + Target: `tools/compound_interest.py`
  + Exceptions: do not use the project-root `compound_interest.py`. A value greater than 1 for the annual rate is a percent.
- [`./instructions/use-flaoting-interest.agent.md`](./use-flaoting-interest.agent.md) — Calculate the monthly EMI with `tools/flaoting-interest.py` and present the printed payment.
  + Keywords: EMI, monthly EMI, equated monthly installment, floating interest, flaoting interest, flaoting-interest.py
  + Target: `tools/flaoting-interest.py`
  + Exceptions: tenure is months and at least 1. A value greater than 1 for the annual rate is a percent. Do not calculate the EMI by hand.
- [`./instructions/read-jira.agent.md`](./read-jira.agent.md) — Read the active Jira Cloud sprint: board, sprint, issues, fields, and the five assignee names.
  + Keywords: jira read, read jira, jira update, create jira project, Jira project, DB Migration, Oracle Migration, JiraClient, active sprint, board issues
  + Target: `sprint_health/jira_client.py`, `project_spec.md`
  + Exceptions: a request to create a Jira project still runs this read. It does not create a project and it does not switch boards.
  + Status: battle-tested
