from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field, SecretStr

from .client import AffixIOClient
from .exceptions import AffixIOApiError, AffixIOConfigurationError, AffixIOToolBlocked
from .models import AffixClientConfig, GuardRequest

try:
    from nat.plugin_api import DynamicFunctionMiddleware, DynamicMiddlewareConfig
except ImportError:
    DynamicFunctionMiddleware = object

    class DynamicMiddlewareConfig(BaseModel):
        def __init_subclass__(cls, **kwargs: Any):
            super().__init_subclass__()


class AffixIONeMoGuardConfig(DynamicMiddlewareConfig, name="affixio_guard"):
    api_key: SecretStr | None = Field(default=None)
    api_key_env: str = Field(default="AFFIXIO_API_KEY")
    api_base: str = Field(default="https://api.affix-io.com")
    agent_id: str = Field(default="nemo-agent")
    timeout_seconds: float = Field(default=8.0, gt=0)
    fail_closed: bool = Field(default=True)
    allow_review: bool = Field(default=False)
    audit: bool = Field(default=True)
    request_attestation: bool = Field(default=True)
    action_type: str = Field(default="nemo_tool_call")
    policy: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class AffixIONeMoGuard(DynamicFunctionMiddleware):
    def __init__(self, config: AffixIONeMoGuardConfig, builder: Any | None = None):
        super().__init__()
        self._config = config
        self._builder = builder
        self._client = AffixIOClient(self._client_config(config))

    async def aclose(self) -> None:
        await self._client.aclose()

    async def pre_invoke(self, context: Any) -> Any | None:
        tool_name = self._tool_name(context)
        tool_input = self._tool_input(context)
        guard_request = GuardRequest(
            agent_id=self._config.agent_id,
            tool_name=tool_name,
            tool_input=tool_input,
            workflow_run_id=self._context_value("workflow_run_id"),
            user_id=self._context_value("user_id"),
            action_type=self._config.action_type,
            resource=tool_name,
            metadata={"middleware": "affixio_guard"},
        )
        try:
            decision = await self._client.decide_tool_call(guard_request, policy=self._config.policy, context=self._config.context)
        except AffixIOApiError:
            if self._config.fail_closed:
                raise
            return None
        if decision.should_execute or (self._config.allow_review and decision.decision == "review"):
            self._attach_decision(context, decision.model_dump(mode="json"))
            return context
        raise AffixIOToolBlocked(decision.model_dump(mode="json"))

    @staticmethod
    def _client_config(config: AffixIONeMoGuardConfig) -> AffixClientConfig:
        key = config.api_key.get_secret_value() if config.api_key else os.getenv(config.api_key_env)
        if not key:
            raise AffixIOConfigurationError("AffixIO API key is required")
        return AffixClientConfig(api_key=SecretStr(key), api_base=config.api_base, timeout_seconds=config.timeout_seconds, audit=config.audit, request_attestation=config.request_attestation)

    @staticmethod
    def _tool_name(context: Any) -> str:
        function_context = getattr(context, "function_context", None)
        name = getattr(function_context, "name", None)
        return str(name or "nemo_tool")

    @staticmethod
    def _tool_input(context: Any) -> Any:
        args = getattr(context, "modified_args", None)
        kwargs = getattr(context, "modified_kwargs", None)
        if args and kwargs:
            return {"args": list(args), "kwargs": dict(kwargs)}
        if args:
            return args[0] if len(args) == 1 else list(args)
        if kwargs:
            return dict(kwargs)
        return None

    @staticmethod
    def _context_value(name: str) -> str | None:
        try:
            from nat.plugin_api import Context

            value = getattr(Context.get(), name, None)
        except (AttributeError, ImportError, LookupError, RuntimeError):
            value = None
        return str(value) if value is not None else None

    @staticmethod
    def _attach_decision(context: Any, decision: dict[str, Any]) -> None:
        metadata = getattr(context, "metadata", None)
        if isinstance(metadata, dict):
            metadata["affixio_decision"] = decision
