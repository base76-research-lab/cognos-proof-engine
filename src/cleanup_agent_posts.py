from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_POSTS_DIR = PROJECT_ROOT / "ops" / "content" / "agent_posts"


def list_capture_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    files = [path for path in directory.glob("agent_post_*.json") if path.is_file()]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return files


def cleanup(directory: Path, keep: int, dry_run: bool) -> tuple[int, list[Path]]:
    files = list_capture_files(directory)
    to_delete = files[keep:] if keep < len(files) else []

    if not dry_run:
        for file_path in to_delete:
            file_path.unlink(missing_ok=True)

    return len(files), to_delete


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean up old captured agent social posts")
    parser.add_argument("--keep", type=int, default=100, help="How many newest files to keep (default: 100)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()

    if args.keep < 0:
        raise SystemExit("--keep must be >= 0")

    total, to_delete = cleanup(AGENT_POSTS_DIR, keep=args.keep, dry_run=args.dry_run)

    print(f"Directory: {AGENT_POSTS_DIR}")
    print(f"Total files: {total}")
    print(f"Keep newest: {args.keep}")

    if not to_delete:
        print("Nothing to delete.")
        return

    action = "Would delete" if args.dry_run else "Deleted"
    print(f"{action}: {len(to_delete)} files")
    for file_path in to_delete[:20]:
        print(f"- {file_path.name}")

    if len(to_delete) > 20:
        print(f"... and {len(to_delete) - 20} more")


if __name__ == "__main__":
    main()
