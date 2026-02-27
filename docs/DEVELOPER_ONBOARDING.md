# Developer Onboarding (External)

This guide is optimized for fast first success with CognOS.

## Target Outcome (15 minutes)
- Send one request through CognOS
- Receive trust envelope + headers
- Fetch trace by `trace_id`

## Prerequisites
- Python 3.10+
- Running gateway endpoint (`COGNOS_BASE_URL`)
- Gateway key (`COGNOS_API_KEY`) if enabled
- Upstream authorization (`COGNOS_UPSTREAM_AUTH`) if gateway does not use server-side key

## Quickstart

```bash
pip install -e .
export COGNOS_BASE_URL="http://127.0.0.1:8788"
export COGNOS_API_KEY=""
export COGNOS_UPSTREAM_AUTH="Bearer YOUR_UPSTREAM_KEY"
cognos chat "What are the key GDPR principles?" --mode monitor
```

Then fetch trace using the returned `X-Cognos-Trace-Id`:

```bash
cognos trace tr_xxxxxxxxxxxx
```

## OpenAI-compatible drop-in example
See:
- `examples/python_openai_compatible.py`

## HTTP examples
See:
- `examples/http_curl_examples.md`

## Troubleshooting
- `401 Unauthorized`: set `COGNOS_API_KEY` correctly.
- `500 Missing upstream authorization`: set `COGNOS_UPSTREAM_AUTH` or configure server-side upstream key.
- No trace found: verify exact `trace_id` from response headers.
