# Roadmap — Operational Cognos

## Fas 0: Scope Lock (Dag 0)
- [ ] Lås MVP-scope enligt `MVP_PRODUCT_SPEC.md`
- [ ] Lås kill-switch och GO-kriterier för dag 30
- [ ] Lås daglig rapportstruktur (kort, mätbar)

## Fas 1: Build Core Gateway (Dag 1–14)
- [ ] Pass-through `POST /v1/chat/completions`
- [ ] `X-Cognos-Trace-Id` i alla svar
- [ ] Trust envelope + decision (`PASS|REFINE|ESCALATE|BLOCK`)
- [ ] Policy modes: `monitor` och `enforce`
- [ ] Mät p95 overhead kontinuerligt

## Fas 2: Activate C-loop (Dag 15–21)
- [ ] Fingerprints + signalvektor (privacy-first)
- [ ] Shadow benchmarking 1% (asynkront)
- [ ] Hotspot/drift sammanställning v0
- [ ] Första auto-policy patch-förslag

## Fas 3: External Traction (Dag 22–30)
- [ ] Onboarda 3–5 externa alpha-utvecklare
- [ ] Generera trust/shadow-report utan manuella steg
- [ ] Minst 1 extern integration i `enforce`
- [ ] Visa stigande TVV-trend över minst 7 dagar

## Kill-switch (Dag 30)
- [ ] Om <3 externa aktiva integrationer: pausa expansion, kör 14-dagars förenklad iteration
- [ ] Om p95 overhead över målnivå: optimera prestanda före nya features
- [ ] Om ingen återkommande extern trafik: revidera distribution före signalförfining

## 90-dagars target
- [ ] 5 externa utvecklare med >1000 requests var
- [ ] 3 veckors retention i rad
- [ ] Positiv trend i TVV + policy usage
- [ ] Bevis på `C × D`-förbättring från verklig data
