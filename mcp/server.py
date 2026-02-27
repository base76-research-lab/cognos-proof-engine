#!/usr/bin/env python3
"""
CognOS MCP Server — Trust verification for Claude and MCP-compatible tools.

Exposes CognOS as a Model Context Protocol server, allowing Claude Code and
other tools to verify AI outputs through the CognOS gateway.
"""

import asyncio
import json
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent, ToolResult

# Initialize MCP server
server = Server("cognos")

# CognOS gateway configuration
COGNOS_BASE_URL = os.getenv("COGNOS_BASE_URL", "http://127.0.0.1:8788")
COGNOS_API_KEY = os.getenv("COGNOS_API_KEY", "")
REQUEST_TIMEOUT = 30


# ============================================================================
# Tool Definitions
# ============================================================================

VERIFY_OUTPUT_TOOL = Tool(
    name="verify_output",
    description="""
Verify an AI-generated output through CognOS trust gateway.

Returns trust verification including:
- decision: "PASS", "REFINE", "ESCALATE", or "BLOCK"
- risk: 0.0-1.0 risk score
- signals: epistemic uncertainty, aleatoric uncertainty, OOD detection
- trace_id: immutable audit trail ID

Perfect for verifying LLM outputs before using them in critical decisions.
    """.strip(),
    inputSchema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The AI-generated content to verify (e.g., medical diagnosis, financial advice)"
            },
            "mode": {
                "type": "string",
                "enum": ["monitor", "enforce"],
                "description": "monitor: Log only. enforce: Apply policies (may block/refine)"
            },
            "model": {
                "type": "string",
                "description": "Model that generated this output (e.g., 'gpt-4o-mini', 'claude-sonnet')"
            },
            "target_risk": {
                "type": "number",
                "description": "Risk threshold for enforce mode (0.0-1.0). Default: 0.1"
            }
        },
        "required": ["content"],
    }
)

GET_TRACE_TOOL = Tool(
    name="get_trace",
    description="""
Retrieve full audit trail for a CognOS verification.

Returns immutable trace record including:
- decision and risk score
- decision signals (epistemic/aleatoric uncertainty, etc.)
- request/response fingerprints
- timestamp and policy applied

Used for compliance reporting and decision audit.
    """.strip(),
    inputSchema={
        "type": "object",
        "properties": {
            "trace_id": {
                "type": "string",
                "description": "Trace ID from verify_output response (e.g., 'tr_abc123xyz')"
            }
        },
        "required": ["trace_id"],
    }
)

CREATE_REPORT_TOOL = Tool(
    name="create_trust_report",
    description="""
Generate a compliance report from CognOS verification traces.

Supports compliance regimes:
- EU_AI_ACT: EU AI Act Article 6 risk assessment
- GDPR: Data protection impact assessment
- SOC2: Security and availability attestation
- DEFAULT: Generic trust report

Returns report with decision breakdown, statistics, and audit trail.
Perfect for compliance documentation, audit evidence, and risk management.
    """.strip(),
    inputSchema={
        "type": "object",
        "properties": {
            "trace_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Array of trace IDs to include in report"
            },
            "regime": {
                "type": "string",
                "enum": ["EU_AI_ACT", "GDPR", "SOC2", "DEFAULT"],
                "description": "Compliance regime for report generation"
            },
            "format": {
                "type": "string",
                "enum": ["json", "csv", "pdf"],
                "description": "Output format (default: json)"
            }
        },
        "required": ["trace_ids", "regime"],
    }
)

HEALTHZ_TOOL = Tool(
    name="healthz",
    description="Check CognOS gateway health and availability.",
    inputSchema={
        "type": "object",
        "properties": {}
    }
)


# ============================================================================
# Tool Implementations
# ============================================================================

async def verify_output(
    content: str,
    mode: str = "monitor",
    model: str = "gpt-4o-mini",
    target_risk: float = 0.1,
) -> ToolResult:
    """Verify AI output through CognOS gateway."""

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Verify this output for trust and safety:\n\n" + content
                    }
                ],
                "cognos": {
                    "mode": mode,
                    "target_risk": target_risk,
                    "policy_id": "default_v1"
                }
            }

            headers = {"Content-Type": "application/json"}
            if COGNOS_API_KEY:
                headers["Authorization"] = f"Bearer {COGNOS_API_KEY}"

            response = await client.post(
                f"{COGNOS_BASE_URL}/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            result = response.json()

            # Extract CognOS decision
            cognos_data = result.get("cognos", {})
            decision = cognos_data.get("decision", "UNKNOWN")
            risk = cognos_data.get("risk", 0.0)
            trace_id = cognos_data.get("trace_id", "unknown")
            signals = cognos_data.get("signals", {})

            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "decision": decision,
                            "risk": risk,
                            "trace_id": trace_id,
                            "signals": signals,
                            "message": f"Output verification complete. Decision: {decision}",
                        }, indent=2)
                    )
                ],
                is_error=False
            )

        except httpx.HTTPError as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error verifying output: {str(e)}"
                    )
                ],
                is_error=True
            )


async def get_trace(trace_id: str) -> ToolResult:
    """Retrieve full audit trail."""

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            headers = {}
            if COGNOS_API_KEY:
                headers["Authorization"] = f"Bearer {COGNOS_API_KEY}"

            response = await client.get(
                f"{COGNOS_BASE_URL}/v1/traces/{trace_id}",
                headers=headers
            )
            response.raise_for_status()

            trace = response.json()

            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(trace, indent=2)
                    )
                ],
                is_error=False
            )

        except httpx.HTTPError as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error retrieving trace {trace_id}: {str(e)}"
                    )
                ],
                is_error=True
            )


async def create_trust_report(
    trace_ids: list[str],
    regime: str = "DEFAULT",
    format: str = "json"
) -> ToolResult:
    """Generate compliance report."""

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            payload = {
                "trace_ids": trace_ids,
                "regime": regime,
                "format": format
            }

            headers = {"Content-Type": "application/json"}
            if COGNOS_API_KEY:
                headers["Authorization"] = f"Bearer {COGNOS_API_KEY}"

            response = await client.post(
                f"{COGNOS_BASE_URL}/v1/reports/trust",
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            report = response.json()

            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(report, indent=2)
                    )
                ],
                is_error=False
            )

        except httpx.HTTPError as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error generating report: {str(e)}"
                    )
                ],
                is_error=True
            )


async def healthz() -> ToolResult:
    """Check gateway health."""

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.get(f"{COGNOS_BASE_URL}/healthz")
            response.raise_for_status()

            health = response.json()
            status = health.get("status", "unknown")

            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "status": status,
                            "gateway_url": COGNOS_BASE_URL,
                            "message": f"CognOS gateway is {status}"
                        }, indent=2)
                    )
                ],
                is_error=False
            )

        except httpx.HTTPError as e:
            return ToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"CognOS gateway unreachable at {COGNOS_BASE_URL}: {str(e)}"
                    )
                ],
                is_error=True
            )


# ============================================================================
# MCP Server Setup
# ============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available CognOS tools."""
    return [
        VERIFY_OUTPUT_TOOL,
        GET_TRACE_TOOL,
        CREATE_REPORT_TOOL,
        HEALTHZ_TOOL,
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> ToolResult:
    """Route tool calls to implementations."""

    if name == "verify_output":
        return await verify_output(
            content=arguments.get("content", ""),
            mode=arguments.get("mode", "monitor"),
            model=arguments.get("model", "gpt-4o-mini"),
            target_risk=arguments.get("target_risk", 0.1),
        )

    elif name == "get_trace":
        return await get_trace(
            trace_id=arguments.get("trace_id", "")
        )

    elif name == "create_trust_report":
        return await create_trust_report(
            trace_ids=arguments.get("trace_ids", []),
            regime=arguments.get("regime", "DEFAULT"),
            format=arguments.get("format", "json")
        )

    elif name == "healthz":
        return await healthz()

    else:
        return ToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )
            ],
            is_error=True
        )


async def main():
    """Run MCP server."""
    print(f"🔐 CognOS MCP Server starting...")
    print(f"   Gateway: {COGNOS_BASE_URL}")
    print(f"   Tools: verify_output, get_trace, create_trust_report, healthz")

    async with server:
        await server.wait()


if __name__ == "__main__":
    asyncio.run(main())
