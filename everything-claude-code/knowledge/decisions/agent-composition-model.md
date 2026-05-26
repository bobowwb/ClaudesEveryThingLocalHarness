# Decision: Agent Composition Model

**Date:** 2026-05-22
**Status:** LOCKED IN by user.
**Source:** User on 2026-05-22: *"All the agents we compose are from A2A and add different wrappers on it to make it robust, communicable, and traceable / observable."*

## The model

Every agent in the system is built by **stacking layers**, in this exact order:

```
┌──────────────────────────────────────────────────┐
│ Layer 5: Orchestration                           │
│ (composes multiple A2A agents into a pipeline    │
│  driven by intent classification)                │
└────────────────┬─────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────┐
│ Layer 4: Observability wrapper (oTel)            │
│ → makes the agent TRACEABLE                      │
│   start_trace / add_step / finish_step           │
│   6 A2A completeness fields recorded on every    │
│   call.                                          │
└────────────────┬─────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────┐
│ Layer 3: Memory wrapper (4D _with_4d_memory)     │
│ → makes the agent CONTINUOUS across sessions     │
│   auto-RAG before stage, auto-persist after      │
│   keys off (trace_id, skill_id, agent_name)      │
└────────────────┬─────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────┐
│ Layer 2: Armor wrapper (L1→L4 pipeline)          │
│ → makes the agent ROBUST                         │
│   validate → permit → execute+retry → reflect    │
│   uniform ArmorResult, never raises              │
└────────────────┬─────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────┐
│ Layer 1: A2A core                                │
│ → makes the agent COMMUNICABLE                   │
│   GET /.well-known/agent.json (the card)         │
│   POST /  (JSON-RPC 2.0 dispatch)                │
│   skills declared explicitly, routed by          │
│   metadata.skill_id                              │
└──────────────────────────────────────────────────┘
```

## Property each layer adds

| Layer | Property | Without this layer... |
|---|---|---|
| **A2A core** | **Communicable** | the agent has no public boundary; it's just an in-process function |
| **Armor** | **Robust** | one bad input crashes the agent; no retry; no permission gate |
| **4D Memory** | **Continuous** | every session starts blank; the agent forgets every preference and decision |
| **oTel** | **Traceable / Observable** | failures are invisible; you can't debug or replay |
| **Orchestration** | **Composable** | each agent is alone; nothing chains them on intent |

## Five layers, four properties

The user's quote names exactly four properties:
1. **robust** ← Armor
2. **communicable** ← A2A
3. **traceable** ← oTel
4. **(observable)** ← oTel (same layer; "observable" is the read-side name)

I'm adding **continuous** (4D Memory) and **composable** (Orchestrator) as natural next properties — both stack cleanly on top.

## Composition rules

1. **No agent skips a layer.** Every agent has all five — even if a layer is a no-op for v1, the slot is reserved.
2. **Layers are added in order.** A2A first, then armor, then memory, then oTel, then orchestrator.
3. **Skipping order causes bolt-on bugs.** If oTel goes in before A2A, oTel has to invent a "call shape" that doesn't match A2A's, and later they fight.
4. **Each layer is independently swappable.** The 4D Memory backend can change (in-mem → SQLite → vector DB) without touching A2A, Armor, oTel, or the orchestrator.
5. **Failures in upper layers MUST NOT break lower layers.** oTel write fails? log warning, return result anyway. Memory unavailable? continue without RAG. Armor circuit broken? still log to oTel.

## How an agent is "from A2A"

The phrase "from A2A" means: **A2A defines the agent's boundary**. Everything outside the agent talks to it via:
- the card (to discover it)
- JSON-RPC POST `/` with a skill_id (to invoke it)

Internal implementation, language, framework — all swappable. The card is the contract.

## Construction recipe (one agent, end to end)

```
Step 1 (A2A core):
  - Write AGENT_CARD with skills[]
  - Two endpoints: GET /.well-known/agent.json, POST /
  - Skill router using metadata.skill_id
  - Skill handlers: dict in → dict out
  → Now communicable.

Step 2 (Armor):
  - For each skill, declare ToolSchema(risk_level, tool_type, timeout_ms, max_retries)
  - Wrap each handler in AgentArmor.execute(skill_id, payload)
  - Return ArmorResult, never raise
  → Now robust.

Step 3 (4D Memory):
  - For each skill handler, wrap in _with_4d_memory(stage_fn, payload, ctx)
  - Auto-reads prior memory before, auto-writes finding after
  - prior_event_id chains causal sequence
  → Now continuous.

Step 4 (oTel):
  - Every _a2a_task call writes start_trace + add_step + finish_step
  - 6 completeness fields populated from A2A meta
  - root_log_id == correlation_id across the trace tree
  → Now traceable / observable.

Step 5 (Orchestrator):
  - LLM-first / keyword-fallback intent classifier
  - Intent → routing table → A2A target agent + skill_id
  - Persist every CHAT_QUERY for self-improvement
  → Now composable.
```

## Forge mapping (concrete)

The 6 specialist agents Forge needs:

| Agent | Skills (A2A) | Layers added |
|---|---|---|
| `forge_writer` | `write_scene`, `revise_scene` | A2A → Armor → Memory → oTel |
| `forge_environment` | `pick_environment`, `list_alternatives` | A2A → Armor → Memory → oTel |
| `forge_character` | `design_character`, `list_alternatives` | A2A → Armor → Memory → oTel |
| `forge_lighting` | `design_lighting` | A2A → Armor → Memory → oTel |
| `forge_audio` | `design_audio` | A2A → Armor → Memory → oTel |
| `forge_editor` | `edit_timeline` | A2A → Armor → Memory → oTel |
| `forge_render` | `render_2d`, `render_3d`, `render_video` | A2A → Armor → Memory → oTel |
| `forge_orchestrator` | (top — chains the above) | Orchestrator over them |

**Each one stands alone**: callable from the network, retries built in, remembers your style, fully traced. The orchestrator picks which to call based on intent.

This is also why the dashboard's middle and right columns can be filled — every A2A Studio agent row maps to one A2A service's `a2a_task_state`. Director's Blueprint pane shows the per-skill output composed.

## Why this beats "just write functions"

- **Fault isolation.** If `forge_render` is slow, the orchestrator doesn't block; oTel records timeout; armor retries; user sees graceful degradation.
- **Replaceability.** Want to swap Three.js for Babylon.js? Rewrite `forge_render` as a different language even — card stays, callers don't change.
- **Testability.** Mock an agent by serving a fake card on a localhost port. The orchestrator can't tell the difference.
- **Multi-tenant ready.** Each agent has `tenant_id` in its trace records (Pattern 01); add bearer tokens at A2A layer when needed.
- **Observability is free.** Every A2A call writes oTel automatically; no per-business-logic instrumentation.

## What "robust + communicable + traceable" implies for Forge dashboard

The user's three words map directly to three dashboard surfaces:

| Property | Dashboard surface | What it shows |
|---|---|---|
| **Communicable** (A2A) | A2A Studio panel | each agent row + agent card peek (name, version, skills) |
| **Robust** (Armor) | Telemetry log | retry counts, circuit breaker state, error reasons with retry markers |
| **Traceable** (oTel) | TraceID + scan-line | live `root_log_id` + step progression as agents finish |

The Director's Blueprint pane adds **Continuous** (4D Memory) — "this looks like the style you picked last Tuesday" annotations.

## Do not deviate

If at any point during Forge work I find myself thinking "I'll just write this as a Python function and skip A2A for now" — **stop**. That's the bolt-on path. Always start with the agent card.

If I find myself thinking "I'll skip the armor wrapper, the function is simple" — **stop**. Without armor, exceptions propagate out of A2A as 500 errors with no retry, and the orchestrator can't recover the route.

The five layers are non-negotiable. They are cheap to add up front. They are expensive to retrofit.
