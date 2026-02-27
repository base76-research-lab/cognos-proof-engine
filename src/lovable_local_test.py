from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

# Local deterministic test settings
os.environ.setdefault("COGNOS_MOCK_UPSTREAM", "true")
os.environ.setdefault("COGNOS_TRACE_DB", "/tmp/operational-cognos-lovable-local.sqlite3")

from main import app


def run() -> tuple[Path, Path]:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")

    out_dir = Path("docs/proofs") / f"lovable_local_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt = (
        "Create a precise Lovable build brief for a single-page product landing page for CognOS. "
        "Must include scope in/out, exact sections, CTA copy, and acceptance criteria."
    )

    payload = {
        "model": "openai:gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "cognos": {"mode": "monitor"},
    }

    with TestClient(app) as client:
        completion = client.post("/v1/chat/completions", json=payload)
        completion.raise_for_status()

        completion_json = completion.json()
        trace_id = completion.headers.get("X-Cognos-Trace-Id") or completion_json.get("cognos", {}).get("trace_id")

        trace = client.get(f"/v1/traces/{trace_id}")
        trace.raise_for_status()

        report = client.post(
            "/v1/reports/trust",
            json={"trace_ids": [trace_id], "regime": "EU_AI_ACT", "format": "json"},
        )
        report.raise_for_status()

    result = {
        "timestamp": now.isoformat(),
        "mode": "local_testclient_mock_upstream",
        "prompt": prompt,
        "chat_status": completion.status_code,
        "trace_id": trace_id,
        "decision": completion.headers.get("X-Cognos-Decision"),
        "trust_score": completion.headers.get("X-Cognos-Trust-Score"),
        "trace_status": trace.status_code,
        "report_status": report.status_code,
        "report_summary": report.json().get("summary", {}),
        "completion_preview": completion_json.get("choices", [{}])[0].get("message", {}).get("content", "")[:600],
    }

    json_path = out_dir / "result.json"
    md_path = out_dir / "summary.md"

    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_md = (
        "# Lovable Local CognOS Test\n\n"
        f"- Timestamp: `{result['timestamp']}`\n"
        f"- Mode: `{result['mode']}`\n"
        f"- chat status: `{result['chat_status']}`\n"
        f"- trace id: `{result['trace_id']}`\n"
        f"- decision: `{result['decision']}`\n"
        f"- trust score: `{result['trust_score']}`\n"
        f"- trace status: `{result['trace_status']}`\n"
        f"- report status: `{result['report_status']}`\n"
        f"- report summary: `{result['report_summary']}`\n\n"
        "## Completion preview\n\n"
        f"{result['completion_preview']}\n"
    )
    md_path.write_text(summary_md, encoding="utf-8")

    return json_path, md_path


if __name__ == "__main__":
    json_path, md_path = run()
    print(f"RESULT_JSON={json_path}")
    print(f"RESULT_MD={md_path}")
