# Claude Code + CognOS MCP Setup Guide

**Get CognOS trust verification working in Claude Code in 5 minutes.**

## Prerequisites

- Claude Code installed
- CognOS gateway running (locally)
- Python 3.10+

## Step 1: Install MCP Dependencies

```bash
cd operational-cognos/mcp
pip install -r requirements.txt
```

Expected output:
```
Successfully installed mcp httpx python-dotenv
```

## Step 2: Locate Your Settings File

Find your Claude Code settings:

**macOS/Linux:**
```bash
~/.claude/settings.json
```

**Windows:**
```
%APPDATA%\Claude\settings.json
```

If the file doesn't exist, create it:
```bash
mkdir -p ~/.claude
touch ~/.claude/settings.json
```

## Step 3: Register CognOS MCP Server

Edit `~/.claude/settings.json`:

```json
{
  "mcp": {
    "servers": {
      "cognos": {
        "command": "python",
        "args": ["/absolute/path/to/operational-cognos/mcp/server.py"],
        "env": {
          "COGNOS_BASE_URL": "http://127.0.0.1:8788",
          "COGNOS_API_KEY": ""
        }
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/` with the actual path. Get it:

```bash
pwd /path/to/operational-cognos
# Output: /Users/bjorn/projects/operational-cognos (example)
# Use this full path
```

## Step 4: Start CognOS Gateway

In a separate terminal:

```bash
cd operational-cognos
export COGNOS_MOCK_UPSTREAM=true
python3 -m uvicorn --app-dir src main:app --port 8788
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8788
INFO:     Application startup complete
```

Or use Docker:

```bash
docker-compose up
```

## Step 5: Restart Claude Code

Close and reopen Claude Code to load the new MCP config.

Check that it connected:
- Look for 🔐 in the status bar (MCP connected)
- Or run: `healthz` tool to test

## Step 6: Test It Works

Create a test file in Claude Code:

```python
# test_cognos_mcp.py

# Claude Code will show autocomplete for cognos tools
result = await tools.call("healthz", {})
print(result)
# Should show: {"status": "ok", "gateway_url": "http://127.0.0.1:8788"}
```

## Usage Examples

### Example 1: Verify Medical Output (High Risk)

```python
response = await tools.call("verify_output", {
    "content": "Patient should take 500mg Aspirin daily for heart health",
    "mode": "enforce",
    "target_risk": 0.05,  # Strict: escalate if risk > 5%
    "model": "gpt-4o-mini"
})

print(response)
# {
#   "decision": "ESCALATE",
#   "risk": 0.12,
#   "trace_id": "tr_abc123xyz",
#   "signals": {"ue": 0.08, "ua": 0.04, ...}
# }

if response["decision"] == "ESCALATE":
    print("⚠️ High risk — escalate to human review")
elif response["decision"] == "PASS":
    print("✅ Safe to use")
```

### Example 2: Get Audit Trail

```python
trace = await tools.call("get_trace", {
    "trace_id": "tr_abc123xyz"
})

# Full audit trail:
# {
#   "trace_id": "tr_abc123xyz",
#   "decision": "ESCALATE",
#   "risk": 0.12,
#   "policy": "healthcare_v1",
#   "request_fingerprint": "sha256:...",
#   "response_fingerprint": "sha256:...",
#   "timestamp": "2026-02-27T12:34:56Z",
#   "signals": {...}
# }
```

### Example 3: Generate Compliance Report

```python
report = await tools.call("create_trust_report", {
    "trace_ids": ["tr_xxx", "tr_yyy", "tr_zzz"],
    "regime": "EU_AI_ACT",
    "format": "json"
})

# Compliance-ready report for audit/regulatory
```

## Troubleshooting

### MCP Shows Red/Disconnected

**Problem:** Settings not applied.

**Fix:**
1. Verify path in settings.json (use absolute path)
2. Restart Claude Code completely
3. Check for typos in "cognos" server name

### "Module not found: mcp"

**Problem:** Requirements not installed.

**Fix:**
```bash
cd operational-cognos/mcp
pip install -r requirements.txt
```

### "CognOS gateway unreachable"

**Problem:** Gateway not running.

**Fix:**
1. Check CognOS is running: `curl http://127.0.0.1:8788/healthz`
2. Start it if needed:
   ```bash
   cd operational-cognos
   docker-compose up
   ```

### Settings.json Has Syntax Error

**Problem:** Invalid JSON.

**Fix:**
1. Copy the example above
2. Use absolute path (no `~`)
3. Validate: `python -m json.tool ~/.claude/settings.json`

## Next Steps

**After setup works:**

1. **Use in workflows** — Claude Code can now verify outputs in real time
2. **Add custom policies** — Modify CognOS gateway to match your needs
3. **Integrate with agents** — Use verify_output in autonomous loops
4. **Generate compliance reports** — Create EU AI Act attestation

## Configuration Options

### High-Risk Mode (Healthcare/Finance)

```json
{
  "mcp": {
    "servers": {
      "cognos": {
        "command": "python",
        "args": ["/path/to/operational-cognos/mcp/server.py"],
        "env": {
          "COGNOS_BASE_URL": "http://127.0.0.1:8788",
          "COGNOS_API_KEY": "your-key-if-needed"
        }
      }
    }
  }
}
```

All calls will use `mode: enforce` with `target_risk: 0.05` (5% threshold).

### Remote Gateway

To use a remote CognOS gateway (not localhost):

```json
{
  "env": {
    "COGNOS_BASE_URL": "https://cognos.yourcompany.com",
    "COGNOS_API_KEY": "your-api-key"
  }
}
```

### Multiple Servers

If you have multiple MCP servers:

```json
{
  "mcp": {
    "servers": {
      "cognos": { ... },
      "other_tool": { ... }
    }
  }
}
```

## Full Settings.json Example

```json
{
  "mcp": {
    "servers": {
      "cognos": {
        "command": "python",
        "args": ["/Users/bjorn/projects/operational-cognos/mcp/server.py"],
        "env": {
          "COGNOS_BASE_URL": "http://127.0.0.1:8788",
          "COGNOS_API_KEY": ""
        }
      }
    }
  }
}
```

## Security Notes

- **API Key:** Only set if your CognOS gateway requires auth
- **URL:** Keep localhost for local development
- **Settings file:** Contains sensitive config — don't commit to git
- **Audit trails:** All CognOS decisions are logged and traceable

## Support

- 📖 [CognOS MCP README](./README.md)
- 🐛 [GitHub Issues](https://github.com/base76-research-lab/operational-cognos/issues)
- 💬 [Discord](https://discord.gg/base76)

---

**You're all set! CognOS is now available in Claude Code.** 🔐

Try: `await tools.call("healthz", {})` to test.
