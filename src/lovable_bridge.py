from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


SYSTEM_PROMPT = (
    "You are CognOS Planning Bridge. "
    "Return ONLY valid JSON. "
    "Create an execution-ready handoff with minimal ambiguity."
)


def _extract_json_object(text: str) -> dict[str, Any]:
    payload = (text or "").strip()
    if payload.startswith("```"):
        payload = payload.strip("`")
        if payload.lower().startswith("json"):
            payload = payload[4:].strip()

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        start = payload.find("{")
        end = payload.rfind("}")
        if start >= 0 and end > start:
            return json.loads(payload[start : end + 1])
        raise


def _fallback_handoff(goal: str, context: str, constraints: str, target: str, mode: str) -> dict[str, Any]:
    handoff: dict[str, Any] = {
        "one_sentence_goal": goal,
        "problem_statement": "Need an execution-ready implementation brief with explicit scope and acceptance criteria.",
        "objective": [
            "Deliver an MVP implementation plan with no ambiguity",
            f"Produce copy/paste prompt for {target}",
            "Define acceptance criteria that can be validated quickly",
        ],
        "scope_in": [
            "Single focused MVP delivery",
            "Explicit section/component requirements",
            "Validation checklist",
        ],
        "scope_out": [
            "Unrequested extra pages/features",
            "Backend architecture changes unless explicitly requested",
            "Non-essential design polish",
        ],
        "functional_requirements": [
            f"Use goal as primary deliverable: {goal}",
            f"Incorporate context: {context or 'N/A'}",
            f"Enforce constraints: {constraints or 'N/A'}",
        ],
        "acceptance_criteria": [
            "All required deliverables are present",
            "No out-of-scope features included",
            "Output can be pasted directly into the target tool",
        ],
    }

    if mode in {"build", "both"}:
        handoff["build_prompt"] = (
            "Build this exactly as specified.\\n\\n"
            f"Target tool: {target}\\n"
            f"Goal: {goal}\\n"
            f"Context: {context or 'N/A'}\\n"
            f"Constraints: {constraints or 'N/A'}\\n\\n"
            "Do NOT implement anything outside the requested MVP scope.\\n"
            "Return changed files and validation results."
        )
        handoff["lovable_build_prompt"] = handoff["build_prompt"]

    if mode in {"verify", "both"}:
        handoff["verification_prompt"] = (
            "Verify this implementation against the acceptance criteria.\\n"
            "Return pass/fail per criterion and concrete evidence."
        )

    handoff["qa_test_prompt"] = (
        "Validate implementation against acceptance criteria.\\n"
        "Report pass/fail per criterion and list any missing requirements."
    )

    return handoff


def _build_messages(goal: str, context: str, constraints: str, target: str, mode: str) -> list[dict[str, str]]:
    user_prompt = f"""
Create a {target}-ready handoff in strict JSON.

Intent mode:
{mode}

Goal:
{goal}

Context:
{context}

Constraints:
{constraints}

Return exactly this JSON shape:
{{
  "one_sentence_goal": "...",
  "problem_statement": "...",
  "objective": ["..."],
  "scope_in": ["..."],
  "scope_out": ["..."],
  "functional_requirements": ["..."],
  "acceptance_criteria": ["..."],
    "build_prompt": "copy/paste build prompt",
    "verification_prompt": "copy/paste verification prompt",
  "qa_test_prompt": "copy/paste QA prompt"
}}

Rules:
- Be concrete and implementation-ready.
- Keep it MVP-focused.
- No placeholders like TBD.
- Include explicit "Do NOT implement" constraints in build_prompt.
- If mode=build, focus on build prompt quality.
- If mode=verify, focus on verification prompt quality.
- If mode=both, include both build_prompt and verification_prompt.
""".strip()

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else default


def run_wizard() -> dict[str, Any]:
    print("\nCognOS Planning Wizard — answer the questions below.\n")

    target = _ask("Target tool/platform", "Lovable")
    mode = _ask("Intent (build / verify / both)", "both").lower()
    if mode not in {"build", "verify", "both"}:
        mode = "both"

    build_goal = _ask("What do you want to build", "Single-page product landing page")
    audience = _ask("Target audience", "Developers and CTOs")
    verification_focus = _ask(
        "What should be verified (e.g. traceability, trust evidence, compliance)",
        "Traceability and audit-ready trust evidence",
    )
    must_have = _ask("Must-have requirements (comma-separated)", "Clear CTA to GitHub, exact scope in/out, acceptance criteria")
    must_not_have = _ask("Must-NOT-have items (comma-separated)", "Extra pages, backend changes, unnecessary features")
    tech_constraints = _ask("Technical constraints", "One page only, no backend")
    success_definition = _ask("How do you define success", "Deliverable is copy/paste-ready for Lovable and testable")
    deadline = _ask("Deadline (optional)", "")

    goal = f"Build/Verify: {build_goal}"
    context = (
        f"Audience: {audience}. "
        f"Verification focus: {verification_focus}. "
        f"Success definition: {success_definition}."
    )
    constraints = (
        f"Must have: {must_have}. "
        f"Must not have: {must_not_have}. "
        f"Technical constraints: {tech_constraints}."
    )
    if deadline:
        constraints = f"{constraints} Deadline: {deadline}."

    return {
        "goal": goal,
        "context": context,
        "constraints": constraints,
        "target": target,
        "mode": mode,
        "answers": {
            "target": target,
            "mode": mode,
            "build_goal": build_goal,
            "audience": audience,
            "verification_focus": verification_focus,
            "must_have": must_have,
            "must_not_have": must_not_have,
            "tech_constraints": tech_constraints,
            "success_definition": success_definition,
            "deadline": deadline,
        },
    }


def generate_lovable_handoff(
    goal: str,
    context: str = "",
    constraints: str = "",
    target: str = "Lovable",
    mode: str = "both",
    *,
    base_url: str,
    api_key: str,
    model: str = "openai:gpt-4o-mini",
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    headers = {"content-type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key

    payload = {
        "model": model,
        "messages": _build_messages(goal, context, constraints, target=target, mode=mode),
        "cognos": {"mode": "monitor"},
    }

    body: dict[str, Any]
    response_headers: dict[str, Any]

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(f"{base_url.rstrip('/')}/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
        body = response.json()
        response_headers = dict(response.headers)
    except httpx.HTTPError:
        from fastapi.testclient import TestClient

        os.environ.setdefault("COGNOS_MOCK_UPSTREAM", "true")
        from main import app

        with TestClient(app) as client:
            response = client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            body = response.json()
            response_headers = dict(response.headers)
    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )

    try:
        parsed = _extract_json_object(content)
    except Exception:
        parsed = _fallback_handoff(goal=goal, context=context, constraints=constraints, target=target, mode=mode)

    if "build_prompt" in parsed and "lovable_build_prompt" not in parsed:
        parsed["lovable_build_prompt"] = parsed["build_prompt"]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": response_headers.get("X-Cognos-Trace-Id") or body.get("cognos", {}).get("trace_id"),
        "decision": response_headers.get("X-Cognos-Decision") or body.get("cognos", {}).get("decision"),
        "trust_score": response_headers.get("X-Cognos-Trust-Score"),
        "model": model,
        "target": target,
        "intent_mode": mode,
        "handoff": parsed,
        "raw_completion": content,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate tool-ready build/verification handoff via CognOS.")
    parser.add_argument("--goal", default="", help="One-sentence build goal.")
    parser.add_argument("--context", default="", help="Additional context for the build.")
    parser.add_argument("--constraints", default="", help="Constraints or non-goals.")
    parser.add_argument("--target", default="Lovable", help="Target tool/platform for the handoff.")
    parser.add_argument("--mode", choices=["build", "verify", "both"], default="both", help="Handoff intent mode.")
    parser.add_argument("--wizard", action="store_true", help="Interactive mode: ask guided questions first.")
    parser.add_argument("--model", default=os.getenv("COGNOS_LOVABLE_MODEL", "openai:gpt-4o-mini"))
    parser.add_argument("--base-url", default=os.getenv("COGNOS_BASE_URL", "http://127.0.0.1:8788"))
    parser.add_argument("--api-key", default=os.getenv("COGNOS_API_KEY", ""))
    parser.add_argument("--out", default="", help="Optional output JSON file path.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    wizard_answers: dict[str, Any] = {}

    if args.wizard:
        wizard_payload = run_wizard()
        goal = wizard_payload["goal"]
        context = wizard_payload["context"]
        constraints = wizard_payload["constraints"]
        target = wizard_payload["target"]
        mode = wizard_payload["mode"]
        wizard_answers = wizard_payload["answers"]
    else:
        goal = args.goal.strip()
        context = args.context
        constraints = args.constraints
        target = args.target
        mode = args.mode

    if not goal:
        raise SystemExit("Missing --goal. Use --goal \"...\" or run with --wizard.")

    result = generate_lovable_handoff(
        goal=goal,
        context=context,
        constraints=constraints,
        target=target,
        mode=mode,
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
    )

    if wizard_answers:
        result["questionnaire_answers"] = wizard_answers

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(f"WROTE={out_path}")

    print(payload)


if __name__ == "__main__":
    main()
