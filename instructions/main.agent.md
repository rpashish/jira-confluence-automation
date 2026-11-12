# Instructions Catalog

Each entry below is an instruction file with a one-line description. Optional sub-fields after `+`:
- **Keywords** — trigger words/phrases: if user's request matches, load this instruction.
- **Target** — file glob pattern: if current file or context matches, consider this instruction relevant.
- **Exceptions** — edge cases or clarifications that don't fit in the one-liner.

---

- [`./instructions/creating-instructions.agent.md`](./creating-instructions.agent.md) — Create, organize, and wire instruction files and their IDE wrappers.
  + Keywords: create instruction, update instruction, instruction file, main.agent.md, cursor rules, agent instructions, shortcut-links
  + Target: `instructions/**/*.agent.md`, `.cursor/rules/**/*.mdc`
- [`./instructions/create-status-report.agent.md`](./create-status-report.agent.md) — Generate a weekly status report in Markdown with Accomplishments, Blockers, and Next week. Bullet points only, 20 lines maximum, professional tone, no fluff words.
  + Keywords: status report, weekly status, accomplishments, blockers, next week
  + Target: `work/**/*.md`, `reports/**/*.md`
- [`./instructions/read-jira.agent.md`](./read-jira.agent.md) — Read the active Jira Cloud sprint: board, sprint, issues, fields, and the five assignee names.
  + Keywords: jira read, read jira, jira update, JiraClient, active sprint, board issues
  + Target: `sprint_health/jira_client.py`, `project_spec.md`
