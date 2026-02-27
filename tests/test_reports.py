"""Unit tests for reports module."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from reports import build_trust_report
from trace_store import init_db, save_trace


class TestBuildTrustReport:
    """Tests for trust report generation."""

    def test_build_report_with_all_found_traces(
        self,
        tmp_db_path: str,
        multiple_trace_records: list[dict[str, Any]],
    ) -> None:
        """Report should show all found traces correctly."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            for record in multiple_trace_records:
                save_trace(record)

            trace_ids = [r["trace_id"] for r in multiple_trace_records]
            report = build_trust_report(trace_ids, regime="EU_AI_ACT")

            assert report["regime"] == "EU_AI_ACT"
            assert report["summary"]["requested_count"] == len(trace_ids)
            assert report["summary"]["found_count"] == len(trace_ids)
            assert report["summary"]["missing_count"] == 0

    def test_build_report_with_partial_missing(
        self,
        tmp_db_path: str,
        multiple_trace_records: list[dict[str, Any]],
    ) -> None:
        """Report should handle missing traces."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            # Only save first 2 records
            for record in multiple_trace_records[:2]:
                save_trace(record)

            # Request all traces
            trace_ids = [r["trace_id"] for r in multiple_trace_records]
            report = build_trust_report(trace_ids, regime="GDPR")

            assert report["summary"]["found_count"] == 2
            assert report["summary"]["missing_count"] == 3
            assert len(report["summary"]["missing_ids"]) == 3

    def test_build_report_decision_breakdown(
        self,
        tmp_db_path: str,
        multiple_trace_records: list[dict[str, Any]],
    ) -> None:
        """Report should provide correct decision breakdown."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            for record in multiple_trace_records:
                save_trace(record)

            trace_ids = [r["trace_id"] for r in multiple_trace_records]
            report = build_trust_report(trace_ids, regime="DEFAULT")

            breakdown = report["summary"]["decision_breakdown"]
            assert breakdown["PASS"] == 3
            assert breakdown["REFINE"] == 2

    def test_build_report_empty_trace_list(self, tmp_db_path: str) -> None:
        """Report with empty trace list should be valid."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            report = build_trust_report([], regime="CUSTOM")

            assert report["summary"]["requested_count"] == 0
            assert report["summary"]["found_count"] == 0
            assert report["summary"]["missing_count"] == 0

    def test_build_report_has_report_id(
        self,
        tmp_db_path: str,
        trace_record: dict[str, Any],
    ) -> None:
        """Report should have unique report ID."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()
            save_trace(trace_record)

            report = build_trust_report([trace_record["trace_id"]], regime="TEST")

            assert report["report_id"].startswith("rpt_")
            assert len(report["report_id"]) > 4

    def test_build_report_has_created_timestamp(
        self,
        tmp_db_path: str,
        trace_record: dict[str, Any],
    ) -> None:
        """Report should have creation timestamp."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()
            save_trace(trace_record)

            report = build_trust_report([trace_record["trace_id"]], regime="TEST")

            assert report["created"] is not None
            assert "T" in report["created"]  # ISO format

    def test_build_report_format_parameter(
        self,
        tmp_db_path: str,
        trace_record: dict[str, Any],
    ) -> None:
        """Report should respect format parameter."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()
            save_trace(trace_record)

            report = build_trust_report(
                [trace_record["trace_id"]],
                regime="TEST",
                fmt="csv",
            )

            assert report["summary"]["format"] == "csv"

    def test_build_report_unknown_decision_handling(
        self,
        tmp_db_path: str,
        trace_record: dict[str, Any],
    ) -> None:
        """Report should handle traces with unknown decision gracefully."""
        with patch.dict("os.environ", {"COGNOS_TRACE_DB": tmp_db_path}):
            import trace_store
            trace_store.DEFAULT_DB_PATH = tmp_db_path
            init_db()

            trace_record["envelope"]["decision"] = "UNKNOWN"
            save_trace(trace_record)

            report = build_trust_report([trace_record["trace_id"]], regime="TEST")

            assert "UNKNOWN" in report["summary"]["decision_breakdown"]
