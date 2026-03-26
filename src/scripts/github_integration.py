"""GitHub API integration for posting code review comments to PRs."""

import os
import sys
from typing import Optional

import requests

from src.models.structured_response import CodeComment


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: Optional[str] = None, repo: str = ""):
        """Initialize GitHub client.

        Args:
            token: GitHub Personal Access Token. If None, uses GITHUB_TOKEN env var.
            repo: Repository in format "owner/repo" (e.g., "anomalyco/pr-assistant")

        Raises:
            ValueError: If token is not provided and GITHUB_TOKEN env var is not set.
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token not provided. Set GITHUB_TOKEN environment variable "
                "or pass --github-token argument."
            )

        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def post_pr_comment(self, pr_number: int, comment: str) -> bool:
        """Post a top-level comment on a PR.

        Args:
            pr_number: PR number
            comment: Comment body

        Returns:
            True if successful, False otherwise.
        """
        url = f"{self.base_url}/repos/{self.repo}/issues/{pr_number}/comments"
        payload = {"body": comment}

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            print(
                f"✓ Posted comment on PR #{pr_number}",
                file=sys.stderr,
            )
            return True
        except requests.exceptions.RequestException as e:
            print(
                f"✗ Failed to post comment on PR #{pr_number}: {e}",
                file=sys.stderr,
            )
            return False

    def post_review_comment(
        self, pr_number: int, file_path: str, line_number: int, comment: str
    ) -> bool:
        """Post a line-specific comment on a PR (review comment).

        This posts a comment on a specific line of a specific file in a PR.

        Args:
            pr_number: PR number
            file_path: File path relative to repo root (e.g., "src/main.py")
            line_number: Line number to comment on
            comment: Comment body

        Returns:
            True if successful, False otherwise.
        """
        # First, get the PR details to find the head commit SHA
        pr_details = self._get_pr_details(pr_number)
        if not pr_details:
            return False

        commit_sha = pr_details.get("head", {}).get("sha")
        if not commit_sha:
            print(
                f"✗ Could not find commit SHA for PR #{pr_number}",
                file=sys.stderr,
            )
            return False

        url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/comments"
        payload = {
            "commit_id": commit_sha,
            "path": file_path,
            "line": line_number,
            "body": comment,
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            print(
                f"✓ Posted review comment on {file_path}:{line_number} "
                f"(PR #{pr_number})",
                file=sys.stderr,
            )
            return True
        except requests.exceptions.RequestException as e:
            print(
                f"✗ Failed to post review comment on {file_path}:{line_number}: {e}",
                file=sys.stderr,
            )
            return False

    def _get_pr_details(self, pr_number: int) -> Optional[dict]:
        """Get PR details including head commit SHA.

        Args:
            pr_number: PR number

        Returns:
            PR details dict or None if request fails.
        """
        url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(
                f"✗ Failed to get PR details for PR #{pr_number}: {e}",
                file=sys.stderr,
            )
            return None

    def post_comments(
        self, pr_number: int, comments: list[CodeComment]
    ) -> tuple[int, int]:
        """Post multiple review comments to a PR.

        Args:
            pr_number: PR number
            comments: List of CodeComment objects to post

        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not comments:
            return 0, 0

        successful = 0
        failed = 0

        print(
            f"Posting {len(comments)} review comments to PR #{pr_number}...",
            file=sys.stderr,
            flush=True,
        )

        for idx, comment in enumerate(comments, 1):
            print(
                f"  [{idx}/{len(comments)}] {comment.file_name}:{comment.line_number}",
                file=sys.stderr,
                flush=True,
            )

            success = self.post_review_comment(
                pr_number=pr_number,
                file_path=comment.file_name,
                line_number=comment.line_number,
                comment=comment.review,
            )

            if success:
                successful += 1
            else:
                failed += 1

        return successful, failed
