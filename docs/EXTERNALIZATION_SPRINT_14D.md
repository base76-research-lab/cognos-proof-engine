# CognOS Proof Engine — Externalization Sprint (14 Days)

![CognOS Brand](assets/logo/cognos-logo-horizontal.svg)

Goal: move from internal proof engine to first external usage.

## Success Criteria
- 3 alpha users invited
- 1 external developer onboarded
- 100 real external requests through gateway
- 1 public proof artifact (demo/video/post)

## Core Message
Use one short message across all channels:

"CognOS adds trust verification to AI API traffic with a minimal integration surface."

## Scope Lock (Do Not Expand)
- No new architecture work
- No extra automation layers
- No UI expansion beyond onboarding essentials
- Focus only on onboarding, usage, and feedback loop

## 14-Day Plan

### Days 1-2: Public Readiness
1. Ensure README clearly states value proposition and quickstart.
2. Prepare a minimal public onboarding path:
   - Health check endpoint
   - One request example
   - One trace retrieval example
3. Verify local reliability with smoke tests.

### Days 3-5: Drop-In Example
1. Publish a minimal client example showing integration change.
2. Keep example language simple and copy-paste ready.
3. Validate the example end-to-end against running gateway.

### Days 6-10: Alpha Outreach
1. Select 3 target alpha users (quality over volume).
2. Send one clear onboarding message with example + expected setup time.
3. Track responses and onboarding status in a simple list.

### Days 11-14: Usage + Proof
1. Support first external user to successful traffic.
2. Confirm 100 external requests target.
3. Publish one proof artifact with concrete numbers:
   - request volume
   - trace visibility
   - integration friction notes

## Daily Operator Checklist
1. Run gateway and verify health.
2. Confirm trace persistence is working.
3. Review current TVV and external integration count.
4. Execute one outreach or onboarding action.
5. Log one outcome from external interaction.

## Recommended Commands
- Start gateway: `uvicorn src.main:app --reload --port 8788`
- Health check: `curl -s http://127.0.0.1:8788/healthz`
- Smoke tests:
  - `python3 src/smoke_oc001.py`
  - `python3 src/smoke_oc002.py`
  - `python3 src/smoke_oc006.py`
- TVV sync: `python3 src/agent_orchestrator.py sync-tvv`

## Exit Condition
Sprint is complete when at least one external developer successfully runs production-like traffic and provides real feedback.
