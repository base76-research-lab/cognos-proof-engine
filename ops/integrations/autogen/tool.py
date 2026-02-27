from __future__ import annotations

from ops.integrations.common.cognos_client import cognos_chat_completions, format_cognos_verdict


def cognos_verify(prompt: str, draft_answer: str, mode: str = "monitor", policy_id: str = "default_v1") -> dict:
    messages = [
        {"role": "system", "content": "You are a verification gateway. Evaluate the draft answer against the prompt."},
        {"role": "user", "content": f"PROMPT:\n{prompt}\n\nDRAFT:\n{draft_answer}\n\nReturn a corrected answer if needed."},
    ]
    response = cognos_chat_completions(messages, mode=mode, policy_id=policy_id)
    return {
        "verdict": format_cognos_verdict(response),
        "cognos": response.get("cognos"),
        "headers": response.get("_cognos_headers"),
        "corrected_answer": ((response.get("choices") or [{}])[0].get("message") or {}).get("content"),
    }
