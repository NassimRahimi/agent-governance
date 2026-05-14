from __future__ import annotations

import argparse
import os
from pathlib import Path

from agent_definitions import (
    PROCUREMENT_AGENT_ID,
    PROCUREMENT_AGENT_NAME,
    RESEARCH_AGENT_ID,
    RESEARCH_AGENT_NAME,
    run_procurement_intake_agent,
)
from agent_io import write_inventory
from agent_models import AgentInventory, AgentInventoryItem, AgentRunPlan, DataAccess, RiskLevel, ToolAccess
from guardrails import runtime_guardrail
from observability import default_log_path, log_event, new_run_id, summarize_run

INPUT_PATH = "data/procurement_request.txt"
ALLOWED_OUTPUT_PATH = "out/procurement_summary.json"
BLOCKED_OUTPUT_PATH = "out/forbidden_summary.json"
INVENTORY_PATH = "inventory/agent_inventory.json"


def build_inventory() -> AgentInventory:
    return AgentInventory(
        agents=[
            AgentInventoryItem(
                agent_id=PROCUREMENT_AGENT_ID,
                name=PROCUREMENT_AGENT_NAME,
                purpose="Reads an approved procurement request and writes a structured local summary.",
                owner="AI Platform Team",
                environments=["dev"],
                risk_level=RiskLevel.MEDIUM,
                tool_access=[
                    ToolAccess(name="read_local_text", description="Read approved local request file.", actions=["read"]),
                    ToolAccess(name="write_local_json", description="Write approved structured output file.", actions=["write"]),
                ],
                data_access=DataAccess(reads=[INPUT_PATH], writes=[ALLOWED_OUTPUT_PATH]),
                requires_human_review=False,
            ),
            AgentInventoryItem(
                agent_id=RESEARCH_AGENT_ID,
                name=RESEARCH_AGENT_NAME,
                purpose="Represents a read-only market research capability for vendor information.",
                owner="AI Platform Team",
                environments=["dev"],
                risk_level=RiskLevel.LOW,
                tool_access=[ToolAccess(name="search_vendor_catalog", description="Read-only vendor catalog lookup.", actions=["read"]),],
                data_access=DataAccess(reads=["data/vendor_catalog.json"], writes=[]),
                requires_human_review=False,
            ),
        ]
    )


def run_once(mode: str, *, run_id: str, log_path: str, environment: str) -> None:
    output_path = ALLOWED_OUTPUT_PATH if mode == "allow" else BLOCKED_OUTPUT_PATH
    plan = AgentRunPlan(
        agent_id=PROCUREMENT_AGENT_ID,
        agent_name=PROCUREMENT_AGENT_NAME,
        environment=environment,
        read_paths=[INPUT_PATH],
        write_paths=[output_path],
        user_intent="Summarize approved procurement request into structured JSON.",
    )

    inventory = build_inventory()
    decision = runtime_guardrail(inventory=inventory, plan=plan)

    log_event(
        log_path,
        "guardrail_allowed" if decision.allowed else "guardrail_blocked",
        run_id,
        agent_id=plan.agent_id,
        agent_name=plan.agent_name,
        reason=decision.reason,
        blocked_rule=decision.blocked_rule,
        mode=mode,
    )

    if not decision.allowed:
        log_event(log_path, "agent_run_blocked", run_id, agent_id=plan.agent_id, reason=decision.reason, mode=mode)
        print(f"BLOCKED [{mode}]: {decision.reason}")
        return

    run_procurement_intake_agent(input_path=INPUT_PATH, output_path=output_path, run_id=run_id, log_path=log_path)
    print(f"ALLOWED [{mode}]: wrote {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agent governance runtime-control demo.")
    parser.add_argument("--mode", choices=["allow", "block", "both"], default="both")
    parser.add_argument("--log", default=default_log_path())
    parser.add_argument("--env", default=os.getenv("AGENT_ENV", "dev"))
    args = parser.parse_args()

    Path("inventory").mkdir(exist_ok=True)
    write_inventory(INVENTORY_PATH, build_inventory())

    run_id = new_run_id()
    log_event(args.log, "run_started", run_id, environment=args.env, inventory_path=INVENTORY_PATH)

    modes = ["allow", "block"] if args.mode == "both" else [args.mode]
    for mode in modes:
        run_once(mode, run_id=run_id, log_path=args.log, environment=args.env)

    log_event(args.log, "run_completed", run_id, status="ok", event_counts=summarize_run(args.log, run_id))
    print(f"Run ID: {run_id}")
    print(f"Log: {args.log}")


if __name__ == "__main__":
    main()
