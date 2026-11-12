"""Authenticated Jira Cloud reads: board, active sprint, issues, and fields."""

import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests

from sprint_health.config import Config

_SPRINT_FIELD_TYPE = "com.pyxis.greenhopper.jira:gh-sprint"
_ATTEMPTS = 4
_PAGE_SIZE = 50


class JiraClient:
    """HTTP Basic client for one Jira Cloud site.

    Network errors and HTTP 5xx are retried up to three times. HTTP 401 and
    403 stop the run without printing the API token.
    """

    def __init__(self, config: Config, session=None, sleeper=time.sleep) -> None:
        self._config = config
        self._session = session or requests.Session()
        self._session.auth = (config.jira_email, config.jira_api_token)
        self._session.headers["Accept"] = "application/json"
        self._sleeper = sleeper
        self._fields_loaded = False
        self._story_points_field: str | None = None
        self._sprint_field: str | None = None

    def board(self) -> dict:
        """Return the board name and project key."""
        payload = self._get(self._board_path())
        location = payload.get("location") or {}
        return {
            "id": payload.get("id"),
            "name": payload.get("name") or "",
            "project_key": location.get("projectKey") or "",
        }

    def active_sprint(self) -> dict | None:
        """Return the active sprint, or None when the board has none.

        When several sprints are active, this is the one with the latest
        start date. `selectionNote` records that choice.
        """
        sprints: list[dict] = []
        start = 0
        while True:
            page = self._get(
                f"{self._board_path()}/sprint",
                {"state": "active", "startAt": start, "maxResults": _PAGE_SIZE},
            )
            values = page.get("values") or []
            sprints.extend(item for item in values if isinstance(item, dict))
            next_start = page.get("startAt", start) + len(values)
            if page.get("isLast", True) or not values or next_start <= start:
                break
            total = page.get("total")
            if total is not None and next_start >= total:
                break
            start = next_start
        if not sprints:
            return None
        chosen = dict(max(sprints, key=_start_sort_key))
        if len(sprints) > 1:
            names = ", ".join(
                sprint.get("name") or str(sprint.get("id")) for sprint in sprints
            )
            chosen["selectionNote"] = (
                f"Several sprints are active ({names}); "
                f"using {chosen.get('name')} because it has the latest start date."
            )
        return chosen

    def sprint_issues(self, sprint_id: int) -> list[dict]:
        """Page the sprint until `total` is exhausted and resolve parent epics."""
        issues: list[dict] = []
        start = 0
        while True:
            page = self._get(
                f"/rest/agile/1.0/sprint/{sprint_id}/issue",
                {
                    "startAt": start,
                    "maxResults": _PAGE_SIZE,
                    "fields": self._issue_fields(),
                },
            )
            batch = page.get("issues") or []
            issues.extend(item for item in batch if isinstance(item, dict))
            total = page.get("total")
            start += len(batch)
            if not batch or total is None or start >= total:
                break
        return self._attach_parent_epics(issues)

    def story_points_field_id(self) -> str | None:
        """Return the Story Points field id, or None when the site has none."""
        self._load_fields()
        return self._story_points_field

    def sprint_field_id(self) -> str | None:
        self._load_fields()
        return self._sprint_field

    def status_order(self) -> list[str]:
        """Board column order, left to right. Empty when Jira omits it."""
        payload = self._get(f"{self._board_path()}/configuration", missing_ok=True)
        if not isinstance(payload, dict):
            return []
        columns = (payload.get("columnConfig") or {}).get("columns") or []
        ordered: list[str | tuple[str, str]] = []
        needs_lookup = False
        for column in columns:
            for status in column.get("statuses") or []:
                name = status.get("name")
                if name:
                    ordered.append(name)
                elif status.get("id") is not None:
                    needs_lookup = True
                    ordered.append(("id", str(status.get("id"))))
        if needs_lookup:
            catalog = self._get("/rest/api/3/status", missing_ok=True)
            if not isinstance(catalog, list):
                catalog = []
            by_id = {
                str(item.get("id")): item.get("name")
                for item in catalog
                if isinstance(item, dict) and item.get("name")
            }
            resolved = []
            for item in ordered:
                if isinstance(item, tuple):
                    name = by_id.get(item[1])
                    if name:
                        resolved.append(name)
                else:
                    resolved.append(item)
            ordered = resolved
        seen: set[str] = set()
        names: list[str] = []
        for name in ordered:
            if isinstance(name, str) and name not in seen:
                seen.add(name)
                names.append(name)
        return names

    def assignee_names(self) -> dict[str, str]:
        """Display name for each configured account. Falls back to the id."""
        names = {}
        for account_id in self._config.assignee_account_ids:
            payload = self._get(
                "/rest/api/3/user",
                {"accountId": account_id},
                missing_ok=True,
            )
            display = payload.get("displayName") if isinstance(payload, dict) else None
            names[account_id] = display or account_id
        return names

    def _issue_fields(self) -> str:
        self._load_fields()
        fields = ["summary", "status", "assignee", "parent"]
        if self._sprint_field:
            fields.append(self._sprint_field)
        if self._story_points_field:
            fields.append(self._story_points_field)
        return ",".join(fields)

    def _load_fields(self) -> None:
        if self._fields_loaded:
            return
        payload = self._get("/rest/api/3/field")
        fields = payload if isinstance(payload, list) else []
        sprint_id = None
        for field in fields:
            custom = ((field.get("schema") or {}).get("custom") or "")
            if custom == _SPRINT_FIELD_TYPE:
                sprint_id = field.get("id")
                break
        if sprint_id is None:
            for field in fields:
                if field.get("name") == "Sprint":
                    sprint_id = field.get("id")
                    break
        story_id = None
        for field in fields:
            if field.get("name") == "Story Points":
                story_id = field.get("id")
                break
        self._sprint_field = sprint_id
        self._story_points_field = story_id
        self._fields_loaded = True

    def _attach_parent_epics(self, issues: list[dict]) -> list[dict]:
        """Follow one parent hop when the immediate parent is not an epic."""
        cache: dict[str, dict | None] = {}
        for issue in issues:
            fields = issue.get("fields")
            if not isinstance(fields, dict):
                fields = {}
                issue["fields"] = fields
            parent = fields.get("parent")
            if not isinstance(parent, dict) or _is_epic(parent):
                continue
            key = parent.get("key")
            if not key:
                continue
            if key not in cache:
                cache[key] = self._get(
                    f"/rest/api/3/issue/{quote(str(key), safe='')}",
                    {"fields": "summary,issuetype,parent"},
                    missing_ok=True,
                )
            fetched = cache[key] if isinstance(cache[key], dict) else {}
            fetched_fields = fetched.get("fields") or {}
            parent_fields = parent.setdefault("fields", {})
            if not parent_fields.get("issuetype") and fetched_fields.get("issuetype"):
                parent_fields["issuetype"] = fetched_fields["issuetype"]
            if not parent_fields.get("summary") and fetched_fields.get("summary"):
                parent_fields["summary"] = fetched_fields["summary"]
            grandparent = fetched_fields.get("parent")
            if isinstance(grandparent, dict):
                parent_fields["parent"] = grandparent
        return issues

    def _board_path(self) -> str:
        return f"/rest/agile/1.0/board/{self._config.jira_board_id}"

    def _get(self, path: str, params: dict | None = None, *, missing_ok: bool = False):
        url = f"{self._config.jira_base_url}{path}"
        for attempt in range(_ATTEMPTS):
            try:
                response = self._session.get(url, params=params, timeout=30)
            except requests.RequestException:
                if attempt < _ATTEMPTS - 1:
                    self._sleeper(0.5 * (2**attempt))
                    continue
                print(f"Jira request failed for {path}", file=sys.stderr)
                raise SystemExit(1)
            status = response.status_code
            if status in (401, 403):
                print(f"HTTP {status}", file=sys.stderr)
                raise SystemExit(1)
            if status == 404:
                if missing_ok:
                    return None
                print(_missing_message(path, self._config.jira_board_id), file=sys.stderr)
                raise SystemExit(1)
            if 500 <= status <= 599:
                if attempt < _ATTEMPTS - 1:
                    self._sleeper(0.5 * (2**attempt))
                    continue
                print(f"HTTP {status}", file=sys.stderr)
                raise SystemExit(1)
            if status >= 400:
                print(f"HTTP {status}", file=sys.stderr)
                raise SystemExit(1)
            try:
                return response.json()
            except ValueError:
                print(f"Jira request failed for {path}", file=sys.stderr)
                raise SystemExit(1)
        print(f"Jira request failed for {path}", file=sys.stderr)
        raise SystemExit(1)


def _start_sort_key(sprint: dict) -> tuple:
    parsed = _parse_datetime(sprint.get("startDate"))
    if parsed is None:
        return (0, "")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (1, parsed.astimezone(timezone.utc))


def _parse_datetime(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_epic(node: dict) -> bool:
    name = (((node.get("fields") or {}).get("issuetype") or {}).get("name") or "")
    return name.lower() == "epic"


def _missing_message(path: str, board_id: str) -> str:
    if path.startswith(f"/rest/agile/1.0/board/{board_id}"):
        return f"HTTP 404 for board {board_id}"
    return "HTTP 404"
