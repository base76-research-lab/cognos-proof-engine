from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx


def _build_headers(api_key: str | None) -> dict[str, str]:
    headers = {"content-type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    return headers


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text


def run_poc(args: argparse.Namespace) -> int:
    headers = _build_headers(args.api_key)
    base_url = args.base_url.rstrip("/")

    completion_payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "cognos": {"mode": args.mode},
    }

    with httpx.Client(timeout=args.timeout_seconds) as client:
        completion = client.post(f"{base_url}/v1/chat/completions", headers=headers, json=completion_payload)

        if completion.status_code >= 400:
            print("[POC] chat/completions failed")
            print(f"status={completion.status_code}")
            print(json.dumps(_safe_json(completion), ensure_ascii=False, indent=2))
            return 1

        completion_body = _safe_json(completion)
        trace_id = completion.headers.get("X-Cognos-Trace-Id")
        if not trace_id and isinstance(completion_body, dict):
            cognos_obj = completion_body.get("cognos", {})
            if isinstance(cognos_obj, dict):
                trace_id = cognos_obj.get("trace_id")

        if not trace_id:
            print("[POC] missing trace_id in headers/body")
            return 1

        print("[POC] completion ok")
        print(f"trace_id={trace_id}")
        print(f"decision={completion.headers.get('X-Cognos-Decision', 'n/a')}")
        print(f"trust_score={completion.headers.get('X-Cognos-Trust-Score', 'n/a')}")

        trace_response = client.get(f"{base_url}/v1/traces/{trace_id}", headers=headers)
        if trace_response.status_code >= 400:
            print("[POC] trace lookup failed")
            print(f"status={trace_response.status_code}")
            print(json.dumps(_safe_json(trace_response), ensure_ascii=False, indent=2))
            return 1

        trace_body = _safe_json(trace_response)
        trace_status = "ok" if isinstance(trace_body, dict) and trace_body.get("trace_id") == trace_id else "unexpected"
        print(f"[POC] trace lookup {trace_status}")

        report_payload = {"trace_ids": [trace_id], "regime": args.regime, "format": "json"}
        report_response = client.post(f"{base_url}/v1/reports/trust", headers=headers, json=report_payload)
        if report_response.status_code >= 400:
            print("[POC] trust report failed")
            print(f"status={report_response.status_code}")
            print(json.dumps(_safe_json(report_response), ensure_ascii=False, indent=2))
            return 1

        report_body = _safe_json(report_response)
        summary = report_body.get("summary", {}) if isinstance(report_body, dict) else {}
        print("[POC] trust report ok")
        print(f"found_count={summary.get('found_count')}")
        print(f"missing_count={summary.get('missing_count')}")

    print("[POC] SUCCESS: end-to-end flow verified")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CognOS proof-of-concept end-to-end check.")
    parser.add_argument("--base-url", default=os.getenv("COGNOS_BASE_URL", "http://127.0.0.1:8788"))
    parser.add_argument("--api-key", default=os.getenv("COGNOS_API_KEY", ""))
    parser.add_argument("--model", default=os.getenv("COGNOS_POC_MODEL", "openai:gpt-4o-mini"))
    parser.add_argument(
        "--prompt",
        default="Proofread and stress-test my concept pitch in 5 bullets.",
    )
    parser.add_argument("--mode", default="monitor", choices=["monitor", "enforce"])
    parser.add_argument("--regime", default="EU_AI_ACT")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(run_poc(_parse_args()))
