# Operational Cognos — MVP Product Spec

![CognOS Brand](assets/logo/cognos-logo-horizontal.svg)

## Produktdefinition
CognOS MVP är en OpenAI-kompatibel Trust Gateway som lägger ett verifieringslager ovanpå existerande LLM-anrop.

## Primär användare
- AI-utvecklare som redan använder LLM-API:er
- Team som behöver trust/compliance-spårbarhet utan att bygga om stacken

## Job-to-be-done
"Låt mig slå på verifiering och riskstyrning i mitt befintliga AI-flöde med minimal kodändring."

## Scope (MVP)

### In
- OpenAI-kompatibel gateway endpoint
- Trace-id och trust headers
- CognOS envelope i svar
- Policy modes (`monitor`, `enforce`)
- Fingerprints + signalvektor + shadow 1%
- JSON trust/shadow-report

### Out
- Full dashboard-suite
- Komplex policy-UI
- Multi-tenant enterprise billing
- PDF-generatorer i version 1

## API-surface (MVP)
- `POST /v1/chat/completions`
- `GET /v1/traces/{trace_id}`
- `POST /v1/reports/trust`
- `POST /v1/reports/shadow`

## Response Contract
Varje completion innehåller:
- originellt LLM-svar
- `cognos.decision`
- `cognos.risk`
- `cognos.signals`
- `cognos.trace_id`
- `cognos.attestation`

## Epistemic Headers
- `X-Cognos-Trace-Id`
- `X-Cognos-Decision`
- `X-Cognos-Trust-Score`
- `X-Cognos-Policy`

## Data Policy
- Ingen rå prompt/response lagras i defaultläge
- Endast fingerprints + signalmetadata + utfall
- Opt-in krävs för utökad lagring

## KPI-set

### North Star
- TVV: verified requests + verified tokens

### Guardrails
- p95 overhead < 100ms (exkl inferens)
- shadow påverkar inte klientens streaminglatens
- beslutsspårbarhet via trace_id i 100% av svar

### Product Traction
- externa aktiva integrationer
- weekly retention per integration
- andel trafik med `enforce`

## Definition of Done (MVP)
MVP är klar när:
1. Extern utvecklare kan integrera på <30 min
2. Gatewayn levererar stabilt under återkommande trafik
3. Trust/shadow-rapport går att generera utan manuellt arbete
4. Teamet kan identifiera och deploya minst 1 policy patch från verklig driftdata
