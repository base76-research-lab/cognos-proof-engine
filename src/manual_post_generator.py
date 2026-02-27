from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "ops" / "content" / "manual_posts"


def generate_payload() -> dict:
    raw = subprocess.check_output(
        ["python3", "src/social_content_pipeline.py", "--stdout"],
        cwd=str(PROJECT_ROOT),
        text=True,
    )
    return json.loads(raw)


def build_markdown(payload: dict, include_linkedin: bool, include_x: bool) -> str:
    generated_at = payload.get("generated_at", dt.datetime.now(dt.UTC).isoformat())
    metrics = payload.get("metrics", {})
    profile_urls = payload.get("meta", {}).get("profile_urls", {})

    lines: list[str] = []
    lines.append("# Operational Cognos — Manual Post Batch")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")
    lines.append("## Snapshot")
    lines.append(f"- TVV requests: {metrics.get('tvv_requests', 0)}")
    lines.append(f"- TVV tokens: {metrics.get('tvv_tokens', 0)}")
    lines.append(f"- External integrations: {metrics.get('external_integrations', 0)}")
    lines.append("")

    if include_linkedin:
        lines.append("## LinkedIn (copy/paste)")
        if profile_urls.get("linkedin"):
            lines.append(f"Profile: {profile_urls['linkedin']}")
            lines.append("")
        lines.append(payload.get("posts", {}).get("linkedin", ""))
        lines.append("")

    if include_x:
        lines.append("## X (copy/paste)")
        if profile_urls.get("x"):
            lines.append(f"Profile: {profile_urls['x']}")
            lines.append("")
        lines.append(payload.get("posts", {}).get("x", ""))
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def save_markdown(content: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = OUT_DIR / f"manual_post_{timestamp}.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate manual social post content from Operational Cognos progress")
    parser.add_argument(
        "--channel",
        choices=["linkedin", "x", "all"],
        default="all",
        help="Which channel content to include",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print generated markdown to stdout",
    )
    args = parser.parse_args()

    payload = generate_payload()
    include_linkedin = args.channel in {"linkedin", "all"}
    include_x = args.channel in {"x", "all"}

    markdown = build_markdown(payload, include_linkedin=include_linkedin, include_x=include_x)

    if args.stdout:
        print(markdown)
        return

    output_path = save_markdown(markdown)
    print(f"Manual post batch generated: {output_path}")


if __name__ == "__main__":
    main()
