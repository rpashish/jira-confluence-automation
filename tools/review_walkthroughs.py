"""Review each walkthrough.md against validation-rules.md.

Usage:
    python tools/review_walkthroughs.py

Lists every walkthrough.md under the project, sends validation-rules.md plus
that file to the Claude CLI, and writes one result per file under
out/walkthrough-reviews/.
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "out", "__pycache__", ".pytest_cache"}


def list_targets(root: Path) -> list[Path]:
    """Return walkthrough.md files under root, skipping generated and hidden trees."""
    found = []
    for path in root.rglob("walkthrough.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            found.append(path)
    return sorted(found)


def build_prompt(rules: str, path: Path, contents: str) -> str:
    """Combine the validation rules with one file for a single review."""
    return (
        "Apply the validation rules below to the file. "
        "Report each failed check with its id, the file path, and the failing "
        "line or the missing heading. If every check passes, say the file passes.\n\n"
        f"{rules}\n\n"
        f"File: {path}\n\n"
        f"{contents}"
    )


def invoke_ai(prompt: str) -> str:
    """Send the prompt to the Claude CLI and return its printed answer."""
    result = subprocess.run(
        ["claude", "-p", "--tools", "", "--no-session-persistence"],
        input=prompt,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "claude exited non-zero"
        raise RuntimeError(detail)
    return result.stdout


def output_path(output_dir: Path, root: Path, source: Path) -> Path:
    """Map a source walkthrough to its review file under the output directory."""
    relative = source.relative_to(root)
    return output_dir / relative.parent / f"{relative.stem}.review.md"


def review_files(root: Path, rules_path: Path, output_dir: Path) -> int:
    """Review every target file. Return 0 when every call succeeds."""
    targets = list_targets(root)
    print(f"Target files: {len(targets)}")
    for path in targets:
        print(path)
    if not targets:
        return 0

    rules = rules_path.read_text(encoding="utf-8")
    failures = 0
    for path in targets:
        contents = path.read_text(encoding="utf-8")
        destination = output_path(output_dir, root, path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = invoke_ai(build_prompt(rules, path, contents))
        except RuntimeError as exc:
            failures += 1
            result = f"Review failed for {path}: {exc}\n"
            print(result, file=sys.stderr, end="")
        destination.write_text(result, encoding="utf-8")
        print(f"Wrote {destination}")
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review each walkthrough.md with the validation rules."
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="Directory to search")
    parser.add_argument(
        "--rules",
        type=Path,
        default=ROOT / "validation-rules.md",
        help="Instruction file sent with each walkthrough",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "out" / "walkthrough-reviews",
        help="Directory for one result file per walkthrough",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sys.exit(review_files(args.root, args.rules, args.output_dir))


if __name__ == "__main__":
    main()
