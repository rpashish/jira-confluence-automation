"""Config loads the sprint health environment and stops before Jira when it is invalid."""

import pytest

from sprint_health.config import load_config

TOKEN = "super-secret-token"

REQUIRED = {
    "JIRA_BASE_URL": "https://example.atlassian.net/",
    "JIRA_EMAIL": "reporter@example.com",
    "JIRA_API_TOKEN": TOKEN,
    "JIRA_BOARD_ID": "42",
    "JIRA_ASSIGNEE_ACCOUNT_IDS": "a, b, c, d, e",
}


def test_defaults_and_five_assignees():
    config = load_config(REQUIRED)
    assert config.jira_base_url == "https://example.atlassian.net"
    assert config.jira_api_token == TOKEN
    assert config.assignee_account_ids == ("a", "b", "c", "d", "e")
    assert config.output_dir == "./out"
    assert config.timezone == "Asia/Kolkata"
    assert config.report_hour_local == 8


def test_optional_settings_override_defaults():
    config = load_config(
        {
            **REQUIRED,
            "REPORT_OUTPUT_DIR": "reports",
            "REPORT_TIMEZONE": "UTC",
            "REPORT_HOUR_LOCAL": "9",
        }
    )
    assert config.output_dir == "reports"
    assert config.timezone == "UTC"
    assert config.report_hour_local == 9


def test_missing_variable_exits_with_its_name_and_hides_the_token(capsys):
    environ = {**REQUIRED, "JIRA_BASE_URL": "  ", "JIRA_EMAIL": ""}
    with pytest.raises(SystemExit) as caught:
        load_config(environ)
    assert caught.value.code == 1
    error = capsys.readouterr().err
    assert "JIRA_BASE_URL" in error
    assert "JIRA_EMAIL" in error
    assert TOKEN not in error


def test_assignee_list_must_be_exactly_five_ids(capsys):
    for raw in ("a,b,c,d", "a,b,c,d,e,f", "a,b,c,d,", "a,b,c,d,e,e"):
        with pytest.raises(SystemExit) as caught:
            load_config({**REQUIRED, "JIRA_ASSIGNEE_ACCOUNT_IDS": raw})
        assert caught.value.code == 1
        error = capsys.readouterr().err
        assert "JIRA_ASSIGNEE_ACCOUNT_IDS" in error
        assert TOKEN not in error


def test_invalid_timezone_and_hour_exit(capsys):
    with pytest.raises(SystemExit) as timezone_error:
        load_config({**REQUIRED, "REPORT_TIMEZONE": "Not/AZone"})
    assert timezone_error.value.code == 1
    assert "REPORT_TIMEZONE" in capsys.readouterr().err

    with pytest.raises(SystemExit) as hour_error:
        load_config({**REQUIRED, "REPORT_HOUR_LOCAL": "noon"})
    assert hour_error.value.code == 1
    assert "REPORT_HOUR_LOCAL" in capsys.readouterr().err
