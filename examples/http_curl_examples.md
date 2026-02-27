# HTTP/Curl Examples

![CognOS Brand](../docs/assets/logo/cognos-logo-horizontal.svg)

## 1) Chat completion via CognOS

```bash
curl -sS http://127.0.0.1:8788/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_GATEWAY_KEY' \
  -H 'x-cognos-upstream-authorization: Bearer YOUR_UPSTREAM_KEY' \
  -d '{
    "model": "openai:gpt-4.1-mini",
    "messages": [{"role":"user","content":"Give 3 GDPR compliance checks."}],
    "cognos": {
      "mode": "monitor",
      "policy_id": "default_v1"
    }
  }'
```

## 2) Fetch trace

```bash
curl -sS http://127.0.0.1:8788/v1/traces/TRACE_ID \
  -H 'x-api-key: YOUR_GATEWAY_KEY'
```

## 3) Create trust report

```bash
curl -sS http://127.0.0.1:8788/v1/reports/trust \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_GATEWAY_KEY' \
  -d '{
    "trace_ids": ["TRACE_ID_1", "TRACE_ID_2"],
    "regime": "EU_AI_ACT",
    "format": "json"
  }'
```
