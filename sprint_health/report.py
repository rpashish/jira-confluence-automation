"""Turn sprint issues into health, phase, and workload rows."""

from datetime import datetime
from zoneinfo import ZoneInfo

from sprint_health.config import Config

OVERLOADED = "Overloaded"
WITHIN_RANGE = "Within range"
NO_PHASE = "No phase"
REPORT_TITLE = "Sprint health — database migration"


def build_report(
    issues: list[dict],
    config: Config,
    sprint: dict | None,
    *,
    board: dict | None = None,
    story_points_field: str | None = None,
    sprint_field: str | None = None,
    status_order: list[str] | None = None,
    assignee_names: dict[str, str] | None = None,
    now: datetime | None = None,
) -> dict:
    """Filter to the configured assignees and compute every report section.

    Issues assigned to anyone else are counted only as exclusions. With no
    active sprint, totals stay at zero and completion is 0%.
    """
    generated_at = _in_timezone(now or datetime.now(ZoneInfo(config.timezone)), config)
    board_info = board or {}
    if sprint is None:
        in_scope: list[dict] = []
        excluded = 0
    else:
        in_scope, excluded = _split_assignees(issues, config)

    rows = [
        _view(issue, sprint, story_points_field, sprint_field) for issue in in_scope
    ]
    people = _people(in_scope, config, assignee_names)
    return {
        "title": REPORT_TITLE,
        "site": config.jira_base_url,
        "project_key": board_info.get("project_key") or "",
        "board_name": board_info.get("name") or "",
        "board_id": config.jira_board_id,
        "sprint": _sprint_info(sprint, generated_at) if sprint else None,
        "no_active_sprint": sprint is None,
        "generated_at": generated_at,
        "timezone": config.timezone,
        "assignees": people,
        "health": _health(rows),
        "statuses": _statuses(rows, status_order or []),
        "phases": _phases(rows),
        "workload": _workload(rows, people),
        "excluded_count": excluded,
        "issue_count": len(rows),
    }


def _split_assignees(issues: list[dict], config: Config) -> tuple[list[dict], int]:
    allowed = set(config.assignee_account_ids)
    in_scope = []
    excluded = 0
    for issue in issues:
        account_id = _account_id(issue)
        if account_id in allowed:
            in_scope.append(issue)
        else:
            excluded += 1
    return in_scope, excluded


def _view(
    issue: dict,
    sprint: dict | None,
    story_points_field: str | None,
    sprint_field: str | None,
) -> dict:
    fields = issue.get("fields") or {}
    status = fields.get("status") or {}
    category = ((status.get("statusCategory") or {}).get("key") or "").lower()
    sprints = _sprint_values(fields, sprint_field)
    epic_key, epic_summary = _epic(fields)
    return {
        "status_name": status.get("name") or "Unknown",
        "done": category == "done",
        "account_id": _account_id(issue),
        "points": _points(fields, story_points_field),
        "spillover": bool(sprint) and _is_spillover(sprints, sprint),
        "epic_key": epic_key,
        "epic_summary": epic_summary,
    }


def _account_id(issue: dict) -> str | None:
    assignee = (issue.get("fields") or {}).get("assignee") or {}
    if not isinstance(assignee, dict):
        return None
    return assignee.get("accountId")


def _points(fields: dict, story_points_field: str | None) -> float | None:
    if not story_points_field:
        return None
    value = fields.get(story_points_field)
    if isinstance(value, bool) or value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _sum_points(values) -> float | None:
    numbers = [value for value in values if value is not None]
    if not numbers:
        return None
    return float(sum(numbers))


def _sprint_values(fields: dict, sprint_field: str | None) -> list[dict]:
    raw = fields.get(sprint_field) if sprint_field else fields.get("sprint")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _is_spillover(sprints: list[dict], active: dict) -> bool:
    """True when the issue is on this sprint and at least one earlier sprint."""
    if len(sprints) < 2:
        return False
    if not any(_same_id(item.get("id"), active.get("id")) for item in sprints):
        return False
    return any(_is_earlier(item, active) for item in sprints)


def _is_earlier(other: dict, active: dict) -> bool:
    if _same_id(other.get("id"), active.get("id")):
        return False
    active_start = _parse_datetime(active.get("startDate"))
    other_start = _parse_datetime(other.get("startDate"))
    if active_start is not None and other_start is not None:
        return other_start < active_start
    return (other.get("state") or "").lower() in {"closed", "completed"}


def _same_id(left, right) -> bool:
    if left is None or right is None:
        return False
    return str(left) == str(right)


def _epic(fields: dict) -> tuple[str | None, str | None]:
    """Use the parent epic, or the epic one hop above a story parent."""
    parent = fields.get("parent")
    if not isinstance(parent, dict):
        return None, None
    if _is_epic(parent):
        return _epic_identity(parent)
    grandparent = (parent.get("fields") or {}).get("parent")
    if isinstance(grandparent, dict) and _is_epic(grandparent):
        return _epic_identity(grandparent)
    return None, None


def _is_epic(node: dict) -> bool:
    name = (((node.get("fields") or {}).get("issuetype") or {}).get("name") or "")
    return name.lower() == "epic"


def _epic_identity(node: dict) -> tuple[str | None, str | None]:
    key = node.get("key")
    if not key:
        return None, None
    summary = (node.get("fields") or {}).get("summary") or ""
    return key, summary


def _health(rows: list[dict]) -> dict:
    scope = len(rows)
    done_rows = [row for row in rows if row["done"]]
    open_rows = [row for row in rows if not row["done"]]
    done = len(done_rows)
    return {
        "scope": scope,
        "scope_points": _sum_points(row["points"] for row in rows),
        "done": done,
        "done_points": _sum_points(row["points"] for row in done_rows),
        "remaining": scope - done,
        "remaining_points": _sum_points(row["points"] for row in open_rows),
        "spillover": sum(1 for row in rows if row["spillover"]),
        "completion": 0.0 if scope == 0 else (done / scope) * 100,
    }


def _statuses(rows: list[dict], status_order: list[str]) -> list[dict]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status_name"]] = counts.get(row["status_name"], 0) + 1
    rank = {name: index for index, name in enumerate(status_order)}
    names = sorted(counts, key=lambda name: (0, rank[name]) if name in rank else (1, name))
    return [{"name": name, "count": counts[name]} for name in names]


def _phases(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    summaries: dict[str, str] = {}
    for row in rows:
        key = row["epic_key"] or ""
        grouped.setdefault(key, []).append(row)
        if key and key not in summaries:
            summaries[key] = row["epic_summary"] or ""
    epic_keys = sorted(key for key in grouped if key)
    ordered = epic_keys + ([""] if "" in grouped else [])
    phases = []
    for key in ordered:
        members = grouped[key]
        scope = len(members)
        done = sum(1 for member in members if member["done"])
        phases.append(
            {
                "key": key,
                "summary": NO_PHASE if key == "" else summaries.get(key, ""),
                "scope": scope,
                "done": done,
                "remaining": scope - done,
                "spillover": sum(1 for member in members if member["spillover"]),
                "completion": 0.0 if scope == 0 else (done / scope) * 100,
            }
        )
    return phases


def _people(
    issues: list[dict],
    config: Config,
    assignee_names: dict[str, str] | None,
) -> list[dict]:
    found = {}
    for issue in issues:
        assignee = (issue.get("fields") or {}).get("assignee") or {}
        account_id = assignee.get("accountId") if isinstance(assignee, dict) else None
        display_name = assignee.get("displayName") if isinstance(assignee, dict) else None
        if account_id and display_name:
            found[account_id] = display_name
    overrides = assignee_names or {}
    return [
        {
            "account_id": account_id,
            "display_name": overrides.get(account_id) or found.get(account_id) or account_id,
        }
        for account_id in config.assignee_account_ids
    ]


def _workload(rows: list[dict], people: list[dict]) -> list[dict]:
    open_by_account: dict[str, list[dict]] = {}
    for row in rows:
        if row["done"]:
            continue
        open_by_account.setdefault(row["account_id"], []).append(row)
    counts = [len(open_by_account.get(person["account_id"], [])) for person in people]
    total_open = sum(counts)
    mean = (total_open / len(people)) if people else 0
    threshold = 1.5 * mean
    workload = []
    for person, count in zip(people, counts, strict=True):
        open_rows = open_by_account.get(person["account_id"], [])
        if total_open == 0:
            balance = WITHIN_RANGE
            share = 0.0
        else:
            balance = OVERLOADED if count > threshold else WITHIN_RANGE
            share = count / total_open
        workload.append(
            {
                "account_id": person["account_id"],
                "display_name": person["display_name"],
                "open_issues": count,
                "remaining_points": _sum_points(row["points"] for row in open_rows),
                "share": share,
                "balance": balance,
            }
        )
    return workload


def _sprint_info(sprint: dict, now: datetime) -> dict:
    return {
        "id": sprint.get("id"),
        "name": sprint.get("name") or "",
        "state": sprint.get("state") or "",
        "start_date": _format_date(sprint.get("startDate"), now),
        "end_date": _format_date(sprint.get("endDate"), now),
        "days_remaining": _days_remaining(sprint.get("endDate"), now),
        "selection_note": sprint.get("selectionNote"),
    }


def _days_remaining(end_date: str | None, now: datetime) -> int | None:
    parsed = _parse_datetime(end_date)
    if parsed is None:
        return None
    end_day = parsed.astimezone(now.tzinfo).date()
    return max(0, (end_day - now.date()).days)


def _format_date(value: str | None, now: datetime) -> str | None:
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    return parsed.astimezone(now.tzinfo).date().isoformat()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _in_timezone(moment: datetime, config: Config) -> datetime:
    zone = ZoneInfo(config.timezone)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=zone)
    return moment.astimezone(zone)
