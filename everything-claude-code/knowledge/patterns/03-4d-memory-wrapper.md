# Pattern 03 — 4D Memory wrapper (`_with_4d_memory`)

> Reference distilled from `C:\EPM_ACCUMULATION\appFnd\app\ltm_orchestrator.py`,
> `app\ltm_multi_agent.py`, `app\reflection_memory.py`, `app\ltm_armored.py`.
> **Idea, not code.** To be re-implemented in Forge in its own way.

## What "4D Memory" actually means

Four dimensions of memory retrieval & write:

| D | Dimension | What it is | Storage table (LTM example) |
|---|---|---|---|
| 1 | **Lexical** | BM25 keyword match | `LTM_EVENTS.CONTENT` |
| 2 | **Semantic** | embedding similarity | `LTM_MEMORY_EVENTS` (enriched nodes) |
| 3 | **Causal** | directed graph of "X causes Y" | `LTM_MEMORY_EDGES` (CAUSES / CONFIRMS / REFUTES / PRECEDES) |
| 4 | **Decision** | human approve/reject/postpone with reason | `LTM_DECISIONS` |

RRF (Reciprocal Rank Fusion) fuses ranks across these dimensions when retrieving. Ebbinghaus decay ages older memories down so recent context dominates.

## The wrapper concept

`_with_4d_memory(stage_fn, payload, ctx)` — every agent stage runs **inside** this wrapper:

```
PRE  ─►  read prior memory nodes for this story_id  (RAG context)
ACT  ─►  await stage_fn(payload + retrieved_memory, ctx)  →  finding
POST ─►  write the finding as a new memory node
         link it causally to the prior node (PRECEDES edge)
return finding
```

So **every stage is auto-RAG'd before, auto-persisted after**. No per-stage memory wiring.

## Stage-as-closure pattern (orchestrator routing)

```python
async def route(self, query, context):
    from app.ltm_multi_agent import _with_4d_memory

    ctx = {**context, "story_id": context.get("story_id", "ORCH")}
    _s: dict = {}   # shared state for closures (so stages can read each other)

    # Stage 1
    async def _intent_agent(payload, _ctx):
        ir = await self._classifier.classify(payload["query"])
        _s["intent_result"] = ir
        return {"finding": f"intent={ir.intent} conf={ir.confidence:.2f}",
                "agent": "LTMIntentClassifier"}
    await _with_4d_memory(_intent_agent, {"query": query}, ctx)

    # Stage 2
    async def _sql_exec_agent(payload, _ctx):
        ir = _s["intent_result"]
        sql, params = self._sql_agent.compose(ir)
        rows = self._execute(sql, params)
        _s["rows"] = rows
        return {"finding": f"sql_intent={ir.intent} rows={len(rows)}",
                "agent": "LTMSQLAgent"}
    await _with_4d_memory(_sql_exec_agent, {}, ctx)

    # Stage 3
    async def _rank_agent(payload, _ctx):
        ranked = self._ranker.rank(_s["rows"], _s["intent_result"], top_k=20)
        _s["ranked"] = ranked
        return {"finding": f"ranked top={len(ranked)}", "agent": "LTMResultRanker"}
    await _with_4d_memory(_rank_agent, {}, ctx)

    return OrchestratorResponse(...)
```

**Three closures, three lines of `_with_4d_memory`.** That's the whole loom.

### Why closures + shared `_s` dict

- Each stage's signature is `(payload, ctx) -> {finding, agent}` — uniform contract for the wrapper
- Cross-stage data flows through `_s` (intent_result → rows → ranked) without polluting the contract
- Wrapper sees `{finding, agent}` only → consistent memory write shape

## ReflectionMemory — the L4 record

```python
ReflectionMemory.record(
    armor_result,        # ArmorResult
    tool_name,
    params,
    session_id,
    prior_event_id,      # links to previous L4 event → causal chain auto-built
) -> event_id
```

Each call returns a new `event_id`. Caller stores it as `_last_event_id` to chain into the next call. So a session forms a temporally-ordered DAG of `event_id` → `event_id` edges automatically.

`flush_enabled=False` keeps it in-memory for tests; `True` flushes to disk.

## Three classes of memory write

| Where | When | Cost |
|---|---|---|
| **`LTM_EVENTS`** | every raw event (user query, agent output, FX update) — ground truth | cheap, append-only |
| **`LTM_MEMORY_EVENTS`** | enriched + scored nodes — written by `_with_4d_memory` after each stage | moderate (embedding + score) |
| **`LTM_MEMORY_EDGES`** | causal links — written **after human evaluation** (CFO approves → CAUSES edge) | cheap but human-gated |
| **`LTM_DECISIONS`** | human action with reason — written by `ltm_decision` armored tool | cheap |

The graph (`MEMORY_EDGES`) is **deliberately gated by humans**. Auto-induced edges would corrupt the causal model. Only PRECEDES edges are written automatically (temporal).

## Memory provider interface (middleware-style)

For the agent-runtime middleware version (`memory_middleware(provider)`):

```python
class _LtmBetaMemoryProvider:
    async def lookup(self, input_payload, context) -> dict:
        # Read prior memories matching this query — feeds back into the agent
        ...
        return {"memories": [...], "metadata": {...}}

    async def write(self, input_payload, output, context) -> None:
        # Persist the agent's output as a new memory node
        ...
```

Middleware calls `lookup` before `agent.run(input)` and `write` after. The agent doesn't know memory exists.

## Forge mapping

Forge needs 4D memory to make the **Director's Blueprint** pane say more than "Waiting for script...". Per dimension:

| Dimension | What Forge stores | UI surface |
|---|---|---|
| **Lexical** | scenes by keyword (genre tags, character names) | autocomplete on script input |
| **Semantic** | blueprints by embedding (style fingerprint) | "use last similar style" suggestion |
| **Causal** | "this style choice → that visual outcome" — gated by user thumbs-up | Director's Blueprint annotations |
| **Decision** | regenerate / accept / discard with reason | hover-card on each scene row |

Tables:
- `FORGE_EVENTS` — raw (user prompt, blueprint generated, video rendered)
- `FORGE_MEMORY_NODES` — enriched scene memories
- `FORGE_MEMORY_EDGES` — style-causality links (human-gated)
- `FORGE_DECISIONS` — accept/regenerate/discard with reason

Wrap each agent stage (Scenario / Environment / Character / Lighting / Audio / Editor) in `_with_4d_memory`. Result: every A2A Studio agent row in the dashboard reflects a real persisted memory event.

## Don't over-design

- Start with TABLE 1 (raw events) only — the rest can be derived/migrated later
- BM25 + simple embedding cosine is enough for v1; don't pull in a vector DB yet
- Causal edges should require explicit human action — never auto-create
- The wrapper's memory read can be a no-op for v1; only the write side delivers immediate value
- Use the same SQLite file as oTel (`devlog/observe.db`) — adds two tables, simpler ops
