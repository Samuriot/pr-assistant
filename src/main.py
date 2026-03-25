"""Entry point that wires diff collection to the orchestrator."""

import sys
from pathlib import Path
from typing import List

# Ensure project root is on sys.path when running `python src/main.py`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scripts.orchestrate import (  # type: ignore  # resolved via sys.path
    DEFAULT_CONFIG_DIR,
    ReviewRequest,
    build_hunks_from_commit,
    build_hunks_from_worktree,
    orchestrate,
)


def main(target_files: List[str] | None = None, use_worktree: bool = True) -> None:
    if use_worktree:
        hunks = build_hunks_from_worktree(target_files=target_files)
        source_label = "worktree"
    else:
        commit = "HEAD"
        hunks = build_hunks_from_commit(commit, target_files=target_files)
        source_label = f"commit {commit}"

    if not hunks:
        print(
            f"No diff hunks found for {source_label}"
            + (f" filtered to {target_files}" if target_files else "")
        )
        return

    request = ReviewRequest(
        pr_number="local-run",
        repo=str(Path.cwd()),
        hunks=hunks,
        max_comments=10,
        min_severity="minor",
    )

    comments = orchestrate(request, config_dir=DEFAULT_CONFIG_DIR)
    if not comments:
        print("No comments generated (severity filter or no issues detected).")
        return

    for comment in comments:
        print(comment)


if __name__ == "__main__":
    main(target_files=None, use_worktree=True)
