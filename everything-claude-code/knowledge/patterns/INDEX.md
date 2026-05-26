# appFnd → Forge Reference Patterns Index

**Date:** 2026-05-22 (revised after user clarification on A2A foundation)
**Source:** `C:\EPM_ACCUMULATION\appFnd\` (reference only — DO NOT touch or copy code)
**Purpose:** Distilled architectural ideas to apply to Forge (`C:\Users\I075354\.accio\accounts\7087759244\agents\DID-2799F4-...\project\`)
**Rule:** Real Forge code goes only into Forge's own folder when the time comes. Patterns here are durable knowledge.

## CRITICAL ordering — A2A is the foundation

> User on 2026-05-22: *"Look at the appFnd's A2A wrapper FIRST, how the agent be created that naturally conform A2A protocol — that is important. All the wrappers should be based on A2A."*

```
                    ┌─────────────────────────────┐
                    │  Pattern 04: Orchestrator   │  ← intent → A2A call chain
                    └────────────┬────────────────┘
                                 │
         ┌───────────────────────┴────────────────────────┐
         │                                                │
┌────────▼─────────┐  ┌─────────────────────┐  ┌──────────▼────────┐
│ Pattern 02:      │  │ Pattern 03:         │  │ Pattern 01:       │
│ Agent Armor      │  │ 4D Memory wrapper   │  │ oTel trace store  │
│ (wraps skills)   │  │ (wraps stages)      │  │ (logs A2A calls)  │
└────────┬─────────┘  └──────────┬──────────┘  └──────────┬────────┘
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │  Pattern 00: A2A Foundation │  ← THE GROUND
                    │  /.well-known/agent.json    │     EVERYTHING
                    │  POST / (JSON-RPC 2.0)      │     SITS ON
                    └─────────────────────────────┘
```

If A2A is in place, the four wrappers compose naturally. If A2A is bolted on later, every wrapper has to special-case "function call vs A2A call" — bug factory.

## The five pillars

| # | Pattern | Layer | What it gives Forge |
|---|---|---|---|
| **00** | **A2A foundation** | **bedrock** | Every agent has `/.well-known/agent.json` + JSON-RPC POST. Discoverable. Replaceable. The agent boundary. |
| 01 | oTel observability | wrapper | Every A2A call recorded with 6 completeness fields; SQLite trace store; powers dashboard `TraceID` + agent rows |
| 02 | Agent Armor | wrapper | L1→L4 pipeline (validate → permit → execute → reflect) on each A2A skill call |
| 03 | 4D Memory | wrapper | `_with_4d_memory` auto-RAGs + auto-persists per stage; keys off `(trace_id, skill_id, agent_name)` |
| 04 | Orchestrator routing | top | LLM-first/keyword-fallback intent classifier; chains A2A calls per intent |

## How they compose (for one user request)

```
User clicks "Generate Movie"
   │
   ▼
forge_orchestrator (Pattern 04)
   │
   ├─ classify_intent      ──┐
   ├─ pick_route             │  each stage wrapped in
   └─ for each step:         │  _with_4d_memory (Pattern 03)
        │                    │
        ▼                    │
   AgentArmor.execute        │
   (Pattern 02 — L1→L4)      │
        │                    │
        ▼                    │
   _a2a_task(url, skill_id) ─┘
   (Pattern 00 — JSON-RPC)
        │
        ▼
   target agent's POST /
        │
        ▼
   skill handler runs
        │
        ▼
   response: { state: "completed", parts: [...] }
        │
        ▼
   each call writes oTel record
   (Pattern 01 — start_trace / add_step / finish_step)
        │
        ▼
   dashboard reads trace, paints UI
```

## Application order for Forge

When skills + tests arrive and we start TDD:

1. **First**, A2A-ify the agents. Each specialist (WR/EN/CH/LI/AU/ED/Render) becomes its own A2A service with card + handler. Replace `studio_orchestrator.py` in-process dispatch with `_a2a_task` calls. (Pattern 00)

2. **Second**, port observability. Drop `forge_observability.py` modeled on `app/observability.py`. The 6 A2A completeness fields slot directly into `add_step()`. Dashboard's existing `TraceID` and A2A scan-line become real. (Pattern 01)

3. **Third**, wrap one skill with armor — start with `render_3d` (cheapest to test, highest value). (Pattern 02)

4. **Fourth**, wire intent routing. Replace `promptToBlueprint.ts` keyword-only with LLM-first/keyword-fallback. Surface `nlp_unknown` instead of silently defaulting to demo blueprints. (Pattern 04)

5. **Fifth**, add `_with_4d_memory` wrapper around each orchestrator stage. (Pattern 03)

The order is critical: **A2A first** unlocks every other layer. Skipping it forces bolt-on later, which fails.

## What goes where

| Layer | Forge file (target) | appFnd reference |
|---|---|---|
| **A2A** | `agents/forge_<role>/a2a_app.py` (one per specialist) + `forge_orchestrator.py` calling `_a2a_task` | `agents/render_agent/a2a_app.py`, `app/routes/a2a_outer.py` |
| oTel | `forge_observability.py` | `app/observability.py` |
| Armor | `forge_armor.py` + `forge_armored_orchestrator.py` | `app/agent_armor.py` + `app/ltm_armored.py` |
| 4D memory | `forge_memory.py` + `_with_4d_memory` helper | `app/reflection_memory.py` + `app/ltm_multi_agent.py` |
| Orchestrator | `forge_orchestrator.py` (replaces `studio_orchestrator.py`) | `app/ltm_orchestrator.py` |
| Schema | `forge/schema.py` (FORGE_EVENTS, FORGE_MEMORY_NODES, FORGE_MEMORY_EDGES, FORGE_DECISIONS) | `app/ltm_orchestrator.py::_SCHEMA` |

## Files

- `00-a2a-foundation.md` ← **read first**
- `01-otel.md`
- `02-armor-wrapper.md`
- `03-4d-memory-wrapper.md`
- `04-orchestrator-routing.md`

## Cross-references to user's prior session rules

| User rule | Captured in pattern |
|---|---|
| "All wrappers based on A2A" | 00 — the foundation |
| "keep orchestrator small but full picture" | 04 — small loop, all routing tables module-level |
| "record how you fix it, after all tell orchestrator then he know how to fix route retry" | 04 — recovery + 03 — failures as memory events |
| "12 NLP need 12 query check return" | 04 — every CHAT_QUERY persisted to events |
| "test show screen ui with records" | 01 — oTel feeds dashboard live |
| "why u stop keep tdd till all green" | applies to all 5 — never raise on infra error, always return uniform result |
| "Not in the RAM, in hard copy" | this whole knowledge/ folder |
