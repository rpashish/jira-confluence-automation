"""Wire config, Jira, the report, and the Excel writer."""

from sprint_health.config import Config, load_config
from sprint_health.excel_writer import write_workbook
from sprint_health.jira_client import JiraClient
from sprint_health.report import build_report


def run(config: Config, client: JiraClient) -> int:
    """Build one workbook. Returns 0 after a complete file is in place."""
    board = client.board()
    sprint = client.active_sprint()
    if sprint is None:
        issues: list[dict] = []
        story_points_field = None
        sprint_field = None
        status_order: list[str] = []
    else:
        issues = client.sprint_issues(sprint["id"])
        story_points_field = client.story_points_field_id()
        sprint_field = client.sprint_field_id()
        status_order = client.status_order()
    report = build_report(
        issues,
        config,
        sprint,
        board=board,
        story_points_field=story_points_field,
        sprint_field=sprint_field,
        status_order=status_order,
        assignee_names=client.assignee_names(),
    )
    path = write_workbook(report, config)
    sprint_id = sprint.get("id") if sprint else "none"
    print(f"sprint_id={sprint_id} issues={report['issue_count']} output={path}")
    return 0


def main() -> int:
    """Run one sprint health report and return a process exit code."""
    config = load_config()
    return run(config, JiraClient(config))


if __name__ == "__main__":
    raise SystemExit(main())
