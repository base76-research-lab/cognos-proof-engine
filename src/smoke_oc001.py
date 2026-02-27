from __future__ import annotations

import os

from fastapi.testclient import TestClient
from models import ChatCompletionResponse

os.environ.setdefault("COGNOS_MOCK_UPSTREAM", "true")

from main import app


def run_smoke() -> None:
    failures = 0

    with TestClient(app) as client:
        for index in range(100):
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai:gpt-4.1-mini",
                    "messages": [{"role": "user", "content": f"Ping {index}"}],
                },
            )

            if response.status_code != 200:
                failures += 1
                continue

            trace_header = response.headers.get("X-Cognos-Trace-Id")
            if not trace_header:
                failures += 1

            if not response.headers.get("X-Cognos-Decision"):
                failures += 1
            if not response.headers.get("X-Cognos-Trust-Score"):
                failures += 1
            if not response.headers.get("X-Cognos-Policy"):
                failures += 1

            body = response.json()
            try:
                parsed = ChatCompletionResponse.model_validate(body)
            except Exception:
                failures += 1
                continue

            if parsed.cognos.decision not in {"PASS", "REFINE", "ESCALATE", "BLOCK"}:
                failures += 1

        invalid = client.post(
            "/v1/chat/completions",
            json={
                "model": "openai:gpt-4.1-mini",
                "messages": [{"role": "user", "content": "invalid enum check"}],
                "cognos": {"mode": "invalid-mode"},
            },
        )
        if invalid.status_code != 400:
            failures += 1

    if failures:
        raise SystemExit(f"Smoke failed: {failures} / 100 requests did not pass requirements")

    print("Smoke OK: contract headers, enums, and required fields validated")


if __name__ == "__main__":
    run_smoke()
