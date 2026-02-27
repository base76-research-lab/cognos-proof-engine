from __future__ import annotations

from pydantic import BaseModel, Field

from ops.integrations.common.cognos_client import cognos_chat_completions, format_cognos_verdict

try:
    from langchain_core.tools import BaseTool
except Exception:
    class BaseTool:  # type: ignore[override]
        pass


class CognosVerifyInput(BaseModel):
    prompt: str = Field(..., description="User prompt")
    draft_answer: str = Field(..., description="Draft answer to verify")
    mode: str = Field("monitor", description="monitor|enforce")
    policy_id: str = Field("default_v1", description="Policy identifier")


class CognosVerifyTool(BaseTool):
    name: str = "cognos_verify"
    description: str = "Verify a draft answer using CognOS Trust Gateway"
    args_schema = CognosVerifyInput

    def _run(self, prompt: str, draft_answer: str, mode: str = "monitor", policy_id: str = "default_v1") -> str:
        messages = [
            {"role": "system", "content": "You are a verification gateway. Evaluate the draft answer against the prompt."},
            {"role": "user", "content": f"PROMPT:\n{prompt}\n\nDRAFT:\n{draft_answer}\n\nReturn a corrected answer if needed."},
        ]
        response = cognos_chat_completions(messages, mode=mode, policy_id=policy_id)

        corrected = ""
        try:
            corrected = response["choices"][0]["message"]["content"]
        except Exception:
            corrected = ""

        return f"{format_cognos_verdict(response)}\n\ncorrected_answer:\n{corrected}"
