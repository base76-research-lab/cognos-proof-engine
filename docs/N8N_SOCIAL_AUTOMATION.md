# CognOS Proof Engine — n8n Social Automation

> Status: **Autopost pausad**. Aktivt läge är manuell publicering via generator + copy/paste.

> Positionering: **CognOS Proof Engine** — From verified progress to public trust.

## Mål
Automatisera återkommande marknadsföring från faktisk agentprogress:

- Agentdata -> content batch
- Content batch -> publicering LinkedIn/X
- Minimal manuell insats

## Primära profiler
- LinkedIn: `https://www.linkedin.com/in/bjornshomelab/`
- X: `https://x.com/Q_for_qualia`

## Flöde
Workflow-fil:
- `ops/n8n/workflows/cognos-social-autopilot.json`

Pipeline:
1. Daily trigger (vardagar 09:00)
2. `python3 src/social_content_pipeline.py --stdout`
3. Parse JSON payload
4. Publicera LinkedIn-post
5. Publicera X-post

## LinkedIn via n8n OAuth (profil)
Rekommenderad väg för LinkedIn är n8n-credential med OAuth2 mot din profil, inte statisk bearer-token i workflow-JSON.

Steg i n8n:
1. Skapa credential för LinkedIn OAuth2 i n8n (Connect account)
2. Använd LinkedIn-route/nod för postning till profil
3. Verifiera att rätt profil är kopplad: `https://www.linkedin.com/in/bjornshomelab/`
4. Kör manuellt test med en kort post innan schemalagd körning

Notera:
- Behörigheter/scope måste stödja profilpublicering i din app-konfiguration
- OAuth i n8n credentials är primär väg; token-url fallback är endast backup

### OAuth-checklista (fält för fält)
1. n8n -> Credentials -> New -> `OAuth2 API` (eller LinkedIn credential om tillgänglig)
2. Sätt namn: `linkedin_bjorn_profile`
3. Authorization URL: `https://www.linkedin.com/oauth/v2/authorization`
4. Access Token URL: `https://www.linkedin.com/oauth/v2/accessToken`
5. Client ID: från din LinkedIn Developer App
6. Client Secret: från din LinkedIn Developer App
7. Scope: lägg minsta nödvändiga för profilpostning enligt din app-policy
8. Redirect URL: kopiera från n8n credential och lägg in exakt samma i LinkedIn App settings
9. Klicka `Connect account` och logga in med rätt konto
10. Verifiera efter auth att kontot är din profil: `https://www.linkedin.com/in/bjornshomelab/`

### Koppla credential i workflow
1. Öppna `Publish LinkedIn`-steget
2. Välj `Authentication = OAuth2` och credential `linkedin_bjorn_profile`
3. Kör workflow manuellt med testtext
4. Bekräfta post på profil innan schema aktiveras

### Driftläge (rekommenderat)
- `LINKEDIN_AUTOPUBLISH=false` under test/review
- Sätt `LINKEDIN_AUTOPUBLISH=true` först när OAuth-test är godkänt
- Behåll token-baserad HTTP-rout endast som fallback

## Miljövariabler (n8n)
- `LINKEDIN_PUBLISH_URL` (fallback)
- `LINKEDIN_TOKEN` (fallback)
- `X_PUBLISH_URL`
- `X_BEARER_TOKEN`
- `LINKEDIN_AUTOPUBLISH` (`true`/`false`, default `false`)
- `X_AUTOPUBLISH` (`true`/`false`, default `false`)

## Säkerhetsprinciper
- Tokens endast i n8n env/credentials, aldrig i repo
- Publicering bygger på agenternas status och completion_notes
- Starta i "review-läge" innan full autopublicering
- Workflowet publicerar endast när respektive `*_AUTOPUBLISH=true`

## Rekommenderad rollout
1. Kör workflow manuellt i test och kontrollera payload
2. Publicera endast LinkedIn första veckan
3. Aktivera X när copy-format validerats
4. Kör veckovis metrics-review: reach, CTR, inbound leads

## Kommandot bakom content batch
- `python3 src/social_content_pipeline.py --stdout`
- eller spara batchfiler i outbox: `python3 src/social_content_pipeline.py`

## Manuell post-generator (rekommenderat nu)
- Skapa färdig copy till markdown för copy/paste:
	- `python3 src/manual_post_generator.py`
- Endast LinkedIn:
	- `python3 src/manual_post_generator.py --channel linkedin`
- Print i terminal:
	- `python3 src/manual_post_generator.py --stdout`

Output:
- `ops/content/manual_posts/`

Agent-capture (automatisk, alla körningar):
- `ops/content/agent_posts/`
- Cleanup (behåll senaste 100):
	- `python3 src/cleanup_agent_posts.py --keep 100 --dry-run`
	- `python3 src/cleanup_agent_posts.py --keep 100`

Outbox:
- `ops/content/outbox/`

## Go-live check (första produktionskörning)
1. OAuth credential `linkedin_bjorn_profile` är ansluten och verifierad mot rätt profil
2. Workflow kör manuellt utan fel med testtext
3. `LINKEDIN_AUTOPUBLISH=true` endast när test är godkänt
4. X hålls avstängd (`X_AUTOPUBLISH=false`) under första veckan
5. Första veckan: verifiera daglig post + logga utfall (reach/CTR/inbound)

## Playwright fallback (web login + manuell confirm)
När OAuth/API-route inte är tillgänglig kan du använda browser-assist:

1. Installera dependencies: `pip install -r requirements.txt`
2. Installera browser runtime: `python3 -m playwright install chromium`
3. Förhandsvisa URL:er: `python3 src/social_web_assist.py --print-only`
4. Öppna compose-flikar: `python3 src/social_web_assist.py`
5. Auto-click LinkedIn (armerad): `python3 src/social_web_assist.py --auto-linkedin-click --arm-key POST_NOW --countdown-seconds 5`
6. Om LinkedIn säger "webbläsaren inte säker": `python3 src/social_web_assist.py --browser-channel chrome --user-data-dir .playwright-profile`
7. Fallback (ingen Playwright-login): `python3 src/social_web_assist.py --open-default-browser`

Detta läge är human-in-the-loop: agenten genererar text och öppnar compose, men du bekräftar publicering manuellt i UI.

Auto-click-läget klickar endast LinkedIn publiceringsknapp efter att du först bekräftat inloggning + text, och endast när `--arm-key POST_NOW` används.

Om LinkedIn blockerar automatiserad browser-signin, använd `--browser-channel chrome` med persistent profil eller kör `--open-default-browser` och gör login/publicering manuellt.
