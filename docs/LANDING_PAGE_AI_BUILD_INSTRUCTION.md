# Landing Page Build Instruction (for External AI Model)

![CognOS Brand](assets/logo/cognos-logo-horizontal.svg)

Purpose: this is the exact instruction package to give an AI coding model.

---

## 1) One-sentence mission

Build a single, production-ready landing page for `base76.se` that positions CognOS as **Trust Infrastructure for AI** and drives users to the GitHub repository.

---

## 2) Copy/Paste prompt to the AI model

Use this prompt exactly:

```text
You are a senior frontend engineer and conversion-focused product marketer.

Build ONE static landing page for base76.se.

Goal:
Position CognOS as "Trust Infrastructure for AI" and send users to GitHub for onboarding.

Critical positioning rules:
- CognOS is infrastructure, not a tool.
- Do NOT frame as research project.
- Do NOT frame as only a security/compliance feature.
- Keep category creation line: "Just as HTTPS secured the internet, CognOS secures AI."

Output requirements:
1) Create a single-file implementation: index.html (with embedded CSS and minimal JS).
2) Mobile-first responsive layout.
3) Fast load, no external frameworks required.
4) Professional and minimal visual style.
5) Include clear CTA buttons linking to:
   - GitHub repo: https://github.com/base76-research-lab/operational-cognos
   - Developer onboarding doc: https://github.com/base76-research-lab/operational-cognos/blob/main/docs/DEVELOPER_ONBOARDING.md
6) Include basic SEO tags (title, description, og:title, og:description, og:type).
7) Include a favicon in `<head>`.
8) Include a visual header/banner at top of page.
9) Include a footer with "Base76 Research Lab" and current year.

Page structure (exact sections):
- Hero
  Headline: "Add Trust Verification to AI in Minutes."
  Subheadline: "CognOS is a verification gateway that detects uncertainty, drift, and risk in AI outputs before they reach users."
  Primary CTA: "View on GitHub"
  Secondary CTA: "Developer Quickstart"

- Problem
  Short copy about hallucinations, silent failures, and missing verification in AI products.

- Solution
  Explain that CognOS sits between app and model providers and adds trust scoring, policy enforcement, traceability.

- How it works
  Show flow line: "Client → CognOS Gateway → Model → Verified Response"
  Include bullets: Risk signals, Decision logic, Trace IDs, Reports.

- Use cases
  AI agents, enterprise AI, RAG, regulated industries.

- Final CTA
  "Start building trusted AI today."
  Buttons to GitHub + Quickstart.

Constraints:
- Keep copy concise and high-signal.
- No fake metrics.
- No backend code.
- No extra pages.

Return:
- Complete index.html
- Short deployment note for static hosting under base76.se
```

Use this exact `<head>` snippet pattern (update paths if needed):

```html
<link rel="icon" type="image/svg+xml" href="/assets/logo/favicon.svg" />
<meta property="og:type" content="website" />
```

Use this header pattern near top of `<body>`:

```html
<header class="hero-header">
  <img src="/assets/logo/cognos-header-banner.svg" alt="CognOS Trust Infrastructure for AI" />
</header>
```

---

## 3) Acceptance criteria (must pass)

- One page only (`index.html`).
- Correct positioning language: "Trust Infrastructure for AI".
- Hero headline and subheadline exactly present.
- CTA links point to correct GitHub URLs.
- Flow section includes "Client → CognOS Gateway → Model → Verified Response".
- No claims with invented numbers.
- Looks good on mobile and desktop.
- Ready for static hosting.
- Favicon is visible in browser tab.
- Header banner is visible above fold on desktop.

---

## 4) Deployment handoff (base76.se)

Expected deliverable from AI model: `index.html`.

Deploy options:
- Upload to web root for `base76.se` (Apache/Nginx static hosting), or
- Deploy as static site via Cloudflare Pages / Netlify and map custom domain.

Post-deploy checks:
1. Open `https://base76.se`
2. Verify both CTA links
3. Check mobile rendering
4. Validate page title + description in source

---

## 5) Optional v2 ask (after v1 is live)

Ask AI model for v2 only after publish:
- Add lightweight language toggle (EN/SV)
- Add architecture SVG block
- Add copy variants for developer vs enterprise audiences

Keep v1 minimal. Ship first.
