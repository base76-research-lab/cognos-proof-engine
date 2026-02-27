from __future__ import annotations


def resolve_decision(mode: str, target_risk: float | None, base_risk: float = 0.12) -> tuple[str, float]:
    risk = min(max(base_risk, 0.0), 1.0)

    if mode == "monitor":
        return "PASS", risk

    threshold = target_risk if target_risk is not None else 0.5
    threshold = min(max(threshold, 0.0), 1.0)

    if risk <= threshold:
        return "PASS", risk
    if risk <= min(threshold + 0.2, 1.0):
        return "REFINE", risk
    if risk <= min(threshold + 0.4, 1.0):
        return "ESCALATE", risk
    return "BLOCK", risk
