# CognOS Trust Report — JSON Schema Reference

> Version 1.0 · Base76 Research Lab · [base76.se](https://base76.se)

---

## Overview

Every inference through the CognOS gateway returns a `CognosEnvelope` — a structured
trust payload attached to the standard OpenAI-compatible response. This document
defines the complete schema for downstream integration.

---

## Per-inference payload (`CognosEnvelope`)

Returned on every `/v1/chat/completions` response under the `cognos` key.

```json
{
  "cognos": {
    "decision": "PASS",
    "risk": 0.12,
    "signals": {
      "ue": 0.08,
      "ua": 0.15,
      "divergence": 0.03,
      "citation_density": 0.91,
      "contradiction": 0.04,
      "out_of_distribution": 0.07
    },
    "trace_id": "tr_a3f9c1d2b8e4",
    "policy": "default_v1",
    "attestation": {
      "hash": "sha256:abc123...",
      "signed_by": "cognos-gateway",
      "ts": "2026-03-01T10:42:00Z",
      "signature": null
    },
    "shadow": null
  }
}
```

### `decision` — the action field

| Value | Meaning | Recommended frontend action |
|-------|---------|----------------------------|
| `PASS` | Low risk, verified | Render output |
| `REFINE` | Borderline, refineable | Show with warning indicator |
| `ESCALATE` | High risk, requires review | Route to human review queue |
| `BLOCK` | Blocked, not forwarded | Suppress output, log event |

### `risk` — composite risk score

Float `0.0–1.0`. Aggregated from the signal vector. Threshold for `BLOCK` is
configurable via `target_risk` in the request control block.

### `signals` — epistemic signal vector

| Field | Type | Description |
|-------|------|-------------|
| `ue` | `float 0–1` | Epistemic uncertainty — model's internal variance |
| `ua` | `float 0–1` | Aleatoric uncertainty — irreducible ambiguity in the question |
| `divergence` | `float 0–1` | Shadow model divergence (if shadow mode enabled) |
| `citation_density` | `float 0–1` | Factual grounding signal |
| `contradiction` | `float 0–1` | Internal self-contradiction score |
| `out_of_distribution` | `float 0–1` | OOD detection — how far from training distribution |

### `trace_id`

Unique identifier for this inference. Use to retrieve the full trace or include
in a trust report. Format: `tr_` + 12 hex chars.

### `attestation`

Cryptographic fingerprint of the decision.

| Field | Description |
|-------|-------------|
| `hash` | SHA-256 of request + response + signals |
| `signed_by` | Gateway instance identifier |
| `ts` | ISO 8601 timestamp (UTC) |
| `signature` | Optional — populated when signing key is configured |

---

## Aggregated Trust Report

Generated via `POST /v1/reports` for a batch of trace IDs.
Used for regulatory submissions and compliance audits.

**Request:**
```json
{
  "trace_ids": ["tr_a3f9c1d2b8e4", "tr_b7e2f1c9a3d5"],
  "regime": "EU_AI_ACT",
  "format": "json"
}
```

**Response:**
```json
{
  "report_id": "rpt_a1b2c3d4e5f6",
  "created": "2026-03-01T10:42:00Z",
  "regime": "EU_AI_ACT",
  "summary": {
    "requested_count": 50,
    "found_count": 50,
    "missing_count": 0,
    "missing_ids": [],
    "decision_breakdown": {
      "PASS": 44,
      "REFINE": 4,
      "ESCALATE": 2,
      "BLOCK": 0
    },
    "format": "json"
  }
}
```

### Supported regimes

| `regime` value | Framework |
|----------------|-----------|
| `EU_AI_ACT` | EU Artificial Intelligence Act |
| `GDPR` | General Data Protection Regulation |
| `SOC2` | SOC 2 Type I/II |
| `HIPAA` | Health Insurance Portability and Accountability Act |

---

## Integration example

```python
import httpx

response = httpx.post("http://localhost:8788/v1/chat/completions", json={
    "model": "openai:gpt-4o-mini",
    "messages": [{"role": "user", "content": "Summarize the patient record."}],
    "cognos": {"mode": "enforce", "target_risk": 0.3}
})

data = response.json()
envelope = data["cognos"]

if envelope["decision"] == "BLOCK":
    trigger_kill_switch(envelope)
elif envelope["decision"] == "ESCALATE":
    route_to_review_queue(envelope["trace_id"])
else:
    render_output(data["choices"][0]["message"]["content"])
```

---

## Retrieve a single trace

```
GET /v1/traces/{trace_id}
```

Returns the full `TraceRecord` including request/response fingerprints,
envelope, and metadata.

---

*Schema version 1.0 — Base76 Research Lab — MIT License*
