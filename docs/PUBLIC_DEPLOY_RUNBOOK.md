# Public Deploy Runbook (Fly.io / Railway)

![CognOS Brand](assets/logo/cognos-logo-horizontal.svg)

This runbook publishes a web-reachable CognOS endpoint for external developers.

## Target
- Public HTTPS endpoint for `POST /v1/chat/completions`
- Gateway key protection (`COGNOS_GATEWAY_API_KEY`)
- Upstream auth via server key (`COGNOS_UPSTREAM_API_KEY`) or caller header (`x-cognos-upstream-authorization`)

## Required Environment Variables
- `COGNOS_UPSTREAM_BASE_URL` (default: `https://api.openai.com/v1`)
- `COGNOS_UPSTREAM_API_KEY` (recommended for production)
- `COGNOS_GATEWAY_API_KEY` (required for public endpoint)
- `COGNOS_DEFAULT_POLICY` (default: `default_v1`)
- `COGNOS_REQUEST_TIMEOUT_SECONDS` (default: `120`)
- `COGNOS_TRACE_DB` (e.g. `data/traces.sqlite3`)
- `COGNOS_MOCK_UPSTREAM=false`

## Local command reference
- Local dev run command:
   - `python3 -m uvicorn --app-dir src main:app --host 127.0.0.1 --port 8788`

## Option A — Railway (fastest)
1. Create new Railway project from this repository.
2. Use included `Procfile` start command:
   - `web: uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}`
3. Set required environment variables.
4. Deploy and copy public URL.
5. Validate:
   - `GET /healthz`
   - `POST /v1/chat/completions`

## Option B — Fly.io
1. Install Fly CLI and authenticate.
2. Use included `fly.toml` in repo root.
3. Set secrets:
   - `fly secrets set COGNOS_GATEWAY_API_KEY=...`
   - `fly secrets set COGNOS_UPSTREAM_API_KEY=...`
   - `fly secrets set COGNOS_MOCK_UPSTREAM=false`
4. Deploy:
   - `fly deploy`

## Production Validation

### Health
```bash
curl -sS https://YOUR_PUBLIC_HOST/healthz
```

### Chat Completion
```bash
curl -sS https://YOUR_PUBLIC_HOST/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_GATEWAY_KEY' \
  -d '{
    "model":"openai:gpt-4.1-mini",
    "messages":[{"role":"user","content":"Explain GDPR lawful basis in 3 bullets."}],
    "cognos":{"mode":"monitor","policy_id":"default_v1"}
  }'
```

Expected:
- `200` response
- response includes `cognos` envelope
- headers include `X-Cognos-Trace-Id`, `X-Cognos-Decision`, `X-Cognos-Trust-Score`, `X-Cognos-Policy`

### Trace Lookup
```bash
curl -sS https://YOUR_PUBLIC_HOST/v1/traces/TRACE_ID \
  -H 'x-api-key: YOUR_GATEWAY_KEY'
```

## Security Minimum (before sharing endpoint)
- Enable `COGNOS_GATEWAY_API_KEY`.
- Disable mock mode (`COGNOS_MOCK_UPSTREAM=false`).
- Use provider-side secret storage for upstream keys.
- Add rate limiting at edge/proxy level (Cloudflare, NGINX, Caddy, or platform-native limits).
- Rotate keys if exposed.

## First External Developer Flow
1. Share endpoint URL + gateway key.
2. Provide one quickstart command (`cognos chat` or curl).
3. Ask for one successful request + one trace ID.
4. Confirm response quality + onboarding friction.
