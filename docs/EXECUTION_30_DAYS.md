# Operational Cognos — 30-dagars Exekvering

## Princip
Leverera minsta möjliga fungerande trust-infrastruktur med extern trafik före dag 30.

## Dag 0 — Scope lock
- Lås MVP-scope (inga extra features)
- Definiera kill-switch och go-kriterier
- Definiera daglig rapportstruktur (max 10 min)

## Vecka 1 (Dag 1–7) — Gateway Skeleton

### Mål
Pass-through gateway med tracebarhet.

### Leveranser
- `POST /v1/chat/completions` passthrough
- OpenAI-kompatibel request/response
- `X-Cognos-Trace-Id` i alla svar
- Grundläggande loggning av metadata

### Acceptanskriterier
- Minst 100 interna testrequests utan kritiskt fel
- p95 gateway-overhead mätt

## Vecka 2 (Dag 8–14) — Trust Envelope + Policy v0

### Mål
Sätta första verifieringslagret.

### Leveranser
- `cognos` envelope i response body
- Beslut: `PASS|REFINE|ESCALATE|BLOCK`
- Policy modes: `monitor` och `enforce`
- Headers: trust-score, decision, policy

### Acceptanskriterier
- Beslutsmotor triggar korrekt på testsignaler
- p95 overhead fortsatt inom målområde

## Vecka 3 (Dag 15–21) — C-loop v0

### Mål
Bygga compounding-kärnan utan rådata.

### Leveranser
- Prompt/response fingerprinting
- Signalvektor per trace
- Shadow benchmarking (1% trafik, asynkront)
- Drift/hotspot-sammanställning v0

### Acceptanskriterier
- Shadow-jobb påverkar inte klientlatens
- Hotspot-lista kan genereras från lagrad data

## Vecka 4 (Dag 22–30) — Extern Alpha

### Mål
Bevisa verklig distribution.

### Leveranser
- 3–5 externa alpha-utvecklare onboardade
- Enkel Trust Report-export (`json`)
- Dashboard/CLI med TVV + drift + divergence
- Första policy patch-förslag automatiserat

### Acceptanskriterier
- Minst 3 externa integrationer aktiva
- Minst 1 integration kör `enforce`
- TVV visar stigande trend över minst 7 dagar

## Kill-switch dag 30

Om följande inte uppnås: pausa expansion, återgå till förenklad iteration i 14 dagar.

- < 3 externa aktiva integrationer
- Ingen återkommande extern trafik
- p95 overhead klart över mål
- Ingen tydlig signal att `C × D` förbättras

## GO-beslut dag 30

Fortsätt skala till dag 90 endast om:

- Externa användare återkommer frivilligt
- `enforce` används i verklig trafik
- Drift/hotspots skapar tydliga policy actions
- Teamet kan leverera veckovis utan scope-översvämning

## Daglig operativ rytm (maximal skärpa)

- 1 prioriterad leverans per dag
- 1 mätpunkt per dag (TVV, latency, drift eller integration)
- 1 blocker per dag som aktivt elimineras
- 1 kort handoff-logg innan sessionstopp
