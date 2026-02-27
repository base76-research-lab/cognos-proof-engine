from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cmd(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        detail = "\n".join(part for part in [stdout, stderr] if part)
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{detail}")
    return result


def has_staged_changes() -> bool:
    result = run_cmd(["git", "diff", "--cached", "--quiet"], check=False)
    return result.returncode == 1


def detect_current_branch() -> str:
    result = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return (result.stdout or "main").strip() or "main"


def main() -> None:
    parser = argparse.ArgumentParser(description="CognOS Proof Engine autopilot: generate content + commit + push")
    parser.add_argument(
        "--channel",
        choices=["linkedin", "x", "all"],
        default="linkedin",
        help="Manual post generator channel (default: linkedin)",
    )
    parser.add_argument("--keep", type=int, default=100, help="How many newest agent capture files to keep")
    parser.add_argument("--no-push", action="store_true", help="Run git commit but skip push")
    parser.add_argument("--no-git", action="store_true", help="Run generation/cleanup only")
    parser.add_argument("--commit-message", default="", help="Custom git commit message")
    args = parser.parse_args()

    print("[1/5] Generating social content payload...")
    outbox_result = run_cmd(["python3", "src/social_content_pipeline.py"])
    if outbox_result.stdout.strip():
        print(outbox_result.stdout.strip())

    print("[2/5] Generating manual post markdown...")
    manual_result = run_cmd(["python3", "src/manual_post_generator.py", "--channel", args.channel])
    if manual_result.stdout.strip():
        print(manual_result.stdout.strip())

    print(f"[3/5] Cleaning old capture files (keep={args.keep})...")
    cleanup_result = run_cmd(["python3", "src/cleanup_agent_posts.py", "--keep", str(args.keep)])
    if cleanup_result.stdout.strip():
        print(cleanup_result.stdout.strip())

    if args.no_git:
        print("[4/5] Git step skipped (--no-git).")
        print("[5/5] Done.")
        return

    print("[4/5] Staging and committing changes...")
    run_cmd(["git", "add", "-A"])

    if not has_staged_changes():
        print("No staged changes. Skipping commit/push.")
        print("[5/5] Done.")
        return

    commit_message = args.commit_message.strip() or f"chore: proof engine autopilot {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M:%SZ')}"
    run_cmd(["git", "commit", "-m", commit_message])
    print(f"Committed: {commit_message}")

    if args.no_push:
        print("[5/5] Push skipped (--no-push).")
        return

    branch = detect_current_branch()
    print(f"[5/5] Pushing to origin/{branch}...")
    run_cmd(["git", "push", "origin", branch])
    print("Autopilot complete: changes pushed.")


if __name__ == "__main__":
    main()
