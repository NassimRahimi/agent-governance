from __future__ import annotations

import re
from pathlib import Path

from agent_io import write_json
from agent_models import ProcurementSummary
from observability import log_event, utc_now

PROCUREMENT_AGENT_ID = "agent.procurement-intake.v1"
PROCUREMENT_AGENT_NAME = "Procurement Intake Agent"
RESEARCH_AGENT_ID = "agent.vendor-research.v1"
RESEARCH_AGENT_NAME = "Vendor Research Agent"


def read_local_text(path: str, *, run_id: str, log_path: str, agent_id: str) -> str:
    log_event(log_path, "tool_invoked", run_id, agent_id=agent_id, tool="read_local_text", path=path)
    text = Path(path).read_text(encoding="utf-8")
    log_event(
        log_path,
        "tool_completed",
        run_id,
        agent_id=agent_id,
        tool="read_local_text",
        path=path,
        status="ok",
        output_characters=len(text),
    )
    return text


def write_local_json(path: str, payload: dict, *, run_id: str, log_path: str, agent_id: str) -> None:
    log_event(log_path, "tool_invoked", run_id, agent_id=agent_id, tool="write_local_json", path=path)
    try:
        write_json(path, payload)
        log_event(log_path, "tool_completed", run_id, agent_id=agent_id, tool="write_local_json", path=path, status="ok")
    except Exception as exc:
        log_event(
            log_path,
            "tool_completed",
            run_id,
            agent_id=agent_id,
            tool="write_local_json",
            path=path,
            status="error",
            error=repr(exc),
        )
        raise


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_list_after(label: str, text: str) -> list[str]:
    value = _first_match(rf"{re.escape(label)}:\s*(.+)", text)
    if not value:
        return []
    value = value.rstrip(".")
    return [item.strip() for item in value.split(",") if item.strip()]


def run_procurement_intake_agent(
    *,
    input_path: str,
    output_path: str,
    run_id: str,
    log_path: str,
) -> ProcurementSummary:
    log_event(
        log_path,
        "agent_run_started",
        run_id,
        agent_id=PROCUREMENT_AGENT_ID,
        agent_name=PROCUREMENT_AGENT_NAME,
        input_path=input_path,
        output_path=output_path,
    )

    text = read_local_text(input_path, run_id=run_id, log_path=log_path, agent_id=PROCUREMENT_AGENT_ID)

    summary = ProcurementSummary(
        input_file=input_path,
        budget=_first_match(r"Budget:\s*(.+)", text),
        key_needs=_extract_list_after("Must have", text),
        restrictions=_extract_list_after("Restrictions", text),
        delivery_target=_first_match(r"Delivery target:\s*(.+)", text),
        requester=_first_match(r"Requester:\s*(.+)", text),
        summary="Structured procurement request summary generated from approved local input.",
        output_file=output_path,
        created_at=utc_now(),
    )

    write_local_json(
        output_path,
        summary.model_dump(mode="json"),
        run_id=run_id,
        log_path=log_path,
        agent_id=PROCUREMENT_AGENT_ID,
    )

    log_event(log_path, "agent_output_validated", run_id, agent_id=PROCUREMENT_AGENT_ID, status="ok")
    log_event(log_path, "agent_run_completed", run_id, agent_id=PROCUREMENT_AGENT_ID, status="ok")
    return summary
