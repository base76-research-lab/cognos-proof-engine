from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = PROJECT_ROOT / "ops" / "agents" / "state.json"
BACKLOG_FILE = PROJECT_ROOT / "ops" / "agents" / "backlog.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "ops" / "research"

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def summarize(backlog: dict[str, Any]) -> dict[str, Any]:
    tasks = backlog.get("tasks", [])
    todo = [task for task in tasks if task.get("status") == "todo"]
    in_progress = [task for task in tasks if task.get("status") == "in_progress"]
    done = [task for task in tasks if task.get("status") == "done"]
    return {
        "todo": todo,
        "in_progress": in_progress,
        "done": done,
        "all": tasks,
    }


def rank_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        tasks,
        key=lambda task: (
            PRIORITY_ORDER.get(str(task.get("priority", "P3")), 9),
            str(task.get("id", "")),
        ),
    )


def to_markdown(state: dict[str, Any], backlog: dict[str, Any], top_n: int) -> str:
    summary = summarize(backlog)
    snapshot = state.get("north_star_snapshot", {})
    cycle = state.get("cycle", {})

    next_candidates = rank_tasks(summary["todo"] + summary["in_progress"])[: max(top_n, 1)]
    done_recent = rank_tasks(summary["done"])[-3:]

    lines: list[str] = []
    lines.append("# CognOS Proof Engine — Manual Research Brief")
    lines.append("")
    lines.append(f"Generated: {dt.datetime.now(dt.UTC).isoformat()}")
    lines.append("")

    lines.append("## Current Snapshot")
    lines.append(f"- Day: {cycle.get('current_day', 'n/a')}")
    lines.append(f"- Phase: {cycle.get('phase', 'n/a')}")
    lines.append(f"- Mode: {cycle.get('mode', 'n/a')}")
    lines.append(f"- TVV requests: {snapshot.get('tvv_requests', 0)}")
    lines.append(f"- TVV tokens: {snapshot.get('tvv_tokens', 0)}")
    lines.append(f"- External integrations: {snapshot.get('external_active_integrations', 0)}")
    lines.append("")

    lines.append("## Research Signals")
    lines.append(f"- Total tasks: {len(summary['all'])}")
    lines.append(f"- Done: {len(summary['done'])}")
    lines.append(f"- In progress: {len(summary['in_progress'])}")
    lines.append(f"- Todo: {len(summary['todo'])}")
    lines.append("")

    lines.append("## Execution Plan (No Agents)")
    if not next_candidates:
        lines.append("- No open execution items found.")
    else:
        for idx, task in enumerate(next_candidates, start=1):
            task_id = task.get("id", "n/a")
            title = task.get("title", "Untitled")
            owner = task.get("owner", "unassigned")
            priority = task.get("priority", "P3")
            status = task.get("status", "todo")
            lines.append(f"{idx}. [{task_id}] {title}")
            lines.append(f"   - Priority: {priority} | Status: {status} | Suggested owner: {owner}")
            dod = task.get("definition_of_done", [])
            if dod:
                lines.append("   - Definition of done:")
                for criterion in dod:
                    lines.append(f"     - {criterion}")
    lines.append("")

    lines.append("## Recent Completed Work")
    if not done_recent:
        lines.append("- No completed tasks yet.")
    else:
        for task in done_recent:
            task_id = task.get("id", "n/a")
            title = task.get("title", "Untitled")
            notes = task.get("completion_notes", "No completion notes")
            lines.append(f"- [{task_id}] {title}")
            lines.append(f"  - Outcome: {notes}")
    lines.append("")

    lines.append("## Suggested Human Workflow")
    lines.append("1. Pick item #1 from Execution Plan and define a 60-90 minute work block.")
    lines.append("2. Execute and validate against its definition of done.")
    lines.append("3. Capture outcome notes and update backlog/state files manually.")
    lines.append("4. Regenerate this brief and continue with the next item.")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_output(markdown: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"research_execution_plan_{stamp}.md"
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a manual research brief and execution plan without agent/autopilot operations"
    )
    parser.add_argument("--top", type=int, default=3, help="Number of prioritized execution items to include")
    parser.add_argument("--stdout", action="store_true", help="Print markdown to stdout instead of writing file")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated markdown plan",
    )
    args = parser.parse_args()

    state = load_json(STATE_FILE)
    backlog = load_json(BACKLOG_FILE)
    markdown = to_markdown(state, backlog, top_n=args.top)

    if args.stdout:
        print(markdown)
        return

    out_path = write_output(markdown, Path(args.output_dir))
    print(f"Manual research plan generated: {out_path}")


if __name__ == "__main__":
    main()
