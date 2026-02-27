from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient
from models import TraceRecord, TrustReportResponse

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
        try:
            parsed_trace = TraceRecord.model_validate(trace_payload)
        except Exception as error:
            raise SystemExit(f"Trace schema validation failed: {error}")

        if parsed_trace.trace_id != trace_id:
            raise SystemExit("Trace payload mismatch")

        report_response = client.post(
            "/v1/reports/trust",
            json={
                "trace_ids": [trace_id, "missing-trace"],
                "regime": "EU_AI_ACT",
                "format": "json",
            },
        )
        if report_response.status_code != 200:
            raise SystemExit(f"Trust report endpoint failed: {report_response.status_code}")

        try:
            report = TrustReportResponse.model_validate(report_response.json())
        except Exception as error:
            raise SystemExit(f"Trust report schema validation failed: {error}")

        missing_ids = report.summary.get("missing_ids", [])
        if "missing-trace" not in missing_ids:
            raise SystemExit("Trust report missing_ids policy not respected")

        print("Smoke OK: TraceRecord and trust report contract validated")


if __name__ == "__main__":
    run_smoke()
