from __future__ import annotations

import json

from ops.integrations.common.cognos_client import cognos_chat_completions, format_cognos_verdict


def cognos_verify(prompt: str, draft_answer: str, mode: str = "monitor", policy_id: str = "default_v1") -> dict:
    messages = [
        {"role": "system", "content": "You are a verification gateway. Evaluate the draft answer against the prompt."},
        {"role": "user", "content": f"PROMPT:\n{prompt}\n\nDRAFT:\n{draft_answer}\n\nReturn a corrected answer if needed."},
    ]
    response = cognos_chat_completions(messages, mode=mode, policy_id=policy_id)

    corrected_answer = None
    try:
        corrected_answer = response["choices"][0]["message"]["content"]
    except Exception:
        corrected_answer = None

    return {
        "verdict": format_cognos_verdict(response),
        "decision": (response.get("cognos") or {}).get("decision"),
        "risk": (response.get("cognos") or {}).get("risk"),
        "trace_id": (response.get("cognos") or {}).get("trace_id") or (response.get("_cognos_headers") or {}).get("x_cognos_trace_id"),
        "corrected_answer": corrected_answer,
    }


if __name__ == "__main__":
    output = cognos_verify(
        prompt="Explain the EU AI Act risk categories briefly.",
        draft_answer="The EU AI Act has only two categories: safe and unsafe.",
        mode="monitor",
        policy_id="default_v1",
    )
    print(json.dumps(output, indent=2))
