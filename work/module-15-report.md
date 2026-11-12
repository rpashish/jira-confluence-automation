# Module 15 Completion Report

## Script Metadata
- Filename: tools/process_walkthrough.py
- Language: Python
- Purpose: Finds every `walkthrough.md` under a root directory, checks each file on its own against `validation-rules.md` (VR-1 through VR-6), and writes one review file per walkthrough. A passing file is reported as passing. Each failure names the check id, the file path, and the failing line or the missing heading.

## Script Contents
```python
"""Check each walkthrough.md on its own against validation-rules.md.

Usage:
    python tools/process_walkthrough.py
    python tools/process_walkthrough.py --file modules/01/walkthrough.md

Reads the rules, then reads and checks one file, writes that file's review,
and only then moves to the next file. A passing file is reported as passing.
Each failure names the check id, the file path, and the failing line or the
missing heading.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "out", "__pycache__", ".pytest_cache"}
CHECK_IDS = ("VR-1", "VR-2", "VR-3", "VR-4", "VR-5", "VR-6")

H1 = re.compile(r"^# (?!#)\s*(.*\S)\s*$")
HEADING = re.compile(r"^(#{1,6}) (?!#)\s*(.*\S)\s*$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\S")
QUESTION = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+.*\?")
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME)\b|lorem ipsum", re.IGNORECASE)


def list_targets(root: Path) -> list[Path]:
    """Return walkthrough.md files under root, skipping generated and hidden trees."""
    found = []
    for path in root.rglob("walkthrough.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            found.append(path)
    return sorted(found)


def display_path(root: Path, source: Path) -> str:
    """Return a stable path for reports."""
    try:
        return source.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return source.as_posix()


def output_path(output_dir: Path, root: Path, source: Path) -> Path:
    """Map one walkthrough to its review file."""
    try:
        relative = source.resolve().relative_to(root.resolve())
    except ValueError:
        relative = Path(source.name)
    return output_dir / relative.parent / f"{relative.stem}.review.md"


def visible_lines(contents: str) -> list[tuple[int, str]]:
    """Return non-fenced lines as (line number, text)."""
    visible = []
    in_fence = False
    for number, line in enumerate(contents.splitlines(), start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            visible.append((number, line))
    return visible


def headings(lines: list[tuple[int, str]]) -> list[tuple[int, int, str]]:
    """Return (line number, level, text) for every ATX heading."""
    found = []
    for number, line in lines:
        match = HEADING.match(line.strip())
        if match:
            found.append((number, len(match.group(1)), match.group(2).strip()))
    return found


def section_body(lines: list[tuple[int, str]], start_line: int) -> list[tuple[int, str]]:
    """Return lines after a heading and before the next heading."""
    body = []
    started = False
    for number, line in lines:
        if number == start_line:
            started = True
            continue
        if not started:
            continue
        if HEADING.match(line.strip()):
            break
        body.append((number, line))
    return body


def find_heading(heads: list[tuple[int, int, str]], level: int, text: str) -> Optional[int]:
    """Return the line number of the first heading with this level and text."""
    for number, found_level, found_text in heads:
        if found_level == level and found_text == text:
            return number
    return None


def check_file(path: str, contents: str) -> list[str]:
    """Apply VR-1 through VR-6. Return one issue string per failure."""
    lines = visible_lines(contents)
    heads = headings(lines)
    h1s = [item for item in heads if item[1] == 1]
    issues = []

    first = next(((number, line) for number, line in lines if line.strip()), None)
    if first is None:
        issues.append(f"VR-1 Title: {path}: missing level-1 heading")
    elif H1.match(first[1].strip()) is None:
        issues.append(
            f"VR-1 Title: {path}: line {first[0]}: "
            "first non-empty line is not a level-1 heading"
        )
    if len(h1s) > 1:
        for number, _, _ in h1s[1:]:
            issues.append(f"VR-1 Title: {path}: line {number}: extra level-1 heading")

    summary = find_heading(heads, 2, "Summary")
    if summary is None:
        issues.append(f"VR-2 Summary: {path}: missing heading Summary")
    else:
        prose = [
            number
            for number, line in section_body(lines, summary)
            if line.strip() and LIST_ITEM.match(line) is None and HEADING.match(line.strip()) is None
        ]
        if not prose:
            issues.append(f"VR-2 Summary: {path}: line {summary}: Summary has no paragraph")

    quiz = find_heading(heads, 2, "Quiz")
    if quiz is None:
        issues.append(f"VR-3 Quiz: {path}: missing heading Quiz")
    else:
        questions = [number for number, line in section_body(lines, quiz) if QUESTION.search(line)]
        if not questions:
            issues.append(
                f"VR-3 Quiz: {path}: line {quiz}: Quiz has no numbered or bulleted question"
            )

    title_line = h1s[0][0] if h1s else None
    if summary is None:
        issues.append(f"VR-4 Order: {path}: missing heading Summary")
    elif title_line is None or summary < title_line:
        issues.append(f"VR-4 Order: {path}: line {summary}: Summary is not after the level-1 title")
    if quiz is None:
        issues.append(f"VR-4 Order: {path}: missing heading Quiz")
    elif title_line is None or quiz < title_line:
        issues.append(f"VR-4 Order: {path}: line {quiz}: Quiz is not after the level-1 title")
    if summary is not None and quiz is not None and not summary < quiz:
        issues.append(f"VR-4 Order: {path}: line {quiz}: Quiz appears before Summary")

    for index, (number, _level, _text) in enumerate(heads):
        next_line = heads[index + 1][0] if index + 1 < len(heads) else None
        has_content = any(
            line.strip()
            for line_number, line in lines
            if line_number > number and (next_line is None or line_number < next_line)
        )
        if not has_content:
            issues.append(f"VR-5 No empty sections: {path}: line {number}: heading has no content")

    for number, line in enumerate(contents.splitlines(), start=1):
        if PLACEHOLDER.search(line):
            issues.append(f"VR-6 No placeholders: {path}: line {number}: {line.strip()}")

    return issues


def render(path: str, issues: list[str]) -> str:
    """Format one file's review."""
    if not issues:
        return f"{path} passes.\n"
    return "".join(f"{issue}\n" for issue in issues)


def process_file(source: Path, rules_path: Path, root: Path, output_dir: Path) -> list[str]:
    """Read the rules, read this file, check it, and write its review."""
    rules = rules_path.read_text(encoding="utf-8")
    missing = [check_id for check_id in CHECK_IDS if check_id not in rules]
    if missing:
        raise RuntimeError(f"{rules_path} is missing {', '.join(missing)}")
    shown = display_path(root, source)
    issues = check_file(shown, source.read_text(encoding="utf-8"))
    destination = output_path(output_dir, root, source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(shown, issues), encoding="utf-8")
    print(f"Wrote {destination}")
    return issues


def process_files(sources: list[Path], rules_path: Path, root: Path, output_dir: Path) -> int:
    """Process each source on its own. Return 1 when any file fails a check."""
    print(f"Target files: {len(sources)}")
    for source in sources:
        print(source)
    failures = 0
    for source in sources:
        issues = process_file(source, rules_path, root, output_dir)
        for issue in issues:
            print(issue)
        if issues:
            failures += 1
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check each walkthrough.md individually.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Directory to search")
    parser.add_argument(
        "--rules",
        type=Path,
        default=ROOT / "validation-rules.md",
        help="Rules read again for every file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "out" / "walkthrough-reviews",
        help="Directory for one result file per walkthrough",
    )
    parser.add_argument(
        "--file",
        type=Path,
        action="append",
        help="Check this walkthrough only. Repeat to check several, one at a time.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sources = args.file if args.file else list_targets(args.root)
    try:
        status = process_files(sources, args.rules, args.root, args.output_dir)
    except (OSError, RuntimeError) as exc:
        print(exc, file=sys.stderr)
        status = 1
    sys.exit(status)


if __name__ == "__main__":
    main()
```

## Parameters
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--root` | Directory to search for `walkthrough.md` files | Project root, the parent of `tools/` |
| `--rules` | Rules file read again for every walkthrough | `validation-rules.md` in the project root |
| `--output-dir` | Directory for one result file per walkthrough | `out/walkthrough-reviews` |
| `--file` | Check this walkthrough only. Repeat the flag to check several files, one at a time. | Omitted. The script then checks every `walkthrough.md` under `--root`. |

## Test Run Output
Two sample files were checked: `samples/pass/walkthrough.md` (title, summary paragraph, and a numbered quiz question) and `samples/gap/walkthrough.md` (no Quiz section, an empty heading, and a `TODO`).

```text
Target files: 2
/var/folders/5g/jv94w0m14dq59wwvxhbznm580000gn/T/tmp.YK2aIwbx5O/samples/gap/walkthrough.md
/var/folders/5g/jv94w0m14dq59wwvxhbznm580000gn/T/tmp.YK2aIwbx5O/samples/pass/walkthrough.md
Wrote /var/folders/5g/jv94w0m14dq59wwvxhbznm580000gn/T/tmp.YK2aIwbx5O/reviews/samples/gap/walkthrough.review.md
VR-3 Quiz: samples/gap/walkthrough.md: missing heading Quiz
VR-4 Order: samples/gap/walkthrough.md: missing heading Quiz
VR-5 No empty sections: samples/gap/walkthrough.md: line 1: heading has no content
VR-5 No empty sections: samples/gap/walkthrough.md: line 7: heading has no content
VR-6 No placeholders: samples/gap/walkthrough.md: line 5: This draft still has a placeholder. TODO
Wrote /var/folders/5g/jv94w0m14dq59wwvxhbznm580000gn/T/tmp.YK2aIwbx5O/reviews/samples/pass/walkthrough.review.md
exit:1
```

`samples/pass/walkthrough.md` was written as `samples/pass/walkthrough.md passes.` The command exited 1 because `samples/gap/walkthrough.md` failed its checks.
