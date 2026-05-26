# Pattern 02 — Agent Armor wrapper

> Reference distilled from `C:\EPM_ACCUMULATION\appFnd\app\ltm_armored.py` + `app\agent_armor.py`.
> **Idea, not code.** To be re-implemented in Forge in its own way.

## Core idea

Every tool call goes through a **standard pipeline of safety checks** before reaching the actual handler. The orchestrator never calls a tool directly — it always goes through the armor.

```
caller.tool(params)
   │
   ▼
AgentArmor.execute(tool_name, params)
   │
   ├─► L1: VALIDATE       — schema check, required params, type check
   ├─► L2: PERMIT         — risk level + permission check (LOW auto / MEDIUM confirm / HIGH block)
   ├─► L3: EXECUTE        — call dispatch handler with retry + timeout + circuit breaker
   └─► L4: REFLECT        — record (params, result, latency, success) to ReflectionMemory
                            + emit OTel span
   ▼
ArmorResult { success, output, error, latency_ms, retry_count }
```

## ToolSchema — declare each tool's contract

```python
ToolSchema(
    name="ltm_hover_action",
    description="...",
    parameters={"required": [...], "properties": {...}},  # JSON-schema-ish
    risk_level=RiskLevel.MEDIUM,        # LOW | MEDIUM | HIGH
    tool_type=ToolType.ACTION,          # READ | COMPUTE | ACTION
    timeout_ms=10000,
    max_retries=1,
    requires_confirmation=False,
)
```

Fields drive the safety pipeline:
- `parameters.required` → L1 missing-arg rejection
- `risk_level` → L2 permission decision
- `tool_type` → L4 tags + retention policy
- `timeout_ms` → L3 hard cap (kill long calls)
- `max_retries` → L3 retry budget
- `requires_confirmation` → L2 forces user prompt for sensitive actions

## ArmorResult — uniform return shape

```python
@dataclass
class ArmorResult:
    success: bool
    output: Any | None
    error: str | None = None
    latency_ms: float | None = None
    retry_count: int = 0
```

**Always returns** — never raises. Callers pattern-match on `result.success`.

## Wrapper class shape (the LTMArmoredOrchestrator pattern)

```
class XxxArmoredOrchestrator:
    def __init__(self, reflection_memory=None, max_steps=30):
        self._reflection = reflection_memory or ReflectionMemory(...)
        self._handlers = { tool_name: handler_fn, ... }
        self._armor = AgentArmor(tools=[schema1, schema2, ...], executor=self._dispatch)

    def _dispatch(self, tool_name, params) -> Any:
        # The ONLY place that knows how to call each handler
        handler = self._handlers[tool_name]
        # unpack params into handler signature
        return handler(**unpacked)

    def _record_l4(self, tool_name, params, result):
        self._reflection.record(result, tool_name, params, prior_event_id=self._last_event_id)
        # emit OTel span here too — single hook for ALL tools

    # Public API — one method per tool
    def memory_search(...) -> ArmorResult:
        params = {...}
        result = self._armor.execute("ltm_memory_search", params)
        self._record_l4("ltm_memory_search", params, result)
        return result
```

## The four canonical wrapped operations (LTM example)

| Tool | Type | Risk | Retries | Use |
|---|---|---|---|---|
| `ltm_memory_search` | READ | LOW | 0 (default) | search memory store |
| `ltm_alpha_forecast` | COMPUTE | LOW | **0** | run forecast model (no retry — expensive) |
| `ltm_hover_action` | ACTION | MEDIUM | 1 | record user UI action |
| `ltm_decision` | ACTION | MEDIUM | 1 | persist decision to DB |

Notice: COMPUTE with `max_retries=0` because re-running a forecast that timed out is worse than reporting failure. ACTION with `max_retries=1` because writes are critical but not idempotent enough to retry blindly.

## Reason gate (business rule baked into wrapper)

```python
def hover_action(self, ..., action, reason, ...):
    if action in ("postpone", "accept") and not reason.strip():
        return ArmorResult(success=False, output=None,
                           error=f"{action.capitalize()} requires a reason.")
    ...
```

Pre-armor business validation catches structural-but-policy-invalid calls before they consume the safety budget.

## Circuit breaker — per-request reset for user-initiated actions

```python
self._armor.circuit_breaker.reset()    # before each user-initiated execute
result = self._armor.execute(...)
```

The shared singleton's circuit breaker accumulates step count across all users. A loop-detection breaker would lock out subsequent users. Reset before each top-level user request → breaker only protects within one request's call tree.

## Sync + async parity

Provide both:
```python
def hover_action(self, ...) -> ArmorResult: ...

async def async_hover_action(self, ...) -> ArmorResult:
    return await asyncio.to_thread(self.hover_action, ...)
```

Async is just a `to_thread` wrap. Don't write two implementations.

## Singleton pattern

```python
_ltm_orchestrator: Optional[LTMArmoredOrchestrator] = None

def get_ltm_orchestrator() -> LTMArmoredOrchestrator:
    global _ltm_orchestrator
    if _ltm_orchestrator is None:
        _ltm_orchestrator = LTMArmoredOrchestrator()
    return _ltm_orchestrator
```

One per process. ReflectionMemory is shared so causal chains across calls are linked via `prior_event_id`.

## Why this is good engineering

| Property | How |
|---|---|
| **One place for cross-cutting concerns** | validation, permissions, retry, timeout, circuit breaker, reflection — all in `AgentArmor` |
| **No silent failures** | every error becomes `ArmorResult(success=False, error=...)`, caller MUST handle |
| **Retroactive observability** | adding OTel later? one edit in `_record_l4` instruments ALL tools |
| **Testable** | swap `_handlers` dict for stubs in tests |
| **Composable** | one orchestrator can wrap any number of tools |

## Forge mapping

Forge currently calls Three.js + LLM + video API directly from `dashboard.html` and `engine3d/*.js`. To apply armor:

```
forge tools to armor:
  - render_3d_scene       (COMPUTE, LOW risk, 0 retries)   — Three.js paint
  - generate_blueprint    (COMPUTE, LOW risk, 1 retry)     — LLM prompt → Movie3DBlueprint
  - generate_video        (ACTION,  MEDIUM, 1 retry)        — fal.ai / replicate / veo
  - persist_user_style    (ACTION,  LOW, 1 retry)           — save 4D-memory entry
  - retrieve_past_styles  (READ,    LOW, 0)                 — 4D-memory lookup
```

Each gets a `ToolSchema`. The dashboard's `generateMovie()` JS function calls `forge_armored_orchestrator.generate_video(...)` (or its async cousin) — never the engine bridge directly.

The reason gate applies: e.g. "regenerate scene" requires a `change_reason` from the user.

## Don't over-design

- L2 permissions can start as a no-op for v1 (always permit if schema passes)
- Circuit breaker can start at `max_steps=30` and never trip in normal use
- ReflectionMemory can write to the same SQLite as oTel; don't open a 2nd DB
- L4 OTel emit can be inline (not async) for v1; optimize later if it's slow
