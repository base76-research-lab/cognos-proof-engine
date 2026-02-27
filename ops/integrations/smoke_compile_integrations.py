from __future__ import annotations

import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INTEGRATIONS = ROOT / "ops" / "integrations"


def main() -> None:
    files = sorted(INTEGRATIONS.rglob("*.py"))
    if not files:
        raise SystemExit("No integration python files found")

    for file_path in files:
        py_compile.compile(str(file_path), doraise=True)

    print(f"Smoke OK: compiled {len(files)} integration modules")


if __name__ == "__main__":
    main()
