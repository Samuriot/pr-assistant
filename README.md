# Git PR Assistant
- This project serves to help developers with their PRs before they publish code reviews
- Using the StrandsAgentSDK for Agentic generation, the Git PR Assistant will look through your changes in git staging, and provide feedback about potential issues, improvements, or general semantic related items with code.
- This is meant to run locally, using Ollama as an LLM base, with potential plans to expand the model choice
- **New:** Automatically post review comments to GitHub PRs!

## Architecture
- The project uses multiple agents with the Swarm Orchestration pattern to have specialized agents reviewing your code
- Two-agent orchestration: Code Reviewer Agent + Coding Agent (for fix suggestions)
- Hunk-based analysis with context preservation (±3 line context)

## Prerequisites
- [Setup Ollama to run locally](https://strandsagents.com/docs/user-guide/concepts/model-providers/ollama/)
- Setup a Python venv and install the requirements.txt
- For GitHub integration: GitHub Personal Access Token (see [GITHUB_INTEGRATION.md](./GITHUB_INTEGRATION.md))

## Quick Start

### 1. Local Review (No GitHub)

```bash
# Dry run - test without calling LLM
python src/main.py --dry-run

# Full review with local LLM
python src/main.py
```

### 2. Review and Post to GitHub PR

```bash
# Set GitHub token (one time)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Run review and post comments to PR #123
python src/main.py \
  --github-repo owner/repo \
  --pr-number 123
```

## Usage Examples

**Review specific files:**
```bash
python src/main.py --target-files "src/main.py,src/models/*.py"
```

**Review a specific commit:**
```bash
python src/main.py --commit abc1234 --github-repo owner/repo --pr-number 123
```

**Adjust sensitivity (only major/blocker issues):**
```bash
python src/main.py --min-severity major --github-repo owner/repo --pr-number 123
```

**Use different model:**
```bash
python src/main.py --model-id mistral:latest --github-repo owner/repo --pr-number 123
```

See [GITHUB_INTEGRATION.md](./GITHUB_INTEGRATION.md) for complete documentation and CI/CD integration examples.

## Current Features
- ✅ Two-agent orchestration (Reviewer + Coder)
- ✅ Hunk-based code analysis
- ✅ Multiple severity levels (nit, minor, major, blocker)
- ✅ Fix suggestion delegation to Coding Agent
- ✅ GitHub PR comment posting
- ✅ Line-specific review comments
- ✅ Dry-run mode for testing
- ✅ Progress feedback to stderr
- ✅ Structured output (Pydantic models)
- ✅ Environment variable support for authentication

## Architecture Details
- **Reviewer Agent:** Analyzes code diffs, identifies issues, severity assessment
- **Coding Agent:** Generates code fixes and suggestions when requested by reviewer
- **Response Models:** Type-safe structured outputs using Pydantic
- **GitHub Integration:** REST API for posting line-specific review comments
- **LLM Backend:** Ollama for local inference (supports any Ollama-compatible model)

## Next Steps (Future Work)
- [ ] Pre-commit hook integration
- [ ] Parallel hunk processing
- [ ] Static analysis tool integration
- [ ] Full-file context analysis option
- [ ] IDE extensions (VS Code, JetBrains)
- [ ] Dashboard for review trends


