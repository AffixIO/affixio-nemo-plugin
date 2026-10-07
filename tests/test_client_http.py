import asyncio

import pytest
from affixio_nemo.client import AffixIOClient
from affixio_nemo.exceptions import AffixIOApiError
from affixio_nemo.models import AffixClientConfig, GuardRequest
from httpx import AsyncClient, MockTransport, Request, Response
from pydantic import SecretStr


def make_client(handler):
    client = AffixIOClient(AffixClientConfig(api_key=SecretStr("aio_test"), audit=False, request_attestation=False))
    client._client = AsyncClient(base_url="https://api.affix-io.com", transport=MockTransport(handler), headers={"X-API-Key": "aio_test", "Content-Type": "application/json"})
    return client


def test_client_sends_api_key_and_payload() -> None:
    async def run() -> None:
        seen = {}

        def handler(request: Request) -> Response:
            seen["path"] = request.url.path
            seen["api_key"] = request.headers.get("x-api-key")
            seen["payload"] = request.read().decode()
            return Response(200, json={"ok": True, "decision": "yes", "allowed": True, "reason_codes": []})

        client = make_client(handler)
        try:
            decision = await client.decide_tool_call(
                GuardRequest(agent_id="agent-1", tool_name="safe_tool", tool_input={"id": "1"}),
                policy={"allowed_tools": ["safe_tool"]},
                context={"case": "unit"},
            )
        finally:
            await client.aclose()

        assert decision.should_execute is True
        assert seen["path"] == "/v1/sdk2/actions/decide"
        assert seen["api_key"] == "aio_test"
        assert "safe_tool" in seen["payload"]

    asyncio.run(run())


def test_client_raises_on_api_error() -> None:
    async def run() -> None:
        def handler(request: Request) -> Response:
            return Response(403, json={"ok": False, "error": "invalid_api_key"})

        client = make_client(handler)
        try:
            with pytest.raises(AffixIOApiError) as exc:
                await client.decide_tool_call(GuardRequest(agent_id="agent-1", tool_name="safe_tool"))
        finally:
            await client.aclose()

        assert exc.value.status_code == 403
        assert "invalid_api_key" in str(exc.value)

    asyncio.run(run())


def test_client_raises_on_invalid_json() -> None:
    async def run() -> None:
        def handler(request: Request) -> Response:
            return Response(200, content=b"not-json")

        client = make_client(handler)
        try:
            with pytest.raises(AffixIOApiError) as exc:
                await client.decide_tool_call(GuardRequest(agent_id="agent-1", tool_name="safe_tool"))
        finally:
            await client.aclose()

        assert "affixio_invalid_json" in str(exc.value)

    asyncio.run(run())
