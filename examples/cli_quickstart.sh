#!/usr/bin/env bash
set -euo pipefail

export COGNOS_BASE_URL="http://127.0.0.1:8788"
export COGNOS_API_KEY=""

# Choose one upstream mode:

# A) OpenAI/API-provider key
export COGNOS_UPSTREAM_AUTH="Bearer sk-..."

# Optional instance keys for prefix routing (fill in later)
# export COGNOS_INSTANCE_OPENAI_API_KEY="sk-..."
# export COGNOS_INSTANCE_GOOGLE_API_KEY="..."
# export COGNOS_INSTANCE_CLAUDE_API_KEY="..."
# export COGNOS_INSTANCE_MISTRAL_API_KEY="..."
# export COGNOS_INSTANCE_OLLAMA_API_KEY="..."

# B) Local Ollama (no upstream key)
# unset COGNOS_UPSTREAM_AUTH

cognos chat "Explain the EU AI Act risk levels in one paragraph" --mode monitor

# Prefix examples:
# cognos chat "Quick summary" --mode monitor --model openai:gpt-4o-mini
# cognos chat "Quick summary" --mode monitor --model google:gemini-2.0-flash-001
# cognos chat "Quick summary" --mode monitor --model claude:claude-sonnet-4
# cognos chat "Quick summary" --mode monitor --model mistral:mistral-small-latest
# cognos chat "Quick summary" --mode monitor --model ollama:llama3.2

# If you got a trace id from output, fetch it:
# cognos trace tr_xxxxxxxxxxxx
