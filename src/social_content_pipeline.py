from __future__ import annotations

import argparse
import datetime as dt
import json
import random
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = PROJECT_ROOT / "ops" / "agents" / "state.json"
BACKLOG_FILE = PROJECT_ROOT / "ops" / "agents" / "backlog.json"
OUTBOX_DIR = PROJECT_ROOT / "ops" / "content" / "outbox"
AGENT_POSTS_DIR = PROJECT_ROOT / "ops" / "content" / "agent_posts"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_done_highlights(backlog: dict[str, Any], limit: int = 3) -> list[str]:
    done_tasks = [task for task in backlog.get("tasks", []) if task.get("status") == "done"]
    done_tasks.sort(key=lambda task: task.get("id", ""), reverse=True)

    highlights: list[str] = []
    for task in done_tasks[:limit]:
        notes = task.get("completion_notes")
        if notes:
            highlights.append(f"{task.get('id')}: {notes}")
        else:
            highlights.append(f"{task.get('id')}: {task.get('title', 'completed task')}")
    return highlights


def build_post_payloads(state: dict[str, Any], backlog: dict[str, Any]) -> dict[str, Any]:
    snapshot = state.get("north_star_snapshot", {})
    tvv_requests = int(snapshot.get("tvv_requests", 0))
    tvv_tokens = int(snapshot.get("tvv_tokens", 0))
    external = int(snapshot.get("external_active_integrations", 0))

    highlights = get_done_highlights(backlog)
    highlights_text = "\n".join([f"- {item}" for item in highlights]) if highlights else "- Inga klara tasks ännu"

    headline_variants = [
        "CognOS build-log: från forskning till körbar trust-infrastruktur",
        "Veckologg från Operational Cognos: shippar trust-lager i produktionstempo",
        "CognOS execution update: konkret progression mot verifierbar AI-trust",
    ]
    headline = random.choice(headline_variants)

    linkedin = (
        f"{headline}\n\n"
        f"Status just nu:\n"
        f"- TVV requests: {tvv_requests}\n"
        f"- TVV tokens: {tvv_tokens}\n"
        f"- Externa integrationer: {external}\n\n"
        f"Senaste leveranser:\n{highlights_text}\n\n"
        "Nästa fokus: extern traction + enforce-usage i verklig trafik.\n"
        "#CognOS #AITrust #ReliabilityEngineering #AppliedAI"
    )

    x_post = (
        f"CognOS build-update 🚀\n"
        f"TVV req: {tvv_requests} | TVV tokens: {tvv_tokens} | external: {external}\n"
        f"Latest: {highlights[0] if highlights else 'build in progress'}\n"
        "Goal: trust-layer that scales like infrastructure, not consulting.\n"
        "#AI #LLM #CognOS"
    )

    now = dt.datetime.now(dt.UTC).isoformat()
    return {
        "generated_at": now,
        "metrics": {
            "tvv_requests": tvv_requests,
            "tvv_tokens": tvv_tokens,
            "external_integrations": external,
        },
        "highlights": highlights,
        "posts": {
            "linkedin": linkedin,
            "x": x_post,
        },
    }


def write_outbox(payload: dict[str, Any]) -> Path:
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUTBOX_DIR / f"post_batch_{timestamp}.json"
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return out_path


def write_agent_capture(payload: dict[str, Any]) -> Path:
    AGENT_POSTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = AGENT_POSTS_DIR / f"agent_post_{timestamp}.json"
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate recurring social content from agent progress")
    parser.add_argument("--stdout", action="store_true", help="Print JSON payload to stdout instead of writing outbox file")
    args = parser.parse_args()

    state = load_json(STATE_FILE)
    backlog = load_json(BACKLOG_FILE)
    payload = build_post_payloads(state, backlog)
    capture_path = write_agent_capture(payload)

    if args.stdout:
        print(json.dumps(payload, ensure_ascii=False))
        return

    out_path = write_outbox(payload)
    print(f"Content batch generated: {out_path}")
    print(f"Agent post captured: {capture_path}")


if __name__ == "__main__":
    main()
