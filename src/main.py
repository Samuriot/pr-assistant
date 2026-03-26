"""Entry point that wires diff collection to the orchestrator."""

import argparse
import sys
from pathlib import Path
from typing import List

# Ensure project root is on sys.path when running `python src/main.py`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scripts.orchestrate import (
    DEFAULT_CONFIG_DIR,
    ReviewRequest,
    build_hunks_from_commit,
    build_hunks_from_worktree,
    orchestrate,
)
from src.scripts.github_integration import GitHubClient


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Strands review orchestrator")
    parser.add_argument(
        "--target-files",
        type=str,
        default=None,
        help="Comma-separated list of files to include (relative paths)",
    )
    parser.add_argument(
        "--use-worktree",
        action="store_true",
        help="Review working tree diff (default if no commit provided)",
    )
    parser.add_argument(
        "--commit",
        type=str,
        default=None,
        help="Commit-ish to diff (overrides --use-worktree)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate review without calling models",
    )
    parser.add_argument(
        "--max-hunks",
        type=int,
        default=5,
        help="Maximum hunks to process",
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        default=10,
        help="Maximum comments to emit",
    )
    parser.add_argument(
        "--min-severity",
        type=str,
        default="minor",
        choices=["nit", "minor", "major", "blocker"],
        help="Minimum severity to emit",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=None,
        help="Override model id (else uses OLLAMA_MODEL_ID or default)",
    )
    parser.add_argument(
        "--model-host",
        type=str,
        default=None,
        help="Override model host (else uses OLLAMA_HOST or default)",
    )
    parser.add_argument(
        "--github-token",
        type=str,
        default=None,
        help="GitHub Personal Access Token (or use GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--github-repo",
        type=str,
        default=None,
        help="GitHub repository in format 'owner/repo' (required to post comments)",
    )
    parser.add_argument(
        "--pr-number",
        type=int,
        default=None,
        help="PR number to post comments to (requires --github-repo)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Parse target files from comma-separated argument
    files_arg = (
        [f.strip() for f in args.target_files.split(",")] if args.target_files else None
    )

    if args.commit:
        print(f"Extracting diffs from commit {args.commit}...", file=sys.stderr)
        hunks = build_hunks_from_commit(args.commit, target_files=files_arg)
        source_label = f"commit {args.commit}"
    else:
        print("Extracting diffs from worktree...", file=sys.stderr)
        hunks = build_hunks_from_worktree(target_files=files_arg)
        source_label = "worktree"

    if not hunks:
        print(
            f"No diff hunks found for {source_label}"
            + (f" filtered to {files_arg}" if files_arg else "")
        )
        return

    request = ReviewRequest(
        pr_number=str(args.pr_number) if args.pr_number else "local-run",
        repo=str(Path.cwd()),
        hunks=hunks,
        max_comments=args.max_comments,
        min_severity=args.min_severity,
    )

    if not args.dry_run:
        print("Starting review...", file=sys.stderr)

    comments = orchestrate(
        request,
        config_dir=DEFAULT_CONFIG_DIR,
        dry_run=args.dry_run,
        max_hunks=args.max_hunks,
        model_id=args.model_id,
        host_url=args.model_host,
    )

    if not comments:
        print("No comments generated (dry run or no issues detected).")
        return

    # Output comments as JSON for programmatic use
    for comment in comments:
        print(comment.model_dump())

    # Post to GitHub if credentials and repo info provided
    if args.github_token or args.github_repo or args.pr_number:
        if not args.github_repo:
            print(
                "Error: --github-repo required to post comments. Format: owner/repo",
                file=sys.stderr,
            )
            return

        if not args.pr_number:
            print(
                "Error: --pr-number required to post comments.",
                file=sys.stderr,
            )
            return

        try:
            gh_client = GitHubClient(token=args.github_token, repo=args.github_repo)
            successful, failed = gh_client.post_comments(args.pr_number, comments)

            print(
                f"\nGitHub: Posted {successful}/{len(comments)} comments",
                file=sys.stderr,
            )
            if failed > 0:
                print(f"GitHub: {failed} comments failed to post", file=sys.stderr)

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
