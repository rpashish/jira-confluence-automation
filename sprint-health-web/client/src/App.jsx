import { useEffect, useState } from "react";

const NO_SPRINT = "There is no active sprint. Health totals are zero.";
const EXCLUSION =
  "Active-sprint issues assigned outside the five accounts are excluded from scope, phase, and workload totals.";

export default function App() {
  const source = new URLSearchParams(window.location.search).get("source");
  const [state, setState] = useState({ status: "loading" });

  useEffect(() => {
    const query = source === "fixture" ? "?source=fixture" : "";
    const controller = new AbortController();
    setState({ status: "loading" });
    fetch(`/api/report${query}`, { signal: controller.signal })
      .then(async (response) => {
        const body = await response.json();
        if (!response.ok) {
          setState({ status: "error", body, httpStatus: response.status });
          return;
        }
        setState({ status: "ready", body });
      })
      .catch((error) => {
        if (error.name !== "AbortError") {
          setState({ status: "error", body: { error: "unavailable" } });
        }
      });
    return () => controller.abort();
  }, [source]);

  return (
    <main>
      <header className="masthead">
        <p className="eyebrow">Database migration</p>
        <h1>Sprint health</h1>
        <p className="lede">Weekday report for the steering committee: scope, phases, and workload for the five migration accounts.</p>
      </header>
      {state.status === "loading" ? <p className="status-line">Loading the report…</p> : null}
      {state.status === "error" ? <ErrorPanel body={state.body} /> : null}
      {state.status === "ready" ? <Report payload={state.body} /> : null}
    </main>
  );
}

function ErrorPanel({ body }) {
  if (body?.error === "missing_config") {
    return (
      <section className="panel">
        <h2>Jira configuration is missing</h2>
        <p>Set these variables in the environment, then reload this page.</p>
        <ul>
          {body.variables.map((name) => (
            <li key={name}>{name}</li>
          ))}
        </ul>
        <p>
          <a href="/?source=fixture">Open the recorded sample</a>
        </p>
      </section>
    );
  }
  return (
    <section className="panel">
      <h2>The report could not be loaded</h2>
      <p>{body?.error || "The API did not respond."}</p>
      <p>
        <a href="/?source=fixture">Open the recorded sample</a>
      </p>
    </section>
  );
}

function Report({ payload }) {
  const report = payload.report;
  const sprint = report.sprint;
  return (
    <>
      {payload.source === "fixture" ? (
        <p className="banner">Sample data from the recorded sprint fixture. This is not the live board.</p>
      ) : null}
      <section className="cover">
        <h2>{report.title}</h2>
        {report.noActiveSprint ? <p className="notice">{NO_SPRINT}</p> : null}
        <dl>
          <div><dt>Jira site</dt><dd>{report.site}</dd></div>
          <div><dt>Project key</dt><dd>{report.projectKey || "—"}</dd></div>
          <div><dt>Board</dt><dd>{report.boardName || "—"}</dd></div>
          <div><dt>Sprint</dt><dd>{report.noActiveSprint ? "No active sprint" : sprint?.name || "—"}</dd></div>
          <div><dt>State</dt><dd>{sprint?.state || "—"}</dd></div>
          <div><dt>Start date</dt><dd>{sprint?.startDate || "—"}</dd></div>
          <div><dt>End date</dt><dd>{sprint?.endDate || "—"}</dd></div>
          <div><dt>Days remaining</dt><dd>{sprint?.daysRemaining ?? "—"}</dd></div>
          <div><dt>Generated at</dt><dd>{report.generatedAtDisplay}</dd></div>
          <div><dt>Timezone</dt><dd>{report.timezone}</dd></div>
        </dl>
        {sprint?.selectionNote ? <p className="note">{sprint.selectionNote}</p> : null}
        <p className="assignees">Assignees: {report.assignees.map((person) => person.displayName).join(", ")}</p>
        <p className="excluded">Excluded issues: {report.excludedCount}. {EXCLUSION}</p>
      </section>

      <section>
        <h2>Sprint health</h2>
        <div className="metrics">
          <Metric label="Scope" count={report.health.scope} points={report.health.scopePoints} />
          <Metric label="Done" count={report.health.done} points={report.health.donePoints} />
          <Metric label="Remaining" count={report.health.remaining} points={report.health.remainingPoints} />
          <Metric label="Spillover" count={report.health.spillover} />
          <Metric label="Completion" count={formatPercent(report.health.completion)} />
        </div>
        <table>
          <caption>Issues by status</caption>
          <thead>
            <tr><th>Status</th><th>Issues</th></tr>
          </thead>
          <tbody>
            {report.statuses.length ? report.statuses.map((status) => (
              <tr key={status.name}><td>{status.name}</td><td>{status.count}</td></tr>
            )) : (
              <tr><td colSpan="2">No issues in scope.</td></tr>
            )}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Migration phases</h2>
        <table>
          <thead>
            <tr>
              <th>Epic</th>
              <th>Phase</th>
              <th>Scope</th>
              <th>Done</th>
              <th>Remaining</th>
              <th>Spillover</th>
              <th>Completion</th>
            </tr>
          </thead>
          <tbody>
            {report.phases.length ? report.phases.map((phase) => (
              <tr key={phase.key || "no-phase"}>
                <td>{phase.key || "—"}</td>
                <td>{phase.summary}</td>
                <td>{phase.scope}</td>
                <td>{phase.done}</td>
                <td>{phase.remaining}</td>
                <td>{phase.spillover}</td>
                <td>{formatPercent(phase.completion)}</td>
              </tr>
            )) : (
              <tr><td colSpan="7">No phase rows.</td></tr>
            )}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Workload balance</h2>
        <table>
          <thead>
            <tr>
              <th>Assignee</th>
              <th>Open issues</th>
              <th>Remaining points</th>
              <th>Share of open work</th>
              <th>Balance</th>
            </tr>
          </thead>
          <tbody>
            {report.workload.map((row) => (
              <tr key={row.accountId}>
                <td>{row.displayName}</td>
                <td>{row.openIssues}</td>
                <td>{formatPoints(row.remainingPoints)}</td>
                <td>{formatPercent(row.share * 100)}</td>
                <td><span className={row.balance === "Overloaded" ? "flag over" : "flag ok"}>{row.balance}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

function Metric({ label, count, points }) {
  return (
    <article className="metric">
      <h3>{label}</h3>
      <p className="count">{count}</p>
      {points !== undefined ? <p className="points">{formatPoints(points)} points</p> : null}
    </article>
  );
}

function formatPercent(value) {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }
  const rounded = Math.round(value * 10) / 10;
  return Number.isInteger(rounded) ? `${rounded}%` : `${rounded.toFixed(1)}%`;
}

function formatPoints(value) {
  if (value == null) {
    return "—";
  }
  return Number.isInteger(value) ? String(value) : String(Math.round(value * 10) / 10);
}
