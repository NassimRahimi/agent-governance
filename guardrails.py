from __future__ import annotations

from pathlib import Path

from agent_models import AgentInventory, AgentRunPlan, GuardrailDecision
from state_utils import is_relative_match, normalize_path, resolve_under

UNSAFE_INTENT_KEYWORDS = {
    "delete",
    "remove all",
    "exfiltrate",
    "leak",
    "password",
    "secret",
    "payment card",
    "production database",
}


def _contains_unsafe_intent(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in UNSAFE_INTENT_KEYWORDS)


def runtime_guardrail(
    *,
    inventory: AgentInventory,
    plan: AgentRunPlan,
    repo_root: str = ".",
    output_root: str = "out",
) -> GuardrailDecision:
    agents = inventory.by_id()
    agent = agents.get(plan.agent_id)
    if agent is None:
        return GuardrailDecision(allowed=False, reason="Agent is not registered in inventory.", blocked_rule="unknown_agent")

    if plan.environment not in agent.environments:
        return GuardrailDecision(
            allowed=False,
            reason=f"Environment '{plan.environment}' is not allowed for this agent.",
            blocked_rule="environment_not_allowed",
        )

    for path in plan.read_paths:
        if not is_relative_match(path, agent.data_access.reads):
            return GuardrailDecision(
                allowed=False,
                reason=f"Read path is not allow-listed in inventory: {path}",
                blocked_rule="read_path_not_allowed",
            )

    for path in plan.write_paths:
        if not is_relative_match(path, agent.data_access.writes):
            return GuardrailDecision(
                allowed=False,
                reason=f"Write path is not allow-listed in inventory: {path}",
                blocked_rule="write_path_not_allowed",
            )

        try:
            resolved = resolve_under(Path(repo_root) / output_root, path)
        except ValueError as exc:
            return GuardrailDecision(allowed=False, reason=str(exc), blocked_rule="path_escape")

        if not normalize_path(resolved).endswith(normalize_path(path)):
            return GuardrailDecision(
                allowed=False,
                reason=f"Resolved path does not match requested path: {path}",
                blocked_rule="path_resolution_mismatch",
            )

    if _contains_unsafe_intent(plan.user_intent):
        return GuardrailDecision(
            allowed=False,
            reason="User intent includes unsafe or out-of-scope action keywords.",
            blocked_rule="unsafe_intent",
        )

    return GuardrailDecision(allowed=True, reason="All runtime guardrail checks passed.")
