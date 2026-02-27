# Proof of Concept (Internal)

Purpose: show that CognOS verifies one real AI request end-to-end in minutes.

## 1) Start gateway

```bash
cd /media/bjorn/iic/workspace/01_RESEARCH/operational-cognos

# Example upstream (choose one provider)
export COGNOS_UPSTREAM_BASE_URL="https://openrouter.ai/api/v1"
export COGNOS_UPSTREAM_API_KEY="YOUR_PROVIDER_KEY"
export COGNOS_MOCK_UPSTREAM=false

python3 -m uvicorn --app-dir src main:app --host 127.0.0.1 --port 8788
```

## 2) Run PoC flow (new terminal)

```bash
cd /media/bjorn/iic/workspace/01_RESEARCH/operational-cognos
python3 src/poc_e2e.py --model openai:gpt-4o-mini
```

Alternative models:

```bash
python3 src/poc_e2e.py --model google:gemini-2.0-flash-001
python3 src/poc_e2e.py --model claude:claude-sonnet-4
```

## 3) What success looks like

Expected terminal output includes:

- `[POC] completion ok`
- `trace_id=...`
- `[POC] trace lookup ok`
- `[POC] trust report ok`
- `[POC] SUCCESS: end-to-end flow verified`

## Optional: local-only demo without provider key

If no API keys are available, use local Ollama:

```bash
export COGNOS_UPSTREAM_BASE_URL="http://127.0.0.1:11434/v1"
export COGNOS_UPSTREAM_API_KEY=""
export COGNOS_ALLOW_NO_UPSTREAM_AUTH=true
export COGNOS_MOCK_UPSTREAM=false
```

Then run:

```bash
python3 src/poc_e2e.py --model llama3.2:latest
```
