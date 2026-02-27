"""CognOS SDK — Trust verification for LLM applications."""

from __future__ import annotations

import httpx
from dataclasses import dataclass
from typing import Any, Optional


__version__ = "0.1.0"
__author__ = "Base76 Research Lab"
__email__ = "hello@base76.se"


@dataclass
class CognosSignals:
    """Risk signals from CognOS evaluation."""
    ue: float  # Semantic uncertainty
    ua: float  # Aleatoric uncertainty
    divergence: float  # Model divergence
    citation_density: float  # Citation strength
    contradiction: float  # Internal contradiction
    out_of_distribution: float  # OOD detection


@dataclass
class CognosEnvelope:
    """Trust verification envelope from CognOS gateway."""
    decision: str  # "PASS" | "REFINE" | "ESCALATE" | "BLOCK"
    risk: float  # 0.0–1.0
    trace_id: str
    policy: str
    signals: CognosSignals


@dataclass
class ChatChoice:
    """Single choice from chat completion."""
    index: int
    message: dict[str, str]
    finish_reason: str


@dataclass
class ChatResponse:
    """Response from CognOS-proxied chat completion."""
    id: str
    choices: list[ChatChoice]
    cognos: CognosEnvelope
    usage: dict[str, int]
    raw_response: dict[str, Any]  # Full upstream response


class CognosClient:
    """Client for CognOS trust verification gateway."""

    def __init__(
        self,
        base_url: str = "http://localhost:8788",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize CognOS client.

        Args:
            base_url: CognOS gateway URL (default: http://localhost:8788)
            api_key: Optional API key for authenticated access
            timeout: Request timeout in seconds (default: 30)

        Example:
            ```python
            client = CognosClient()
            response = client.chat(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}]
            )
            print(response.cognos.decision)  # "PASS"
            ```
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        mode: str = "monitor",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatResponse:
        """
        Call LLM through CognOS gateway.

        Args:
            model: Model ID (e.g., "gpt-4o-mini", "claude:claude-3-sonnet")
                   Supports prefixes: "openai:", "google:", "claude:", "mistral:", "ollama:"
            messages: List of chat messages with "role" and "content"
            mode: "monitor" (always pass) or "enforce" (apply policies)
            temperature: Sampling temperature (0.0–2.0)
            max_tokens: Maximum tokens to generate
            stream: Enable streaming (not fully supported yet)
            **kwargs: Additional parameters (top_p, frequency_penalty, etc.)

        Returns:
            ChatResponse with cognos envelope containing decision, risk, trace_id

        Raises:
            httpx.HTTPError: If upstream request fails
            ValueError: If response format is invalid

        Example:
            ```python
            response = client.chat(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "What is 2+2?"}],
                mode="enforce",
                temperature=0.7
            )
            if response.cognos.decision == "PASS":
                print(f"AI Response: {response.choices[0].message['content']}")
            elif response.cognos.decision == "ESCALATE":
                print("Risk detected. Human review required.")
            ```
        """
        headers = self._build_headers()

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "cognos": {
                "mode": mode,
                "policy_id": "default_v1",
            },
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stream:
            payload["stream"] = stream

        payload.update(kwargs)

        try:
            response = self._client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"CognOS request failed: {e}")

        data = response.json()
        return self._parse_response(data)

    def get_trace(self, trace_id: str) -> dict[str, Any]:
        """
        Retrieve full trace record for a request.

        Args:
            trace_id: Trace ID from ChatResponse.cognos.trace_id

        Returns:
            Dictionary with complete trace data (decision, fingerprints, signals, etc.)

        Example:
            ```python
            response = client.chat(...)
            trace = client.get_trace(response.cognos.trace_id)
            print(f"Trust Score: {trace['trust_score']}")
            print(f"Risk Level: {trace['risk']}")
            ```
        """
        headers = self._build_headers()
        try:
            response = self._client.get(
                f"{self.base_url}/v1/traces/{trace_id}",
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"Failed to retrieve trace {trace_id}: {e}")

        return response.json()

    def create_trust_report(
        self,
        trace_ids: list[str],
        regime: str = "DEFAULT",
        fmt: str = "json",
    ) -> dict[str, Any]:
        """
        Generate trust report from multiple traces.

        Args:
            trace_ids: List of trace IDs to include in report
            regime: Compliance regime ("EU_AI_ACT", "GDPR", "SOC2", "DEFAULT")
            fmt: Report format ("json", "csv", "pdf")

        Returns:
            Dictionary with report_id, summary, decision breakdown

        Example:
            ```python
            report = client.create_trust_report(
                trace_ids=["tr_xxx", "tr_yyy"],
                regime="EU_AI_ACT"
            )
            print(f"Found {report['summary']['found_count']} traces")
            print(f"Decisions: {report['summary']['decision_breakdown']}")
            ```
        """
        headers = self._build_headers()
        payload = {
            "trace_ids": trace_ids,
            "regime": regime,
            "format": fmt,
        }

        try:
            response = self._client.post(
                f"{self.base_url}/v1/reports/trust",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"Failed to create trust report: {e}")

        return response.json()

    def healthz(self) -> dict[str, str]:
        """
        Check if CognOS gateway is healthy.

        Returns:
            Dictionary with status and service name

        Example:
            ```python
            if client.healthz()['status'] == 'ok':
                print("Gateway is ready")
            ```
        """
        try:
            response = self._client.get(f"{self.base_url}/healthz")
            response.raise_for_status()
        except httpx.HTTPError:
            return {"status": "error", "service": "operational-cognos-gateway"}

        return response.json()

    def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        self._client.close()

    def __enter__(self) -> CognosClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with optional API key."""
        headers: dict[str, str] = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def _parse_response(self, data: dict[str, Any]) -> ChatResponse:
        """Parse upstream response into ChatResponse."""
        if "error" in data:
            raise ValueError(f"Upstream error: {data['error']}")

        cognos_data = data.get("cognos", {})
        signals_data = cognos_data.get("signals", {})

        signals = CognosSignals(
            ue=signals_data.get("ue", 0.0),
            ua=signals_data.get("ua", 0.0),
            divergence=signals_data.get("divergence", 0.0),
            citation_density=signals_data.get("citation_density", 0.0),
            contradiction=signals_data.get("contradiction", 0.0),
            out_of_distribution=signals_data.get("out_of_distribution", 0.0),
        )

        envelope = CognosEnvelope(
            decision=cognos_data.get("decision", "UNKNOWN"),
            risk=cognos_data.get("risk", 0.0),
            trace_id=cognos_data.get("trace_id", ""),
            policy=cognos_data.get("policy", "default_v1"),
            signals=signals,
        )

        choices = [
            ChatChoice(
                index=c.get("index", 0),
                message=c.get("message", {}),
                finish_reason=c.get("finish_reason", ""),
            )
            for c in data.get("choices", [])
        ]

        return ChatResponse(
            id=data.get("id", ""),
            choices=choices,
            cognos=envelope,
            usage=data.get("usage", {"total_tokens": 0}),
            raw_response=data,
        )


__all__ = [
    "CognosClient",
    "ChatResponse",
    "ChatChoice",
    "CognosEnvelope",
    "CognosSignals",
]
