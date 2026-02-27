from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from ops.integrations.common.cognos_client import cognos_chat_completions, format_cognos_verdict

app = FastAPI(title="CognOS MCP-Compatible Tool Bridge", version="0.1.0")


class VerifyIn(BaseModel):
    prompt: str
    draft_answer: str
    mode: str = "monitor"
    policy_id: str = "default_v1"


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.post("/tools/cognos_verify")
def cognos_verify(input_data: VerifyIn) -> dict:
    messages = [
        {"role": "system", "content": "You are a verification gateway. Evaluate the draft answer against the prompt."},
        {
            "role": "user",
            "content": (
                f"PROMPT:\n{input_data.prompt}\n\n"
                f"DRAFT:\n{input_data.draft_answer}\n\n"
                "Return a corrected answer if needed."
            ),
        },
    ]

    response = cognos_chat_completions(messages, mode=input_data.mode, policy_id=input_data.policy_id)

    corrected_answer = None
    try:
        corrected_answer = response["choices"][0]["message"]["content"]
    except Exception:
        corrected_answer = None

    return {
        "verdict": format_cognos_verdict(response),
        "cognos": response.get("cognos"),
        "headers": response.get("_cognos_headers"),
        "corrected_answer": corrected_answer,
    }
