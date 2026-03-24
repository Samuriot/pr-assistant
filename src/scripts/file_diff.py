import re
import subprocess

from typing import List, Optional
from pydantic import BaseModel


class LineChange(BaseModel):
    line_number: int
    line_diff: str


class File(BaseModel):
    file_name: str
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    additions: List[LineChange]
    removals: List[LineChange]


def get_file_diff(commit: str) -> List[File]:
    """Return structured line additions/removals for a commit."""
    process = subprocess.run(
        ["git", "show", "-U0", "--no-color", "--no-ext-diff", commit],
        check=True,
        text=True,
        capture_output=True,
    )

    # local vars to keep track while parsing
    files: List[File] = []
    current: Optional[file] = none
    old_line_no: optional[int] = none
    new_line_no: optional[int] = none

    # regex pattern for keeping track of new lines
    hunk_pattern = re.compile(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@")

    for raw in process.stdout.splitlines():
        # case 1: new file defined
        if raw.startswith("diff --git "):
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
            )
            old_line_no = None
            new_line_no = None
            continue
        
        # if there's no diff, continue through the lines
        if current is None:
            continue
        
        # if it's a binary, no need to handle, skip
        if raw.startswith("Binary files "):
            continue
        
        # case 2: hunk pattern matching
        hunk_match = hunk_pattern.match(raw)
        if hunk_match:
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
            continue
        
        # disregard +++ & --- patterns
        if raw.startswith("+++") or raw.startswith("---"):
            continue

        # case 3: file additions
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
        
        # case 4: file deletions
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

        # Context line
        if old_line_no is not None:
            old_line_no += 1
        if new_line_no is not None:
            new_line_no += 1

    if current:
        files.append(current)

    return files

