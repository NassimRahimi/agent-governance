from __future__ import annotations

from pathlib import Path


def normalize_path(path: str | Path) -> str:
    return str(Path(path).as_posix())


def resolve_under(base_dir: str | Path, candidate: str | Path) -> Path:
    base = Path(base_dir).resolve()
    target = Path(candidate).resolve()
    if target != base and base not in target.parents:
        raise ValueError(f"Path escapes allowed base directory: {candidate}")
    return target


def is_relative_match(candidate: str | Path, allowed: list[str]) -> bool:
    normalized = normalize_path(candidate)
    return normalized in {normalize_path(item) for item in allowed}


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
