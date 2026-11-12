"""Jira client tests use a fake session and do not open a network connection."""

import pytest
import requests

from sprint_health.config import Config
from sprint_health.jira_client import JiraClient

TOKEN = "super-secret-token"


class Response:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._payload = {} if payload is None else payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []
        self.auth = None
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return self.handler(url, params, len(self.calls))


def config() -> Config:
    return Config(
        jira_base_url="https://example.atlassian.net",
        jira_email="reporter@example.com",
        jira_api_token=TOKEN,
        jira_board_id="42",
        assignee_account_ids=("a1", "a2", "a3", "a4", "a5"),
        output_dir="./out",
        timezone="Asia/Kolkata",
        report_hour_local=8,
    )


def test_active_sprint_pages_and_keeps_the_latest_start():
    def handler(url, params, _call):
        assert url.startswith("https://example.atlassian.net/rest/agile/1.0/board/42/sprint")
        if params["startAt"] == 0:
            return Response(
                200,
                {
                    "isLast": False,
                    "startAt": 0,
                    "values": [
                        {
                            "id": 1,
                            "name": "Older",
                            "state": "active",
                            "startDate": "2026-10-01T00:00:00.000Z",
                        }
                    ],
                },
            )
        return Response(
            200,
            {
                "isLast": True,
                "startAt": 1,
                "values": [
                    {
                        "id": 2,
                        "name": "Newer",
                        "state": "active",
                        "startDate": "2026-10-15T00:00:00.000Z",
                    }
                ],
            },
        )

    session = FakeSession(handler)
    client = JiraClient(config(), session=session, sleeper=lambda _delay: None)
    chosen = client.active_sprint()
    assert session.auth == ("reporter@example.com", TOKEN)
    assert chosen["id"] == 2
    assert "Newer" in chosen["selectionNote"]
    assert "latest start date" in chosen["selectionNote"]
    assert "Older" in chosen["selectionNote"]


def test_sprint_issues_page_until_total_and_follow_one_parent_hop():
    def handler(url, params, _call):
        if url.endswith("/field"):
            return Response(
                200,
                [
                    {"id": "customfield_10016", "name": "Story Points"},
                    {
                        "id": "customfield_10020",
                        "name": "Sprint",
                        "schema": {"custom": "com.pyxis.greenhopper.jira:gh-sprint"},
                    },
                ],
            )
        if url.endswith("/sprint/20/issue"):
            assert params["fields"] == (
                "summary,status,assignee,parent,customfield_10020,customfield_10016"
            )
            if params["startAt"] == 0:
                return Response(
                    200,
                    {
                        "total": 2,
                        "issues": [
                            {
                                "key": "MIG-9",
                                "fields": {
                                    "summary": "Subtask",
                                    "parent": {
                                        "key": "MIG-8",
                                        "fields": {
                                            "summary": "Story",
                                            "issuetype": {"name": "Story"},
                                        },
                                    },
                                },
                            }
                        ],
                    },
                )
            assert params["startAt"] == 1
            return Response(
                200,
                {"total": 2, "issues": [{"key": "MIG-1", "fields": {"summary": "First"}}]},
            )
        if url.endswith("/issue/MIG-8"):
            return Response(
                200,
                {
                    "key": "MIG-8",
                    "fields": {
                        "summary": "Story",
                        "issuetype": {"name": "Story"},
                        "parent": {
                            "key": "MIG-100",
                            "fields": {
                                "summary": "Schema cutover",
                                "issuetype": {"name": "Epic"},
                            },
                        },
                    },
                },
            )
        raise AssertionError(url)

    client = JiraClient(config(), session=FakeSession(handler), sleeper=lambda _delay: None)
    issues = client.sprint_issues(20)
    assert [issue["key"] for issue in issues] == ["MIG-9", "MIG-1"]
    parent = issues[0]["fields"]["parent"]["fields"]["parent"]
    assert parent["key"] == "MIG-100"
    assert client.story_points_field_id() == "customfield_10016"
    assert client.sprint_field_id() == "customfield_10020"


def test_missing_story_points_field_is_left_out_of_the_request():
    def handler(url, params, _call):
        if url.endswith("/field"):
            return Response(200, [{"id": "customfield_10020", "name": "Sprint"}])
        assert "customfield_10016" not in params["fields"]
        assert params["fields"].startswith("summary,status,assignee,parent")
        return Response(200, {"total": 0, "issues": []})

    client = JiraClient(config(), session=FakeSession(handler), sleeper=lambda _delay: None)
    assert client.sprint_issues(20) == []
    assert client.story_points_field_id() is None


def test_status_order_follows_board_columns():
    def handler(url, _params, _call):
        if url.endswith("/configuration"):
            return Response(
                200,
                {
                    "columnConfig": {
                        "columns": [
                            {"statuses": [{"id": "10"}]},
                            {"statuses": [{"id": "20"}]},
                        ]
                    }
                },
            )
        if url.endswith("/status"):
            return Response(
                200,
                [
                    {"id": "20", "name": "Done"},
                    {"id": "10", "name": "To Do"},
                ],
            )
        raise AssertionError(url)

    client = JiraClient(config(), session=FakeSession(handler), sleeper=lambda _delay: None)
    assert client.status_order() == ["To Do", "Done"]


@pytest.mark.parametrize("status", [401, 403])
def test_auth_failure_exits_without_the_token(status, capsys):
    session = FakeSession(lambda _url, _params, _call: Response(status, {"error": TOKEN}))
    client = JiraClient(config(), session=session, sleeper=lambda _delay: None)
    with pytest.raises(SystemExit) as caught:
        client.board()
    assert caught.value.code == 1
    error = capsys.readouterr().err
    assert f"HTTP {status}" in error
    assert TOKEN not in error
    assert len(session.calls) == 1


def test_board_404_names_the_board_id(capsys):
    session = FakeSession(lambda _url, _params, _call: Response(404, {}))
    client = JiraClient(config(), session=session, sleeper=lambda _delay: None)
    with pytest.raises(SystemExit) as caught:
        client.board()
    assert caught.value.code == 1
    error = capsys.readouterr().err
    assert "HTTP 404 for board 42" in error
    assert TOKEN not in error


def test_retries_server_errors_then_succeeds():
    delays = []

    def handler(_url, _params, call):
        if call < 4:
            return Response(503, {})
        return Response(200, {"id": 42, "name": "Migration", "location": {"projectKey": "MIG"}})

    session = FakeSession(handler)
    client = JiraClient(config(), session=session, sleeper=delays.append)
    assert client.board()["project_key"] == "MIG"
    assert delays == [0.5, 1.0, 2.0]
    assert len(session.calls) == 4


def test_retries_network_errors_then_exits(capsys):
    class DownSession(FakeSession):
        def get(self, url, params=None, timeout=None):
            self.calls.append(url)
            raise requests.ConnectionError(f"down {TOKEN}")

    session = DownSession(lambda *_args: None)
    client = JiraClient(config(), session=session, sleeper=lambda _delay: None)
    with pytest.raises(SystemExit) as caught:
        client.board()
    assert caught.value.code == 1
    error = capsys.readouterr().err
    assert "Jira request failed for /rest/agile/1.0/board/42" in error
    assert TOKEN not in error
    assert len(session.calls) == 4
