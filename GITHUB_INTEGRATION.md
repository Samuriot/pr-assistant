# GitHub Integration Guide

## Overview

The PR Assistant can automatically post review comments to GitHub pull requests. Comments are posted as line-specific review comments on the exact lines where issues were detected.

## Setup

### 1. Create a GitHub Personal Access Token (PAT)

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "pr-assistant")
4. Select scopes:
   - `repo` - Full control of private repositories
5. Click "Generate token"
6. Copy the token (you won't see it again!)

### 2. Set Environment Variable (Optional but Recommended)

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

You can also add this to your `.bashrc`, `.zshrc`, or `.env` file.

## Usage

### Basic Local Review (No GitHub Posting)

```bash
python src/main.py --dry-run
```

### Review and Post to GitHub PR

```bash
python src/main.py \
  --github-repo owner/repo \
  --pr-number 123 \
  --github-token $GITHUB_TOKEN
```

If `GITHUB_TOKEN` is set in environment, you can omit `--github-token`:

```bash
python src/main.py \
  --github-repo owner/repo \
  --pr-number 123
```

### Post Comments from Working Tree

```bash
python src/main.py \
  --github-repo anomalyco/pr-assistant \
  --pr-number 42
```

### Post Comments from Specific Commit

```bash
python src/main.py \
  --commit abc1234 \
  --github-repo owner/repo \
  --pr-number 123
```

### Filter to Specific Files

```bash
python src/main.py \
  --target-files "src/main.py,src/models/*.py" \
  --github-repo owner/repo \
  --pr-number 123
```

### Adjust Review Sensitivity

```bash
# Only post major/blocker issues
python src/main.py \
  --min-severity major \
  --github-repo owner/repo \
  --pr-number 123

# Post all issues (including nits)
python src/main.py \
  --min-severity nit \
  --github-repo owner/repo \
  --pr-number 123
```

### Control Model and Processing

```bash
python src/main.py \
  --model-id mistral:latest \
  --max-hunks 50 \
  --max-comments 30 \
  --github-repo owner/repo \
  --pr-number 123
```

## Available Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--github-token` | string | `GITHUB_TOKEN` env var | GitHub Personal Access Token |
| `--github-repo` | string | None | Repository in format `owner/repo` |
| `--pr-number` | int | None | PR number to post comments to |
| `--dry-run` | flag | False | Simulate without calling model |
| `--commit` | string | None | Specific commit to review |
| `--target-files` | string | None | Comma-separated files to filter |
| `--min-severity` | choice | `minor` | Minimum issue severity: `nit`, `minor`, `major`, `blocker` |
| `--max-hunks` | int | 5 | Maximum hunks to process |
| `--max-comments` | int | 10 | Maximum comments to emit |
| `--model-id` | string | `llama3.2:3b` | LLM model to use |
| `--model-host` | string | `http://localhost:11434` | Ollama host URL |

## Output

The tool outputs in two streams:

**Stdout (JSON):** Review comments in JSON format for programmatic use
```json
{'file_name': 'src/main.py', 'line_number': 42, 'review': 'Issue: Variable name unclear...'}
```

**Stderr:** Progress information and GitHub posting status
```
Extracting diffs from worktree...
Initializing agents...
Found 5 hunks to review
Processing hunk 1/5 (src/main.py:42)...
  → Issue found: MINOR
...
GitHub: Posted 3/5 comments
```

## Error Handling

### Missing GitHub Token

```
Error: GitHub token not provided. Set GITHUB_TOKEN environment variable or pass --github-token argument.
```

**Solution:** Export `GITHUB_TOKEN` or pass `--github-token` flag

### Missing Repository

```
Error: --github-repo required to post comments. Format: owner/repo
```

**Solution:** Add `--github-repo owner/repo`

### Missing PR Number

```
Error: --pr-number required to post comments.
```

**Solution:** Add `--pr-number <number>`

### Failed to Post Comment

```
✗ Failed to post review comment on src/main.py:42: 422 Client Error
```

**Possible causes:**
- Line number doesn't exist in the PR diff
- File not changed in the PR
- Invalid commit SHA
- Insufficient permissions

## Security Notes

1. **Never commit your token** - Keep it in environment variables or `.env` (not in git)
2. **Token scopes** - Use minimal required scopes (just `repo`)
3. **Temporary tokens** - Consider using short-lived tokens for CI/CD
4. **Rotate regularly** - Regenerate tokens periodically

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Code Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Ollama
        run: docker run -d -p 11434:11434 ollama/ollama
        
      - name: Pull model
        run: docker exec -i $(docker ps -q) ollama pull mistral:latest
      
      - name: Review PR
        run: |
          python src/main.py \
            --github-repo ${{ github.repository }} \
            --pr-number ${{ github.event.pull_request.number }} \
            --model-id mistral:latest
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Examples

### Review with All Defaults

```bash
python src/main.py --github-repo owner/repo --pr-number 1
```

### Strict Review (Major Issues Only)

```bash
python src/main.py \
  --min-severity major \
  --max-comments 5 \
  --github-repo owner/repo \
  --pr-number 1
```

### Lenient Review (All Levels)

```bash
python src/main.py \
  --min-severity nit \
  --max-hunks 100 \
  --max-comments 50 \
  --github-repo owner/repo \
  --pr-number 1
```

### Dry Run (Test Without Posting)

```bash
python src/main.py \
  --dry-run \
  --github-repo owner/repo \
  --pr-number 1
```

## Troubleshooting

### Comments not appearing on PR

**Check if line exists in PR diff:**
- GitHub only allows comments on lines that are part of the PR diff
- If a file wasn't changed in the PR, comments can't be posted to it
- Use `--dry-run` first to see which lines would get comments

**Check PR commit:**
- Ensure the PR commit SHA matches the changes you're reviewing
- If you pushed new commits, use the latest commit

### Rate Limiting

GitHub has rate limits on API calls:
- Authenticated: 5,000 requests/hour
- Each comment post is 1 request

**If rate limited:**
```
403 Client Error: rate limit exceeded
```

Wait for the rate limit to reset (check `X-RateLimit-Reset` header)

### Large PRs

For PRs with many hunks:
```bash
python src/main.py \
  --max-hunks 100 \
  --max-comments 50 \
  --github-repo owner/repo \
  --pr-number 123
```

## Advanced: Batch Processing Multiple PRs

Create a script to process multiple PRs:

```bash
#!/bin/bash

for pr in 1 2 3 4 5; do
  echo "Processing PR #$pr..."
  python src/main.py \
    --github-repo owner/repo \
    --pr-number $pr \
    --min-severity major
done
```

## FAQ

**Q: Can I review local uncommitted changes?**
A: Yes, use `--dry-run` flag. Comments won't post without `--github-repo` and `--pr-number`.

**Q: Can I review multiple commits?**
A: No, specify one commit with `--commit` or use `--use-worktree` for local changes.

**Q: Do comments overwrite each other?**
A: No, each run creates new comments. You'll see duplicates if you run multiple times on the same PR.

**Q: Can I delete posted comments?**
A: Comments are posted as reviews, you must delete them manually from GitHub UI.

**Q: What if a file was renamed in the PR?**
A: The tool reviews the new file path. GitHub's API handles renamed files correctly.
