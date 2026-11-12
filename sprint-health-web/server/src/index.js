/** HTTP API for the Module 08 sprint health report. */

import path from "node:path";
import { fileURLToPath } from "node:url";

import dotenv from "dotenv";
import express from "express";

import { ConfigError, loadConfig } from "./config.js";
import { loadFixtureReport } from "./fixture.js";
import { JiraClient, JiraError } from "./jiraClient.js";
import { buildReport } from "./report.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../..");
dotenv.config({ path: path.join(repoRoot, ".env") });
dotenv.config({ path: path.join(here, "../.env") });

export function createApp() {
  const app = express();
  app.get("/api/health", (_req, res) => {
    res.json({ ok: true });
  });
  app.get("/api/report", async (req, res) => {
    try {
      if (req.query.source === "fixture") {
        res.json(loadFixtureReport());
        return;
      }
      const config = loadConfig(process.env);
      const report = await buildLiveReport(config, new JiraClient(config));
      res.json({ source: "jira", report });
    } catch (error) {
      if (error instanceof ConfigError) {
        res.status(400).json({ error: "missing_config", variables: error.variables });
        return;
      }
      if (error instanceof JiraError) {
        res.status(error.status).json({ error: error.message });
        return;
      }
      res.status(500).json({ error: "report_failed" });
    }
  });
  return app;
}

export async function buildLiveReport(config, client) {
  const board = await client.board();
  const sprint = await client.activeSprint();
  let issues = [];
  let storyPointsField = null;
  let sprintField = null;
  let statusOrder = [];
  if (sprint) {
    issues = await client.sprintIssues(sprint.id);
    storyPointsField = await client.storyPointsFieldId();
    sprintField = await client.sprintFieldId();
    statusOrder = await client.statusOrder();
  }
  return buildReport({
    issues,
    config,
    sprint,
    board,
    storyPointsField,
    sprintField,
    statusOrder,
    assigneeNames: await client.assigneeNames(),
  });
}

const port = Number(process.env.PORT || 3001);
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  createApp().listen(port, "127.0.0.1", () => {
    console.log(`Sprint health API listening on http://127.0.0.1:${port}`);
  });
}
