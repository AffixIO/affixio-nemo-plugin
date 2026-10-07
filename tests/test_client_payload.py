from affixio_nemo.client import AffixIOClient
from affixio_nemo.models import AffixClientConfig, GuardRequest
from pydantic import SecretStr


def test_payload_keeps_tool_context() -> None:
    client = AffixIOClient(AffixClientConfig(api_key=SecretStr("aio_test"), audit=False))
    payload = client._payload(
        GuardRequest(
            agent_id="agent-1",
            tool_name="customer_lookup",
            tool_input={"customer_id": "cus_1"},
            workflow_run_id="run-1",
            user_id="user-1",
        ),
        policy={"allowed_tools": ["customer_lookup"]},
        context={"environment": "test"},
    )
    assert payload["agent"]["id"] == "agent-1"
    assert payload["action"]["tool"] == "customer_lookup"
    assert payload["action"]["metadata"]["tool_input"] == {"customer_id": "cus_1"}
    assert payload["policy"]["allowed_tools"] == ["customer_lookup"]
    assert payload["context"]["environment"] == "test"
