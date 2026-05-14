from __future__ import annotations

import argparse

from agent_io import group_by_run_id, load_jsonl, read_inventory
from agent_models import ReadinessResult, ReadinessStatus, RiskLevel

REQUIRED_INVENTORY_FIELDS = ["owner", "risk_level", "environments", "tool_access", "data_access"]


def _latest_run_id(events: list[dict]) -> str | None:
    if not events:
        return None
    return events[-1].get("run_id")


def _check_inventory_completeness(inventory_path: str) -> list[str]:
    inventory = read_inventory(inventory_path)
    reasons: list[str] = []
    for agent in inventory.agents:
        raw = agent.model_dump(mode="json")
        for field in REQUIRED_INVENTORY_FIELDS:
            value = raw.get(field)
            if value in (None, "", [], {}):
                reasons.append(f"Inventory incomplete for {agent.agent_id}: missing {field}")
        if agent.risk_level == RiskLevel.HIGH and not agent.requires_human_review:
            reasons.append(f"High-risk agent must require human review: {agent.agent_id}")
    return reasons


def _check_run(events: list[dict]) -> list[str]:
    reasons: list[str] = []
    for event in events:
        if event.get("event_type") == "guardrail_blocked":
            reasons.append(f"Guardrail block found: {event.get('reason')}")
        if event.get("event_type") == "agent_run_blocked":
            reasons.append(f"Agent run blocked: {event.get('reason')}")

    invoked = [event for event in events if event.get("event_type") == "tool_invoked"]
    completed = [event for event in events if event.get("event_type") == "tool_completed"]
    completed_keys = {(event.get("agent_id"), event.get("tool"), event.get("path")) for event in completed}
    for event in invoked:
        key = (event.get("agent_id"), event.get("tool"), event.get("path"))
        if key not in completed_keys:
            reasons.append(f"Tool invoked without completion: {event.get('tool')} {event.get('path')}")
    return reasons


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate agent production readiness from inventory and logs.")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--run-id", required=False)
    args = parser.parse_args()

    events = load_jsonl(args.log)
    grouped = group_by_run_id(events)
    run_id = args.run_id or _latest_run_id(events)
    selected_events = grouped.get(run_id, []) if run_id else []

    reasons = []
    reasons.extend(_check_inventory_completeness(args.inventory))
    if not run_id:
        reasons.append("No run ID found in event log.")
    else:
        reasons.extend(_check_run(selected_events))

    status = ReadinessStatus.READY if not reasons else ReadinessStatus.NOT_READY
    result = ReadinessResult(status=status, run_id=run_id, reasons=reasons)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
