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
