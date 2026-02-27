# CognOS Proof Engine — n8n Social Automation

> Status: **Autopost is paused**. Current production mode is manual publishing.

## Product Scope
This document covers only the production social pipeline:

- Agent output -> social payload
- Social payload -> LinkedIn/X publishing flow
- Manual-first operation with gated autopublish

## Primary Profiles
- LinkedIn: `https://www.linkedin.com/in/bjornshomelab/`
- X: `https://x.com/Q_for_qualia`

## Workflow
- File: `ops/n8n/workflows/cognos-social-autopilot.json`

Pipeline:
1. Scheduled trigger (weekdays)
2. `python3 src/social_content_pipeline.py --stdout`
3. Parse JSON payload
4. LinkedIn publish path
5. X publish path

## Runtime Configuration
- `LINKEDIN_PROFILE_URL`
- `X_PROFILE_URL`
- `LINKEDIN_AUTOPUBLISH` (`true`/`false`, default `false`)
- `X_AUTOPUBLISH` (`true`/`false`, default `false`)
- `LINKEDIN_PUBLISH_URL` (fallback HTTP route)
- `LINKEDIN_TOKEN` (fallback token)
- `X_PUBLISH_URL`
- `X_BEARER_TOKEN`

Publishing is blocked unless platform-specific gate flags are enabled:

- LinkedIn requires `LINKEDIN_AUTOPUBLISH=true`
- X requires `X_AUTOPUBLISH=true`

## LinkedIn Authentication
Recommended: n8n OAuth credential for profile posting.

OAuth endpoints:
- Authorization URL: `https://www.linkedin.com/oauth/v2/authorization`
- Access Token URL: `https://www.linkedin.com/oauth/v2/accessToken`

Use static token-based HTTP only as fallback.

## Manual Publishing (Current Mode)
- Generate copy batch: `python3 src/manual_post_generator.py`
- LinkedIn only: `python3 src/manual_post_generator.py --channel linkedin`
- Print only: `python3 src/manual_post_generator.py --stdout`

Output folders:
- Manual posts: `ops/content/manual_posts/`
- Agent captures: `ops/content/agent_posts/`
- Outbox: `ops/content/outbox/`

Cleanup:
- Dry run: `python3 src/cleanup_agent_posts.py --keep 100 --dry-run`
- Apply: `python3 src/cleanup_agent_posts.py --keep 100`

## Browser Fallback (Human-in-the-Loop)
When OAuth/API posting is unavailable:

1. Install runtime: `python3 -m playwright install chromium`
2. Preview targets: `python3 src/social_web_assist.py --print-only`
3. Open compose tabs: `python3 src/social_web_assist.py`
4. Optional armed click mode: `python3 src/social_web_assist.py --auto-linkedin-click --arm-key POST_NOW --countdown-seconds 5`
5. If LinkedIn blocks browser safety: `python3 src/social_web_assist.py --browser-channel chrome --user-data-dir .playwright-profile`
6. Default browser fallback: `python3 src/social_web_assist.py --open-default-browser`

In fallback mode, the agent prepares content and opens compose views; final publishing remains manual confirmation in the UI.
