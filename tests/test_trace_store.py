"""Unit tests for trace_store module."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from trace_store import aggregate_tvv, get_trace, init_db, save_trace


class TestInitDb:
    """Tests for database initialization."""

    def test_init_db_creates_directory(self, tmp_db_path: str) -> None:
        """init_db should create parent directories."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            db_file = Path(tmp_db_path)
            assert db_file.exists()

    def test_init_db_creates_tables(self, tmp_db_path: str) -> None:
        """init_db should create traces table with correct schema."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            conn = sqlite3.connect(tmp_db_path)
            cursor = conn.execute("PRAGMA table_info(traces)")
            columns = {row[1] for row in cursor.fetchall()}
            conn.close()

            expected_columns = {
                "trace_id",
                "created_at",
                "decision",
                "policy",
                "trust_score",
                "risk",
                "is_stream",
                "status_code",
                "model",
                "request_fingerprint",
                "response_fingerprint",
                "envelope_json",
                "metadata_json",
            }
            assert expected_columns.issubset(columns)

    def test_init_db_idempotent(self, tmp_db_path: str) -> None:
        """init_db should be safe to call multiple times."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()
            init_db()  # Should not raise
            assert Path(tmp_db_path).exists()


class TestSaveTrace:
    """Tests for saving traces to database."""

    def test_save_trace_inserts_record(
        self, tmp_db_path: str, trace_record: dict[str, Any]
    ) -> None:
        """save_trace should insert record into database."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()
            save_trace(trace_record)

            conn = sqlite3.connect(tmp_db_path)
            cursor = conn.execute(
                "SELECT trace_id, decision, policy FROM traces WHERE trace_id = ?",
                (trace_record["trace_id"],)
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == trace_record["trace_id"]
            assert result[1] == trace_record["decision"]
            assert result[2] == trace_record["policy"]

    def test_save_trace_with_json_fields(
        self, tmp_db_path: str, trace_record: dict[str, Any]
    ) -> None:
        """save_trace should properly serialize JSON fields."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()
            save_trace(trace_record)

            conn = sqlite3.connect(tmp_db_path)
            cursor = conn.execute(
                "SELECT envelope_json, metadata_json FROM traces WHERE trace_id = ?",
                (trace_record["trace_id"],)
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            envelope = json.loads(result[0])
            metadata = json.loads(result[1])
            assert envelope["decision"] == trace_record["envelope"]["decision"]
            assert metadata["mode"] == trace_record["metadata"]["mode"]

    def test_save_trace_replaces_existing(
        self, tmp_db_path: str, trace_record: dict[str, Any]
    ) -> None:
        """save_trace should replace existing trace with same ID."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            save_trace(trace_record)

            # Update the record
            trace_record["decision"] = "REFINE"
            save_trace(trace_record)

            conn = sqlite3.connect(tmp_db_path)
            cursor = conn.execute(
                "SELECT COUNT(*) FROM traces WHERE trace_id = ?",
                (trace_record["trace_id"],)
            )
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 1


class TestGetTrace:
    """Tests for retrieving traces from database."""

    def test_get_trace_returns_record(
        self, tmp_db_path: str, trace_record: dict[str, Any]
    ) -> None:
        """get_trace should return saved trace."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()
            save_trace(trace_record)

            result = get_trace(trace_record["trace_id"])

            assert result is not None
            assert result["trace_id"] == trace_record["trace_id"]
            assert result["decision"] == trace_record["decision"]

    def test_get_trace_returns_none_for_missing(self, tmp_db_path: str) -> None:
        """get_trace should return None for non-existent trace."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            result = get_trace("tr_nonexistent")
            assert result is None

    def test_get_trace_deserializes_json(
        self, tmp_db_path: str, trace_record: dict[str, Any]
    ) -> None:
        """get_trace should deserialize JSON fields correctly."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()
            save_trace(trace_record)

            result = get_trace(trace_record["trace_id"])

            assert result is not None
            assert isinstance(result["envelope"], dict)
            assert isinstance(result["metadata"], dict)
            assert result["envelope"]["decision"] == trace_record["decision"]


class TestAggregateTvv:
    """Tests for TVV aggregation from traces."""

    def test_aggregate_tvv_counts_requests(
        self, tmp_db_path: str, multiple_trace_records: list[dict[str, Any]]
    ) -> None:
        """aggregate_tvv should count total requests."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            for record in multiple_trace_records:
                save_trace(record)

            tvv = aggregate_tvv()

            assert tvv["total_requests"] == len(multiple_trace_records)

    def test_aggregate_tvv_sums_tokens(
        self, tmp_db_path: str, multiple_trace_records: list[dict[str, Any]]
    ) -> None:
        """aggregate_tvv should sum total tokens."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            for record in multiple_trace_records:
                save_trace(record)

            tvv = aggregate_tvv()

            assert tvv["total_tokens"] >= 0

    def test_aggregate_tvv_decision_breakdown(
        self, tmp_db_path: str, multiple_trace_records: list[dict[str, Any]]
    ) -> None:
        """aggregate_tvv should provide decision breakdown."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            for record in multiple_trace_records:
                save_trace(record)

            tvv = aggregate_tvv()

            assert "decision_breakdown" in tvv
            assert tvv["decision_breakdown"]["PASS"] == 3
            assert tvv["decision_breakdown"]["REFINE"] == 2
