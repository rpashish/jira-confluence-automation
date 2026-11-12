"""Write the sprint health workbook."""

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from sprint_health.config import Config

_TITLE_FONT = Font(name="Calibri", size=16, bold=True, color="1F4E79")
_LABEL_FONT = Font(name="Calibri", size=11, bold=True, color="1F4E79")
_HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
_BODY_FONT = Font(name="Calibri", size=11)
_NO_SPRINT = "There is no active sprint. Health totals are zero."
_EXCLUSION = (
    "Active-sprint issues assigned outside the five accounts are excluded "
    "from scope, phase, and workload totals."
)


def write_workbook(report: dict, config: Config) -> Path:
    """Write sprint-health-YYYY-MM-DD.xlsx and return its path.

    The workbook is saved to a temporary file in the output directory and
    replaces that day's file only after the save finishes.
    """
    directory = Path(config.output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    generated = _generated_at(report, config)
    final = directory / f"sprint-health-{generated.date().isoformat()}.xlsx"
    temporary = directory / f".{final.name}.{os.getpid()}.partial"
    workbook = Workbook()
    _write_cover(workbook.active, report, generated)
    _write_health(workbook.create_sheet("Sprint health"), report)
    _write_phases(workbook.create_sheet("Migration phases"), report)
    _write_workload(workbook.create_sheet("Workload balance"), report)
    try:
        workbook.save(temporary)
        os.replace(temporary, final)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    finally:
        workbook.close()
    return final


def _write_cover(sheet, report: dict, generated: datetime) -> None:
    sheet.title = "Cover"
    sheet["A1"] = report["title"]
    sheet["A1"].font = _TITLE_FONT
    sheet.merge_cells("A1:B1")
    sprint = report.get("sprint") or {}
    rows = [
        ("Jira site", report["site"]),
        ("Project key", report["project_key"]),
        ("Board", report["board_name"]),
        ("Sprint", "No active sprint" if report["no_active_sprint"] else sprint.get("name") or ""),
        ("State", sprint.get("state") or ""),
        ("Start date", sprint.get("start_date") or ""),
        ("End date", sprint.get("end_date") or ""),
        ("Days remaining", "" if sprint.get("days_remaining") is None else sprint.get("days_remaining")),
        ("Sprint selection", sprint.get("selection_note") or ""),
        ("Generated at", generated.strftime("%Y-%m-%d %H:%M")),
        ("Timezone", report["timezone"]),
    ]
    for offset, (label, value) in enumerate(rows, start=3):
        _label(sheet.cell(offset, 1), label)
        _body(sheet.cell(offset, 2), value)
    row = 3 + len(rows)
    _label(sheet.cell(row, 1), "Assignees")
    for person in report["assignees"]:
        _body(sheet.cell(row, 2), person["display_name"])
        row += 1
    row += 1
    _label(sheet.cell(row, 1), "Excluded issues")
    _body(sheet.cell(row, 2), report["excluded_count"])
    row += 1
    _body(sheet.cell(row, 1), _EXCLUSION)
    sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    sheet.cell(row, 1).alignment = Alignment(wrap_text=True)
    sheet.row_dimensions[row].height = 32
    if report["no_active_sprint"]:
        row += 1
        _body(sheet.cell(row, 1), _NO_SPRINT)
        sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 1
    sheet.sheet_properties.pageSetUpPr.fitToPage = True


def _write_health(sheet, report: dict) -> None:
    health = report["health"]
    _table_header(sheet, ("Metric", "Issues", "Story points"))
    metrics = (
        ("Scope", health["scope"], health["scope_points"]),
        ("Done", health["done"], health["done_points"]),
        ("Remaining", health["remaining"], health["remaining_points"]),
        ("Spillover", health["spillover"], None),
    )
    for index, (metric, count, points) in enumerate(metrics, start=2):
        _body(sheet.cell(index, 1), metric)
        _body(sheet.cell(index, 2), count)
        _write_points(sheet.cell(index, 3), points)
    _body(sheet.cell(6, 1), "Completion")
    _percent(sheet.cell(6, 2), health["completion"])
    _table_header(sheet, ("Status", "Issues"), row=8)
    for index, status in enumerate(report["statuses"], start=9):
        _body(sheet.cell(index, 1), status["name"])
        _body(sheet.cell(index, 2), status["count"])
    _widths(sheet, (22, 16, 18))
    _print_table(sheet)


def _write_phases(sheet, report: dict) -> None:
    headers = ("Epic key", "Epic summary", "Scope", "Done", "Remaining", "Spillover", "Completion")
    _table_header(sheet, headers)
    for index, phase in enumerate(report["phases"], start=2):
        _body(sheet.cell(index, 1), phase["key"])
        _body(sheet.cell(index, 2), phase["summary"])
        _body(sheet.cell(index, 3), phase["scope"])
        _body(sheet.cell(index, 4), phase["done"])
        _body(sheet.cell(index, 5), phase["remaining"])
        _body(sheet.cell(index, 6), phase["spillover"])
        _percent(sheet.cell(index, 7), phase["completion"])
    _widths(sheet, (16, 36, 12, 12, 14, 14, 14))
    _print_table(sheet)


def _write_workload(sheet, report: dict) -> None:
    headers = (
        "Assignee",
        "Open issues",
        "Remaining points",
        "Share of open work",
        "Balance",
    )
    _table_header(sheet, headers)
    for index, person in enumerate(report["workload"], start=2):
        _body(sheet.cell(index, 1), person["display_name"])
        _body(sheet.cell(index, 2), person["open_issues"])
        _write_points(sheet.cell(index, 3), person["remaining_points"])
        _percent(sheet.cell(index, 4), person["share"] * 100)
        _body(sheet.cell(index, 5), person["balance"])
    _widths(sheet, (24, 16, 20, 22, 18))
    _print_table(sheet)


def _table_header(sheet, titles: tuple[str, ...], row: int = 1) -> None:
    for column, title in enumerate(titles, start=1):
        cell = sheet.cell(row, column, title)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="left")
    if row == 1:
        sheet.freeze_panes = "A2"
        sheet.row_dimensions[1].height = 20


def _label(cell, value) -> None:
    cell.value = value
    cell.font = _LABEL_FONT


def _body(cell, value) -> None:
    cell.value = value
    cell.font = _BODY_FONT


def _percent(cell, percentage: float) -> None:
    cell.value = percentage / 100
    cell.number_format = "0%"
    cell.font = _BODY_FONT


def _write_points(cell, value: float | None) -> None:
    cell.font = _BODY_FONT
    if value is None:
        cell.value = None
        return
    number = float(value)
    cell.value = int(number) if number.is_integer() else number


def _widths(sheet, widths: tuple[int, ...]) -> None:
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[_column(index)].width = width


def _print_table(sheet) -> None:
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 1
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.horizontalCentered = True
    sheet.page_margins.left = 0.5
    sheet.page_margins.right = 0.5
    sheet.oddHeader.left.text = "Sprint health — database migration"
    sheet.oddFooter.right.text = "Page &P of &N"


def _column(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _generated_at(report: dict, config: Config) -> datetime:
    generated = report["generated_at"]
    zone = ZoneInfo(config.timezone)
    if generated.tzinfo is None:
        return generated.replace(tzinfo=zone)
    return generated.astimezone(zone)
