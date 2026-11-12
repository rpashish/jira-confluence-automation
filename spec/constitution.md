# Jira/Confluence Automation Constitution

## Core Principles

### I. Spec Before Code

Every feature starts as a specification under `spec/`. The spec states the user-facing behavior and the reason it exists. The technical plan, the task list, and the implementation follow that spec and stay consistent with it. A change to behavior updates the spec in the same change as the code.

### II. Locked Stack

The supported stack is React 18 with Vite for the frontend, Node.js with Express for the backend, and PostgreSQL 15 running in Docker for the database. A new framework, a different major version of React or PostgreSQL, or a database outside Docker requires an amendment to this constitution before any plan adopts it.

### III. One API Boundary

The Vite application talks only to the Express HTTP API. Jira, Confluence, and PostgreSQL are reached only from the backend. Credentials and Atlassian requests stay on the server. The browser never receives an API token, a database URL, or a direct Atlassian host.

### IV. Official Atlassian APIs

Jira Cloud and Confluence Cloud are accessed through their current official REST APIs. Each call uses the site, the product, and the account configured for that environment. Tokens and passwords come from environment variables, are excluded from git, and are omitted from logs, error responses, and client bundles.

### V. Idempotent Sync

A sync or automation run can be repeated safely. Creating or updating a Jira issue or a Confluence page uses a stable external key stored in PostgreSQL so a second run updates the existing record. A failed run leaves the previous successful state in place and reports which step stopped.

## Technology Stack

- **Frontend:** React 18, built and served in development by Vite. UI state and routing live in the frontend. Data loading goes through the Express API.
- **Backend:** Node.js (Active LTS) and Express. The API is JSON over HTTP, versioned under `/api`. Request validation happens at the route boundary before any Atlassian or database call.
- **Database:** PostgreSQL 15, started from the project Docker Compose file. Schema changes ship as ordered migrations. Application code uses parameterized queries. Local development and automated tests use this same major version.
- **Configuration:** Environment-specific values live in environment variables. The repository holds an example file with names and empty values. Secrets stay out of source control, images, and logs.

## Delivery Rules

- A feature is planned against this constitution, then broken into tasks, then implemented. Review checks the spec, the plan, and the tasks before the code is treated as done.
- Automated tests cover the Express API, the sync rules, and the migration path. A change to Jira or Confluence mapping includes a fixture-based test that uses recorded payloads with secrets removed.
- Logs name the operation, the Jira or Confluence object id, and the outcome. They omit tokens, request bodies that contain credentials, and page or issue bodies that are not required to diagnose the failure.
- Docker Compose is the supported way to run PostgreSQL 15. The app connects with the URL from the environment and refuses to start when a required variable is missing.

## Governance

This constitution outranks feature specs, plans, and task lists. A spec or plan that conflicts with a principle is amended, or the constitution is amended first.

An amendment updates this file, raises the version below, and sets **Last Amended** to the date of the change. Principles are added, tightened, or removed only by an amendment. Patch-level wording clarifications that do not change a rule bump the patch version.

Reviews reject a change that introduces a stack outside section II, that calls Jira, Confluence, or PostgreSQL from the frontend, that commits a secret, or that can create a duplicate Jira issue or Confluence page when the same sync runs twice.

**Version**: 1.0.0 | **Ratified**: 2026-11-13 | **Last Amended**: 2026-11-13
