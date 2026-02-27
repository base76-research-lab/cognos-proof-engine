from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from trace_store import get_trace


def build_trust_report(trace_ids: list[str], regime: str, fmt: str = "json") -> dict[str, Any]:
    found = 0
    missing: list[str] = []
    decisions: dict[str, int] = {}

    for trace_id in trace_ids:
        trace = get_trace(trace_id)
        if trace is None:
            missing.append(trace_id)
            continue
        found += 1
        decision = str((trace.get("envelope") or {}).get("decision", "UNKNOWN"))
        decisions[decision] = decisions.get(decision, 0) + 1

    summary: dict[str, Any] = {
        "requested_count": len(trace_ids),
        "found_count": found,
        "missing_count": len(missing),
        "missing_ids": missing,
        "decision_breakdown": decisions,
        "format": fmt,
    }

    return {
        "report_id": f"rpt_{uuid.uuid4().hex[:12]}",
        "created": datetime.now(timezone.utc).isoformat(),
        "regime": regime,
        "summary": summary,
    }
