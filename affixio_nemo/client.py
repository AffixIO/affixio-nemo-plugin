from __future__ import annotations

from typing import Any

import httpx

from .exceptions import AffixIOApiError
from .models import AffixClientConfig, AffixDecision, GuardRequest


class AffixIOClient:
    def __init__(self, config: AffixClientConfig):
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.api_base.rstrip("/"),
            timeout=config.timeout_seconds,
            headers={
                "X-API-Key": config.api_key.get_secret_value(),
                "Content-Type": "application/json",
                "User-Agent": "affixio-nemo-plugin/0.1.0",
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def decide_tool_call(
        self,
        request: GuardRequest,
        *,
        policy: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> AffixDecision:
        payload = self._payload(request, policy=policy, context=context)
        response = await self._client.post("/v1/sdk2/actions/decide", json=payload)
        data = self._json(response)
        if response.status_code >= 400 or data.get("ok") is False:
            raise AffixIOApiError(str(data.get("error") or "affixio_decision_failed"), status_code=response.status_code, response=data)
        return AffixDecision.model_validate(data)

    def _payload(self, request: GuardRequest, *, policy: dict[str, Any] | None, context: dict[str, Any] | None) -> dict[str, Any]:
        action = {
            "type": request.action_type,
            "resource": request.resource or request.tool_name,
            "tool": request.tool_name,
            "merchant": request.merchant,
            "recipient": request.recipient,
            "amount_minor": request.amount_minor,
            "currency": request.currency,
            "metadata": {
                "tool_input": request.tool_input,
                "workflow_run_id": request.workflow_run_id,
                "user_id": request.user_id,
                **request.metadata,
            },
        }
        return {
            "agent": {"id": request.agent_id, "type": "nemo_agent_toolkit"},
            "action": {k: v for k, v in action.items() if v is not None},
            "policy": policy or {},
            "context": context or {},
            "audit": self.config.audit,
            "request_attestation": self.config.request_attestation,
        }

    @staticmethod
    def _json(response: httpx.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise AffixIOApiError("affixio_invalid_json", status_code=response.status_code) from exc
        if not isinstance(data, dict):
            raise AffixIOApiError("affixio_unexpected_response", status_code=response.status_code, response=data)
        return data
