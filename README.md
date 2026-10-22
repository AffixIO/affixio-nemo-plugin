
# AffixIO NeMo Plugin

AffixIO NeMo Plugin lets a NVIDIA NeMo Agent Toolkit workflow ask the AffixIO API whether an agent tool call should run before the tool executes.

```text
NeMo Agent Toolkit → AffixIO NeMo Plugin → AffixIO API → ALLOW / DENY / REVIEW → Execute or block tool
```

Built for teams developing agentic systems where tool access requires policy enforcement, verifiable evidence and auditability rather than blind execution.

## Why It Exists

AI agents are moving beyond conversations into real-world actions.

They look up customers, update tickets, call APIs, run workflows, request refunds and trigger paid tools.

The challenge isn't simply choosing the correct tool. It's determining whether an agent should be permitted to execute that tool, for a particular user, with particular inputs, at a particular moment.

AffixIO NeMo Plugin provides a host-side decision layer:

- **ALLOW:** Permits the tool to execute.
- **DENY:** Blocks the tool before execution.
- **REVIEW:** Blocks execution by default unless a separate human approval mechanism is implemented.
- **Fail-closed:** API failures block execution when `fail_closed: true`.
- **Evidence:** Decision requests can include attestation and audit preferences.

The plugin uses AffixIO's remote decision API. It does not replace NeMo Agent Toolkit's existing authentication, security controls or workflow management.

## Installation

### Requirements

- Python 3.11, 3.12 or 3.13
- An AffixIO API key
- Network access to the AffixIO API

The plugin declares `nvidia-nat-core>=1.5,<2` as a required dependency. It is installed automatically when installing the plugin from the updated project configuration.

### Install the plugin

```bash
pip install affixio-nemo-plugin
```

**Note:** Until a new package version containing the dependency changes is published to PyPI, the command above may install the older package metadata.

To install the latest repository version:

```bash
pip install git+https://github.com/AffixIO/affixio-nemo-plugin.git
```

### Local development

Clone the repository:

```bash
git clone https://github.com/AffixIO/affixio-nemo-plugin.git
cd affixio-nemo-plugin
```

Install the plugin and development dependencies:

```bash
pip install -e ".[dev]"
```

### Configure your API key

Set the environment variable:

```bash
export AFFIXIO_API_KEY="aio_..."
```

Do not hardcode production API keys in source files, prompts or public repositories.

## Quick Start

Example configuration showing the intended AffixIO guard placement:

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

This example illustrates the intended configuration. Replace the example tool names with actual registered NeMo functions and validate the configuration against the installed toolkit version.

## Decision Flow

When a protected tool is called, the intended flow is:

1. The NeMo workflow requests a tool execution.
2. The AffixIO plugin receives the relevant tool-call context.
3. The plugin sends a decision request to the AffixIO API.
4. AffixIO evaluates the request against the supplied policy context.
5. The plugin interprets the returned decision.
6. The tool executes only when the decision permits execution.

### Decision outcomes

| Decision | Behaviour |
| --- | --- |
| `ALLOW` | Tool execution is permitted. |
| `DENY` | Tool execution is blocked. |
| `REVIEW` | Tool execution is blocked by default pending a separately implemented approval process. |
| API error | Execution is blocked when `fail_closed: true`. |

## What Gets Sent to AffixIO

The plugin sends structured decision requests to:

```http
POST https://api.affix-io.com/v1/sdk2/actions/decide
```

Depending on the available workflow context and configuration, requests can include:

- NeMo agent ID
- Tool name
- Tool input payload
- Workflow run ID, when available
- User ID, when available
- Policy context
- Request context
- Attestation preferences
- Audit preferences

The AffixIO API returns a decision that the plugin uses to determine whether execution should proceed.

Only send the information required to evaluate the decision. Avoid including unnecessary personal information, credentials or sensitive data in tool inputs.

## Python API

The plugin also exposes a Python client for requesting AffixIO decisions.

```python
from affixio_nemo import AffixIOClient, GuardRequest
from affixio_nemo.models import AffixClientConfig
from pydantic import SecretStr
import os

client = AffixIOClient(
    AffixClientConfig(
        api_key=SecretStr(os.environ["AFFIXIO_API_KEY"])
    )
)

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
    # Execute the approved tool here.
    pass
else:
    # Do not execute the tool.
    pass
```

The example assumes execution inside an asynchronous Python function or environment.

## Safety Defaults

The plugin is designed to support conservative enforcement behaviour.

| Setting | Default | Purpose |
| --- | --- | --- |
| `fail_closed` | `true` | Blocks tool execution when decision requests fail. |
| `allow_review` | `false` | Prevents review outcomes from automatically executing tools. |
| `request_attestation` | `true` | Requests decision evidence where supported. |
| `audit` | `true` | Includes decision requests in the configured audit path. |

### Important security considerations

- Keep API keys in environment variables or an appropriate secret manager.
- Never expose API credentials through prompts or tool arguments.
- Treat agent-generated tool inputs as untrusted.
- Validate authorization before performing protected actions.
- Avoid automatically converting `REVIEW` decisions into permission to execute.
- Test failure behaviour before production deployment.
- Use least-privilege policies for tools and workflows.

## NeMo Plugin Registration

The package declares a NeMo Agent Toolkit plugin entry point in `pyproject.toml`:

```toml
[project.entry-points."nat.plugins"]
affixio_nemo = "affixio_nemo.register"
```

The entry point allows compatible NeMo Agent Toolkit installations to discover the plugin through Python package metadata.

## Testing

Install the development dependencies before running the tests:

```bash
pip install -e ".[dev]"
```

Run the test suite:

```bash
python -m pytest tests -q
```

Previously reported local test result:

```text
15 passed
```

This result predates the latest dependency changes. Installation, plugin discovery and compatibility tests must be rerun against the updated configuration.

## Building

Build the Python package:

```bash
python -m build
```

Validate the generated distribution:

```bash
python -m twine check dist/*
```

Before publishing, verify that the built package contains the correct dependency metadata and plugin entry point.

## Security

The AffixIO NeMo Plugin uses remote AffixIO API decisions rather than running a local policy engine.

It is intended to provide an additional authorization decision point for protected tool calls.

It does not independently guarantee the security of an entire agent workflow, and its enforcement depends on correct integration with the host application.

Do not place AffixIO API keys in:

- Prompts
- Public repositories
- Notebooks shared with third parties
- Browser-side code
- Application logs

To report a security vulnerability, email:

**hello@affix-io.com**

Subject:

`Security: affixio-nemo-plugin`

Please avoid publicly disclosing exploitable vulnerabilities before they can be investigated.

## Project Links

- **AffixIO:** https://www.affix-io.com/
- **Documentation:** https://www.affix-io.com/docs/
- **API capabilities:** https://api.affix-io.com/v1/sdk2/capabilities
- **Source repository:** https://github.com/AffixIO/affixio-nemo-plugin
- **PyPI package:** https://pypi.org/project/affixio-nemo-plugin/
- **NVIDIA NeMo Agent Toolkit:** https://github.com/NVIDIA/NeMo-Agent-Toolkit
- **NVIDIA integration discussion:** https://github.com/NVIDIA/NeMo-Agent-Toolkit/issues/2427

## License

Apache-2.0
