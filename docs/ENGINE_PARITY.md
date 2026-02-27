# CognOS Engine Parity Checklist (OpenAPI MVP)

![CognOS Brand](assets/logo/cognos-logo-horizontal.svg)

This checklist is the execution contract for API parity.

Source of truth:
- `docs/spec/cognos_openapi_mvp.yaml`

Scope policy:
- P0 parity first
- P1 only after P0 is green
- Freeze new ops/social features until P0 parity is complete

## P0 — Definition of Done
- `/v1/chat/completions` accepts CognOS control surface and returns schema-compliant `cognos` envelope.
- `/v1/traces/{trace_id}` returns `TraceRecord` 1:1 with required fields.
- Headers are always present on successful chat responses:
  - `X-Cognos-Trust-Score`
  - `X-Cognos-Decision`
  - `X-Cognos-Trace-Id`
  - `X-Cognos-Policy`
- Smoke tests enforce headers, enums, required fields, and expected error behavior.

## Engine / Ops Boundary
- Engine zone (`src/`): `main.py`, `models.py`, `gateway.py`, `policy.py`, `trace_store.py`, `reports.py`
- Ops zone (`ops/`, social, autopilot docs/scripts)
- No engine logic should move into ops files.

## Task List

### P0-1 Contract Source-of-Truth
Status: TODO

Tasks:
- Keep OpenAPI canonical in `docs/spec/cognos_openapi_mvp.yaml`.
- Reference it from `README.md` under contract-first policy.

Acceptance:
- API changes require OpenAPI + smoke-test updates.

Touchpoints:
- `README.md`
- `docs/spec/cognos_openapi_mvp.yaml`

### P0-2 Chat Request Parity (`cognos` controls)
Status: TODO

Tasks:
- Parse and validate:
  - `mode` (`monitor|enforce`, default `monitor`)
  - `policy_id` (default `default_v1`)
  - `target_risk` (optional)
  - `shadow_pct` (default `0.0`)
  - `shadow_models` (default `[]`)
  - `retention` (`none|fingerprints|enhanced`, default `fingerprints`)
- Reject invalid enums with HTTP 400.

Acceptance:
- Requests with and without `cognos` behave deterministically with defaults.

Touchpoints:
- `src/main.py`
- `src/models.py`
- `src/policy.py`

### P0-3 Chat Response Parity (envelope + headers)
Status: TODO

Tasks:
- Ensure `cognos` includes required fields and enum values.
- Keep uppercase decisions (`PASS|REFINE|ESCALATE|BLOCK`).
- Keep response headers synchronized with envelope values.

Acceptance:
- Envelope validates against schema in smoke checks.

Touchpoints:
- `src/main.py`
- `src/models.py`

### P0-4 TraceRecord Parity
Status: TODO

Tasks:
- Persist and return:
  - `trace_id`
  - `created`
  - `request_fingerprint`
  - `response_fingerprint`
  - `envelope`
- Keep fingerprints privacy-safe (no raw text storage).

Acceptance:
- `chat -> trace` roundtrip returns schema-compliant `TraceRecord`.

Touchpoints:
- `src/trace_store.py`
- `src/main.py`
- `src/models.py`

### P0-5 Smoke Tests as Contract Guards
Status: TODO

Tasks:
- Update smoke tests to assert:
  - required headers
  - envelope required fields
  - enum values
  - expected status behavior (`400`/`404` and auth behavior)

Acceptance:
- Tests fail on schema drift, not only runtime crash.

Touchpoints:
- `src/smoke_oc001.py`
- `src/smoke_oc002.py`
- `src/smoke_oc006.py`

## P1 — After P0 Green

### P1-1 Trust Reports Endpoint
Status: TODO

Tasks:
- Implement `/v1/reports/trust` request/response schema.
- Return JSON report now; PDF later.

Acceptance:
- Valid trace IDs return report payload with required fields.

Touchpoints:
- `src/main.py`
- `src/reports.py`
- `src/models.py`
