# CognOS MCP Server

**Model Context Protocol server for CognOS trust verification.**

This MCP server exposes CognOS as a tool for Claude Code and other MCP-compatible applications. Use it to verify AI-generated content, retrieve audit trails, and generate compliance reports.

## Installation

### 1. Install MCP Server

```bash
cd mcp
pip install -r requirements.txt
```

### 2. Configure Claude Code

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "mcp": {
    "servers": {
      "cognos": {
        "command": "python",
        "args": ["/path/to/operational-cognos/mcp/server.py"],
        "env": {
          "COGNOS_BASE_URL": "http://127.0.0.1:8788",
          "COGNOS_API_KEY": ""
        }
      }
    }
  }
}
```

Replace `/path/to/operational-cognos/` with the actual path to your operational-cognos repo.

### 3. Start CognOS Gateway

In another terminal, start the CognOS gateway:

```bash
cd /path/to/operational-cognos
export COGNOS_MOCK_UPSTREAM=true
python3 -m uvicorn --app-dir src main:app --port 8788
```

Or use Docker:

```bash
docker-compose up
```

## Usage in Claude Code

Once registered, Claude Code can use CognOS tools:

### Verify Output

```python
# Claude Code can now call verify_output tool
response = await tools.call("verify_output", {
    "content": "The patient has hypertension and should take 200mg Lisinopril daily",
    "mode": "enforce",
    "target_risk": 0.05
})

# Response:
# {
#   "decision": "ESCALATE",
#   "risk": 0.12,
#   "trace_id": "tr_abc123xyz",
#   "signals": {
#     "ue": 0.08,
#     "ua": 0.04,
#     "out_of_distribution": 0.02
#   }
# }
```

### Get Audit Trail

```python
trace = await tools.call("get_trace", {
    "trace_id": "tr_abc123xyz"
})

# Returns full audit trail with decision reasoning, timestamps, fingerprints
```

### Generate Compliance Report

```python
report = await tools.call("create_trust_report", {
    "trace_ids": ["tr_xxx", "tr_yyy", "tr_zzz"],
    "regime": "EU_AI_ACT",
    "format": "json"
})

# Returns compliance-ready report with decision breakdown
```

### Check Gateway Health

```python
health = await tools.call("healthz", {})

# Returns gateway status: {"status": "ok", "gateway_url": "..."}
```

## Available Tools

### verify_output

Verify AI-generated content through CognOS.

**Parameters:**
- `content` (string, required) — The AI output to verify
- `mode` (string) — "monitor" (log only) or "enforce" (apply policies)
- `model` (string) — Model that generated the output (e.g., "gpt-4o-mini")
- `target_risk` (number) — Risk threshold for enforce mode (0.0-1.0)

**Returns:**
- `decision` — "PASS", "REFINE", "ESCALATE", or "BLOCK"
- `risk` — Risk score (0.0-1.0)
- `trace_id` — Immutable audit trail ID
- `signals` — Epistemic/aleatoric uncertainty, OOD detection, etc.

### get_trace

Retrieve full audit trail for a verification.

**Parameters:**
- `trace_id` (string, required) — Trace ID from verify_output response

**Returns:**
- Complete trace record with decision, signals, fingerprints, timestamp, policy

### create_trust_report

Generate compliance report from traces.

**Parameters:**
- `trace_ids` (array, required) — Array of trace IDs to include
- `regime` (string) — Compliance regime: "EU_AI_ACT", "GDPR", "SOC2", "DEFAULT"
- `format` (string) — Output format: "json", "csv", "pdf"

**Returns:**
- Compliance-ready report with decision breakdown, statistics, audit evidence

### healthz

Check CognOS gateway health.

**Parameters:** (none)

**Returns:**
- `status` — "ok" or error message
- `gateway_url` — CognOS gateway URL
- Connection status

## Environment Variables

```bash
# CognOS gateway configuration
COGNOS_BASE_URL="http://127.0.0.1:8788"    # Default: localhost:8788
COGNOS_API_KEY=""                           # Optional API key for gateway auth

# For Claude Code settings.json
# These are passed via 'env' in MCP server configuration
```

## Use Cases

### Healthcare
Verify AI-generated diagnoses and treatment recommendations before delivery:
```python
await tools.call("verify_output", {
    "content": "Patient should receive insulin therapy",
    "mode": "enforce",
    "target_risk": 0.05
})
```

### Finance
Risk-score loan decisions before approval:
```python
await tools.call("verify_output", {
    "content": "Applicant approved for $50k mortgage",
    "mode": "enforce",
    "target_risk": 0.08
})
```

### Legal
Generate audit evidence for AI-assisted legal research:
```python
trace = await tools.call("get_trace", {"trace_id": "tr_xxx"})
# Use for discovery, audit, compliance
```

### Compliance
Generate audit-ready compliance reports:
```python
report = await tools.call("create_trust_report", {
    "trace_ids": traces,
    "regime": "EU_AI_ACT"
})
# Use for regulatory reporting, ISO audit, risk assessment
```

## Troubleshooting

### "CognOS gateway unreachable"

**Check:**
1. Is CognOS running? `curl http://127.0.0.1:8788/healthz`
2. Is `COGNOS_BASE_URL` correct in settings?
3. Are ports open? (default: 8788)

**Fix:**
```bash
# Start gateway
docker-compose up
# or
python3 -m uvicorn --app-dir src main:app --port 8788
```

### "Unknown tool" error

**Check:**
1. Is MCP server running? `python mcp/server.py`
2. Is Claude Code connected? Check `~/.claude/settings.json`
3. Did you restart Claude Code after adding MCP config?

**Fix:**
```bash
# Restart Claude Code settings
# Check that "cognos" appears in MCP servers list
```

### "Invalid authentication"

**Check:**
1. Is `COGNOS_API_KEY` set correctly?
2. Does the gateway require auth?

**Fix:**
- Leave `COGNOS_API_KEY` empty for local gateway
- Set it if using remote authenticated endpoint

## Integration with Workflows

### With LangChain
```python
from cognos import CognosClient

async def verify_with_cognos(content):
    async with CognosClient() as client:
        response = await client.chat(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": content}],
            mode="enforce"
        )
        return response.cognos.decision
```

### With Claude Workflows (Future)
When Claude Workflows add MCP support, you'll be able to build workflows that automatically verify outputs:

```
Input → Claude (generate) → CognOS verify → Decision → Action
```

## Architecture

```
Claude Code
    ↓
MCP Server (mcp/server.py)
    ↓
HTTP Client (httpx)
    ↓
CognOS Gateway (localhost:8788)
    ↓
LLM Provider (OpenAI, Claude, Google, etc.)
```

The MCP server is a thin wrapper around CognOS. It:
1. Receives tool calls from Claude Code
2. Converts them to HTTP requests
3. Sends to local CognOS gateway
4. Returns results to Claude Code

## Development

### Run Server Locally

```bash
cd mcp
COGNOS_BASE_URL=http://127.0.0.1:8788 python server.py
```

### Test a Tool

```bash
# In Python REPL
import asyncio
from mcp.server import Server
from mcp.types import TextContent, ToolResult

# Load and test
asyncio.run(verify_output("Test content", mode="monitor"))
```

### Add New Tools

1. Create tool definition (e.g., `MY_TOOL = Tool(...)`)
2. Implement function (e.g., `async def my_tool()`)
3. Add to `list_tools()` return
4. Add case to `call_tool()` router

## License

MIT License. See [LICENSE](../LICENSE) for details.

## Support

- 📖 [CognOS Docs](https://docs.cognos.base76.se)
- 🐛 [GitHub Issues](https://github.com/base76-research-lab/operational-cognos/issues)
- 💬 [Discord Community](https://discord.gg/base76)

---

**Made by [Base76 Research Lab](https://base76.se)**
