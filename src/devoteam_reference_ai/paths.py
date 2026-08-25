"""Safe project-path primitives that protect the read-only source boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class UnsafePathError(ValueError):
    """Raised when code attempts to write outside the approved project root."""


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def assert_safe_write_path(
    target: str | Path,
    project_root: str | Path,
    forbidden_roots: Iterable[str | Path] = (),
) -> Path:
    resolved_target = Path(target).expanduser().resolve()
    resolved_project = Path(project_root).expanduser().resolve()
    if not _is_within(resolved_target, resolved_project):
        raise UnsafePathError(f"Write target is outside project root: {resolved_target}")
    for forbidden in forbidden_roots:
        resolved_forbidden = Path(forbidden).expanduser().resolve()
        if _is_within(resolved_target, resolved_forbidden):
            raise UnsafePathError(f"Write target is inside a forbidden root: {resolved_target}")
    return resolved_target


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @classmethod
    def from_root(cls, root: str | Path) -> "ProjectPaths":
        return cls(Path(root).expanduser().resolve())

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def manifests(self) -> Path:
        return self.root / "manifests" / "runs"

    @property
    def data(self) -> Path:
        return self.root / "data"

    def create_runtime_directories(self) -> None:
        for path in (
            self.logs,
            self.manifests,
            self.data / "snapshots",
            self.data / "canonical",
            self.data / "indexes",
            self.root / "reports" / "generated",
        ):
            safe_path = assert_safe_write_path(path, self.root)
            safe_path.mkdir(parents=True, exist_ok=True)
