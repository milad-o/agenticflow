# Security & Policy (Local)

This document explains local validation and policy guardrails and how to use them in examples or your own scripts.

## Components

- TaskSchemaRegistry
  - Register per agent:task schemas (JSON Schema if installed, fallback to required-only check).
  - Enforced before task assignment; rejects invalid params with `task_validation_failed` event and, if lifecycle is enabled, a `workflow_failed` event.
  - When using `jsonschema`, errors include a path and message; for missing required properties a hint is appended (e.g., `hint: add 'foo' to params`).

- PolicyGuard
  - Simple allow/deny lists per agent for task types.
  - Deny takes precedence; if neither list provided for an agent, `default_allow` applies.
  - Enforced before assignment; rejects with `task_policy_denied` and a `workflow_failed` if lifecycle is enabled.

## Dev-only policy loader

For convenience in examples, a loader is provided under `examples/utils/policy_loader.py` that can read YAML or JSON files and return a `(TaskSchemaRegistry, PolicyGuard)` pair.

Example YAML (`examples/policy_profiles/local_default.yaml`):

```yaml
schemas:
  "reader:fs_read":
    type: object
    properties:
      path: {type: string}
    required: [path]
policy:
  allow_agent_tasks:
    reader: [fs_read]
    processor: [compute_stats]
    writer: [write_report]
  default_allow: false
```

## Usage in code

```python
from agenticflow.orchestration.core.orchestrator import Orchestrator
from examples.utils.policy_loader import load_policy

orch = Orchestrator(emit_workflow_started=True, emit_workflow_lifecycle=True)
loaded = load_policy("examples/policy_profiles/local_default.yaml")
if loaded.schema:
    orch.set_task_schema_registry(loaded.schema)
if loaded.guard:
    orch.set_policy_guard(loaded.guard)
```

## Troubleshooting validation errors

Here are common validation failures and how to fix them.

- Missing required property
  - Symptom: `'foo' is a required property` (hint appended: `hint: add 'foo' to params`)
  - Fix: Add the property to the params: `{"foo": 1}`

- Wrong type
  - Example schema: `{"type":"object","properties":{"foo":{"type":"number"}}}`
  - Symptom: `"bar" is not of type 'number' at 'foo'`
  - Fix: Provide a number: `{"foo": 42}`

- Additional properties
  - Example schema with `additionalProperties: false`
  - Symptom: `Additional properties are not allowed ('extra' was unexpected)`
  - Fix: Remove `extra` or add it to `properties`

If `jsonschema` is not installed, only `required` is enforced. Install `jsonschema` to enable full validation.

## Notes
- Keep loaders/dev helpers outside the framework package to avoid hard dependencies.
- Prefer provider-free and safe defaults; set `default_allow` to `false` and allowlist explicitly in hardened profiles.
- If `jsonschema` is not installed, only `required` keys are enforced by the fallback.
