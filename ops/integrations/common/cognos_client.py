from __future__ import annotations

import os
import time
from typing import Any

import httpx


COGNOS_BASE_URL = os.getenv("COGNOS_BASE_URL", "http://127.0.0.1:8788")
COGNOS_API_KEY = os.getenv("COGNOS_API_KEY", "")
COGNOS_UPSTREAM_AUTH = os.getenv("COGNOS_UPSTREAM_AUTH", "")
DEFAULT_POLICY_ID = os.getenv("COGNOS_POLICY_ID", "default_v1")
DEFAULT_MODE = os.getenv("COGNOS_MODE", "monitor")
DEFAULT_MODEL = os.getenv("COGNOS_MODEL", "openai:gpt-4.1-mini")


class CognosError(RuntimeError):
    pass


def cognos_chat_completions(
    messages: list[dict[str, Any]],
    model: str = DEFAULT_MODEL,
    *,
    mode: str = DEFAULT_MODE,
    policy_id: str = DEFAULT_POLICY_ID,
    target_risk: float | None = None,
    shadow_pct: float = 0.0,
    shadow_models: list[str] | None = None,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
    url = f"{COGNOS_BASE_URL.rstrip('/')}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    if COGNOS_API_KEY:
        headers["x-api-key"] = COGNOS_API_KEY

    if COGNOS_UPSTREAM_AUTH:
        headers["x-cognos-upstream-authorization"] = COGNOS_UPSTREAM_AUTH

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "cognos": {
            "mode": mode,
            "policy_id": policy_id,
            "shadow_pct": shadow_pct,
            "shadow_models": shadow_models or [],
        },
    }
    if target_risk is not None:
        payload["cognos"]["target_risk"] = target_risk

    t0 = time.time()
    with httpx.Client(timeout=timeout_s) as client:
        response = client.post(url, json=payload, headers=headers)
    dt_ms = int((time.time() - t0) * 1000)

    if response.status_code >= 400:
        raise CognosError(f"HTTP {response.status_code}: {response.text[:500]}")

    data = response.json()
    data["_cognos_headers"] = {
        "x_cognos_trace_id": response.headers.get("X-Cognos-Trace-Id"),
        "x_cognos_policy": response.headers.get("X-Cognos-Policy"),
        "x_cognos_decision": response.headers.get("X-Cognos-Decision"),
        "x_cognos_trust_score": response.headers.get("X-Cognos-Trust-Score"),
        "latency_ms_client": dt_ms,
    }
    return data


def format_cognos_verdict(resp_json: dict[str, Any]) -> str:
    envelope = resp_json.get("cognos") or {}
    headers = resp_json.get("_cognos_headers") or {}

    decision = envelope.get("decision") or headers.get("x_cognos_decision") or "UNKNOWN"
    risk = envelope.get("risk")
    trace_id = envelope.get("trace_id") or headers.get("x_cognos_trace_id")
    policy = envelope.get("policy") or headers.get("x_cognos_policy")
    signals = envelope.get("signals") or {}

    lines: list[str] = [f"decision: {decision}"]
    if isinstance(risk, (int, float)):
        lines.append(f"risk: {risk:.3f}")
    if trace_id:
        lines.append(f"trace_id: {trace_id}")
    if policy:
        lines.append(f"policy: {policy}")

    for key in ("ue", "ua", "divergence"):
        value = signals.get(key)
        if isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")

    return "\n".join(lines)
