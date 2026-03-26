import json
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel, ValidationError

from src.models.agent import LocalAgent


class AgentConfig(BaseModel):
    name: str
    base_prompt: str
    tasks: List[str] = []
    sub_agents: List[str] = []


def _build_prompt(config: AgentConfig) -> str:
    prompt_sections = [config.base_prompt.strip()]
    if config.tasks:
        tasks_block = "\n".join(f"- {task}" for task in config.tasks)
        prompt_sections.append(f"Tasks:\n{tasks_block}")
    if config.sub_agents:
        subs_block = ", ".join(config.sub_agents)
        prompt_sections.append(f"Sub-agents: {subs_block}")
    return "\n\n".join(prompt_sections)


def _discover_config_paths(config_dir: Path | None = None) -> List[Path]:
    base_dir = config_dir or Path(__file__).parent
    return sorted(base_dir.rglob("*.json"))


def load_agent_configs(config_dir: Path | None = None) -> List[AgentConfig]:
    configs: List[AgentConfig] = []

    for path in _discover_config_paths(config_dir):
        try:
            data = json.loads(path.read_text())
            configs.append(AgentConfig(**data))
        except (json.JSONDecodeError, ValidationError) as exc:
            print(f"Skipping {path}: {exc}")

    return configs


def setup_strands_agents(
    config_dir: Path | None = None,
    model_id: str | None = None,
    host_url: str | None = None,
    temperature: float = 0.7,
) -> Dict[str, dict]:
    """Load agent configs and instantiate Strands agents keyed by name.

    Returns a mapping of agent name to a dict with keys: agent, prompt, config.
    """

    agents: Dict[str, dict] = {}
    configs = load_agent_configs(config_dir)

    for config in configs:
        local = LocalAgent(
            model_id=model_id, host_url=host_url, temperature=temperature
        )
        local.setup_agent()
        agents[config.name] = {
            "agent": local.agent,
            "prompt": _build_prompt(config),
            "config": config,
        }

    return agents

def build_reviewer_prompt(hunk: DiffHunk, min_severity: str) -> str:
    prior = "\n".join(hunk.existing_comments or [])
    return (
        "You are the code review agent. Analyze the provided diff hunk and "
        "decide if a comment is warranted. If you need a concrete fix snippet, "
        "you may delegate to the Coding Agent.\n"
        "Input context:\n"
        f"- file: {hunk.file_path}\n"
        f"- start_line: {hunk.start_line}\n"
        f"- existing_thread: {prior or 'none'}\n"
        "- diff hunk:\n"
        f"{hunk.hunk}\n\n"
        "Provide your response as a structured object with these fields:\n"
        "- needs_comment (bool): Whether a comment is warranted\n"
        "- severity (str): One of 'nit', 'minor', 'major', 'blocker'\n"
        "- issue (str): Description of the identified issue\n"
        "- impact (str): Impact of the issue on code quality\n"
        "- ask_coder (bool): Whether to delegate fix generation to coding agent\n"
        "- coder_request (str or null): Precise ask for coder if ask_coder is true\n"
        "- suggestion (str or null): Initial suggestion or placeholder\n"
        "- line (int): Line number where comment should be placed\n\n"
        f"Enforce minimum severity: {min_severity}. If below threshold, set "
        "needs_comment=false."
    )


def build_coder_prompt(hunk: DiffHunk, request: str) -> str:
    return (
        "You are the coding agent. Provide a concise fix snippet.\n"
        f"File: {hunk.file_path}\n"
        f"Diff hunk:\n{hunk.hunk}\n\n"
        f"Task: {request}\n\n"
        "Provide your response as a structured object with these fields:\n"
        "- snippet (str): The code fix or implementation snippet\n"
        "- rationale (str): Explanation of the fix"
    )
