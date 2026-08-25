"""Central logging configuration."""

from __future__ import annotations

import logging.config
from pathlib import Path

from .config import load_yaml


def configure_logging(project_root: str | Path) -> None:
    configuration = load_yaml(Path(project_root) / "config" / "logging.yaml")
    logging.config.dictConfig(configuration)
