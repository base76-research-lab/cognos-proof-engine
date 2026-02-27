# Agent Execution — Operational Cognos

## Syfte

Spinna upp ett agent-kluster som driver CognOS från MVP till extern traction med strikt operativ disciplin.

## Agenter (MVP)

- Conductor
- Builder
- Growth

Konfig:

- `ops/agents/agents.json`
- `ops/agents/backlog.json`
- `ops/agents/state.json`
- `ops/prompts/*.md`

## Körning (CLI)

Från projektroten:

`cd /media/bjorn/iic/workspace/01_RESEARCH/operational-cognos`

1. Status
`python3 src/agent_orchestrator.py status`

2. Hämta nästa uppgift (globalt)
`python3 src/agent_orchestrator.py next`

3. Hämta nästa uppgift per agent
`python3 src/agent_orchestrator.py next --agent builder`
`python3 src/agent_orchestrator.py next --agent growth`
`python3 src/agent_orchestrator.py next --agent conductor`

4. Markera start
`python3 src/agent_orchestrator.py start --id OC-001`

5. Markera klart
`python3 src/agent_orchestrator.py complete --id OC-001 --notes "Passthrough stabil i 100 testrequests"`

6. Uppdatera north-star
`python3 src/agent_orchestrator.py metrics --tvv-requests 1200 --tvv-tokens 450000 --external-integrations 1 --enforce-share 0.12`

7. Synka TVV från trace-db
`python3 src/agent_orchestrator.py sync-tvv`

## Operativ rytm (dagligen)

1. Conductor kör `status` + `next`
2. Builder/Growth tar varsin P0/P1-uppgift
3. Uppgifter markeras `in_progress` -> `done`
4. Metrics uppdateras före sessionstopp

## Policy för fart

- Max 1 huvudmål per dag
- Ingen ny feature utan koppling till TVV eller extern integration
- Blockers över 24h måste eskaleras

## GitHub-automation

- Builder/Growth får köra repo-create + push autonomt via:
  - `python3 src/gh_autopilot.py --repo operational-cognos --owner base76-research-lab --visibility private`
- Full guide: `docs/GITHUB_AUTOPILOT.md`

## Första sprintmål

- Stabil gateway
- Trace retrieval
- Första externa dev onboardad
- Första riktiga requests genom gateway
