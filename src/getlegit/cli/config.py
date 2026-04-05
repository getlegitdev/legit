"""Configuration reader/writer for legit.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    name: str
    endpoint: str
    timeout: int = 300


class BenchmarkConfig(BaseModel):
    version: str = "v1"
    categories: list[str] = Field(default_factory=lambda: ["all"])


class OutputConfig(BaseModel):
    dir: str = ".legit/results"


class LegitConfig(BaseModel):
    agent: AgentConfig
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


DEFAULT_CONFIG_NAME = "legit.yaml"


def create_config(
    agent_name: str,
    agent_endpoint: str,
    path: Path | None = None,
) -> Path:
    """Create a new legit.yaml configuration file."""
    config = LegitConfig(
        agent=AgentConfig(name=agent_name, endpoint=agent_endpoint),
    )
    config_path = (path or Path.cwd()) / DEFAULT_CONFIG_NAME
    config_path.write_text(
        yaml.dump(config.model_dump(), default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return config_path


def load_config(path: Path | None = None) -> LegitConfig:
    """Load and validate legit.yaml from the given directory or cwd."""
    config_path = (path or Path.cwd()) / DEFAULT_CONFIG_NAME
    if not config_path.exists():
        raise FileNotFoundError(
            f"No {DEFAULT_CONFIG_NAME} found in {config_path.parent}. "
            "Run `legit init` first."
        )
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return LegitConfig(**raw)


def results_dir(config: LegitConfig, base: Path | None = None) -> Path:
    """Return the results directory, creating it if needed."""
    rd = (base or Path.cwd()) / config.output.dir
    rd.mkdir(parents=True, exist_ok=True)
    return rd
