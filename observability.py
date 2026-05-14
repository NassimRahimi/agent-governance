from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Any


def new_run_id() -> str:
    return str(uuid4())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_log_path() -> str:
    return os.getenv("LOG_PATH", "logs/agent_events.jsonl")


def log_event(log_path: str | Path, event_type: str, run_id: str, **fields: Any) -> None:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": utc_now(),
        "run_id": run_id,
        "event_type": event_type,
        **fields,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def summarize_run(log_path: str | Path, run_id: str) -> dict[str, int]:
    path = Path(log_path)
    if not path.exists():
        return {}
    counts: Counter[str] = Counter()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("run_id") == run_id:
                counts[event.get("event_type", "unknown")] += 1
    return dict(counts)
