"""Load and validate environment variables for a sprint health run."""

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

REQUIRED_VARIABLES = (
    "JIRA_BASE_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_BOARD_ID",
    "JIRA_ASSIGNEE_ACCOUNT_IDS",
)
ASSIGNEE_COUNT = 5


@dataclass(frozen=True)
class Config:
    """Site, credentials, board, assignees, and local report settings."""

    jira_base_url: str
    jira_email: str
    jira_api_token: str
    jira_board_id: str
    assignee_account_ids: tuple[str, ...]
    output_dir: str
    timezone: str
    report_hour_local: int


def load_config(environ: Mapping[str, str] | None = None) -> Config:
    """Read configuration from the environment and exit 1 when it is invalid.

    A passed mapping is used as-is so tests do not touch the process environment.
    The command loads `.env` from the project root without overriding variables
    that are already set.
    """
    if environ is None:
        load_dotenv(_project_root() / ".env")
        environ = os.environ

    missing = [name for name in REQUIRED_VARIABLES if not _text(environ, name)]
    if missing:
        for name in missing:
            print(name, file=sys.stderr)
        raise SystemExit(1)

    account_ids = tuple(
        part.strip() for part in environ["JIRA_ASSIGNEE_ACCOUNT_IDS"].split(",")
    )
    if (
        len(account_ids) != ASSIGNEE_COUNT
        or any(not account_id for account_id in account_ids)
        or len(set(account_ids)) != ASSIGNEE_COUNT
    ):
        print("JIRA_ASSIGNEE_ACCOUNT_IDS", file=sys.stderr)
        raise SystemExit(1)

    timezone = _text(environ, "REPORT_TIMEZONE") or "Asia/Kolkata"
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        print("REPORT_TIMEZONE", file=sys.stderr)
        raise SystemExit(1)

    hour_text = _text(environ, "REPORT_HOUR_LOCAL") or "8"
    try:
        hour = int(hour_text)
    except ValueError:
        print("REPORT_HOUR_LOCAL", file=sys.stderr)
        raise SystemExit(1)
    if not 0 <= hour <= 23:
        print("REPORT_HOUR_LOCAL", file=sys.stderr)
        raise SystemExit(1)

    return Config(
        jira_base_url=_text(environ, "JIRA_BASE_URL").rstrip("/"),
        jira_email=_text(environ, "JIRA_EMAIL"),
        jira_api_token=_text(environ, "JIRA_API_TOKEN"),
        jira_board_id=_text(environ, "JIRA_BOARD_ID"),
        assignee_account_ids=account_ids,
        output_dir=_text(environ, "REPORT_OUTPUT_DIR") or "./out",
        timezone=timezone,
        report_hour_local=hour,
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _text(environ: Mapping[str, str], name: str) -> str:
    return (environ.get(name) or "").strip()
