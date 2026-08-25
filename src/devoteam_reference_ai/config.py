"""Versioned YAML configuration loading and foundation validation."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(ValueError):
    """Raised when a required configuration contract is invalid."""


_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)(?::-([^}]*))?\}")


def _expand_environment(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_environment(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_environment(item) for item in value]
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        key, default = match.group(1), match.group(2)
        if key in os.environ:
            return os.environ[key]
        if default is not None:
            return default
        raise ConfigurationError(f"Required environment variable is missing: {key}")

    return _ENV_PATTERN.sub(replace, value)


def load_yaml(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        content = yaml.safe_load(handle)
    if not isinstance(content, dict):
        raise ConfigurationError(f"Configuration must be a mapping: {config_path}")
    return _expand_environment(content)


def load_project_configuration(project_root: str | Path) -> dict[str, dict[str, Any]]:
    root = Path(project_root)
    names = ("project", "security", "models", "filters", "logging")
    configuration = {name: load_yaml(root / "config" / f"{name}.yaml") for name in names}
    validate_project_configuration(configuration)
    return configuration


def validate_project_configuration(configuration: dict[str, dict[str, Any]]) -> None:
    required = {"project", "security", "models", "filters", "logging"}
    missing = sorted(required.difference(configuration))
    if missing:
        raise ConfigurationError(f"Missing configuration groups: {missing}")

    project = configuration["project"]
    security = configuration["security"]
    filters = configuration["filters"]
    models = configuration["models"]

    if project.get("project", {}).get("delivery_level") != "enterprise_pilot":
        raise ConfigurationError("Phase 0 decision A1 is not represented")
    if project.get("drive", {}).get("source_access_mode") != "read_only":
        raise ConfigurationError("Source Drive access must remain read_only")
    if project.get("write_policy", {}).get("original_source_mutation_allowed") is not False:
        raise ConfigurationError("Original source mutation must be disabled")
    if security.get("policy") != "D1":
        raise ConfigurationError("Security policy must be D1")
    if security.get("default_classification") != "INTERNAL":
        raise ConfigurationError("Unreviewed content must default to INTERNAL")
    expected_levels = {"PUBLIC", "INTERNAL", "RESTRICTED", "CONFIDENTIAL"}
    if set(security.get("classifications", {})) != expected_levels:
        raise ConfigurationError("D1 confidentiality levels are incomplete")
    if security.get("external_llm", {}).get("enabled") is not False:
        raise ConfigurationError("External LLM calls must start disabled")
    if filters.get("catalogue") != "G1":
        raise ConfigurationError("Filter catalogue must be G1")
    if filters.get("behavior", {}).get("allow_hidden_llm_filters") is not False:
        raise ConfigurationError("Hidden LLM filters must be disabled")
    if models.get("llm", {}).get("provider") != "provider_neutral":
        raise ConfigurationError("The LLM interface must remain provider-neutral")
