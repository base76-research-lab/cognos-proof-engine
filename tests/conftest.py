"""Pytest configuration and shared fixtures for Operational Cognos."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def tmp_db_path() -> Generator[str, None, None]:
    """Provide a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_traces.sqlite3"
        yield str(db_path)


@pytest.fixture
def mock_db(tmp_db_path: str) -> Generator[None, None, None]:
    """Patch COGNOS_TRACE_DB to use temporary database."""
    with patch.dict(os.environ, {"COGNOS_TRACE_DB": tmp_db_path}):
        yield


@pytest.fixture
def test_client(mock_db: None) -> TestClient:
    """Provide a FastAPI TestClient with mocked database."""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_upstream_response() -> dict[str, Any]:
    """Mock upstream API response."""
    return {
        "id": "chatcmpl_test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response from upstream",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    }


@pytest.fixture
def valid_chat_request() -> dict[str, Any]:
    """Provide a valid chat completion request."""
    return {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Hello, what is 2+2?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "cognos": {
            "mode": "monitor",
            "policy_id": "default_v1",
        },
    }


@pytest.fixture
def stream_chat_request() -> dict[str, Any]:
    """Provide a streaming chat completion request."""
    return {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Stream test"}
        ],
        "stream": True,
        "cognos": {"mode": "monitor"},
    }


@pytest.fixture
def trace_record() -> dict[str, Any]:
    """Provide a sample trace record."""
    return {
        "trace_id": "tr_test123",
        "created_at": "2026-02-27T12:00:00Z",
        "decision": "PASS",
        "policy": "default_v1",
        "trust_score": 0.88,
        "risk": 0.12,
        "is_stream": False,
        "status_code": 200,
        "model": "gpt-4o-mini",
        "request_fingerprint": {
            "simhash": "sha256:abc123",
            "embedding_hash": "sha256:abc123def456",
            "length": 150,
            "model_id": "gpt-4o-mini",
            "cluster_id": None,
        },
        "response_fingerprint": {
            "simhash": "sha256:def456",
            "embedding_hash": "sha256:def456abc123",
            "length": 200,
            "model_id": "gpt-4o-mini",
            "cluster_id": None,
        },
        "envelope": {
            "decision": "PASS",
            "risk": 0.12,
            "signals": {
                "ue": 0.05,
                "ua": 0.02,
                "divergence": 0.01,
                "citation_density": 0.0,
                "contradiction": 0.0,
                "out_of_distribution": 0.04,
            },
            "trace_id": "tr_test123",
            "policy": "default_v1",
            "attestation": {
                "hash": "sha256:hash123",
                "signed_by": "cognos",
                "ts": "2026-02-27T12:00:00Z",
            },
        },
        "metadata": {
            "mode": "mock",
            "upstream": "none",
            "usage": {"total_tokens": 30},
            "retention": "fingerprints",
        },
    }


@pytest.fixture
def multiple_trace_records() -> list[dict[str, Any]]:
    """Provide multiple trace records for aggregation tests."""
    base = {
        "created_at": "2026-02-27T12:00:00Z",
        "policy": "default_v1",
        "is_stream": False,
        "status_code": 200,
        "model": "gpt-4o-mini",
        "metadata": {},
        "request_fingerprint": {},
        "response_fingerprint": {},
        "envelope": {"attestation": {"ts": "2026-02-27T12:00:00Z"}},
    }
    return [
        {
            **base,
            "trace_id": f"tr_pass_{i}",
            "decision": "PASS",
            "risk": 0.1,
            "trust_score": 0.9,
        }
        for i in range(3)
    ] + [
        {
            **base,
            "trace_id": f"tr_refine_{i}",
            "decision": "REFINE",
            "risk": 0.35,
            "trust_score": 0.65,
        }
        for i in range(2)
    ]


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Provide a mock httpx AsyncClient."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {
        "id": "mock_response",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4o-mini",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "Mock"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
    }
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = mock_response
    return mock_client


@pytest.fixture(autouse=True)
def reset_env() -> Generator[None, None, None]:
    """Reset critical environment variables before each test."""
    saved_env = {}
    critical_vars = [
        "COGNOS_MOCK_UPSTREAM",
        "COGNOS_UPSTREAM_BASE_URL",
        "COGNOS_GATEWAY_API_KEY",
        "COGNOS_TRACE_DB",
    ]
    for var in critical_vars:
        saved_env[var] = os.environ.get(var)

    yield

    for var, original_value in saved_env.items():
        if original_value is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = original_value
