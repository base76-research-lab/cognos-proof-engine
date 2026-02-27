# Live Launch Checklist (Copy/Paste)

Goal: get one real external developer request with a valid `trace_id`.

## 0) Prerequisites
- Repository is up to date on `main`
- You have upstream model credentials
- You have chosen platform: Fly.io or Railway

## 1) Set production secrets

Required values:
- `COGNOS_GATEWAY_API_KEY`
- `COGNOS_UPSTREAM_API_KEY`
- `COGNOS_MOCK_UPSTREAM=false`
- `COGNOS_DEFAULT_POLICY=default_v1`

---

## 2A) Fly.io launch (recommended if Fly CLI already installed)

```bash
cd /media/bjorn/iic/workspace/01_RESEARCH/operational-cognos
fly auth login
fly deploy
fly secrets set COGNOS_GATEWAY_API_KEY="YOUR_GATEWAY_KEY"
fly secrets set COGNOS_UPSTREAM_API_KEY="YOUR_UPSTREAM_KEY"
fly secrets set COGNOS_MOCK_UPSTREAM="false"
fly secrets set COGNOS_DEFAULT_POLICY="default_v1"
fly deploy
```

Get URL:

```bash
fly status
```

---

## 2B) Railway launch (fastest UI flow)

1. Create project from repo in Railway.
2. Ensure `Procfile` is detected.
3. Add env vars:
   - `COGNOS_GATEWAY_API_KEY`
   - `COGNOS_UPSTREAM_API_KEY`
   - `COGNOS_MOCK_UPSTREAM=false`
   - `COGNOS_DEFAULT_POLICY=default_v1`
4. Deploy and copy public URL.

---

## 3) Production health check

```bash
export COGNOS_PUBLIC_URL="https://YOUR_PUBLIC_HOST"
curl -sS "$COGNOS_PUBLIC_URL/healthz"
```

Expected:
- `{"status":"ok","service":"operational-cognos-gateway"}`

---

## 4) First real request (public endpoint)

```bash
curl -sS "$COGNOS_PUBLIC_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_GATEWAY_KEY' \
  -d '{
    "model": "openai:gpt-4.1-mini",
    "messages": [{"role":"user","content":"Explain GDPR lawful basis in three bullets."}],
    "cognos": {"mode":"monitor","policy_id":"default_v1"}
  }'
```

Check response:
- `cognos.decision` exists
- `cognos.trace_id` exists

---

## 5) Trace verification

Use returned `trace_id`:

```bash
curl -sS "$COGNOS_PUBLIC_URL/v1/traces/TRACE_ID" \
  -H 'x-api-key: YOUR_GATEWAY_KEY'
```

Check payload:
- `trace_id`
- `request_fingerprint`
- `response_fingerprint`
- `envelope`

---

## 6) Trust report verification

```bash
curl -sS "$COGNOS_PUBLIC_URL/v1/reports/trust" \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_GATEWAY_KEY' \
  -d '{
    "trace_ids": ["TRACE_ID"],
    "regime": "EU_AI_ACT",
    "format": "json"
  }'
```

Check payload:
- `report_id`
- `regime`
- `summary.found_count >= 1`

---

## 7) External developer activation

Send to one alpha developer:
- public URL
- gateway key
- one curl command from step 4
- one follow-up ask: “send your returned trace_id”

Definition of success today:
- 1 external request completed
- 1 valid external trace_id received
