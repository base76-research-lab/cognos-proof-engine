# Operational Cognos

> **CognOS Proof Engine** — From verified progress to public trust.

## Syfte

Ett operativt projekt för att ta CognOS från forskning till produkt med maximal hastighet och mätbar unicorn-dynamik.

## Fokus (MVP)

- Bygg Trust Gateway (OpenAI-kompatibel)
- Etablera C-loop (compounding data moat)
- Etablera D-loop (friktionsfri distribution)
- Mät TVV och externa integrationer

## Struktur

- `docs/` – beslut, design och protokoll
- `src/` – implementation

## Snabbstart

1. Läs `docs/UNICORN_BLUEPRINT.md` (strategisk riktning)
2. Kör `docs/EXECUTION_30_DAYS.md` som daglig operativ plan
3. Bygg enligt `docs/MVP_PRODUCT_SPEC.md`
4. Uppdatera status i `docs/ROADMAP.md` dagligen

## Operativ princip

- Scope lock: inga sidospår före extern trafik
- Shipping > polish
- Product loop > konsultleverans

## Nordstjärna

`TVV (Total Verified Volume)` + externa återkommande integrationer

## Kör gateway (vecka 1)

1. Installera dependencies: `pip install -r requirements.txt`
2. Sätt miljövariabler (kopiera `.env.example`)
3. Starta server: `uvicorn src.main:app --reload --port 8788`
4. Hälsokoll: `GET http://127.0.0.1:8788/healthz`

Ubuntu/PEP668-notis:

- Om `pip` är låst i systemmiljön, kör: `python3 -m pip install --user --break-system-packages -r requirements.txt`

## Mock-läge för snabb validering

- Aktivera lokalt mock upstream: `export COGNOS_MOCK_UPSTREAM=true`
- Kör OC-001 smoke-test (100 requests): `python3 src/smoke_oc001.py`
- Kör OC-002 smoke-test (trace persist + endpoint): `python3 src/smoke_oc002.py`
- Kör OC-006 smoke-test (TVV sync från trace-db): `python3 src/smoke_oc006.py`

## Trace-persistens

- DB-sökväg styrs av `COGNOS_TRACE_DB` (default: `data/traces.sqlite3`)
- Hämta trace: `GET /v1/traces/{trace_id}`

## Kör agent-OS

1. Se status: `python3 src/agent_orchestrator.py status`
2. Hämta nästa uppgift: `python3 src/agent_orchestrator.py next`
3. Filtrera per agent: `python3 src/agent_orchestrator.py next --agent builder`
4. Markera start/klart:
   - `python3 src/agent_orchestrator.py start --id OC-001`
   - `python3 src/agent_orchestrator.py complete --id OC-001 --notes "done"`
5. Uppdatera metrics:
   - `python3 src/agent_orchestrator.py metrics --tvv-requests 100 --tvv-tokens 30000 --external-integrations 1 --enforce-share 0.1`
6. Synka TVV automatiskt från trace-db:
   - `python3 src/agent_orchestrator.py sync-tvv`

Detaljerad körning: `docs/AGENT_EXECUTION.md`

## GitHub-autopilot (agentstyrt)

- Skapa repo + commit + push automatiskt:
   - `python3 src/gh_autopilot.py --repo operational-cognos --owner base76-research-lab --visibility private`
- Guide: `docs/GITHUB_AUTOPILOT.md`

## n8n social autopilot

Status: autopost är pausad (PIN) tills vidare. Aktivt läge är manuell publicering.

Detta flöde utgör distributionlagret i **CognOS Proof Engine**.

- Generera content från agentdata:
   - `python3 src/social_content_pipeline.py --stdout`
- Workflow för publicering:
   - `ops/n8n/workflows/cognos-social-autopilot.json`
- LinkedIn: använd n8n OAuth credential kopplad till profil (`/in/bjornshomelab`) som primär väg
- Profil-URL:er (för metadata/templates):
   - `LINKEDIN_PROFILE_URL`, `X_PROFILE_URL` i `.env`
- Publiceringsgate:
   - `LINKEDIN_AUTOPUBLISH=true` och/eller `X_AUTOPUBLISH=true` krävs för faktisk postning
- Guide:
   - `docs/N8N_SOCIAL_AUTOMATION.md`
- Agent-capture (alla genererade payloads):
   - `ops/content/agent_posts/`

## Manuell post-generator (aktivt läge)

- Generera copy för LinkedIn + X till markdown-fil:
   - `python3 src/manual_post_generator.py`
- Endast LinkedIn:
   - `python3 src/manual_post_generator.py --channel linkedin`
- Print till terminal istället för fil:
   - `python3 src/manual_post_generator.py --stdout`
- Output-katalog:
   - `ops/content/manual_posts/`
- Cleanup capture-filer (behåll senaste 100):
   - `python3 src/cleanup_agent_posts.py --keep 100 --dry-run`
   - `python3 src/cleanup_agent_posts.py --keep 100`

## CognOS Proof Engine Autopilot (handsfree)

- Kör hela kedjan automatiskt (generate + cleanup + commit + push):
   - `python3 src/proof_engine_autopilot.py`
- Endast generation (ingen git):
   - `python3 src/proof_engine_autopilot.py --no-git`
- Commit utan push:
   - `python3 src/proof_engine_autopilot.py --no-push`
