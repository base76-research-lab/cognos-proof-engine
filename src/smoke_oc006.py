from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

TEST_DB = Path("/tmp/operational-cognos-oc006.sqlite3")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ.setdefault("COGNOS_MOCK_UPSTREAM", "true")
os.environ["COGNOS_TRACE_DB"] = str(TEST_DB)
os.environ["COGNOS_GATEWAY_API_KEY"] = "test-gateway-key"

from main import app


def run_smoke() -> None:
    with TestClient(app) as client:
        for index in range(3):
            response = client.post(
                "/v1/chat/completions",
                headers={"x-api-key": "test-gateway-key"},
                json={
                    "model": "openai:gpt-4.1-mini",
                    "messages": [{"role": "user", "content": f"TVV sample {index}"}],
                },
            )
            if response.status_code != 200:
                raise SystemExit(f"Failed to seed trace data: {response.status_code}")

    env = dict(os.environ)
    project_root = Path(__file__).resolve().parents[1]

    sync_cmd = ["python3", "src/agent_orchestrator.py", "sync-tvv"]
    sync_result = subprocess.run(sync_cmd, cwd=project_root, env=env, capture_output=True, text=True)
    if sync_result.returncode != 0:
        raise SystemExit(f"sync-tvv failed: {sync_result.stderr}")

    status_cmd = ["python3", "src/agent_orchestrator.py", "status"]
    status_result = subprocess.run(status_cmd, cwd=project_root, env=env, capture_output=True, text=True)
    if status_result.returncode != 0:
        raise SystemExit(f"status failed: {status_result.stderr}")

    output = status_result.stdout
    if "TVV requests: 3" not in output:
        raise SystemExit(f"Unexpected TVV requests output:\n{output}")

    if "TVV tokens: 42" not in output:
        raise SystemExit(f"Unexpected TVV tokens output:\n{output}")

    print("Smoke OK: sync-tvv updates state from trace-db (requests=3, tokens=42)")


if __name__ == "__main__":
    run_smoke()
