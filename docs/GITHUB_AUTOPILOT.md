# GitHub Autopilot — Operational Cognos

## Syfte

Låta agenter skapa repo + pusha kod automatiskt utan manuell GitHub-hantering.

## Krav

- `gh` installerad
- `gh auth status` OK
- Token-scope inkluderar `repo` och `workflow`

## Kommando (autonomt)

Kör från projektroten:

`python3 src/gh_autopilot.py --repo operational-cognos --owner base76-research-lab --visibility private`

Detta gör:

1. Verifierar GitHub-auth
2. Initierar git-repo vid behov
3. Säkrar branch (`main`)
4. Skapar repo om det saknas
5. Lägger remote `origin`
6. Commit + push

## Vanliga varianter

Publikt repo:

`python3 src/gh_autopilot.py --repo operational-cognos --owner base76-research-lab --visibility public`

Skapa/uppdatera remote men utan push:

`python3 src/gh_autopilot.py --repo operational-cognos --owner base76-research-lab --no-push`

## Agentpolicy

- Builder får köra autopilot efter varje P0/P1-mergepunkt.
- Growth får köra autopilot före extern onboarding.
- Conductor loggar repo-URL i handoff.
