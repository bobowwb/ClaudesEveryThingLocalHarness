# Pattern 01 — oTel (Observability) layer

> Reference distilled from `C:\EPM_ACCUMULATION\appFnd\app\observability.py`.
> **Idea, not code.** To be re-implemented in Forge in its own way.

## Core idea

Every agent invocation produces a **trace tree**, persisted to a local SQLite store, fully reconstructible from `(root_log_id, step_index)`.

```
User prompt
    │
    ▼
start_trace()  ─►  root LogRecord (parent_log_id = NULL, step_index = 0)
    │
    ├─► add_step(parent=root, name="classify_intent")     step_index=1
    │       └─► add_step(parent=above, name="llm_call")   step_index=2
    │              └─► finish_step(SUCCESS|ERROR, output, error)
    │
    ├─► add_step(parent=root, name="sql_compose")         step_index=3
    │       └─► add_step(parent=above, name="db_execute") step_index=4
    │
    └─► add_step(parent=root, name="rank_results")        step_index=5
```

## Schema (the 30 fields that matter)

| Field group | Fields |
|---|---|
| **Identity** | `log_id` (uuid PK), `correlation_id` (8-char shared across whole trace), `parent_log_id`, `root_log_id`, `session_id`, `step_index` |
| **Agent** | `agent_id`, `agent_version`, `agent_type` (orchestrator / tool / sub-agent), `scenario_id`, `scenario_name`, `function_name` |
| **Trigger** | `trigger_type` (user_message / agent_call), `triggered_by`, `user_prompt`, `input_params` (JSON) |
| **Time** | `start_ts`, `end_ts`, `duration_ms` |
| **Routing** | `selected_scenario`, `selected_function`, `call_path` (JSON array — full breadcrumb) |
| **Network** | `direction` (inbound/outbound), `action_called`, `api_endpoint`, `protocol` (Joule / A2A / HTTP / tool / DB) |
| **Payload** | `request_payload` (redacted JSON), `response_status`, `response_payload` (redacted JSON), `retry_count` |
| **Status** | `execution_status` (SUCCESS / ERROR / PARTIAL / RUNNING / TIMEOUT / SKIPPED), `output_result`, `error_code`, `error_message` |
| **Tenant** | `tenant_id`, `created_at` |

## Three required helpers

```python
start_trace(user_prompt, scenario_id, scenario_name, session_id, input_params) -> LogRecord
add_step(parent, step_name, function_name, action_called, protocol, direction, request_payload) -> LogRecord
finish_step(rec, status, output, error) -> None
```

## Three retrieval helpers

```python
get_trace(root_log_id) -> list[dict]      # full ordered chain for replay
list_recent_traces(limit=20) -> list[dict] # dashboard feed
```

## Redaction rule (security)

A recursive `_redact()` walks dicts/lists up to depth 6 and replaces values for keys in:
```
{authorization, x-authorization, token, access_token, client_secret,
 password, passwd, pwd, cookie, credential, key, secret}
```
with `***REDACTED***`. **Always pre-redact before JSON-serializing into request/response_payload.**

## Storage decisions

- SQLite, single file at `<project>/devlog/observe.db`
- Schema auto-init at module import time (`_ensure_schema()`)
- Three indexes: `idx_root` on `root_log_id`, `idx_corr` on `correlation_id`, `idx_sess` on `session_id`
- `INSERT OR REPLACE` on save (idempotent — calling save twice on same `log_id` updates not duplicates)
- All saves wrapped in try/except → log warning, never raise (observability must NEVER break the agent)

## Why this design works

| Property | How it's achieved |
|---|---|
| **Replay any session** | `get_trace(root_log_id)` returns ordered tree |
| **Cross-session correlation** | `correlation_id` is shared by root + all children |
| **Privacy-safe** | `_redact()` strips secrets before write |
| **Crash-safe** | observability errors are swallowed, never block agent |
| **Cheap** | local SQLite, no network |
| **Hot-introspectable** | `list_recent_traces()` powers a live dashboard feed |

## Forge mapping

The Forge dashboard already has the **UI scaffolding** for oTel: `TraceID`, scan-line animation, A2A Studio agent rows. What's missing is the backing store. Drop a `forge_observability.py` modeled on this pattern, then:

- `#traceId` ← reads `root_log_id`
- `#orchestratorMsg` ← reads root's latest child's `scenario_name` + `execution_status`
- `#orchScan` (animation) ← visible while any child has `execution_status='RUNNING'`
- agent rows (WR/EN/CH/LI/AU/ED) ← each gets its own step record; row colour = `execution_status`
- `#telemetryLog` ← polls `list_recent_traces()` or reads root's `call_path` live

## Don't over-design

- No remote OTLP collector required for v1 — local SQLite is enough
- No need for distributed tracing across processes for Forge yet
- The `protocol` field is enough granularity; don't add MORE columns
- Resist adding "trace_flags", "trace_state", "baggage" until a real consumer needs them
