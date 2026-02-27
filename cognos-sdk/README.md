# CognOS SDK — Trust Verification for Python

Python SDK for [CognOS](https://github.com/base76-research-lab/operational-cognos) trust verification gateway.

**Verify every AI decision. Prove correctness. Pass compliance.**

## Install

```bash
pip install cognos-sdk
```

## Quick Start

```python
from cognos import CognosClient

# Create client (defaults to localhost:8788)
client = CognosClient()

# Call LLM through gateway
response = client.chat(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    mode="monitor"  # or "enforce" for policy enforcement
)

# Check decision
if response.cognos.decision == "PASS":
    print(f"✅ {response.choices[0].message['content']}")
elif response.cognos.decision == "ESCALATE":
    print(f"⚠️ Risk: {response.cognos.risk}")
```

## Features

- ✅ **Simple API** — 3-line integration
- ✅ **Multi-provider** — OpenAI, Claude, Google, Mistral, Ollama
- ✅ **Trust verification** — Decision proof + risk scoring
- ✅ **Audit trails** — Immutable trace for every request
- ✅ **Policy enforcement** — Monitor or enforce mode
- ✅ **Zero config** — Works with CognOS gateway out of box

## Usage Examples

### Monitor Mode (Always Passes)

```python
response = client.chat(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    mode="monitor"  # Logs decision but always passes
)

print(f"Decision: {response.cognos.decision}")  # "PASS"
print(f"Trace ID: {response.cognos.trace_id}")  # "tr_xxx"
print(f"Risk: {response.cognos.risk}")  # 0.0–1.0
```

### Enforce Mode (Applies Policies)

```python
response = client.chat(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Health info question"}],
    mode="enforce",
    target_risk=0.1  # Escalate if risk > 10%
)

if response.cognos.decision == "PASS":
    # Safe to return
    return response.choices[0].message["content"]
elif response.cognos.decision == "REFINE":
    # Reword response or apply filter
    return "Please consult a healthcare provider"
elif response.cognos.decision == "ESCALATE":
    # Send to human review
    escalate_to_human(response.cognos.trace_id)
elif response.cognos.decision == "BLOCK":
    # Reject outright
    return "Request cannot be processed"
```

### Check Decision Details

```python
# Access signals
print(f"Semantic uncertainty: {response.cognos.signals.ue}")
print(f"Aleatoric uncertainty: {response.cognos.signals.ua}")
print(f"Out-of-distribution: {response.cognos.signals.out_of_distribution}")

# Access usage
print(f"Total tokens: {response.usage['total_tokens']}")

# Get full trace
trace = client.get_trace(response.cognos.trace_id)
print(f"Trust score: {trace['trust_score']}")
```

### Retrieve Trace Records

```python
# Get full audit trail
trace = client.get_trace("tr_abc123")

print(trace["decision"])          # Decision made
print(trace["policy"])             # Policy applied
print(trace["trust_score"])        # 0.0–1.0
print(trace["request_fingerprint"]) # Hash of request
print(trace["response_fingerprint"]) # Hash of response
```

### Generate Trust Reports

```python
# Create compliance report from traces
report = client.create_trust_report(
    trace_ids=["tr_xxx", "tr_yyy", "tr_zzz"],
    regime="EU_AI_ACT"  # or "GDPR", "SOC2", "DEFAULT"
)

print(f"Found {report['summary']['found_count']} traces")
print(f"Decisions: {report['summary']['decision_breakdown']}")
# Output: {'PASS': 2, 'REFINE': 1}

print(f"Report ID: {report['report_id']}")  # For compliance records
```

### Use with Different Models

```python
# OpenAI (default)
response = client.chat(model="gpt-4o-mini", messages=[...])

# Claude via OpenRouter
response = client.chat(model="claude:claude-3-sonnet", messages=[...])

# Google
response = client.chat(model="google:gemini-2.0-flash", messages=[...])

# Mistral
response = client.chat(model="mistral:mistral-small-latest", messages=[...])

# Local Ollama
response = client.chat(model="ollama:llama2", messages=[...])
```

### Context Manager (Recommended)

```python
# Automatically closes connection
with CognosClient() as client:
    response = client.chat(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}]
    )
```

### Custom Gateway + Authentication

```python
client = CognosClient(
    base_url="https://cognos.yourcompany.com",
    api_key="your-secret-key",
    timeout=60
)

response = client.chat(...)
```

## Configuration

### Environment Variables

```bash
# Use these to configure without code changes
export COGNOS_BASE_URL="http://localhost:8788"
export COGNOS_API_KEY="your-key"
```

### From Code

```python
client = CognosClient(
    base_url="http://localhost:8788",
    api_key="your-api-key",
    timeout=30
)
```

## Error Handling

```python
from httpx import HTTPError

try:
    response = client.chat(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}]
    )
except HTTPError as e:
    print(f"Request failed: {e}")
    # Fallback: use direct LLM call without verification
except ValueError as e:
    print(f"Invalid response: {e}")
```

## Response Structure

```python
ChatResponse(
    id: str                           # Upstream response ID
    choices: list[ChatChoice]         # Completed choices
    cognos: CognosEnvelope           # Trust metadata
    usage: dict[str, int]            # Token usage
    raw_response: dict[str, Any]     # Full upstream response
)

CognosEnvelope(
    decision: str                    # "PASS" | "REFINE" | "ESCALATE" | "BLOCK"
    risk: float                      # 0.0–1.0
    trace_id: str                    # Unique ID for audit trail
    policy: str                      # Policy name applied
    signals: CognosSignals          # Risk signals breakdown
)

CognosSignals(
    ue: float                        # Semantic uncertainty (epistemic)
    ua: float                        # Aleatoric uncertainty (stochastic)
    divergence: float                # Model divergence from baseline
    citation_density: float          # How well-grounded response is
    contradiction: float             # Internal logical contradictions
    out_of_distribution: float       # OOD detection score
)
```

## Integration Examples

### With LangChain

```python
from langchain.callbacks import BaseCallbackHandler
from cognos import CognosClient

class CognosCallback(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        # Verify response through CognOS
        client = CognosClient()
        cognos_response = client.chat(
            model=response.llm_output.get("model"),
            messages=response.llm_input.get("messages")
        )
        if cognos_response.cognos.decision != "PASS":
            print(f"⚠️ Risk detected: {cognos_response.cognos.risk}")
```

### With FastAPI

```python
from fastapi import FastAPI
from cognos import CognosClient

app = FastAPI()
cognos_client = CognosClient()

@app.post("/chat")
async def chat(user_message: str):
    response = cognos_client.chat(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_message}]
    )

    if response.cognos.decision == "BLOCK":
        return {"error": "Request blocked"}

    return {"message": response.choices[0].message["content"]}
```

### With Django

```python
from django.views import View
from cognos import CognosClient

class ChatView(View):
    def post(self, request):
        client = CognosClient()
        response = client.chat(
            model="gpt-4o-mini",
            messages=request.POST.get("messages", [])
        )

        return {
            "content": response.choices[0].message["content"],
            "trace_id": response.cognos.trace_id,
            "decision": response.cognos.decision
        }
```

## API Reference

### CognosClient

#### `__init__(base_url, api_key, timeout)`

Initialize the client.

**Parameters:**
- `base_url` (str): CognOS gateway URL (default: `http://localhost:8788`)
- `api_key` (str, optional): API key for authentication
- `timeout` (float): Request timeout in seconds (default: 30)

---

#### `chat(model, messages, mode, ...)`

Call LLM through gateway.

**Parameters:**
- `model` (str): Model ID (required)
- `messages` (list): Chat messages (required)
- `mode` (str): "monitor" or "enforce" (default: "monitor")
- `temperature` (float, optional): 0.0–2.0
- `max_tokens` (int, optional): Max tokens to generate
- `stream` (bool): Enable streaming (default: False)
- `**kwargs`: Additional LLM parameters

**Returns:** `ChatResponse`

---

#### `get_trace(trace_id)`

Retrieve full trace record.

**Parameters:**
- `trace_id` (str): Trace ID from response

**Returns:** `dict` with trace data

---

#### `create_trust_report(trace_ids, regime, fmt)`

Generate compliance report.

**Parameters:**
- `trace_ids` (list): Trace IDs to include
- `regime` (str): Compliance regime ("EU_AI_ACT", "GDPR", "SOC2", "DEFAULT")
- `fmt` (str): Format ("json", "csv", "pdf")

**Returns:** `dict` with report

---

#### `healthz()`

Check gateway health.

**Returns:** `dict` with status

---

#### `close()`

Close client connection.

---

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=cognos
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## Support

- 📖 [Documentation](https://docs.cognos.base76.se)
- 💬 [Discord Community](https://discord.gg/...)
- 🐛 [Issue Tracker](https://github.com/base76-research-lab/operational-cognos/issues)

---

**Made by [Base76 Research Lab](https://base76.se)**
