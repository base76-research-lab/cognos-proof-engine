# CognOS Proof Snapshot — 2026-02-27

Status: Verified live end-to-end on public endpoint.

## What was proven

- Chat completion works through CognOS gateway.
- Trace is persisted and retrievable by trace ID.
- Trust report is generated successfully from that trace.

## Live run evidence

- Endpoint: `https://cognos-proof-engine.fly.dev`
- Chat status: `200`
- Trace ID: `tr_e9f8bd669382`
- Decision header: `PASS`
- Trust score header: `0.88`
- Trace fetch status: `200`
- Report status: `200`
- Report summary: `found_count=1`, `missing_count=0`

## Why this matters

This validates both:

- **Proof of Concept (PoC):** the architecture works end-to-end.
- **Proof of Use (PoU):** the deployed system produces operational trust artifacts in real traffic.

## Re-run checklist

1. Send one request to `/v1/chat/completions`.
2. Extract `X-Cognos-Trace-Id` from response headers.
3. Fetch `/v1/traces/{trace_id}`.
4. Generate `/v1/reports/trust` with that trace ID.

Expected success criteria:

- all three endpoints return `200`
- report summary shows `found_count >= 1`

## Notes

- This snapshot captures one concrete live verification event.
- Repeatability is supported through the same endpoint flow and criteria.
