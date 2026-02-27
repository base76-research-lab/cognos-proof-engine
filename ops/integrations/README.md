# CognOS Integration Pack (Ops Zone)

![CognOS Brand](../../docs/assets/logo/cognos-logo-horizontal.svg)

This package exposes CognOS verification across multiple agent/tool ecosystems while keeping the engine logic in `src/`.

## Included
- `common/cognos_client.py` shared gateway client
- `anthropic/` tool schema + wrapper example
- `mcp/` MCP-compatible HTTP bridge
- `langchain/` tool wrapper + example
- `autogen/` function wrapper + example
- `crewai/` class wrapper + example

## Environment

```bash
export COGNOS_BASE_URL="http://127.0.0.1:8788"
export COGNOS_API_KEY=""                 # set if gateway key is enabled
export COGNOS_UPSTREAM_AUTH="Bearer ..." # required if gateway has no server-side upstream key
export COGNOS_POLICY_ID="default_v1"
export COGNOS_MODE="monitor"
```

## Quick checks

```bash
python3 ops/integrations/anthropic/example_anthropic_tool.py
python3 ops/integrations/langchain/example_langchain.py
python3 ops/integrations/autogen/example_autogen.py
python3 ops/integrations/crewai/example_crewai.py
uvicorn ops.integrations.mcp.server:app --port 8799 --reload
```

## Notes
- This is a distribution layer only; API source-of-truth remains `docs/spec/cognos_openapi_mvp.yaml`.
- The MCP component is a bridge endpoint (`/tools/cognos_verify`) suitable for tool runtimes and proxies.
