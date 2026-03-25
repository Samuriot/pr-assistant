import re
import subprocess
from typing import List, Optional

from pydantic import BaseModel


class LineChange(BaseModel):
    line_number: int
    line_diff: str


class Hunk(BaseModel):
    start_line: int
    header: str
    lines: List[str]


class File(BaseModel):
    file_name: str
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    additions: List[LineChange]
    removals: List[LineChange]
    hunks: List[Hunk]


def _parse_diff_output(output: str) -> List[File]:
    files: List[File] = []
    current: Optional[File] = None
    current_hunk: Optional[Hunk] = None
    old_line_no: Optional[int] = None
    new_line_no: Optional[int] = None

    hunk_pattern = re.compile(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@")

    for raw in output.splitlines():
        if raw.startswith("diff --git "):
            if current_hunk:
                current.hunks.append(current_hunk)  # type: ignore[arg-type]
                current_hunk = None
            if current:
                files.append(current)
            parts = raw.split()
            file_name = parts[-1][2:] if len(parts) >= 4 else ""
            current = File(
                file_name=file_name,
                old_start=0,
                old_len=0,
                new_start=0,
                new_len=0,
                additions=[],
                removals=[],
                hunks=[],
            )
            old_line_no = None
            new_line_no = None
            continue

        if current is None:
            continue

        if raw.startswith("Binary files "):
            continue

        hunk_match = hunk_pattern.match(raw)
        if hunk_match:
            if current_hunk:
                current.hunks.append(current_hunk)
            old_start = int(hunk_match.group(1))
            old_len = int(hunk_match.group(2) or 1)
            new_start = int(hunk_match.group(3))
            new_len = int(hunk_match.group(4) or 1)

            if current.old_start == 0:
                current.old_start = old_start
                current.old_len = old_len
                current.new_start = new_start
                current.new_len = new_len

            old_line_no = old_start
            new_line_no = new_start
            current_hunk = Hunk(start_line=new_start, header=raw, lines=[raw])
            continue

        if raw.startswith("+++") or raw.startswith("---"):
            continue

        if current_hunk:
            current_hunk.lines.append(raw)

        if raw.startswith("+"):
            if new_line_no is not None:
                current.additions.append(
                    LineChange(
                        line_number=new_line_no,
                        line_diff=re.sub(r"^\s+", "", raw[1:]),
                    )
                )
                new_line_no += 1
            continue

        if raw.startswith("-"):
            if old_line_no is not None:
                current.removals.append(
                    LineChange(
                        line_number=old_line_no,
                        line_diff=re.sub(r"^\s+", "", raw[1:]),
                    )
                )
                old_line_no += 1
            continue

        if old_line_no is not None:
            old_line_no += 1
        if new_line_no is not None:
            new_line_no += 1

    if current_hunk and current:
        current.hunks.append(current_hunk)
    if current:
        files.append(current)

    return files


def get_file_diff(commit: str) -> List[File]:
    """Return structured line additions/removals and raw hunks for a commit."""

    process = subprocess.run(
        ["git", "show", "-U3", "--no-color", "--no-ext-diff", commit],
        check=True,
        text=True,
        capture_output=True,
    )

    return _parse_diff_output(process.stdout)


def get_worktree_diff() -> List[File]:
    """Return structured diff for unstaged/staged changes in the working tree."""

    process = subprocess.run(
        ["git", "diff", "-U3", "--no-color", "--no-ext-diff"],
        check=True,
        text=True,
        capture_output=True,
    )

    return _parse_diff_output(process.stdout)
