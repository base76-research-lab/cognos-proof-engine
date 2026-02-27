from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def run_print(cmd: list[str], cwd: Path, check: bool = True) -> None:
    try:
        result = run(cmd, cwd=cwd, check=check)
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout.strip())
        if error.stderr:
            print(error.stderr.strip())
        raise

    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())


def ensure_gh_auth(cwd: Path) -> None:
    run_print(["gh", "auth", "status", "-h", "github.com"], cwd=cwd)


def ensure_git_identity(cwd: Path) -> None:
    user_name = run(["git", "config", "user.name"], cwd=cwd, check=False).stdout.strip()
    user_email = run(["git", "config", "user.email"], cwd=cwd, check=False).stdout.strip()

    if user_name and user_email:
        return

    gh_login = run(["gh", "api", "user", "-q", ".login"], cwd=cwd).stdout.strip()
    if not gh_login:
        raise SystemExit("Kunde inte läsa GitHub-användare via gh api user")

    if not user_name:
        run_print(["git", "config", "user.name", gh_login], cwd=cwd)

    if not user_email:
        noreply = f"{gh_login}@users.noreply.github.com"
        run_print(["git", "config", "user.email", noreply], cwd=cwd)


def ensure_git_repo(cwd: Path, branch: str) -> None:
    git_dir = cwd / ".git"
    if not git_dir.exists():
        run_print(["git", "init", "-b", branch], cwd=cwd)


def ensure_branch(cwd: Path, branch: str) -> None:
    result = run(["git", "branch", "--show-current"], cwd=cwd)
    current = result.stdout.strip()
    if not current:
        run_print(["git", "checkout", "-b", branch], cwd=cwd)
        return
    if current != branch:
        run_print(["git", "checkout", "-B", branch], cwd=cwd)


def ensure_remote(cwd: Path, owner: str, repo: str, visibility: str, branch: str) -> str:
    remote_url = f"https://github.com/{owner}/{repo}.git"

    remotes = run(["git", "remote"], cwd=cwd).stdout.split()
    if "origin" in remotes:
        return remote_url

    repo_exists = run(["gh", "repo", "view", f"{owner}/{repo}"], cwd=cwd, check=False)
    if repo_exists.returncode == 0:
        run_print(["git", "remote", "add", "origin", remote_url], cwd=cwd)
        return remote_url

    create_cmd = [
        "gh",
        "repo",
        "create",
        f"{owner}/{repo}",
        "--source",
        ".",
        "--remote",
        "origin",
        "--disable-issues",
    ]

    if visibility == "public":
        create_cmd.append("--public")
    else:
        create_cmd.append("--private")

    run_print(create_cmd, cwd=cwd)

    return remote_url


def ensure_commit(cwd: Path, message: str) -> None:
    run_print(["git", "add", "-A"], cwd=cwd)

    status = run(["git", "status", "--porcelain"], cwd=cwd).stdout.strip()
    has_commit = run(["git", "rev-parse", "--verify", "HEAD"], cwd=cwd, check=False).returncode == 0

    if status or not has_commit:
        run_print(["git", "commit", "-m", message], cwd=cwd)


def push(cwd: Path, branch: str) -> None:
    run_print(["git", "push", "-u", "origin", branch], cwd=cwd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autonom GitHub repo bootstrap + push for Operational Cognos")

    parser.add_argument("--source", default=".", help="Path to project directory")
    parser.add_argument("--owner", default="base76-research-lab", help="GitHub owner/org")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--visibility", choices=["private", "public"], default="private")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--message", default=None, help="Commit message")
    parser.add_argument("--no-push", action="store_true", help="Skip push step")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cwd = Path(args.source).resolve()

    if not cwd.exists() or not cwd.is_dir():
        raise SystemExit(f"Invalid source directory: {cwd}")

    commit_message = args.message or f"chore: agent autopush {dt.datetime.now(dt.UTC).isoformat()}"

    ensure_gh_auth(cwd)
    ensure_git_repo(cwd, branch=args.branch)
    ensure_branch(cwd, branch=args.branch)
    ensure_git_identity(cwd)
    remote_url = ensure_remote(cwd, owner=args.owner, repo=args.repo, visibility=args.visibility, branch=args.branch)
    ensure_commit(cwd, message=commit_message)

    if not args.no_push:
        push(cwd, branch=args.branch)

    print(f"Autopilot complete: {remote_url}")


if __name__ == "__main__":
    main()
