# Agent Governance Runtime Controls Demo

A Python demo for governing AI-agent workflows with inventory, runtime guardrails, audit logs, and production-readiness checks.

The demo is intentionally small and deterministic. It does not require an LLM API key. The goal is to show the control pattern clearly:

```text
agent inventory → run plan → runtime guardrail → controlled tool execution → audit log → readiness gate
```

## Why this matters for AI Governance

This demo is a small, runnable expression of three controls every AI governance function asks for in production:

- **Risk classification → readiness gate.** `readiness_check.py` decides whether a run is acceptable for promotion based on artifacts (inventory, audit log, blocked-action evidence), not opinion. Blocked behavior must be reviewed before promotion — the same risk-proportionate gate logic used to decide which AI systems can run unattended and which require human review.
- **Runtime controls → guardrails + allow-lists.** `guardrails.py` enforces read/write allow-lists, path containment, and tool permissions before any action runs. Agent task logic and governance controls are kept separate, so the same guardrail layer can be reused across agents without rewriting agent code.
- **Auditability → JSONL event log with run_id.** `audit_logs.py` writes structured JSONL events with `run_id`, `operation_id`, attempted action, decision (allowed / blocked), and outcome. The log is scannable for violations, risky tools, and anomalies — the evidence trail a regulator, internal audit, or model-risk function actually needs.

The repo is intentionally deterministic and requires no LLM API key, so the control pattern is the focus, not the model.

## What this demonstrates

- Agent inventory as the source of governance metadata
- Separation between agent task logic and governance controls
- Read/write allow-lists for tool access
- Path containment checks to prevent unsafe writes
- Structured JSONL audit logging with run IDs
- Audit-log scanning for violations, risky tools, and anomalies
- Production-readiness gate based on artifacts, not opinion

## Repository structure

```text
.
├── main.py                  # Runs a safe and blocked agent execution demo
├── agent_models.py          # Pydantic governance models
├── agent_definitions.py     # Deterministic demo agents and tool wrappers
├── agent_io.py              # Inventory and JSONL helpers
├── guardrails.py            # Runtime guardrail enforcement
├── observability.py         # Structured logging and run IDs
├── audit_logs.py            # Audit-log scanner
├── readiness_check.py       # Production-readiness gate
├── state_utils.py           # Safe path helpers
├── data/                    # Synthetic input data
├── inventory/               # Static inventory source of truth
└── .github/workflows/       # CI check
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

Run the demo:

```bash
python main.py
```

This creates local runtime artifacts:

```text
logs/agent_events.jsonl
out/procurement_summary.json
```

Scan the audit log:

```bash
python audit_logs.py --log logs/agent_events.jsonl
```

Run the readiness gate:

```bash
python readiness_check.py \
  --inventory inventory/agent_inventory.json \
  --log logs/agent_events.jsonl
```

The default demo runs one allowed execution and one intentionally blocked execution. Therefore, the readiness gate should report `NOT_READY`, because blocked behavior must be reviewed before promotion.

## Run only the allowed path

```bash
rm -rf logs out
python main.py --mode allow
python readiness_check.py --inventory inventory/agent_inventory.json --log logs/agent_events.jsonl
```

## Governance interpretation

This demo uses a simple procurement-intake workflow:

- The **agent** reads a request and writes a structured summary.
- The **inventory** defines what the agent is allowed to read/write.
- The **guardrail** enforces the inventory before any action runs.
- The **log** proves what was attempted, allowed, blocked, and completed.
- The **readiness gate** decides whether the run is acceptable for promotion.

## Public-use note

Demonstration repo. Patterns shown here mirror controls used in regulated enterprise environments.
