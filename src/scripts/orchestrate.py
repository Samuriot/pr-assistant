"""Minimal orchestration loop wiring Review -> Coding agent with Strands.

This keeps the reviewer as the primary agent and delegates fix/snippet
generation to the coding agent. The orchestrator here is a thin function that
you can plug into your PR processing pipeline (e.g., iterate over diffs and
existing comments, then post via GitHub). It focuses on:
- passing only the diff hunk, file path, and any prior comment thread for
  context (keeps prompts lean)
- enforcing a simple severity filter and max comment cap
- calling the coding agent only when the reviewer asks for a fix snippet

Dependencies: strands, your existing LocalAgent wrapper, agent_init helpers.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.scripts.agent_init import setup_strands_agents
from src.scripts.file_diff import get_file_diff
from src.models.structured_response import CodeComment


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@dataclass
class DiffHunk:
    file_path: str
    hunk: str
    start_line: int
    existing_comments: List[str] | None = None


@dataclass
class ReviewRequest:
    pr_number: str
    repo: str
    hunks: List[DiffHunk]
    max_comments: int = 15
    min_severity: str = "minor"  # options: nit, minor, major, blocker


def _should_emit(severity: str, min_severity: str) -> bool:
    order = {"nit": 0, "minor": 1, "major": 2, "blocker": 3}
    return order.get(severity, 1) >= order.get(min_severity, 1)


def _build_reviewer_prompt(hunk: DiffHunk, min_severity: str) -> str:
    prior = "\n".join(hunk.existing_comments or [])
    return (
        "You are the code review agent. Analyze the provided diff hunk and "
        "decide if a comment is warranted. If you need a concrete fix snippet, "
        "you may delegate to the Coding Agent. Respond with JSON only.\n"
        "Input context:\n"
        f"- file: {hunk.file_path}\n"
        f"- start_line: {hunk.start_line}\n"
        f"- existing_thread: {prior or 'none'}\n"
        "- diff hunk:\n"
        f"{hunk.hunk}\n\n"
        "Output JSON schema:\n"
        "{\n"
        "  'needs_comment': bool,\n"
        "  'severity': 'nit'|'minor'|'major'|'blocker',\n"
        "  'issue': str,\n"
        "  'impact': str,\n"
        "  'ask_coder': bool,\n"
        "  'coder_request': str | null,  # precise ask if ask_coder\n"
        "  'suggestion': str | null,     # may be placeholder before coder reply\n"
        "  'line': int                   # line number for the comment\n"
        "}\n"
        f"Enforce min severity: {min_severity}. If below threshold, set "
        "needs_comment=false."
    )


def _build_coder_prompt(hunk: DiffHunk, request: str) -> str:
    return (
        "You are the coding agent. Provide a concise fix snippet only.\n"
        f"File: {hunk.file_path}\n"
        f"Diff hunk:\n{hunk.hunk}\n\n"
        f"Task: {request}\n"
        "Respond with JSON: { 'snippet': str, 'rationale': str }"
    )


def _files_to_hunks(
    files: List[File], target_files: Optional[Iterable[str]]
) -> List[DiffHunk]:
    target = set(target_files) if target_files else None
    hunks: List[DiffHunk] = []

    for f in files:
        if target and f.file_name not in target:
            continue
        for h in f.hunks:
            hunks.append(
                DiffHunk(
                    file_path=f.file_name,
                    hunk="\n".join(h.lines),
                    start_line=h.start_line,
                    existing_comments=[],
                )
            )

    return hunks


def build_hunks_from_commit(
    commit: str, target_files: Optional[Iterable[str]] = None
) -> List[DiffHunk]:
    """Convert git show output into DiffHunk entries, optionally filtering files."""

    return _files_to_hunks(get_file_diff(commit), target_files)


def build_hunks_from_worktree(
    target_files: Optional[Iterable[str]] = None,
) -> List[DiffHunk]:
    """Convert git diff (working tree) output into DiffHunk entries."""

    from src.scripts.file_diff import get_worktree_diff

    return _files_to_hunks(get_worktree_diff(), target_files)


def orchestrate(
    review_request: ReviewRequest,
    model_id: Optional[str] = None,
    host_url: Optional[str] = None,
    config_dir: Optional[Path] = None,
    dry_run: bool = False,
    max_hunks: int | None = None,
) -> List[CodeComment]:
    """Runs review over hunks, delegating to coding agent when asked.

    Returns a list of comment payloads ready to post (dicts with keys like
    file_path, line, body, severity). Posting is left to the caller.
    """

    print("Initializing agents...", file=sys.stderr)
    agents = setup_strands_agents(
        config_dir=config_dir or DEFAULT_CONFIG_DIR,
        model_id=model_id,
        host_url=host_url,
    )
    reviewer = agents.get("Code Reviewer")
    coder = agents.get("Coding Agent")

    if not reviewer or not coder:
        raise RuntimeError(
            "Missing required agents: ensure 'Code Reviewer' and 'Coding Agent' configs exist"
        )

    print(f"Found {len(review_request.hunks)} hunks to review", file=sys.stderr)
    comments: List[CodeComment] = []

    for idx, hunk in enumerate(review_request.hunks):
        if max_hunks is not None and idx >= max_hunks:
            break
        if len(comments) >= review_request.max_comments:
            break

        print(
            f"Processing hunk {idx + 1}/{len(review_request.hunks)} "
            f"({hunk.file_path}:{hunk.start_line})...",
            file=sys.stderr,
            flush=True,
        )

        if dry_run:
            comments.append(
                CodeComment(
                    file_name=hunk.file_path,
                    line_number=hunk.start_line,
                    review=f"[dry-run] Would review hunk starting at line {hunk.start_line}",
                )
            )
            continue

        prompt = _build_reviewer_prompt(hunk, review_request.min_severity)
        review_raw = reviewer["agent"](prompt, system_prompt=reviewer["prompt"])
        try:
            review = json.loads(str(review_raw))
        except json.JSONDecodeError:
            continue

        if not review.get("needs_comment"):
            continue

        severity = review.get("severity", "minor")
        if not _should_emit(severity, review_request.min_severity):
            continue

        suggestion = review.get("suggestion")
        rationale = None
        if review.get("ask_coder") and review.get("coder_request"):
            coder_prompt = _build_coder_prompt(hunk, review["coder_request"])
            coder_raw = coder["agent"](coder_prompt, system_prompt=coder["prompt"])
            try:
                coder_resp = json.loads(str(coder_raw))
                suggestion = coder_resp.get("snippet") or suggestion
                rationale = coder_resp.get("rationale")
            except json.JSONDecodeError:
                rationale = None

        body_lines = [
            f"Issue: {review.get('issue', '').strip()}",
            f"Impact: {review.get('impact', '').strip()}",
        ]
        if suggestion:
            body_lines.append(f"Suggestion:\n{suggestion}")
        if rationale:
            body_lines.append(f"Rationale: {rationale}")

        severity = review.get("severity", "minor")
        print(f"  → Issue found: {severity.upper()}", file=sys.stderr, flush=True)

        comments.append(
            CodeComment(
                file_name=hunk.file_path,
                line_number=review.get("line") or hunk.start_line,
                review="\n".join(body_lines).strip(),
            )
        )

    issue_word = "issue" if len(comments) == 1 else "issues"
    print(
        f"Review complete: {len(comments)} {issue_word} found",
        file=sys.stderr,
    )
    return comments
