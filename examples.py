#!/usr/bin/env python3
"""
Example script demonstrating GitHub PR Assistant integration.

This script shows how to use the PR Assistant to review a PR and post comments to GitHub.
"""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[0]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.scripts.github_integration import GitHubClient
from src.models.structured_response import CodeComment


def example_dry_run():
    """Example 1: Local review without GitHub posting."""
    print("=" * 60)
    print("Example 1: Local Review (Dry Run)")
    print("=" * 60)
    print("\nCommand:")
    print("  python src/main.py --dry-run")
    print("\nThis reviews your working tree without calling the model.")
    print("Useful for testing and debugging.\n")


def example_github_review():
    """Example 2: Review and post to GitHub."""
    print("=" * 60)
    print("Example 2: Review and Post to GitHub PR")
    print("=" * 60)
    print("\nCommand:")
    print("  export GITHUB_TOKEN='ghp_xxxxxxxxxxxxxxxxxxxx'")
    print("  python src/main.py \\")
    print("    --github-repo owner/repo \\")
    print("    --pr-number 123")
    print("\nThis will:")
    print("  1. Extract diffs from your working tree")
    print("  2. Run code review with LLM")
    print("  3. Post review comments to PR #123")
    print("  4. Show progress on stderr\n")


def example_specific_files():
    """Example 3: Review specific files."""
    print("=" * 60)
    print("Example 3: Review Specific Files")
    print("=" * 60)
    print("\nCommand:")
    print("  python src/main.py \\")
    print("    --target-files 'src/main.py,src/models/*.py' \\")
    print("    --github-repo owner/repo \\")
    print("    --pr-number 123")
    print("\nThis reviews only the specified files.\n")


def example_strict_review():
    """Example 4: Strict review (major/blocker only)."""
    print("=" * 60)
    print("Example 4: Strict Review (Major Issues Only)")
    print("=" * 60)
    print("\nCommand:")
    print("  python src/main.py \\")
    print("    --min-severity major \\")
    print("    --max-comments 5 \\")
    print("    --github-repo owner/repo \\")
    print("    --pr-number 123")
    print("\nThis only posts major and blocker issues (max 5 comments).\n")


def example_commit_review():
    """Example 5: Review specific commit."""
    print("=" * 60)
    print("Example 5: Review Specific Commit")
    print("=" * 60)
    print("\nCommand:")
    print("  python src/main.py \\")
    print("    --commit abc1234def5 \\")
    print("    --github-repo owner/repo \\")
    print("    --pr-number 123")
    print("\nThis reviews changes from a specific commit.\n")


def example_different_model():
    """Example 6: Use different LLM model."""
    print("=" * 60)
    print("Example 6: Use Different Model")
    print("=" * 60)
    print("\nCommand:")
    print("  python src/main.py \\")
    print("    --model-id mistral:latest \\")
    print("    --github-repo owner/repo \\")
    print("    --pr-number 123")
    print("\nFirst pull the model:")
    print("  ollama pull mistral:latest")
    print("\nSupported models: Any model available in Ollama\n")


def example_github_client_direct():
    """Example 7: Direct use of GitHubClient."""
    print("=" * 60)
    print("Example 7: Direct GitHubClient Usage")
    print("=" * 60)
    print("\nPython code example:")
    print("""
from src.scripts.github_integration import GitHubClient
from src.models.structured_response import CodeComment

# Initialize client (uses GITHUB_TOKEN env var)
gh = GitHubClient(repo="owner/repo")

# Create sample comments
comments = [
    CodeComment(
        file_name="src/main.py",
        line_number=42,
        review="Variable name is unclear. Consider renaming to be more descriptive."
    ),
    CodeComment(
        file_name="src/models.py",
        line_number=100,
        review="Missing error handling for edge case."
    ),
]

# Post comments to PR
successful, failed = gh.post_comments(pr_number=123, comments=comments)
print(f"Posted {successful}/{len(comments)} comments")
""")
    print()


def example_ci_cd():
    """Example 8: CI/CD integration."""
    print("=" * 60)
    print("Example 8: GitHub Actions CI/CD Integration")
    print("=" * 60)
    print("\n.github/workflows/review.yml:")
    print("""
name: Code Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -e .
      
      - name: Set up Ollama
        run: docker run -d -p 11434:11434 ollama/ollama
      
      - name: Pull model
        run: docker exec -i $(docker ps -q) ollama pull mistral
      
      - name: Review PR
        run: |
          python src/main.py \\
            --github-repo ${{ github.repository }} \\
            --pr-number ${{ github.event.pull_request.number }} \\
            --model-id mistral:latest \\
            --min-severity major
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
""")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║  Git PR Assistant - GitHub Integration Examples         ║")
    print("╚" + "═" * 58 + "╝")
    print()

    examples = [
        example_dry_run,
        example_github_review,
        example_specific_files,
        example_strict_review,
        example_commit_review,
        example_different_model,
        example_github_client_direct,
        example_ci_cd,
    ]

    for example in examples:
        example()

    print("=" * 60)
    print("For more information, see GITHUB_INTEGRATION.md")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
