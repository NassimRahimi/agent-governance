from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from agent_models import AgentInventory


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_inventory(path: str | Path, inventory: AgentInventory) -> None:
    write_json(path, inventory.model_dump(mode="json"))


def read_inventory(path: str | Path) -> AgentInventory:
    return AgentInventory.model_validate(read_json(path))


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def group_by_run_id(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[event.get("run_id", "missing-run-id")].append(event)
    return dict(grouped)
