from __future__ import annotations

from ops.integrations.common.cognos_client import cognos_chat_completions, format_cognos_verdict


class CognosVerify:
    name = "cognos_verify"
    description = "Verify a draft answer using CognOS Trust Gateway"

    def run(self, prompt: str, draft_answer: str, mode: str = "monitor", policy_id: str = "default_v1") -> str:
        messages = [
            {"role": "system", "content": "You are a verification gateway. Evaluate the draft answer against the prompt."},
            {"role": "user", "content": f"PROMPT:\n{prompt}\n\nDRAFT:\n{draft_answer}\n\nReturn a corrected answer if needed."},
        ]
        response = cognos_chat_completions(messages, mode=mode, policy_id=policy_id)

        corrected = ((response.get("choices") or [{}])[0].get("message") or {}).get("content", "")
        return f"{format_cognos_verdict(response)}\n\ncorrected_answer:\n{corrected}"
