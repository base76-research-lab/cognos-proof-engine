# CognOS Proof Engine

> **CognOS Proof Engine** — From verified progress to public trust.

## What This Repo Contains

Only the operational engine components built and run by agents:

- Gateway runtime
- Agent orchestration
- Social content generation and publishing pipeline
- End-to-end autopilot (generate → cleanup → git → push)

## Gateway Runtime

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables (copy `.env.example`)
3. Start server: `uvicorn src.main:app --reload --port 8788`
4. Health check: `GET http://127.0.0.1:8788/healthz`

Ubuntu/PEP668 note:

- If `pip` is locked in the system environment, run: `python3 -m pip install --user --break-system-packages -r requirements.txt`

## Smoke + Validation

- Enable local mock upstream: `export COGNOS_MOCK_UPSTREAM=true`
- Run OC-001 smoke test (100 requests): `python3 src/smoke_oc001.py`
- Run OC-002 smoke test (trace persist + endpoint): `python3 src/smoke_oc002.py`
- Run OC-006 smoke test (TVV sync from trace-db): `python3 src/smoke_oc006.py`

## Trace Persistence

- DB path is controlled by `COGNOS_TRACE_DB` (default: `data/traces.sqlite3`)
- Get trace: `GET /v1/traces/{trace_id}`

## Agent Orchestration

1. Check status: `python3 src/agent_orchestrator.py status`
2. Fetch next task: `python3 src/agent_orchestrator.py next`
3. Filter by agent: `python3 src/agent_orchestrator.py next --agent builder`
4. Mark start/complete:
   - `python3 src/agent_orchestrator.py start --id OC-001`
   - `python3 src/agent_orchestrator.py complete --id OC-001 --notes "done"`
5. Update metrics:
   - `python3 src/agent_orchestrator.py metrics --tvv-requests 100 --tvv-tokens 30000 --external-integrations 1 --enforce-share 0.1`
6. Sync TVV automatically from trace-db:
   - `python3 src/agent_orchestrator.py sync-tvv`

Detailed runbook: `docs/AGENT_EXECUTION.md`

## GitHub Autopilot

- Create repo + commit + push automatically:
   - `python3 src/gh_autopilot.py --repo operational-cognos --owner base76-research-lab --visibility private`
- Guide: `docs/GITHUB_AUTOPILOT.md`

## n8n Social Autopilot

Status: autopost is paused (PIN). Active mode is manual publishing.

This flow is the distribution layer in **CognOS Proof Engine**.

- Generate content from agent data:
   - `python3 src/social_content_pipeline.py --stdout`
- Publishing workflow:
   - `ops/n8n/workflows/cognos-social-autopilot.json`
- LinkedIn: use n8n OAuth credential connected to profile (`/in/bjornshomelab`) as primary path
- Profile URLs (for metadata/templates):
   - `LINKEDIN_PROFILE_URL`, `X_PROFILE_URL` in `.env`
- Publishing gate:
   - `LINKEDIN_AUTOPUBLISH=true` and/or `X_AUTOPUBLISH=true` required for live posting
- Guide:
   - `docs/N8N_SOCIAL_AUTOMATION.md`
- Agent capture (all generated payloads):
   - `ops/content/agent_posts/`

## Manual Post Generator

- Generate copy for LinkedIn + X to markdown file:
   - `python3 src/manual_post_generator.py`
- LinkedIn only:
   - `python3 src/manual_post_generator.py --channel linkedin`
- Print to terminal instead of file:
   - `python3 src/manual_post_generator.py --stdout`
- Output directory:
   - `ops/content/manual_posts/`
- Cleanup capture files (keep latest 100):
   - `python3 src/cleanup_agent_posts.py --keep 100 --dry-run`
   - `python3 src/cleanup_agent_posts.py --keep 100`

## CognOS Proof Engine Autopilot (handsfree)

- Run full chain automatically (generate + cleanup + commit + push):
   - `python3 src/proof_engine_autopilot.py`
- Generation only (no git):
   - `python3 src/proof_engine_autopilot.py --no-git`
- Commit without push:
   - `python3 src/proof_engine_autopilot.py --no-push`

## Manual Research Mode (No Agents)

- Generate a manual research brief + execution plan:
   - `python3 src/research_execution_plan.py`
- Print plan to terminal:
   - `python3 src/research_execution_plan.py --stdout`
- Include more prioritized items:
   - `python3 src/research_execution_plan.py --top 5`
- Guide:
   - `docs/RESEARCH_EXECUTION_MODE.md`
