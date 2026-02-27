# Test Suite for Operational Cognos

Comprehensive pytest suite with 20+ test cases covering unit tests, integration tests, and end-to-end flows.

## Setup

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_policy.py

# Run specific test class
pytest tests/test_api.py::TestHealthzEndpoint

# Run specific test
pytest tests/test_policy.py::TestResolveDecisionMonitorMode::test_monitor_mode_always_passes
```

## Test Organization

### Unit Tests

- **`test_policy.py`** (6 test classes, 15+ tests)
  - Policy decision logic in monitor/enforce modes
  - Risk threshold boundaries
  - Edge cases (clamping, invalid modes)

- **`test_trace_store.py`** (4 test classes, 12+ tests)
  - Database initialization
  - Trace persistence and retrieval
  - JSON serialization
  - TVV aggregation

- **`test_reports.py`** (7 test methods)
  - Trust report generation
  - Decision breakdown aggregation
  - Missing trace handling

### Integration Tests

- **`test_api.py`** (7 test classes, 20+ tests)
  - `/healthz` endpoint
  - `/v1/chat/completions` (mock upstream, streaming)
  - `/v1/traces/{id}` endpoint
  - `/v1/reports/trust` endpoint
  - Authentication & authorization
  - Model prefix routing

### End-to-End Flow Tests

- **`test_gateway_flows.py`** (6 test classes, 15+ tests)
  - Complete chat flows (monitor & enforce modes)
  - Streaming flows with shadow models
  - Error recovery & isolation
  - Reporting pipeline
  - Policy escalation chains
  - Concurrent request handling

## Test Fixtures

Defined in `conftest.py`:

- `tmp_db_path` — Temporary SQLite database
- `mock_db` — Environment patching for test database
- `test_client` — FastAPI TestClient
- `valid_chat_request` — Sample valid request
- `stream_chat_request` — Streaming request
- `trace_record` — Sample trace data
- `multiple_trace_records` — Multiple traces for aggregation
- `mock_upstream_response` — Mock API response
- `reset_env` — Auto-reset critical environment variables

## Running Test Suites

### All Tests (Recommended)
```bash
pytest -v
```

### Unit Tests Only
```bash
pytest tests/test_policy.py tests/test_trace_store.py tests/test_reports.py -v
```

### Integration Tests Only
```bash
pytest tests/test_api.py -v
```

### Flow Tests Only
```bash
pytest tests/test_gateway_flows.py -v
```

### With Coverage Report
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

The HTML report will be in `htmlcov/index.html`.

### Verbose Output
```bash
pytest -vv --tb=short
```

## Test Markers

Run tests by marker:

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Flow tests only
pytest -m flow

# Exclude slow tests
pytest -m "not slow"
```

## Key Test Coverage

### Policy Logic
- ✅ Monitor mode always passes
- ✅ Enforce mode respects thresholds
- ✅ Risk clamping to [0, 1]
- ✅ Threshold boundary transitions
- ✅ Invalid mode handling

### Database & Tracing
- ✅ Table creation & migrations
- ✅ Trace persistence (CRUD)
- ✅ JSON serialization
- ✅ TVV aggregation
- ✅ Multiple concurrent traces

### API Endpoints
- ✅ `/healthz` health check
- ✅ `/v1/chat/completions` (non-streaming)
- ✅ `/v1/chat/completions` (streaming)
- ✅ `/v1/traces/{id}` retrieval
- ✅ `/v1/reports/trust` generation
- ✅ Authentication & authorization
- ✅ Model prefix routing
- ✅ Error handling (invalid JSON, missing fields)

### End-to-End Flows
- ✅ Complete request → gateway → response → trace
- ✅ Monitor vs enforce mode comparison
- ✅ Policy escalation chains
- ✅ Streaming with shadow models
- ✅ Report generation from traces
- ✅ Error recovery without data corruption
- ✅ Request isolation
- ✅ Concurrent request handling

## Debugging Failed Tests

### View Full Traceback
```bash
pytest tests/test_api.py::TestChatCompletionsEndpoint::test_chat_completions_with_mock_upstream -vv --tb=long
```

### Run with Print Statements
```bash
pytest -s tests/test_policy.py
```

### Check Database State
```python
# In failing test, add:
import sqlite3
from pathlib import Path
from trace_store import _resolve_db_path

db_path = _resolve_db_path()
conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT COUNT(*) FROM traces")
print(f"Traces in DB: {cursor.fetchone()[0]}")
conn.close()
```

## Common Issues

### Test Isolation
All tests automatically reset environment variables via `reset_env` fixture. If you see state leakage:
- Check that fixtures are applied correctly
- Verify `mock_db` is used for database tests
- Use `COGNOS_MOCK_UPSTREAM=true` for API tests

### Database Locking
If you see SQLite lock errors:
- Ensure previous test processes terminated
- Use `conftest.py` fixtures instead of manual DB setup
- Each test gets its own temporary database

### Async Tests
Tests using async functions should be marked with `@pytest.mark.asyncio` or use `pytest-asyncio` (already in requirements-test.txt).

## Extending Tests

### Add New Test
1. Create test file: `tests/test_new_module.py`
2. Import fixtures from `conftest.py`
3. Use `test_client` or `mock_db` as needed
4. Run: `pytest tests/test_new_module.py`

### Add New Fixture
1. Add to `conftest.py`
2. Use `@pytest.fixture` decorator
3. Reference in test functions as parameter

### Example
```python
@pytest.fixture
def my_fixture():
    return {"data": "value"}

def test_something(my_fixture):
    assert my_fixture["data"] == "value"
```

## CI/CD Integration

To run tests in CI:

```bash
# Install
pip install -r requirements.txt -r requirements-test.txt

# Run with coverage
pytest --cov=src --cov-report=xml

# Generate JUnit XML for CI
pytest --junit-xml=test-results.xml
```

## Performance

Current test suite runs in ~10–15 seconds (depending on hardware). For faster iteration:

```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```
