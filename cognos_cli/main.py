from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx


def _base_url() -> str:
    return os.getenv("COGNOS_BASE_URL", "http://127.0.0.1:8788").rstrip("/")


def _headers() -> dict[str, str]:
    headers = {"content-type": "application/json"}
    api_key = os.getenv("COGNOS_API_KEY", "")
    upstream_auth = os.getenv("COGNOS_UPSTREAM_AUTH", "")

    if api_key:
        headers["x-api-key"] = api_key
    if upstream_auth:
        headers["x-cognos-upstream-authorization"] = upstream_auth

    return headers


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_chat(args: argparse.Namespace) -> int:
    url = f"{_base_url()}/v1/chat/completions"
    body: dict[str, Any] = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": False,
        "cognos": {
            "mode": args.mode,
            "policy_id": args.policy_id,
            "shadow_pct": args.shadow_pct,
            "shadow_models": args.shadow_models or [],
        },
    }
    if args.target_risk is not None:
        body["cognos"]["target_risk"] = args.target_risk

    with httpx.Client(timeout=args.timeout) as client:
        response = client.post(url, headers=_headers(), json=body)

    if response.status_code >= 400:
        print(response.text, file=sys.stderr)
        return 1

    payload = response.json()
    payload["_headers"] = {
        "X-Cognos-Trace-Id": response.headers.get("X-Cognos-Trace-Id"),
        "X-Cognos-Decision": response.headers.get("X-Cognos-Decision"),
        "X-Cognos-Trust-Score": response.headers.get("X-Cognos-Trust-Score"),
        "X-Cognos-Policy": response.headers.get("X-Cognos-Policy"),
    }
    _print_json(payload)
    return 0


def cmd_trace(args: argparse.Namespace) -> int:
    url = f"{_base_url()}/v1/traces/{args.trace_id}"
    with httpx.Client(timeout=args.timeout) as client:
        response = client.get(url, headers=_headers())

    if response.status_code >= 400:
        print(response.text, file=sys.stderr)
        return 1

    _print_json(response.json())
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    url = f"{_base_url()}/v1/reports/trust"
    body = {
        "trace_ids": args.trace_ids,
        "regime": args.regime,
        "format": args.format,
    }
    with httpx.Client(timeout=args.timeout) as client:
        response = client.post(url, headers=_headers(), json=body)

    if response.status_code >= 400:
        print(response.text, file=sys.stderr)
        return 1

    _print_json(response.json())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CognOS Trust Gateway CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat_parser = subparsers.add_parser("chat", help="Send one prompt through CognOS chat completions")
    chat_parser.add_argument("prompt", help="Prompt text")
    chat_parser.add_argument("--model", default=os.getenv("COGNOS_MODEL", "openai:gpt-4.1-mini"))
    chat_parser.add_argument("--mode", choices=["monitor", "enforce"], default=os.getenv("COGNOS_MODE", "monitor"))
    chat_parser.add_argument("--policy-id", default=os.getenv("COGNOS_POLICY_ID", "default_v1"))
    chat_parser.add_argument("--target-risk", type=float, default=None)
    chat_parser.add_argument("--shadow-pct", type=float, default=0.0)
    chat_parser.add_argument("--shadow-models", nargs="*", default=[])
    chat_parser.add_argument("--timeout", type=float, default=60.0)
    chat_parser.set_defaults(func=cmd_chat)

    trace_parser = subparsers.add_parser("trace", help="Get trace by trace_id")
    trace_parser.add_argument("trace_id")
    trace_parser.add_argument("--timeout", type=float, default=30.0)
    trace_parser.set_defaults(func=cmd_trace)

    report_parser = subparsers.add_parser("report", help="Create trust report for trace IDs")
    report_parser.add_argument("--trace-ids", nargs="+", required=True)
    report_parser.add_argument("--regime", default="EU_AI_ACT")
    report_parser.add_argument("--format", choices=["json", "pdf"], default="json")
    report_parser.add_argument("--timeout", type=float, default=30.0)
    report_parser.set_defaults(func=cmd_report)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
