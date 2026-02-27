from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("COGNOS_MOCK_UPSTREAM", "true")

from main import app


def run_smoke() -> None:
    client = TestClient(app)
    failures = 0

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

    if failures:
        raise SystemExit(f"Smoke failed: {failures} / 100 requests did not pass requirements")

    print("Smoke OK: 100/100 requests passed with X-Cognos-Trace-Id")


if __name__ == "__main__":
    run_smoke()
