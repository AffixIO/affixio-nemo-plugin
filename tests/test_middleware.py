import asyncio

import pytest
from affixio_nemo.exceptions import AffixIOApiError, AffixIOToolBlocked
from affixio_nemo.middleware import AffixIONeMoGuard, AffixIONeMoGuardConfig
from affixio_nemo.models import AffixDecision
from pydantic import SecretStr


class DummyFunctionContext:
    name = "customer_lookup"


class DummyContext:
    def __init__(self):
        self.function_context = DummyFunctionContext()
        self.modified_args = ({"customer_id": "cus_1"},)
        self.modified_kwargs = {}
        self.metadata = {}


class DummyClient:
    def __init__(self, decision: str | None = None, *, raises: bool = False):
        self.decision = decision
        self.raises = raises
        self.requests = []

    async def aclose(self):
        return None

    async def decide_tool_call(self, request, *, policy, context):
        self.requests.append((request, policy, context))
        if self.raises:
            raise AffixIOApiError("api_down", status_code=503)
        return AffixDecision(decision=self.decision, allowed=self.decision == "yes", reason_codes=[])


async def invoke(decision: str | None = None, *, raises: bool = False, allow_review: bool = False, fail_closed: bool = True):
    guard = AffixIONeMoGuard(
        AffixIONeMoGuardConfig(api_key=SecretStr("aio_test"), allow_review=allow_review, fail_closed=fail_closed)
    )
    guard._client = DummyClient(decision, raises=raises)
    context = DummyContext()
    try:
        result = await guard.pre_invoke(context)
        return guard, result, context
    finally:
        await guard.aclose()


def test_yes_allows_tool() -> None:
    async def run() -> None:
        guard, result, context = await invoke("yes")
        assert result is context
        assert guard._client.requests[0][0].tool_name == "customer_lookup"

    asyncio.run(run())


def test_no_blocks_tool() -> None:
    async def run() -> None:
        with pytest.raises(AffixIOToolBlocked):
            await invoke("no")

    asyncio.run(run())


def test_review_blocks_by_default() -> None:
    async def run() -> None:
        with pytest.raises(AffixIOToolBlocked):
            await invoke("review")

    asyncio.run(run())


def test_review_can_be_allowed_when_configured() -> None:
    async def run() -> None:
        _, result, context = await invoke("review", allow_review=True)
        assert result is context

    asyncio.run(run())


def test_api_failure_fails_closed() -> None:
    async def run() -> None:
        with pytest.raises(AffixIOApiError):
            await invoke(raises=True)

    asyncio.run(run())


def test_api_failure_can_fail_open_when_configured() -> None:
    async def run() -> None:
        _, result, _ = await invoke(raises=True, fail_closed=False)
        assert result is None

    asyncio.run(run())
