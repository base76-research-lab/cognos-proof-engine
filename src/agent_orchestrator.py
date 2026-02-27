from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trace_store import aggregate_tvv

ROOT = Path(__file__).resolve().parents[1]
AGENTS_FILE = ROOT / "ops" / "agents" / "agents.json"
BACKLOG_FILE = ROOT / "ops" / "agents" / "backlog.json"
STATE_FILE = ROOT / "ops" / "agents" / "state.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def pick_next_task(backlog: dict[str, Any], agent_id: str | None) -> dict[str, Any] | None:
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    tasks = [task for task in backlog.get("tasks", []) if task.get("status") in {"todo", "in_progress"}]

    if agent_id:
        tasks = [task for task in tasks if task.get("owner") == agent_id]

    tasks.sort(key=lambda task: (priority_order.get(task.get("priority", "P3"), 9), task.get("id", "")))
    return tasks[0] if tasks else None


def cmd_status() -> None:
    state = load_json(STATE_FILE)
    backlog = load_json(BACKLOG_FILE)

    todo = sum(1 for task in backlog.get("tasks", []) if task.get("status") == "todo")
    in_progress = sum(1 for task in backlog.get("tasks", []) if task.get("status") == "in_progress")
    done = sum(1 for task in backlog.get("tasks", []) if task.get("status") == "done")

    print("=== Operational Cognos Agent Status ===")
    print(f"Day: {state['cycle']['current_day']} | Phase: {state['cycle']['phase']} | Mode: {state['cycle']['mode']}")
    print(
        f"TVV requests: {state['north_star_snapshot']['tvv_requests']} | "
        f"TVV tokens: {state['north_star_snapshot']['tvv_tokens']} | "
        f"External integrations: {state['north_star_snapshot']['external_active_integrations']}"
    )
    print(f"Tasks -> todo: {todo}, in_progress: {in_progress}, done: {done}")


def cmd_next(agent_id: str | None) -> None:
    backlog = load_json(BACKLOG_FILE)
    task = pick_next_task(backlog, agent_id)

    if not task:
        print("No task available for selection.")
        return

    print("=== Next Task ===")
    print(f"ID: {task['id']}")
    print(f"Title: {task['title']}")
    print(f"Owner: {task['owner']}")
    print(f"Priority: {task['priority']}")
    print(f"Status: {task['status']}")
    print(f"Tags: {', '.join(task.get('tags', []))}")
    print("Definition of Done:")
    for line in task.get("definition_of_done", []):
        print(f"- {line}")


def cmd_start(task_id: str) -> None:
    backlog = load_json(BACKLOG_FILE)

    for task in backlog.get("tasks", []):
        if task.get("id") == task_id:
            task["status"] = "in_progress"
            save_json(BACKLOG_FILE, backlog)
            print(f"Task {task_id} marked as in_progress.")
            return

    print(f"Task {task_id} not found.")


def cmd_complete(task_id: str, notes: str | None) -> None:
    backlog = load_json(BACKLOG_FILE)
    state = load_json(STATE_FILE)

    for task in backlog.get("tasks", []):
        if task.get("id") == task_id:
            task["status"] = "done"
            if notes:
                task["completion_notes"] = notes
            save_json(BACKLOG_FILE, backlog)
            state["last_update"] = datetime.now(timezone.utc).isoformat()
            save_json(STATE_FILE, state)
            print(f"Task {task_id} marked as done.")
            return

    print(f"Task {task_id} not found.")


def cmd_update_metrics(tvv_requests: int | None, tvv_tokens: int | None, external_integrations: int | None, enforce_share: float | None) -> None:
    state = load_json(STATE_FILE)
    snapshot = state["north_star_snapshot"]

    if tvv_requests is not None:
        snapshot["tvv_requests"] = tvv_requests
    if tvv_tokens is not None:
        snapshot["tvv_tokens"] = tvv_tokens
    if external_integrations is not None:
        snapshot["external_active_integrations"] = external_integrations
    if enforce_share is not None:
        snapshot["enforce_share"] = enforce_share

    state["last_update"] = datetime.now(timezone.utc).isoformat()
    save_json(STATE_FILE, state)
    print("North star metrics updated.")


def cmd_sync_tvv() -> None:
    state = load_json(STATE_FILE)
    snapshot = state["north_star_snapshot"]
    aggregate = aggregate_tvv()

    snapshot["tvv_requests"] = int(aggregate.get("tvv_requests", 0))
    snapshot["tvv_tokens"] = int(aggregate.get("tvv_tokens", 0))

    state["last_update"] = datetime.now(timezone.utc).isoformat()
    save_json(STATE_FILE, state)

    print(
        "TVV synced from trace-db: "
        f"requests={snapshot['tvv_requests']}, tokens={snapshot['tvv_tokens']}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operational Cognos agent orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show current state and task summary")

    next_parser = subparsers.add_parser("next", help="Show next prioritized task")
    next_parser.add_argument("--agent", dest="agent_id", default=None, help="Filter next task by owner agent id")

    start_parser = subparsers.add_parser("start", help="Mark task as in progress")
    start_parser.add_argument("--id", dest="task_id", required=True, help="Task id")

    complete_parser = subparsers.add_parser("complete", help="Mark task as done")
    complete_parser.add_argument("--id", dest="task_id", required=True, help="Task id")
    complete_parser.add_argument("--notes", dest="notes", default=None, help="Completion notes")

    metrics_parser = subparsers.add_parser("metrics", help="Update north star metrics")
    metrics_parser.add_argument("--tvv-requests", dest="tvv_requests", type=int)
    metrics_parser.add_argument("--tvv-tokens", dest="tvv_tokens", type=int)
    metrics_parser.add_argument("--external-integrations", dest="external_integrations", type=int)
    metrics_parser.add_argument("--enforce-share", dest="enforce_share", type=float)

    subparsers.add_parser("sync-tvv", help="Sync TVV metrics from trace database")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "next":
        cmd_next(agent_id=args.agent_id)
    elif args.command == "start":
        cmd_start(task_id=args.task_id)
    elif args.command == "complete":
        cmd_complete(task_id=args.task_id, notes=args.notes)
    elif args.command == "metrics":
        cmd_update_metrics(
            tvv_requests=args.tvv_requests,
            tvv_tokens=args.tvv_tokens,
            external_integrations=args.external_integrations,
            enforce_share=args.enforce_share,
        )
    elif args.command == "sync-tvv":
        cmd_sync_tvv()


if __name__ == "__main__":
    main()
