from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CognosControl(BaseModel):
    mode: Literal["monitor", "enforce"] = "monitor"
    policy_id: str = "default_v1"
    target_risk: float | None = Field(default=None, ge=0.0, le=1.0)
    shadow_pct: float = Field(default=0.0, ge=0.0, le=1.0)
    shadow_models: list[str] = Field(default_factory=list)
    retention: Literal["none", "fingerprints", "enhanced"] = "fingerprints"


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool | None = None
    cognos: CognosControl = Field(default_factory=CognosControl)


class Choice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class Fingerprint(BaseModel):
    simhash: str
    embedding_hash: str
    length: int
    model_id: str | None = None
    cluster_id: str | None = None


class Attestation(BaseModel):
    hash: str
    signed_by: str
    ts: datetime
    signature: str | None = None


class SignalVector(BaseModel):
    ue: float = Field(ge=0.0, le=1.0)
    ua: float = Field(ge=0.0, le=1.0)
    divergence: float = Field(ge=0.0, le=1.0)
    citation_density: float = Field(ge=0.0, le=1.0)
    contradiction: float = Field(ge=0.0, le=1.0)
    out_of_distribution: float = Field(ge=0.0, le=1.0)


class ShadowResult(BaseModel):
    enabled: bool
    compared_models: list[str] = Field(default_factory=list)
    divergence: float = Field(ge=0.0, le=1.0)
    note: str | None = None


class CognosEnvelope(BaseModel):
    decision: Literal["PASS", "REFINE", "ESCALATE", "BLOCK"]
    risk: float = Field(ge=0.0, le=1.0)
    signals: SignalVector
    trace_id: str
    policy: str
    attestation: Attestation
    shadow: ShadowResult | None = None


class TraceRecord(BaseModel):
    trace_id: str
    created: datetime
    request_fingerprint: Fingerprint
    response_fingerprint: Fingerprint
    envelope: CognosEnvelope
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    choices: list[Choice]
    usage: Usage | None = None
    cognos: CognosEnvelope


class TrustReportRequest(BaseModel):
    trace_ids: list[str]
    regime: str
    format: Literal["json", "pdf"] = "json"


class TrustReportResponse(BaseModel):
    report_id: str
    created: datetime
    regime: str
    summary: dict[str, Any]
