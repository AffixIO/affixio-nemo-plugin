from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr

DecisionValue = Literal["yes", "no", "review"]


class AffixDecision(BaseModel):
    model_config = ConfigDict(extra="allow")

    ok: bool = True
    decision: DecisionValue
    allowed: bool
    reason_codes: list[str] = Field(default_factory=list)
    digest: str | None = None
    proof_ref: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    attestation: dict[str, Any] | None = None
    merkle: dict[str, Any] | None = None

    @property
    def should_execute(self) -> bool:
        return self.allowed and self.decision == "yes"


class GuardRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    agent_id: str
    tool_name: str
    tool_input: Any = None
    workflow_run_id: str | None = None
    user_id: str | None = None
    action_type: str = "nemo_tool_call"
    resource: str | None = None
    merchant: str | None = None
    recipient: str | None = None
    amount_minor: int | None = None
    currency: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AffixClientConfig(BaseModel):
    api_key: SecretStr
    api_base: str = "https://api.affix-io.com"
    timeout_seconds: float = Field(default=8.0, gt=0)
    audit: bool = True
    request_attestation: bool = True
    sdk_version: str = "2.0.0-beta.1"
