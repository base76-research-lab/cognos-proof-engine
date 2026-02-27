from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from models import ChatCompletionRequest, ChatCompletionResponse, TraceRecord, TrustReportRequest, TrustReportResponse
from policy import resolve_decision
from reports import build_trust_report
from trace_store import get_trace, init_db, save_trace

app = FastAPI(title="Operational Cognos Gateway", version="0.1.0")

UPSTREAM_BASE_URL = os.getenv("COGNOS_UPSTREAM_BASE_URL", "https://api.openai.com/v1")
UPSTREAM_API_KEY = os.getenv("COGNOS_UPSTREAM_API_KEY", "")
DEFAULT_POLICY = os.getenv("COGNOS_DEFAULT_POLICY", "default_v1")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("COGNOS_REQUEST_TIMEOUT_SECONDS", "120"))
MOCK_UPSTREAM = os.getenv("COGNOS_MOCK_UPSTREAM", "false").lower() in {"1", "true", "yes"}
GATEWAY_API_KEY = os.getenv("COGNOS_GATEWAY_API_KEY", "")


@app.on_event("startup")
async def on_startup() -> None:
    init_db()


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "operational-cognos-gateway"}


@app.get("/v1/traces/{trace_id}")
async def trace_by_id(trace_id: str) -> dict[str, Any]:
    trace = get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return TraceRecord.model_validate(trace).model_dump(mode="json")


@app.post("/v1/reports/trust")
async def create_trust_report(request: Request) -> dict[str, Any]:
    _require_gateway_auth(request.headers)
    try:
        payload = await request.json()
        report_request = TrustReportRequest.model_validate(payload)
    except ValidationError as error:
        raise HTTPException(status_code=400, detail=json.loads(error.json()))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {error}")

    report = build_trust_report(report_request.trace_ids, regime=report_request.regime, fmt=report_request.format)
    return TrustReportResponse.model_validate(report).model_dump(mode="json")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Response:
    _require_gateway_auth(request.headers)
    trace_id = f"tr_{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc).isoformat()

    try:
        payload = await request.json()
        request_model = ChatCompletionRequest.model_validate(payload)
        payload = request_model.model_dump(exclude_none=True)
        cognos_cfg = request_model.cognos
    except Exception as error:
        if isinstance(error, ValidationError):
            raise HTTPException(status_code=400, detail=json.loads(error.json()))
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {error}")

    model = request_model.model
    decision, risk = resolve_decision(cognos_cfg.mode, cognos_cfg.target_risk)
    active_policy = cognos_cfg.policy_id or DEFAULT_POLICY

    upstream_url = f"{UPSTREAM_BASE_URL.rstrip('/')}/chat/completions"
    is_stream = bool(request_model.stream)
    response_headers = _epistemic_headers(
        trace_id=trace_id,
        decision=decision,
        trust_score=1.0 - risk,
        policy=active_policy,
    )

    request_fingerprint = _payload_fingerprint(payload, model_id=model)
    upstream_payload = {k: v for k, v in payload.items() if k != "cognos"}

    if MOCK_UPSTREAM:
        if is_stream:
            envelope = _build_cognos_envelope(
                trace_id=trace_id,
                policy=active_policy,
                decision=decision,
                risk=risk,
                shadow_pct=cognos_cfg.shadow_pct,
                shadow_models=cognos_cfg.shadow_models,
            )
            _persist_trace(
                trace_id=trace_id,
                created_at=created_at,
                is_stream=True,
                status_code=200,
                model=model,
                request_fingerprint=request_fingerprint,
                response_fingerprint=_payload_fingerprint({"trace_id": trace_id, "stream": True}, model_id=model),
                envelope=envelope,
                metadata={"mode": "mock", "upstream": "none", "usage": {"total_tokens": 0}, "retention": cognos_cfg.retention},
            )
            return StreamingResponse(_mock_sse_stream(trace_id), media_type="text/event-stream", headers=response_headers)
        upstream_json = _mock_non_stream_response(upstream_payload)
        envelope = _build_cognos_envelope(
            trace_id=trace_id,
            policy=active_policy,
            decision=decision,
            risk=risk,
            shadow_pct=cognos_cfg.shadow_pct,
            shadow_models=cognos_cfg.shadow_models,
        )
        upstream_json["cognos"] = envelope
        ChatCompletionResponse.model_validate(upstream_json)
        _persist_trace(
            trace_id=trace_id,
            created_at=created_at,
            is_stream=False,
            status_code=200,
            model=model,
            request_fingerprint=request_fingerprint,
            response_fingerprint=_payload_fingerprint(upstream_json, model_id=model),
            envelope=envelope,
            metadata={"mode": "mock", "upstream": "none", "usage": _extract_usage(upstream_json), "retention": cognos_cfg.retention},
        )
        return JSONResponse(status_code=200, content=upstream_json, headers=response_headers)

    outbound_headers = _build_upstream_headers(request.headers)

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            upstream_response = await client.post(upstream_url, headers=outbound_headers, json=upstream_payload)
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {error}")

    if upstream_response.status_code >= 400:
        envelope = _build_cognos_envelope(trace_id=trace_id, policy=active_policy, decision="ESCALATE", risk=1.0)
        _persist_trace(
            trace_id=trace_id,
            created_at=created_at,
            is_stream=is_stream,
            status_code=upstream_response.status_code,
            model=model,
            request_fingerprint=request_fingerprint,
            response_fingerprint=_payload_fingerprint({"error": True, "status": upstream_response.status_code}, model_id=model),
            envelope=envelope,
            metadata={"mode": "live", "upstream": "error", "usage": {"total_tokens": 0}, "retention": cognos_cfg.retention},
        )
        return JSONResponse(
            status_code=upstream_response.status_code,
            content={
                "error": "Upstream provider returned an error",
                "trace_id": trace_id,
                "upstream_body": _safe_json_or_text(upstream_response),
            },
        )

    content_type = upstream_response.headers.get("content-type", "")

    if is_stream and "text/event-stream" in content_type:
        envelope = _build_cognos_envelope(
            trace_id=trace_id,
            policy=active_policy,
            decision=decision,
            risk=risk,
            shadow_pct=cognos_cfg.shadow_pct,
            shadow_models=cognos_cfg.shadow_models,
        )
        _persist_trace(
            trace_id=trace_id,
            created_at=created_at,
            is_stream=True,
            status_code=200,
            model=model,
            request_fingerprint=request_fingerprint,
            response_fingerprint=_payload_fingerprint({"trace_id": trace_id, "stream": True}, model_id=model),
            envelope=envelope,
            metadata={"mode": "live", "upstream": "stream", "usage": {"total_tokens": 0}, "retention": cognos_cfg.retention},
        )

        async def stream_body() -> AsyncIterator[bytes]:
            async for chunk in _iter_stream_chunks(upstream_response):
                yield chunk

        return StreamingResponse(stream_body(), media_type="text/event-stream", headers=response_headers)

    upstream_json = upstream_response.json()
    envelope = _build_cognos_envelope(
        trace_id=trace_id,
        policy=active_policy,
        decision=decision,
        risk=risk,
        shadow_pct=cognos_cfg.shadow_pct,
        shadow_models=cognos_cfg.shadow_models,
    )
    upstream_json["cognos"] = envelope
    ChatCompletionResponse.model_validate(upstream_json)

    _persist_trace(
        trace_id=trace_id,
        created_at=created_at,
        is_stream=False,
        status_code=200,
        model=model,
        request_fingerprint=request_fingerprint,
        response_fingerprint=_payload_fingerprint(upstream_json, model_id=model),
        envelope=envelope,
        metadata={"mode": "live", "upstream": "json", "usage": _extract_usage(upstream_json), "retention": cognos_cfg.retention},
    )

    return JSONResponse(status_code=200, content=upstream_json, headers=response_headers)


def _build_upstream_headers(incoming_headers: Any) -> dict[str, str]:
    headers = {"content-type": "application/json"}

    incoming_auth = incoming_headers.get("authorization")
    incoming_upstream_auth = incoming_headers.get("x-cognos-upstream-authorization")

    if UPSTREAM_API_KEY:
        headers["authorization"] = f"Bearer {UPSTREAM_API_KEY}"
    elif incoming_upstream_auth:
        headers["authorization"] = incoming_upstream_auth
    elif incoming_auth and not GATEWAY_API_KEY:
        headers["authorization"] = incoming_auth
    else:
        raise HTTPException(status_code=500, detail="Missing upstream authorization")

    return headers


def _require_gateway_auth(incoming_headers: Any) -> None:
    if not GATEWAY_API_KEY:
        return

    provided = incoming_headers.get("x-api-key")
    if not provided:
        auth_header = incoming_headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            provided = auth_header.split(" ", 1)[1].strip()

    if provided != GATEWAY_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _epistemic_headers(trace_id: str, decision: str, trust_score: float, policy: str) -> dict[str, str]:
    return {
        "X-Cognos-Trace-Id": trace_id,
        "X-Cognos-Decision": decision,
        "X-Cognos-Trust-Score": str(trust_score),
        "X-Cognos-Policy": policy,
    }


def _build_cognos_envelope(
    trace_id: str,
    policy: str,
    decision: str = "PASS",
    risk: float = 0.0,
    shadow_pct: float = 0.0,
    shadow_models: list[str] | None = None,
) -> dict[str, Any]:
    signals = {
        "ue": 0.0,
        "ua": 0.0,
        "divergence": 0.0,
        "citation_density": 0.0,
        "contradiction": 0.0,
        "out_of_distribution": 0.0,
    }
    attestation_payload = {
        "trace_id": trace_id,
        "policy": policy,
        "decision": decision,
        "risk": risk,
        "signals": signals,
    }
    canonical = json.dumps(attestation_payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    envelope: dict[str, Any] = {
        "decision": decision,
        "risk": risk,
        "signals": signals,
        "trace_id": trace_id,
        "policy": policy,
        "attestation": {
            "hash": f"sha256:{digest}",
            "signed_by": "cognos",
            "ts": datetime.now(timezone.utc).isoformat(),
        },
    }

    if shadow_pct > 0:
        envelope["shadow"] = {
            "enabled": True,
            "compared_models": shadow_models or [],
            "divergence": 0.0,
            "note": "MVP shadow placeholder",
        }

    return envelope


async def _iter_stream_chunks(upstream_response: httpx.Response) -> AsyncIterator[bytes]:
    async for line in upstream_response.aiter_bytes():
        yield line


async def _mock_sse_stream(trace_id: str) -> AsyncIterator[bytes]:
    chunks = [
        f'data: {{"id":"{trace_id}","object":"chat.completion.chunk","choices":[{{"index":0,"delta":{{"content":"Mock response"}},"finish_reason":null}}]}}\n\n',
        'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n',
        "data: [DONE]\n\n",
    ]
    for chunk in chunks:
        yield chunk.encode("utf-8")


def _mock_non_stream_response(payload: dict[str, Any]) -> dict[str, Any]:
    model = payload.get("model", "mock:model")
    now_ts = int(datetime.now(timezone.utc).timestamp())
    return {
        "id": f"chatcmpl_{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": now_ts,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Mock response from CognOS gateway."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 8, "completion_tokens": 6, "total_tokens": 14},
    }


def _safe_json_or_text(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text


def _payload_fingerprint(payload: dict[str, Any], model_id: str | None = None) -> dict[str, Any]:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "simhash": f"sha256:{digest[:16]}",
        "embedding_hash": f"sha256:{digest}",
        "length": len(canonical),
        "model_id": model_id,
        "cluster_id": None,
    }


def _extract_usage(payload: dict[str, Any]) -> dict[str, int]:
    usage = payload.get("usage", {}) if isinstance(payload, dict) else {}
    if not isinstance(usage, dict):
        return {"total_tokens": 0}

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens")

    if not isinstance(prompt_tokens, int):
        prompt_tokens = 0
    if not isinstance(completion_tokens, int):
        completion_tokens = 0
    if not isinstance(total_tokens, int):
        total_tokens = prompt_tokens + completion_tokens

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def _persist_trace(
    trace_id: str,
    created_at: str,
    is_stream: bool,
    status_code: int,
    model: str | None,
    request_fingerprint: dict[str, Any],
    response_fingerprint: dict[str, Any],
    envelope: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    save_trace(
        {
            "trace_id": trace_id,
            "created_at": created_at,
            "decision": envelope.get("decision", "PASS"),
            "policy": envelope.get("policy", DEFAULT_POLICY),
            "trust_score": 1.0 - float(envelope.get("risk", 0.0)),
            "risk": float(envelope.get("risk", 0.0)),
            "is_stream": is_stream,
            "status_code": status_code,
            "model": model,
            "request_fingerprint": request_fingerprint,
            "response_fingerprint": response_fingerprint,
            "envelope": envelope,
            "metadata": metadata,
        }
    )
