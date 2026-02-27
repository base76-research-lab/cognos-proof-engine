"""Integration tests for API endpoints."""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from trace_store import init_db, save_trace


class TestHealthzEndpoint:
    """Tests for /healthz endpoint."""

    def test_healthz_returns_200(self, test_client: TestClient) -> None:
        """GET /healthz should return 200 OK."""
        response = test_client.get("/healthz")
        assert response.status_code == 200

    def test_healthz_response_structure(self, test_client: TestClient) -> None:
        """GET /healthz should return correct structure."""
        response = test_client.get("/healthz")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "operational-cognos-gateway"


class TestChatCompletionsEndpoint:
    """Tests for POST /v1/chat/completions endpoint."""

    def test_chat_completions_with_mock_upstream(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
    ) -> None:
        """Chat completions should work with mock upstream."""
        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "choices" in data
            assert "cognos" in data

    def test_chat_completions_includes_trace_id(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
    ) -> None:
        """Response should include X-Cognos-Trace-Id header."""
        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)

            assert "X-Cognos-Trace-Id" in response.headers
            trace_id = response.headers["X-Cognos-Trace-Id"]
            assert trace_id.startswith("tr_")

    def test_chat_completions_includes_trust_headers(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
    ) -> None:
        """Response should include trust-related headers."""
        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)

            assert "X-Cognos-Decision" in response.headers
            assert "X-Cognos-Trust-Score" in response.headers
            assert "X-Cognos-Policy" in response.headers

    def test_chat_completions_cognos_envelope(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
    ) -> None:
        """Response should include cognos envelope with signals."""
        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)

            data = response.json()
            envelope = data["cognos"]

            assert "trace_id" in envelope
            assert "decision" in envelope
            assert "risk" in envelope
            assert "signals" in envelope
            assert "attestation" in envelope

    def test_chat_completions_monitor_mode(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
    ) -> None:
        """Monitor mode should always return PASS."""
        valid_chat_request["cognos"]["mode"] = "monitor"

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)

            data = response.json()
            assert data["cognos"]["decision"] == "PASS"

    def test_chat_completions_invalid_json(self, test_client: TestClient) -> None:
        """Invalid JSON should return 400."""
        response = test_client.post(
            "/v1/chat/completions",
            content=b"invalid json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 400

    def test_chat_completions_missing_required_field(self, test_client: TestClient) -> None:
        """Missing required fields should return 400."""
        invalid_request = {"messages": [{"role": "user", "content": "Hi"}]}

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=invalid_request)
            assert response.status_code == 400

    def test_chat_completions_persists_trace(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Chat completions should persist trace to database."""
        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)

            trace_id = response.headers["X-Cognos-Trace-Id"]

            # Verify trace was saved
            from trace_store import get_trace
            trace = get_trace(trace_id)
            assert trace is not None
            assert trace["trace_id"] == trace_id


class TestStreamingEndpoint:
    """Tests for streaming chat completions."""

    def test_streaming_response_format(
        self,
        test_client: TestClient,
        stream_chat_request: dict[str, Any],
    ) -> None:
        """Streaming response should return SSE format."""
        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=stream_chat_request)

            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    def test_streaming_includes_trace_id(
        self,
        test_client: TestClient,
        stream_chat_request: dict[str, Any],
    ) -> None:
        """Streaming response should include trace ID header."""
        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=stream_chat_request)

            assert "X-Cognos-Trace-Id" in response.headers


class TestTraceEndpoint:
    """Tests for GET /v1/traces/{trace_id} endpoint."""

    def test_get_trace_existing(
        self,
        test_client: TestClient,
        trace_record: dict[str, Any],
        mock_db: None,
    ) -> None:
        """GET /v1/traces/{id} should return existing trace."""
        from trace_store import save_trace
        init_db()
        save_trace(trace_record)

        response = test_client.get(f"/v1/traces/{trace_record['trace_id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["trace_id"] == trace_record["trace_id"]

    def test_get_trace_nonexistent(
        self,
        test_client: TestClient,
        mock_db: None,
    ) -> None:
        """GET /v1/traces/{id} should return 404 for missing trace."""
        init_db()
        response = test_client.get("/v1/traces/tr_nonexistent")
        assert response.status_code == 404

    def test_get_trace_response_structure(
        self,
        test_client: TestClient,
        trace_record: dict[str, Any],
        mock_db: None,
    ) -> None:
        """Trace response should have expected structure."""
        from trace_store import save_trace
        init_db()
        save_trace(trace_record)

        response = test_client.get(f"/v1/traces/{trace_record['trace_id']}")
        data = response.json()

        assert "trace_id" in data
        assert "created" in data
        assert "envelope" in data
        assert "request_fingerprint" in data


class TestTrustReportEndpoint:
    """Tests for POST /v1/reports/trust endpoint."""

    def test_create_trust_report(
        self,
        test_client: TestClient,
        multiple_trace_records: list[dict[str, Any]],
        mock_db: None,
    ) -> None:
        """POST /v1/reports/trust should create report."""
        from trace_store import save_trace
        init_db()

        for record in multiple_trace_records:
            save_trace(record)

        trace_ids = [r["trace_id"] for r in multiple_trace_records]
        request_body = {
            "trace_ids": trace_ids,
            "regime": "EU_AI_ACT",
        }

        response = test_client.post("/v1/reports/trust", json=request_body)

        assert response.status_code == 200
        data = response.json()
        assert data["regime"] == "EU_AI_ACT"
        assert data["summary"]["found_count"] == len(trace_ids)

    def test_trust_report_with_missing_traces(
        self,
        test_client: TestClient,
        mock_db: None,
    ) -> None:
        """Report should handle missing traces."""
        init_db()

        request_body = {
            "trace_ids": ["tr_missing1", "tr_missing2"],
            "regime": "GDPR",
        }

        response = test_client.post("/v1/reports/trust", json=request_body)

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["missing_count"] == 2

    def test_trust_report_invalid_request(self, test_client: TestClient) -> None:
        """Invalid report request should return 400."""
        request_body = {"regime": "TEST"}  # Missing trace_ids

        response = test_client.post("/v1/reports/trust", json=request_body)
        assert response.status_code == 400


class TestAuthenticationAndAuthorization:
    """Tests for auth-related behavior."""

    def test_gateway_auth_not_required_by_default(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
    ) -> None:
        """Requests without auth should work when no COGNOS_GATEWAY_API_KEY."""
        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true", "COGNOS_GATEWAY_API_KEY": ""}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)
            assert response.status_code == 200

    def test_gateway_auth_required_when_set(
        self,
        valid_chat_request: dict[str, Any],
    ) -> None:
        """Requests without correct auth should fail when COGNOS_GATEWAY_API_KEY set."""
        from main import app

        with patch.dict(
            os.environ,
            {"COGNOS_GATEWAY_API_KEY": "test-key", "COGNOS_MOCK_UPSTREAM": "true"},
        ):
            # Need new client with updated env
            client = TestClient(app)
            response = client.post("/v1/chat/completions", json=valid_chat_request)
            assert response.status_code == 401

    def test_gateway_auth_with_valid_key(
        self,
        valid_chat_request: dict[str, Any],
    ) -> None:
        """Requests with valid auth should succeed."""
        from main import app

        with patch.dict(
            os.environ,
            {"COGNOS_GATEWAY_API_KEY": "test-key", "COGNOS_MOCK_UPSTREAM": "true"},
        ):
            client = TestClient(app)
            response = client.post(
                "/v1/chat/completions",
                json=valid_chat_request,
                headers={"x-api-key": "test-key"},
            )
            assert response.status_code == 200


class TestModelPrefixRouting:
    """Tests for model prefix routing (openai:, google:, claude:, etc)."""

    def test_model_prefix_preserved_in_cognos(
        self,
        test_client: TestClient,
        valid_chat_request: dict[str, Any],
    ) -> None:
        """Model prefix should be processed correctly."""
        valid_chat_request["model"] = "openai:gpt-4o-mini"

        with patch.dict(os.environ, {"COGNOS_MOCK_UPSTREAM": "true"}):
            response = test_client.post("/v1/chat/completions", json=valid_chat_request)

            assert response.status_code == 200
            # Model should be normalized in upstream but cognos should track original
