from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = os.getenv("COGNOS_TRACE_DB", "data/traces.sqlite3")


def _resolve_db_path() -> Path:
    db_path = Path(DEFAULT_DB_PATH)
    if not db_path.is_absolute():
        project_root = Path(__file__).resolve().parents[1]
        db_path = project_root / db_path
    return db_path


def init_db() -> None:
    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                decision TEXT NOT NULL,
                policy TEXT NOT NULL,
                trust_score REAL NOT NULL,
                risk REAL NOT NULL,
                is_stream INTEGER NOT NULL,
                status_code INTEGER NOT NULL,
                model TEXT,
                request_fingerprint TEXT,
                envelope_json TEXT,
                metadata_json TEXT
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def save_trace(record: dict[str, Any]) -> None:
    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    envelope_json = json.dumps(record.get("envelope", {}), ensure_ascii=False)
    metadata_json = json.dumps(record.get("metadata", {}), ensure_ascii=False)

    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            INSERT OR REPLACE INTO traces (
                trace_id,
                created_at,
                decision,
                policy,
                trust_score,
                risk,
                is_stream,
                status_code,
                model,
                request_fingerprint,
                envelope_json,
                metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["trace_id"],
                record["created_at"],
                record["decision"],
                record["policy"],
                float(record.get("trust_score", 0.0)),
                float(record.get("risk", 0.0)),
                int(bool(record.get("is_stream", False))),
                int(record.get("status_code", 200)),
                record.get("model"),
                record.get("request_fingerprint"),
                envelope_json,
                metadata_json,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_trace(trace_id: str) -> dict[str, Any] | None:
    db_path = _resolve_db_path()
    if not db_path.exists():
        return None

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.execute("SELECT * FROM traces WHERE trace_id = ?", (trace_id,))
        row = cursor.fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    envelope = json.loads(row["envelope_json"]) if row["envelope_json"] else {}
    metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}

    return {
        "trace_id": row["trace_id"],
        "created_at": row["created_at"],
        "decision": row["decision"],
        "policy": row["policy"],
        "trust_score": row["trust_score"],
        "risk": row["risk"],
        "is_stream": bool(row["is_stream"]),
        "status_code": row["status_code"],
        "model": row["model"],
        "request_fingerprint": row["request_fingerprint"],
        "envelope": envelope,
        "metadata": metadata,
    }


def aggregate_tvv() -> dict[str, int]:
    db_path = _resolve_db_path()
    if not db_path.exists():
        return {"tvv_requests": 0, "tvv_tokens": 0}

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute("SELECT metadata_json FROM traces").fetchall()
    finally:
        connection.close()

    tvv_requests = len(rows)
    tvv_tokens = 0

    for row in rows:
        metadata_raw = row["metadata_json"]
        if not metadata_raw:
            continue
        try:
            metadata = json.loads(metadata_raw)
        except Exception:
            continue

        usage = metadata.get("usage", {}) if isinstance(metadata, dict) else {}
        if isinstance(usage, dict):
            total_tokens = usage.get("total_tokens", 0)
            if isinstance(total_tokens, int):
                tvv_tokens += total_tokens

    return {"tvv_requests": tvv_requests, "tvv_tokens": tvv_tokens}
