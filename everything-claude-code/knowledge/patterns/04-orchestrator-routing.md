# Pattern 04 — Orchestrator routing & agent runtime middleware

> Reference distilled from `C:\EPM_ACCUMULATION\appFnd\app\ltm_orchestrator.py`, `app\ltm_agent.py`, `app\agent_runtime.py`, `app\ltm_semantic_router.py`, `app\ltm_nlp_fallback.py`.
> **Idea, not code.** To be re-implemented in Forge in its own way.

## The orchestrator's job

> "Keep the orchestrator small but with the full picture."

The orchestrator does **only routing and stitching**. It never implements business logic. It always knows:
1. What was asked (intent)
2. Which agent/tool can answer (routing)
3. Where the answer goes (memory + reply)

Everything else is delegated.

## The 3-stage canonical loop

```
       User query
          │
          ▼
   ┌─────────────────┐
   │ 1. Classify     │  intent + entities + confidence
   │    Intent       │  (LLM-first, keyword-fallback)
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ 2. Compose +    │  pick SQL template by intent
   │    Execute      │  bind entities → run query → rows
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ 3. Rank         │  apply intent-specific keyword boosts
   │    Results      │  return top_k
   └────────┬────────┘
            │
            ▼
       Response
```

Each stage wrapped in `_with_4d_memory` (see Pattern 03).

## Intent classification — LLM first, keyword fallback (BOTH always)

```python
async def classify(self, query):
    if self._llm:
        try:
            resp = await self._llm.ainvoke(prompt_with_schema_summary)
            return parse_intent_json(resp)
        except Exception:
            pass    # silent fall-through — DO NOT raise
    return _keyword_classify(query)   # always works, never raises
```

**Two rules:**
1. LLM call always wrapped in try/except — failure falls through silently
2. Keyword classifier ALWAYS works (returns `IntentResult` with default intent if no match)

Confidence carries the source: LLM → 0.9, keyword → 0.75, default → 0.5.

## Intent → routing mapping (the small full picture)

```
KNOWN_INTENTS:
  causal_chain        → multi_agent pipeline → graph traversal stage
  memory_search       → multi_agent pipeline → flat memory query
  decision_record     → multi_agent pipeline → DECISIONS table write
  decision_search     → DEDICATED handler (own task_type)
  fx_analysis         → multi_agent pipeline → FX subset
  forecast_run        → multi_agent pipeline → forecast subset
  cfo_analysis        → DEFAULT (catch-all on top of LTM_EVENTS)
```

The `classify_intent()` sync method returns one of three buckets:
```python
"decision_search"  →  dedicated handler
"multi_agent"      →  generic _MULTI_AGENT_INTENTS pipeline
"nlp_unknown"      →  do NOT silently default to cfo_analysis — surface the unknown
```

**Critical rule:** if intent doesn't match anything known, return `nlp_unknown` — DO NOT silently default. Failures must surface so the orchestrator can re-route or ask the user to clarify. (This is your "record how you fix it, after all tell orchestrator then he know how to fix route retry" rule baked in.)

## SQL template per intent (parameterized)

```python
_SQL_TEMPLATES = {
    "causal_chain":   "...JOIN MEMORY_EDGES...WHERE STORY_ID=? ORDER BY SCORE DESC",
    "memory_search":  "...EVENT_TYPE != 'SYSTEM' ORDER BY CREATED_AT DESC",
    "decision_record": "...DECISIONS ORDER BY CREATED_AT DESC",
    "fx_analysis":    "...EVENT_TYPE = 'FX_UPDATE'",
    "forecast_run":   "...EVENT_TYPE = 'FORECAST'",
    "cfo_analysis":   "...ORDER BY SCORE DESC",  # catch-all
}
```

Every template is **parameterized** (`?` placeholders, never string-concat). SQL agent's `compose()` returns `(sql, params)` — never embeds user data into SQL string.

## Result ranking (cheap intent boost)

```python
_INTENT_BOOST_KEYWORDS = {
    "causal_chain":   ["causal", "casual", "chain", "relation", "hedge"],
    "fx_analysis":    ["usd", "jpy", "fx", "rate", "currency"],
    ...
}

def rank(rows, intent_result, top_k=8):
    keywords = _INTENT_BOOST_KEYWORDS[intent_result.intent]
    for row in rows:
        boost = sum(0.1 for kw in keywords if kw in row['content'].lower())
        row['score'] = round(min(1.0, base + boost), 4)
    return sorted(rows, key='score', reverse=True)[:top_k]
```

Simple: each keyword found = +0.1 to score, capped at 1.0. No re-ranking model needed for v1.

## Persist every chat query as event (for RAG later)

```python
def _persist_query_event(self, query, intent_result):
    try:
        conn.execute(
            "INSERT INTO LTM_EVENTS (EVENT_TYPE, CONTENT, SCORE) VALUES (?, ?, ?)",
            ("CHAT_QUERY", json.dumps({"query": query, "intent": intent}), confidence)
        )
        conn.commit()
    except Exception:
        pass  # silent — DB unavailable is OK in dev
```

**Every NLP query becomes a queryable event.** This is what makes the system self-improving — you can later RAG over past queries to improve classification.

## Agent runtime middleware chain

For the runtime version (`agent_runtime.create_agent_runtime`):

```python
runtime = (
    create_agent_runtime(adapter, config)
        .use(audit_middleware())          # log inputs/outputs to oTel
        .use(telemetry_middleware())      # spans + metrics
        .use(guardrail_middleware())      # PII scrub, prompt injection check
        .use(memory_middleware(provider)) # 4D memory lookup before / write after
        .use(cost_tracking_middleware())  # tokens in/out, $ cost
        .use(evaluation_middleware("ONLINE_LIGHT_EVAL"))  # quality eval
        .build()
)
```

**Order matters.** Audit first (so we log even rejected requests), guardrail before memory (don't poison memory with bad inputs), evaluation last (eval the final output).

Each middleware wraps `agent.run(input, ctx)` in a `before / after / on_error` shape. Adding a new middleware = one `.use()` call, no agent code changes.

## Adapter pattern — agent stays plain

```python
class _GeneratedLtmAgentAdapter:
    async def run(self, input_payload, context=None) -> dict:
        return await _run_ltm_agent_core(input_payload)
```

The agent itself is a plain `async def run() -> dict`. The adapter is the only thing the runtime sees. Means: business logic stays testable in isolation, infrastructure (oTel, memory, cost) stays in middleware.

## How "small orchestrator + full picture" stays small

- Orchestrator only stitches stages — doesn't compose SQL, doesn't classify, doesn't rank
- Each stage class has ONE method (`classify`, `compose`, `rank`)
- Cross-stage data flows via shared `_s` dict — no class state pollution
- Routing tables (`_KEYWORD_RULES`, `_SQL_TEMPLATES`, `_INTENT_BOOST_KEYWORDS`) are module-level constants, not instance fields
- Single `route()` method ≈ 50 lines

## Recovery / retry pattern (your "tell orchestrator how to fix route retry")

```
Stage fails
   │
   ▼
Catch + record fix to memory:
   {finding: "intent=fx_analysis but SQL 0 rows; recommend wider window",
    agent: "stage2_recovery"}
   │
   ▼
Orchestrator reads memory before next user query for same story:
   sees "recommend wider window" → adjusts SQL template binding for fx_analysis
   │
   ▼
Re-route automatically next time → no human intervention
```

The orchestrator becomes self-improving by reading its own past failures from 4D memory. **This is why every stage is wrapped in `_with_4d_memory` — failures are first-class memory events too.**

## Forge mapping

Forge's `studio_orchestrator.py` already exists but does straight A2A dispatch. The intent layer is missing — `promptToBlueprint.ts` does keyword matching but with no LLM-first / fallback split, and no orchestrator routing intent → agent.

What to add:

```
forge/orchestrator.py:
  ForgeOrchestrator
    - classifier      # LLM-first, keyword fallback (genre, mood, lighting)
    - dispatcher      # picks specialist agent by intent
    - composer        # stitches per-scene results
    - ranker          # ranks shot suggestions

  Intents:
    new_movie         → full pipeline (WR → EN → CH → LI → AU → ED)
    re_render_scene   → harmonize_delta only (one scene)
    style_inquiry     → memory_search ("show last similar")
    accept_blueprint  → DECISIONS write
    regenerate_with   → re-classify + re-route (the retry path)
```

Each agent (Scenario / Environment / Character / Lighting / Audio / Editor) becomes an adapter. Wrap with the middleware chain. Wire to dashboard via the existing A2A Studio panel — orchestrator's `step_index` drives which row lights up.

## Don't over-design

- Don't build LLM classification first — keyword rules + template SQL gets you 80% of cases for free
- Don't put intent rules in a database — module-level constants are FINE and faster to iterate
- The middleware chain is the LAST thing to wire — start with a bare adapter and add middlewares one by one when you need them
- `_with_4d_memory` can be a no-op for v1; the closure pattern is what matters — install the wrapper later
- Don't try to make the orchestrator self-improving before the basic 3-stage loop works
