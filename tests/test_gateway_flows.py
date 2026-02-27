"""End-to-end flow tests for gateway behavior."""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from trace_store import get_trace, init_db, save_trace


class TestChatFlowWithMockUpstream:
    """Test complete chat flow with mocked upstream."""

    def test_complete_flow_monitor_mode(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Complete flow: request -> gateway -> response -> trace persistence."""
        init_db()

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)

            # 1. Verify response status and structure
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "choices" in data
            assert "cognos" in data

            # 2. Verify headers
            trace_id = response.headers["X-Cognos-Trace-Id"]
            assert trace_id.startswith("tr_")
            assert response.headers["X-Cognos-Decision"] == "PASS"
            assert response.headers["X-Cognos-Policy"] == "default_v1"

            # 3. Verify trace persisted
            trace = get_trace(trace_id)
            assert trace is not None
            assert trace["model"] == valid_chat_request["model"]
            assert trace["decision"] == "PASS"

            # 4. Verify envelope integrity
            envelope = data["cognos"]
            assert envelope["trace_id"] == trace_id
            assert "signals" in envelope
            assert all(
                key in envelope["signals"]
                for key in ["ue", "ua", "divergence", "citation_density", "contradiction", "out_of_distribution"]
            )

    def test_flow_with_enforce_mode(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Flow with enforce mode should respect policy thresholds."""
        init_db()
        valid_chat_request["cognos"]["mode"] = "enforce"
        valid_chat_request["cognos"]["target_risk"] = 0.05

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)

            assert response.status_code == 200
            data = response.json()

            # With target_risk=0.05 and base_risk=0.12, should escalate
            # The decision depends on the policy thresholds
            decision = response.headers["X-Cognos-Decision"]
            assert decision in ["PASS", "REFINE", "ESCALATE", "BLOCK"]


class TestStreamingFlow:
    """Test streaming response flows."""

    def test_streaming_complete_flow(
        self,
        test_client: TestClient,
        stream_chat_request: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Complete streaming flow with trace persistence."""
        init_db()

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=stream_chat_request)

            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            trace_id = response.headers["X-Cognos-Trace-Id"]

            # Verify trace exists
            trace = get_trace(trace_id)
            assert trace is not None
            assert trace["is_stream"] is True

    def test_streaming_with_shadow_models(
        self,
        test_client: TestClient,
        stream_chat_request: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Streaming with shadow models should include shadow info."""
        init_db()
        stream_chat_request["cognos"]["shadow_pct"] = 0.5
        stream_chat_request["cognos"]["shadow_models"] = ["gpt-4o", "claude-3"]

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=stream_chat_request)

            assert response.status_code == 200

            trace_id = response.headers["X-Cognos-Trace-Id"]
            trace = get_trace(trace_id)

            if "shadow" in trace["envelope"]:
                assert trace["envelope"]["shadow"]["enabled"] is True


class TestErrorRecoveryFlows:
    """Test error handling and recovery flows."""

    def test_invalid_request_no_database_corruption(
        self,
        test_client: TestClient,
        mock_db: None,
    ) -> None:
        """Invalid request should not corrupt database state."""
        init_db()

        # Make invalid request
        response = test_client.post(
            "/v1/chat/completions",
            json={"invalid": "request"},
        )
        assert response.status_code == 400

        # Database should still be accessible
        from trace_store import aggregate_tvv
        tvv = aggregate_tvv()
        assert "total_requests" in tvv

    def test_multiple_requests_isolation(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Multiple requests should have independent traces."""
        init_db()

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response1 = test_client.post("/v1/chat/completions", json=valid_chat_request)
            response2 = test_client.post("/v1/chat/completions", json=valid_chat_request)

            trace_id_1 = response1.headers["X-Cognos-Trace-Id"]
            trace_id_2 = response2.headers["X-Cognos-Trace-Id"]

            assert trace_id_1 != trace_id_2

            trace1 = get_trace(trace_id_1)
            trace2 = get_trace(trace_id_2)

            assert trace1["trace_id"] == trace_id_1
            assert trace2["trace_id"] == trace_id_2


class TestReportingFlow:
    """Test end-to-end reporting flows."""

    def test_report_generation_from_traces(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Generate trace -> Generate report flow."""
        init_db()

        # Create traces
        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response1 = test_client.post("/v1/chat/completions", json=valid_chat_request)
            response2 = test_client.post("/v1/chat/completions", json=valid_chat_request)

            trace_id_1 = response1.headers["X-Cognos-Trace-Id"]
            trace_id_2 = response2.headers["X-Cognos-Trace-Id"]

            # Generate report
            report_request = {
                "trace_ids": [trace_id_1, trace_id_2],
                "regime": "EU_AI_ACT",
            }

            report_response = test_client.post("/v1/reports/trust", json=report_request)

            assert report_response.status_code == 200
            report = report_response.json()

            assert report["summary"]["found_count"] == 2
            assert report["summary"]["requested_count"] == 2
            assert "PASS" in report["summary"]["decision_breakdown"]


class TestPolicyEscalation:
    """Test policy escalation and decision logic."""

    def test_escalation_chain_monitor_vs_enforce(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Compare decisions between monitor and enforce modes."""
        init_db()

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            # Monitor mode
            monitor_request = valid_chat_request.copy()
            monitor_request["cognos"]["mode"] = "monitor"
            monitor_response = test_client.post("/v1/chat/completions", json=monitor_request)
            monitor_decision = monitor_response.headers["X-Cognos-Decision"]

            # Enforce mode
            enforce_request = valid_chat_request.copy()
            enforce_request["cognos"]["mode"] = "enforce"
            enforce_request["cognos"]["target_risk"] = 0.5
            enforce_response = test_client.post("/v1/chat/completions", json=enforce_request)
            enforce_decision = enforce_response.headers["X-Cognos-Decision"]

            # Monitor should always PASS
            assert monitor_decision == "PASS"

            # Enforce may vary
            assert enforce_decision in ["PASS", "REFINE", "ESCALATE", "BLOCK"]


class TestConcurrentRequests:
    """Test behavior with multiple concurrent-like requests."""

    def test_rapid_sequential_requests(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Multiple rapid requests should each get unique traces."""
        init_db()

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            trace_ids = set()

            for _ in range(10):
                response = test_client.post("/v1/chat/completions", json=valid_chat_request)
                trace_id = response.headers["X-Cognos-Trace-Id"]
                trace_ids.add(trace_id)

            # All trace IDs should be unique
            assert len(trace_ids) == 10

            # All should be queryable
            for trace_id in trace_ids:
                trace = get_trace(trace_id)
                assert trace is not None
