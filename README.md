

AffixIO NeMo Plugin lets a NeMo workflow ask the AffixIO API whether an agent tool call should run before the tool executes.

```text
NeMo Agent Toolkit -> AffixIO NeMo plugin -> AffixIO API -> ALLOW / DENY / REVIEW -> tool executes or is blocked
```

This is for teams building agentic systems where tool access needs policy, evidence and auditability instead of blind execution.

## Why It Exists

Agents are moving from chat into actions. They look up customers, update tickets, call APIs, run workflows, request refunds and trigger paid tools. The hard part is not only choosing the right tool. The hard part is proving the agent should be allowed to use that tool for this user, with this input, right now.

AffixIO NeMo Plugin gives NeMo builders a small enforcement layer:

- `ALLOW` lets the tool run.
- `DENY` blocks the tool.
- `REVIEW` blocks by default unless you wire a separate human approval layer.
- API failure blocks by default through `fail_closed: true`.
- Decision context can request AffixIO attestation and audit data.

## Install

```bash
pip install affixio-nemo-plugin
```

For a NeMo Agent Toolkit environment:

```bash
pip install "affixio-nemo-plugin[nemo]"
```

For local development from source:

```bash
pip install -e ".[dev]"
```

Set your AffixIO API key:

```bash
export AFFIXIO_API_KEY="aio_..."
```

## Quick Start

```yaml
middleware:
  affixio_gate:
    _type: affixio_guard
    api_key_env: AFFIXIO_API_KEY
    api_base: https://api.affix-io.com
    agent_id: nvidia-nemo-agent
    fail_closed: true
    allow_review: false
    audit: true
    request_attestation: true
    register_workflow_functions: true
    policy:
      allowed_actions:
        - nemo_tool_call
      allowed_tools:
        - approved_customer_lookup
        - approved_ticket_update

functions:
  approved_customer_lookup:
    _type: customer_lookup
    middleware:
      - affixio_gate
```

## What Gets Sent To AffixIO

For every protected tool call, the plugin sends a structured decision request to:

```text
POST https://api.affix-io.com/v1/sdk2/actions/decide
```

The request can include:

- NeMo agent id
- tool name
- tool input payload
- workflow run id when available
- user id when available
- policy context
- request context
- attestation and audit preferences

AffixIO returns the decision used by the plugin to execute or block the tool.

## Python API

```python
from affixio_nemo import AffixIOClient, GuardRequest
from affixio_nemo.models import AffixClientConfig
from pydantic import SecretStr

client = AffixIOClient(AffixClientConfig(api_key=SecretStr("aio_...")))

decision = await client.decide_tool_call(
    GuardRequest(
        agent_id="nemo-agent",
        tool_name="approved_customer_lookup",
        tool_input={"customer_id": "cus_123"},
    ),
    policy={
        "allowed_actions": ["nemo_tool_call"],
        "allowed_tools": ["approved_customer_lookup"],
    },
)

if decision.should_execute:
    pass
```

## Safety Defaults

The plugin is intentionally conservative.

| Setting | Default | Why it matters |
| --- | --- | --- |
| `fail_closed` | `true` | API errors block execution instead of silently allowing tools. |
| `allow_review` | `false` | Review outcomes do not execute unless you add a separate approval layer. |
| `request_attestation` | `true` | AffixIO can return signed decision evidence where enabled. |
| `audit` | `true` | Decision calls can be included in the audit path. |

## NeMo Plugin Entry Point

The package registers itself through:

```toml
[project.entry-points."nat.plugins"]
affixio_nemo = "affixio_nemo.register"
```

## Test

```bash
python -m pytest tests -q
```

Current local package test status: `15 passed`.

## Build

```bash
python -m build
python -m twine check dist/*
```

## Security

Do not put AffixIO API keys in prompts, notebooks, logs or browser code. Use environment variables or NeMo configuration secrets.

The plugin does not run a local policy engine. It uses AffixIO API decisions, forwards only the tool-call context needed for a decision, and fails closed unless configured otherwise.

To report a vulnerability, email `hello@affix-io.com` with the subject `Security: affixio-nemo-plugin`.

## Links

- AffixIO: https://www.affix-io.com/
- Docs: https://www.affix-io.com/docs/
- API capabilities: https://api.affix-io.com/v1/sdk2/capabilities
- PyPI package: https://pypi.org/project/affixio-nemo-plugin/

## License

Apache-2.0
