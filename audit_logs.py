from __future__ import annotations

import argparse
from collections import Counter

from agent_io import group_by_run_id, load_jsonl

VIOLATION_EVENTS = {"guardrail_blocked", "agent_run_blocked"}
RISKY_TOOL_KEYWORDS = {"write", "delete", "remove", "update"}
WEB_TOOL_KEYWORDS = {"web", "search", "http", "vendor_catalog"}


def _contains_keyword(value: str, keywords: set[str]) -> bool:
    return any(keyword in value.lower() for keyword in keywords)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan agent JSONL logs for governance signals.")
    parser.add_argument("--log", required=True, help="Path to logs/agent_events.jsonl")
    args = parser.parse_args()

    events = load_jsonl(args.log)
    grouped = group_by_run_id(events)

    print(f"Runs found: {len(grouped)}")
    for run_id, run_events in grouped.items():
        counts = Counter(event.get("event_type", "unknown") for event in run_events)
        violations = [event for event in run_events if event.get("event_type") in VIOLATION_EVENTS]
        risky_tools = [
            event
            for event in run_events
            if event.get("event_type") == "tool_invoked" and _contains_keyword(str(event.get("tool", "")), RISKY_TOOL_KEYWORDS)
        ]
        web_tools = [
            event
            for event in run_events
            if event.get("event_type") == "tool_invoked" and _contains_keyword(str(event.get("tool", "")), WEB_TOOL_KEYWORDS)
        ]

        invoked = [event for event in run_events if event.get("event_type") == "tool_invoked"]
        completed = [event for event in run_events if event.get("event_type") == "tool_completed"]
        completed_keys = {(event.get("agent_id"), event.get("tool"), event.get("path")) for event in completed}
        anomalies = [
            event
            for event in invoked
            if (event.get("agent_id"), event.get("tool"), event.get("path")) not in completed_keys
        ]

        print("\n--- Run", run_id, "---")
        print("Event counts:", dict(counts))
        print("Violations:", len(violations))
        for event in violations:
            print(f"  - {event.get('event_type')}: {event.get('reason')}")
        print("Risky local write/update tools:", len(risky_tools))
        for event in risky_tools:
            print(f"  - {event.get('tool')} -> {event.get('path')}")
        print("Web/catalog tools:", len(web_tools))
        print("Anomalies invoked_without_completed:", len(anomalies))


if __name__ == "__main__":
    main()
