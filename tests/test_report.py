"""Report, workbook, and schedule-path tests. Fixtures stand in for Jira."""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from openpyxl import load_workbook

import sprint_health
from sprint_health.__main__ import run
from sprint_health.config import Config, load_config
from sprint_health.excel_writer import write_workbook
from sprint_health.jira_client import JiraClient
from sprint_health.report import build_report

TOKEN = "super-secret-token"
ACCOUNTS = ("a1", "a2", "a3", "a4", "a5")
POINTS = "customfield_10016"
SPRINT_FIELD = "customfield_10020"
ACTIVE = {
    "id": 20,
    "name": "Sprint 12",
    "state": "active",
    "startDate": "2026-11-02T03:30:00.000Z",
    "endDate": "2026-11-13T03:30:00.000Z",
}
FIXTURE = Path(__file__).parent / "fixtures" / "sprint_payload.json"
NOW = datetime(2026, 11, 12, 8, 0, tzinfo=ZoneInfo("Asia/Kolkata"))


def test_package_exposes_the_report_pipeline():
    assert sprint_health.__version__ == "0.1.0"
    assert callable(load_config)
    assert callable(build_report)
    assert callable(write_workbook)
    assert JiraClient.__init__ is not None


def test_config_holds_the_spec_fields():
    config = sample()
    assert len(config.assignee_account_ids) == 5
    assert config.timezone == "Asia/Kolkata"
    assert config.report_hour_local == 8


def test_spillover_requires_the_active_sprint_and_an_earlier_one():
    active_entry = {"id": 20, "name": "Sprint 12", "state": "active", "startDate": ACTIVE["startDate"]}
    issues = [
        issue("EARLIER", sprints=[
            {"id": 19, "name": "Sprint 11", "state": "closed", "startDate": "2026-10-19T03:30:00.000Z"},
            active_entry,
        ]),
        issue("ONLY", sprints=[active_entry]),
        issue("FUTURE", sprints=[
            active_entry,
            {"id": 21, "name": "Sprint 13", "state": "future", "startDate": "2026-11-16T03:30:00.000Z"},
        ]),
        issue("CLOSED", sprints=[active_entry, {"id": 18, "name": "Sprint 10", "state": "closed"}]),
    ]
    report = build(issues)
    assert report["health"]["scope"] == 4
    assert report["health"]["spillover"] == 2


def test_epic_grouping_follows_one_parent_hop_and_closes_with_no_phase():
    issues = [
        issue("DIRECT", parent=epic("MIG-100", "Schema cutover")),
        issue("HOP", parent=story_under("MIG-200", "Data move")),
        issue("ORPHAN", parent={"key": "MIG-50", "fields": {"summary": "Story", "issuetype": {"name": "Story"}}}),
        issue("NONE"),
    ]
    phases = build(issues)["phases"]
    assert [(phase["key"], phase["summary"], phase["scope"]) for phase in phases] == [
        ("MIG-100", "Schema cutover", 1),
        ("MIG-200", "Data move", 1),
        ("", "No phase", 2),
    ]


def test_zero_scope_completion_is_zero_percent():
    report = build([])
    assert report["health"]["scope"] == 0
    assert report["health"]["done"] == 0
    assert report["health"]["remaining"] == 0
    assert report["health"]["spillover"] == 0
    assert report["health"]["completion"] == 0
    assert report["phases"] == []
    assert [row["balance"] for row in report["workload"]] == ["Within range"] * 5


def test_overload_threshold_uses_open_issues_and_includes_zeros():
    even = build(open_issues({"a1": 3, "a2": 3, "a3": 2, "a4": 1, "a5": 1}))
    assert {row["account_id"]: row["balance"] for row in even["workload"]} == {
        account: "Within range" for account in ACCOUNTS
    }

    uneven = build(open_issues({"a1": 4, "a2": 2, "a3": 2, "a4": 1, "a5": 1}))
    balances = {row["account_id"]: row["balance"] for row in uneven["workload"]}
    assert balances["a1"] == "Overloaded"
    assert balances["a2"] == "Within range"

    idle = build([])
    assert [row["balance"] for row in idle["workload"]] == ["Within range"] * 5

    done_only = [
        issue(f"DONE-{index}", account="a1", category="done", status="Done") for index in range(4)
    ]
    done_only.extend(open_issues({"a2": 4}))
    mixed = build(done_only)
    mixed_balances = {row["account_id"]: row["balance"] for row in mixed["workload"]}
    assert mixed_balances["a1"] == "Within range"
    assert mixed_balances["a2"] == "Overloaded"
    assert mixed["workload"][0]["open_issues"] == 0
    assert mixed["workload"][1]["open_issues"] == 4


def test_other_assignees_are_excluded_from_the_totals():
    report = build(
        [
            issue("IN", account="a1", points=2),
            issue("OUT", account="z9", points=8),
            issue("UNASSIGNED", account=None, points=4),
        ]
    )
    assert report["health"]["scope"] == 1
    assert report["health"]["scope_points"] == 2
    assert report["excluded_count"] == 2
    assert report["health"]["completion"] == 0


def test_missing_story_points_field_leaves_points_blank():
    report = build_report([issue("MIG-1", points=5)], sample(), ACTIVE)
    assert report["health"]["scope_points"] is None
    assert report["workload"][0]["remaining_points"] is None


def test_recorded_sprint_payload_matches_sheet_rows(tmp_path):
    payload = json.loads(FIXTURE.read_text())
    output = tmp_path / "nested" / "out"
    report = build_report(
        payload["issues"],
        sample(output_dir=str(output)),
        payload["sprint"],
        board=payload["board"],
        story_points_field=payload["story_points_field"],
        sprint_field=payload["sprint_field"],
        status_order=payload["status_order"],
        assignee_names={"a1": "Ada", "a2": "Ben", "a3": "Cy", "a4": "Dee", "a5": "Ed"},
        now=NOW,
    )
    assert report["health"] == {
        "scope": 5,
        "scope_points": 11,
        "done": 2,
        "done_points": 7,
        "remaining": 3,
        "remaining_points": 4,
        "spillover": 1,
        "completion": 40,
    }
    assert report["excluded_count"] == 2
    assert [(phase["key"], phase["summary"]) for phase in report["phases"]] == [
        ("MIG-100", "Schema cutover"),
        ("MIG-200", "Data move"),
        ("", "No phase"),
    ]
    path = write_workbook(report, sample(output_dir=str(output)))
    assert path.name == "sprint-health-2026-11-12.xlsx"
    assert output.is_dir()
    assert list(output.glob(".*.partial")) == []

    workbook = load_workbook(path)
    assert workbook.sheetnames == ["Cover", "Sprint health", "Migration phases", "Workload balance"]
    cover = labels(workbook["Cover"])
    assert cover["Jira site"] == ["https://example.atlassian.net"]
    assert cover["Project key"] == ["MIG"]
    assert cover["Board"] == ["Migration board"]
    assert cover["Sprint"] == ["Sprint 12"]
    assert cover["State"] == ["active"]
    assert cover["Start date"] == ["2026-11-02"]
    assert cover["End date"] == ["2026-11-13"]
    assert cover["Days remaining"] == [1]
    assert cover["Generated at"] == ["2026-11-12 08:00"]
    assert cover["Timezone"] == ["Asia/Kolkata"]
    assert cover["Assignees"] == ["Ada", "Ben", "Cy", "Dee", "Ed"]
    assert cover["Excluded issues"] == [2]

    health = workbook["Sprint health"]
    assert [health.cell(2, column).value for column in (1, 2, 3)] == ["Scope", 5, 11]
    assert [health.cell(3, column).value for column in (1, 2, 3)] == ["Done", 2, 7]
    assert [health.cell(4, column).value for column in (1, 2, 3)] == ["Remaining", 3, 4]
    assert [health.cell(5, column).value for column in (1, 2)] == ["Spillover", 1]
    assert health.cell(6, 1).value == "Completion"
    assert health.cell(6, 2).value == 0.4
    assert [health.cell(row, 1).value for row in (9, 10, 11)] == ["To Do", "In Progress", "Done"]
    assert [health.cell(row, 2).value for row in (9, 10, 11)] == [1, 2, 2]

    phases = workbook["Migration phases"]
    assert [phases.cell(2, column).value for column in range(1, 8)] == [
        "MIG-100", "Schema cutover", 2, 1, 1, 1, 0.5,
    ]
    assert [phases.cell(3, column).value for column in range(1, 7)] == [
        "MIG-200", "Data move", 1, 0, 1, 0,
    ]
    assert phases.cell(3, 7).value == 0
    assert phases.cell(4, 2).value == "No phase"
    assert [phases.cell(4, column).value for column in range(3, 8)] == [2, 1, 1, 0, 0.5]

    workload = workbook["Workload balance"]
    assert [workload.cell(row, 1).value for row in range(2, 7)] == ["Ada", "Ben", "Cy", "Dee", "Ed"]
    assert [workload.cell(row, 2).value for row in range(2, 7)] == [1, 1, 0, 1, 0]
    assert workload.cell(2, 3).value == 3
    assert workload.cell(3, 3).value is None
    assert workload.cell(5, 3).value == 1
    assert workload.cell(2, 4).value == pytest.approx(1 / 3)
    assert [workload.cell(row, 5).value for row in range(2, 7)] == [
        "Overloaded", "Overloaded", "Within range", "Overloaded", "Within range",
    ]
    workbook.close()

    empty = build_report([], sample(output_dir=str(output)), None, now=NOW)
    replaced = write_workbook(empty, sample(output_dir=str(output)))
    assert replaced == path
    assert list(output.glob("*.xlsx")) == [path]
    reread = load_workbook(path)
    assert reread["Sprint health"]["B2"].value == 0
    assert reread["Sprint health"]["B6"].value == 0
    assert any(cell.value == "There is no active sprint. Health totals are zero." for row in reread["Cover"] for cell in row)
    assert labels(reread["Cover"])["Sprint"] == ["No active sprint"]
    reread.close()


def test_file_date_uses_the_configured_timezone(tmp_path):
    moment = datetime(2026, 11, 12, 20, 0, tzinfo=ZoneInfo("UTC"))
    report = build_report([], sample(output_dir=str(tmp_path)), None, now=moment)
    path = write_workbook(report, sample(output_dir=str(tmp_path)))
    assert path.name == "sprint-health-2026-11-13.xlsx"


def test_no_active_sprint_exits_zero_and_logs_without_the_token(tmp_path, capsys):
    code = run(sample(output_dir=str(tmp_path), token=TOKEN), Stub(sprint=None))
    assert code == 0
    output = capsys.readouterr().out
    assert "sprint_id=none" in output
    assert "issues=0" in output
    assert TOKEN not in output
    workbook = load_workbook(next(tmp_path.glob("*.xlsx")))
    assert any(
        cell.value == "There is no active sprint. Health totals are zero."
        for row in workbook["Cover"]
        for cell in row
    )
    workbook.close()


def test_auth_failure_does_not_replace_a_finished_workbook(tmp_path):
    report = build_report([], sample(output_dir=str(tmp_path)), None, now=NOW)
    path = write_workbook(report, sample(output_dir=str(tmp_path)))
    before = path.read_bytes()

    class Boom:
        def board(self):
            raise SystemExit(1)

    with pytest.raises(SystemExit):
        run(sample(output_dir=str(tmp_path), token=TOKEN), Boom())
    assert path.read_bytes() == before


def test_sprint_choice_is_recorded_on_the_cover(tmp_path):
    sprint = {**ACTIVE, "selectionNote": "Several sprints are active (Older, Sprint 12); using Sprint 12 because it has the latest start date."}
    report = build_report([], sample(output_dir=str(tmp_path)), sprint, now=NOW)
    path = write_workbook(report, sample(output_dir=str(tmp_path)))
    workbook = load_workbook(path)
    assert "latest start date" in labels(workbook["Cover"])["Sprint selection"][0]
    workbook.close()


def sample(output_dir="./out", token="fixture") -> Config:
    return Config(
        jira_base_url="https://example.atlassian.net",
        jira_email="reporter@example.com",
        jira_api_token=token,
        jira_board_id="42",
        assignee_account_ids=ACCOUNTS,
        output_dir=output_dir,
        timezone="Asia/Kolkata",
        report_hour_local=8,
    )


def build(issues, sprint=None):
    return build_report(
        issues,
        sample(),
        ACTIVE if sprint is None else sprint,
        story_points_field=POINTS,
        sprint_field=SPRINT_FIELD,
    )


def issue(key, account="a1", category="indeterminate", status="In Progress", points=None, sprints=None, parent=None):
    fields = {
        "summary": key,
        "status": {"name": status, "statusCategory": {"key": category}},
    }
    if account is None:
        fields["assignee"] = None
    else:
        fields["assignee"] = {"accountId": account, "displayName": account}
    if parent is not None:
        fields["parent"] = parent
    if points is not None:
        fields[POINTS] = points
    if sprints is not None:
        fields[SPRINT_FIELD] = sprints
    return {"key": key, "fields": fields}


def open_issues(counts: dict[str, int]) -> list[dict]:
    issues = []
    for account, count in counts.items():
        issues.extend(issue(f"{account}-{index}", account=account) for index in range(count))
    return issues


def epic(key, summary):
    return {"key": key, "fields": {"summary": summary, "issuetype": {"name": "Epic"}}}


def story_under(key, summary):
    return {
        "key": "MIG-50",
        "fields": {
            "summary": "Story",
            "issuetype": {"name": "Story"},
            "parent": epic(key, summary),
        },
    }


def labels(sheet) -> dict[str, list]:
    found: dict[str, list] = {}
    current = None
    for row in range(1, sheet.max_row + 1):
        label = sheet.cell(row, 1).value
        value = sheet.cell(row, 2).value
        if label:
            current = label
            found.setdefault(current, [])
        if current is not None and value is not None and value != "":
            found[current].append(value)
    return found


class Stub:
    def __init__(self, sprint):
        self._sprint = sprint

    def board(self):
        return {"name": "Migration board", "project_key": "MIG"}

    def active_sprint(self):
        return self._sprint

    def sprint_issues(self, sprint_id):
        return []

    def story_points_field_id(self):
        return None

    def sprint_field_id(self):
        return None

    def status_order(self):
        return []

    def assignee_names(self):
        return {account: account for account in ACCOUNTS}
