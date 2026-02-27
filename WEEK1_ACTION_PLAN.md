# Week 1 Action Plan — Unicorn Sprint

**Goal:** Make CognOS so easy to adopt that it spreads virally.

**Energy Required:** 70–80% (this is YOUR work, not delegation)

---

## Day 1–2: Docker + Marketing Site (4 hours)

### Task 1: Ship Docker Image (2 hours)

1. **Create `Dockerfile`** at repo root:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy only requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY src/ src/
COPY .env.example .env

# Default: mock mode (zero config needed)
ENV COGNOS_MOCK_UPSTREAM=true
ENV COGNOS_TRACE_DB=/data/traces.sqlite3

EXPOSE 8788

CMD ["python3", "-m", "uvicorn", "--app-dir", "src", "main:app", "--host", "0.0.0.0", "--port", "8788"]
```

2. **Create `.dockerignore`:**
```
__pycache__
.git
.venv
tests
*.pyc
```

3. **Build + Test locally:**
```bash
docker build -t base76/cognos:latest .
docker run -p 8788:8788 base76/cognos:latest

# In another terminal:
curl http://localhost:8788/healthz
```

4. **Push to Docker Hub:**
```bash
docker tag base76/cognos:latest base76/cognos:v0.1.0
docker push base76/cognos:v0.1.0
```

### Task 2: One-Page Marketing Site (2 hours)

**File:** `docs/www/index.html` (static HTML, no framework)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CognOS — Trust Infrastructure for AI</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
        h1 { font-size: 3em; margin: 0 0 20px 0; color: #000; }
        .subtitle { font-size: 1.3em; color: #666; margin-bottom: 40px; }
        .cta-btn { background: #000; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; display: inline-block; margin: 10px 10px 10px 0; }
        .cta-btn:hover { background: #333; }
        code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        .quickstart { background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 30px 0; }
        .features { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 40px 0; }
        .feature { padding: 20px; border: 1px solid #eee; border-radius: 8px; }
        .feature h3 { margin-top: 0; }
        footer { border-top: 1px solid #eee; margin-top: 60px; padding-top: 20px; color: #999; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CognOS</h1>
        <p class="subtitle">Trust Verification for Every AI Request</p>

        <p style="font-size: 1.1em;">
            Attestation layer for LLM applications. Prove decision origin. Audit everything. Pass compliance.
        </p>

        <div>
            <a href="https://github.com/base76-research-lab/operational-cognos" class="cta-btn">⭐ GitHub</a>
            <a href="https://docs.cognos.base76.se" class="cta-btn">📖 Docs</a>
            <a href="https://discord.gg/..." class="cta-btn">💬 Discord</a>
        </div>

        <h2>Try It Now (30 seconds)</h2>

        <div class="quickstart">
            <h3>Option 1: Docker (simplest)</h3>
            <pre><code>docker run -p 8788:8788 base76/cognos:latest

# Test in another terminal:
curl http://localhost:8788/healthz</code></pre>

            <h3>Option 2: Python SDK</h3>
            <pre><code>pip install cognos-sdk

from cognos import CognosClient
client = CognosClient()
response = client.chat(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hi"}]
)
print(response.cognos.decision)  # "PASS"</code></pre>
        </div>

        <h2>Why CognOS?</h2>
        <div class="features">
            <div class="feature">
                <h3>📋 Audit Trails</h3>
                <p>Immutable record of every AI decision. Who asked? What did it answer? What was the risk?</p>
            </div>
            <div class="feature">
                <h3>✅ Proof of Correctness</h3>
                <p>Cryptographic attestation. Prove to regulators that your AI is behaving as intended.</p>
            </div>
            <div class="feature">
                <h3>⚖️ Compliance Ready</h3>
                <p>EU AI Act. GDPR. SOC2. We generate the reports.</p>
            </div>
            <div class="feature">
                <h3>🔌 Provider Agnostic</h3>
                <p>Works with OpenAI, Claude, Google, Mistral, Ollama. Your choice.</p>
            </div>
        </div>

        <h2>For Enterprises</h2>
        <p>Need compliance documentation? Custom policies? Threat intelligence?
        <a href="mailto:hello@base76.se">Contact us</a>.</p>

        <footer>
            Made by <a href="https://base76.se">Base76 Research Lab</a> •
            <a href="https://github.com/base76-research-lab/operational-cognos">Open Source</a> •
            <a href="https://twitter.com/base76_ai">Follow</a>
        </footer>
    </div>
</body>
</html>
```

Deploy to GitHub Pages or Vercel (free).

---

## Day 3–4: Python SDK (4 hours)

### Task: Build Minimal Python SDK

**File:** `cognos-sdk/cognos/__init__.py` (new directory)

```python
from __future__ import annotations

import httpx
from dataclasses import dataclass
from typing import Any


@dataclass
class CognosEnvelope:
    decision: str  # "PASS" | "REFINE" | "ESCALATE" | "BLOCK"
    risk: float
    trace_id: str
    policy: str


@dataclass
class ChatResponse:
    id: str
    choices: list[dict[str, Any]]
    cognos: CognosEnvelope


class CognosClient:
    def __init__(self, base_url: str = "http://localhost:8788", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.Client()

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        mode: str = "monitor",
        **kwargs: Any,
    ) -> ChatResponse:
        """
        Call LLM through CognOS gateway.

        Args:
            model: Model ID (e.g., "gpt-4o-mini", "claude:claude-3-sonnet")
            messages: List of messages
            mode: "monitor" (always pass) or "enforce" (apply policies)
            **kwargs: Additional parameters (temperature, max_tokens, etc)

        Returns:
            ChatResponse with cognos envelope
        """
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        payload = {
            "model": model,
            "messages": messages,
            "cognos": {
                "mode": mode,
                "policy_id": "default_v1",
            },
            **kwargs,
        }

        response = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        envelope_data = data.get("cognos", {})
        envelope = CognosEnvelope(
            decision=envelope_data.get("decision", "UNKNOWN"),
            risk=envelope_data.get("risk", 0.0),
            trace_id=envelope_data.get("trace_id", ""),
            policy=envelope_data.get("policy", ""),
        )

        return ChatResponse(
            id=data.get("id", ""),
            choices=data.get("choices", []),
            cognos=envelope,
        )

    def get_trace(self, trace_id: str) -> dict[str, Any]:
        """Retrieve full trace record."""
        response = self.client.get(f"{self.base_url}/v1/traces/{trace_id}")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self) -> CognosClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


__all__ = ["CognosClient", "ChatResponse", "CognosEnvelope"]
```

**File:** `cognos-sdk/setup.py`

```python
from setuptools import setup

setup(
    name="cognos-sdk",
    version="0.1.0",
    description="Trust verification SDK for LLM applications",
    author="Base76 Research Lab",
    author_email="hello@base76.se",
    url="https://github.com/base76-research-lab/operational-cognos",
    packages=["cognos"],
    install_requires=["httpx>=0.27.0"],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
```

**Build + Publish:**
```bash
cd cognos-sdk
python setup.py sdist bdist_wheel
twine upload dist/  # Requires PyPI account
```

---

## Day 5: Marketing Push (2 hours)

### Task 1: Post to Hacker News (30 min)

```
Title: CognOS – Trust Verification Layer for LLM Applications
Link: https://github.com/base76-research-lab/operational-cognos
Text:

We built CognOS because enterprises need to prove their AI works.
Not just monitor it. PROVE it.

- Cryptographic attestation for every AI request
- Audit trails for compliance (EU AI Act, GDPR, SOC2)
- Works with any provider (OpenAI, Claude, Google, etc)
- Zero-config Docker: `docker run -p 8788:8788 base76/cognos`

It's open source + MIT licensed. Try it now.

Feedback welcome. (I'm the author.)
```

**Timing:** Tuesday 10am ET (peak HN traffic)

### Task 2: Tweet Thread (30 min)

```
🧵 We just open-sourced CognOS:
Trust verification layer for LLM apps.

Why it matters:
- EU AI Act → enterprises need audit trails
- LLM failures → need proof of decision origin
- No good solutions → we built one

1/5

---

Problem: "My AI works" ≠ "My AI is trustworthy"
- Hallucinations happen
- Bias creeps in
- Regulators want proof
- Current solutions? Just monitoring (insufficient)

We built attestation instead.

2/5

---

How it works:
Every AI request gets:
✅ Unique trace ID
✅ Cryptographic signature
✅ Risk assessment
✅ Policy decision (PASS/ESCALATE/BLOCK)

All queryable. All auditable.

3/5

---

Try it now:

```
docker run -p 8788:8788 base76/cognos
curl http://localhost:8788/healthz
```

Or Python:
```
pip install cognos-sdk
from cognos import CognosClient
client = CognosClient()
```

4/5

---

We're hiring + fundraising for enterprise sales.
If you're in AI safety/compliance space: DM me.

Open source: github.com/base76-research-lab/operational-cognos
Website: cognos.base76.se

5/5
```

**Post to:** Twitter, LinkedIn, Reddit (/r/MachineLearning, /r/webdev)

### Task 3: Email to Key Networks (1 hour)

Send personal emails to:
- AI safety researchers you know
- Compliance officers at startups
- VCs interested in AI infrastructure
- Beta testers (offer free tier)

Subject: "Try CognOS — 30-second setup, production-ready trust infrastructure"

---

## Week 1 Deliverables Checklist

- [ ] Dockerfile built + pushed to Docker Hub
- [ ] Static marketing site deployed
- [ ] Python SDK published to PyPI
- [ ] Posted to Hacker News
- [ ] Tweet thread live
- [ ] Emails sent to 20+ key contacts

**Expected Outcomes:**
- 50–100 GitHub stars (if HN hits front page)
- 5–10 Docker pulls
- 2–3 SDK pip installs
- 3–5 "I want to try this" replies

---

## Week 2–3 Milestones (Follow-up)

### Week 2: Capture First Users
- [ ] Respond to every GitHub issue within 6 hours
- [ ] Create "getting started" video (3 min)
- [ ] Ship first community policy (e.g., "Healthcare Compliance")
- [ ] Launch Discord (free community)

### Week 3: Measure Product-Market Fit
- [ ] Survey users: "Would you recommend to a friend?"
- [ ] Track: Docker pulls/week, GitHub stars, SDK downloads
- [ ] If NPS > 40: Validate. If < 40: Iterate.

---

## Time Investment Summary

- **Day 1–2:** 4 hours (Docker + marketing site)
- **Day 3–4:** 4 hours (Python SDK)
- **Day 5:** 2 hours (Marketing push)

**Total: 10 hours over 5 days = 2 hours/day**

This is **high-ROI work**. Each hour compounds into distribution.

---

## Key Principle

**Friction kills startups.**

Every step should feel like:
1. Read about CognOS (1 min)
2. Try it (30 sec: `docker run`)
3. Integrate it (5 min: copy 5 lines of code)
4. Recommend it (to 3 friends)

That's the unicorn path. Ship this first.

---

**Ready? Start Day 1 tomorrow.**
