from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

TEST_DB = Path("/tmp/operational-cognos-oc002.sqlite3")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ.setdefault("COGNOS_MOCK_UPSTREAM", "true")
os.environ["COGNOS_TRACE_DB"] = str(TEST_DB)

from main import app


def run_smoke() -> None:
    with TestClient(app) as client:
        completion = client.post(
            "/v1/chat/completions",
            json={
                "model": "openai:gpt-4.1-mini",
                "messages": [{"role": "user", "content": "Trace check"}],
            },
        )

        if completion.status_code != 200:
            raise SystemExit(f"Completion call failed: {completion.status_code}")

        trace_id = completion.headers.get("X-Cognos-Trace-Id")
        if not trace_id:
            raise SystemExit("Missing X-Cognos-Trace-Id header")

        trace_response = client.get(f"/v1/traces/{trace_id}")
        if trace_response.status_code != 200:
            raise SystemExit(f"Trace endpoint failed: {trace_response.status_code}")

        trace_payload = trace_response.json()
        if trace_payload.get("trace_id") != trace_id:
            raise SystemExit("Trace payload mismatch")

        if not trace_payload.get("request_fingerprint", "").startswith("sha256:"):
            raise SystemExit("Missing or invalid request fingerprint")

        print("Smoke OK: trace persistence and GET /v1/traces/{trace_id} working")


if __name__ == "__main__":
    run_smoke()
