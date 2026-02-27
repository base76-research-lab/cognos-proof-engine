from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
import webbrowser

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_generated_payload() -> dict:
    raw = subprocess.check_output(
        ["python3", "src/social_content_pipeline.py", "--stdout"],
        cwd=str(PROJECT_ROOT),
        text=True,
    )
    return json.loads(raw)


def build_compose_urls(payload: dict) -> dict[str, str]:
    linkedin_text = payload.get("posts", {}).get("linkedin", "")
    x_text = payload.get("posts", {}).get("x", "")

    linkedin_url = "https://www.linkedin.com/feed/?shareActive=true&text=" + quote(linkedin_text)
    x_url = "https://x.com/intent/tweet?text=" + quote(x_text)

    return {
        "linkedin": linkedin_url,
        "x": x_url,
    }


def auto_click_linkedin_post(linkedin_page) -> bool:
    selectors = [
        ("role", re.compile(r"^(Post|Publicera|Publicera nu|Posta)$", re.IGNORECASE)),
        ("css", "button.share-actions__primary-action"),
        ("css", "button[data-control-name='share.post']"),
    ]

    for selector_type, selector_value in selectors:
        try:
            if selector_type == "role":
                button = linkedin_page.get_by_role("button", name=selector_value).first
            else:
                button = linkedin_page.locator(selector_value).first

            if button.is_visible(timeout=2000) and button.is_enabled(timeout=2000):
                button.click(timeout=3000)
                return True
        except Exception:
            continue
    return False


def run_browser_assist(
    compose_urls: dict[str, str],
    auto_linkedin_click: bool,
    arm_key: str,
    countdown_seconds: int,
    browser_channel: str,
    user_data_dir: str,
) -> None:
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel=browser_channel,
        )

        linkedin_page = context.new_page()
        linkedin_page.goto(compose_urls["linkedin"], wait_until="domcontentloaded")

        x_page = context.new_page()
        x_page.goto(compose_urls["x"], wait_until="domcontentloaded")

        print("\nPlaywright assist active.")
        print("1) Log in manually in each tab if you are not already signed in")
        print("2) Verify the generated text")

        if auto_linkedin_click:
            if arm_key != "POST_NOW":
                print("\nAuto-click aborted: use --arm-key POST_NOW to arm publishing.")
            else:
                input("\nPress Enter when the LinkedIn tab is ready (signed in + text verified)...")
                print(f"Armed auto-click in {countdown_seconds}s...")
                time.sleep(max(countdown_seconds, 0))
                clicked = auto_click_linkedin_post(linkedin_page)
                if clicked:
                    print("LinkedIn: auto-click executed on publish button.")
                else:
                    print("LinkedIn: could not find active publish button, click manually.")
        else:
            print("3) Click Publish manually")

        input("\nPress Enter when you are done to close the browser...")

        context.close()


def open_in_default_browser(compose_urls: dict[str, str]) -> None:
    print("\nOpening compose URLs in the system default browser...")
    webbrowser.open(compose_urls["linkedin"])
    webbrowser.open(compose_urls["x"])
    print("Done. Sign in/publish manually in the opened tabs.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open LinkedIn/X compose pages with generated Operational Cognos content (human-in-the-loop)."
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print generated compose URLs without opening browser",
    )
    parser.add_argument(
        "--auto-linkedin-click",
        action="store_true",
        help="Attempt to auto-click LinkedIn publish button after manual login/review",
    )
    parser.add_argument(
        "--arm-key",
        default="",
        help="Safety arming key required for auto-click (must be POST_NOW)",
    )
    parser.add_argument(
        "--countdown-seconds",
        type=int,
        default=5,
        help="Countdown before auto-click when armed",
    )
    parser.add_argument(
        "--browser-channel",
        choices=["chrome", "msedge", "chromium"],
        default="chrome",
        help="Browser channel for Playwright session (default: chrome)",
    )
    parser.add_argument(
        "--user-data-dir",
        default=str(PROJECT_ROOT / ".playwright-profile"),
        help="Persistent browser profile directory for login sessions",
    )
    parser.add_argument(
        "--open-default-browser",
        action="store_true",
        help="Open compose URLs in system browser instead of Playwright",
    )
    args = parser.parse_args()

    payload = load_generated_payload()
    compose_urls = build_compose_urls(payload)

    print("Generated compose URLs:")
    print(f"- LinkedIn: {compose_urls['linkedin']}")
    print(f"- X: {compose_urls['x']}")

    if args.print_only:
        return

    if args.open_default_browser:
        open_in_default_browser(compose_urls)
        return

    try:
        run_browser_assist(
            compose_urls,
            auto_linkedin_click=args.auto_linkedin_click,
            arm_key=args.arm_key,
            countdown_seconds=args.countdown_seconds,
            browser_channel=args.browser_channel,
            user_data_dir=args.user_data_dir,
        )
    except Exception as exc:
        print("\nPlaywright session failed:", exc)
        print("Tip: run with --browser-channel chrome or --open-default-browser")


if __name__ == "__main__":
    main()
