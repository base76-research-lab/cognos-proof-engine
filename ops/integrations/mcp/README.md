# CognOS MCP-Compatible Tool Bridge

This service exposes CognOS verification as a tool-style HTTP endpoint.

Run:

```bash
uvicorn ops.integrations.mcp.server:app --port 8799 --reload
```

Endpoints:
- `GET /healthz`
- `POST /tools/cognos_verify`

Example:

```bash
curl -s http://127.0.0.1:8799/tools/cognos_verify \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"What is GDPR?","draft_answer":"GDPR is optional.","mode":"monitor"}'
```
