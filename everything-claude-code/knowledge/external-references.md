# External Knowledge — Existing Agent Q&A in Obsidian Wiki

**Purpose:** Pointer/catalogue of user's existing Q&A-style principles for agents already on disk.
**Last updated:** 2026-05-22
**Discovery context:** User on 2026-05-22 said: *"Find the agent Q&A, there is a knowledge in your local — some principles."*

## Where it lives

```
C:\AI\knowledge\           ← Obsidian-style wiki, the source of truth for agent principles
├── index.md                       ← master index
├── 4d-memory-armor-wrapper-knowledge.md   ← THE Q&A handbook (688 lines)
├── concepts\
│   └── MAGMA — 4 Orthogonal Memory Dimensions.md   ← 4D theory
├── synthesis\
│   ├── Agent-Architecture-Selection.md             ← single vs multi-agent decision tree
│   ├── Agent Memory Landscape — MAGMA vs OpenTelemetry.md
│   ├── APS-Agent-Scenarios.md
│   ├── FPA-LTM-Plan-B-AppFnd-OTel-MAGMA.md
│   ├── FPA-Agent-LongTerm-Memory-Research-Plan.md
│   └── MAGMA Discussion — Business Agent Memory Implementation.md
└── references\
    ├── Joule Dev Guide — BYOA Code-Based Agents.md  ← A2A v0.3.0 protocol principles
    ├── Joule Dev Guide — Development Overview.md
    ├── Joule CLI Dev and Deploy Guide — AppFND pws_agent.md
    └── Joule Deploy Best Practice — AppFND.md
```

## Top 5 to read first (in order)

| # | File | Why |
|---|------|-----|
| 1 | `references\Joule Dev Guide — BYOA Code-Based Agents.md` | A2A v0.3.0 protocol principles. JSON-RPC `message/send`. Sync/async/multi-turn. Capability YAML. The CANONICAL agent contract. |
| 2 | `4d-memory-armor-wrapper-knowledge.md` | Q&A handbook covering Armor 4 layers, ReflectionMemory L4, HANA 4D persistence, complete orchestrator boilerplate, BM25/RRF/Ebbinghaus terms. |
| 3 | `synthesis\Agent-Architecture-Selection.md` | Decision table: single agent vs single-with-skills vs multi-agent. Key insight: sub-task sophistication → its own sub-agent → keeps main context window clean. |
| 4 | `concepts\MAGMA — 4 Orthogonal Memory Dimensions.md` | TEMPORAL / SEMANTIC / CAUSAL / ENTITY dimensions explained. PRECEDES/SUCCEEDS/CONCURRENT, RELATED_TO/PART_OF, LEADS_TO/BECAUSE_OF/ENABLES/PREVENTS edges. |
| 5 | `synthesis\Agent Memory Landscape — MAGMA vs OpenTelemetry.md` | Critical distinction: OTel = observability (spans/traces), NOT memory. MAGMA = long-term semantic memory. 4-layer FP&A arch: in-context + MAGMA + OTel + HANA. |

## Key principles distilled from these references

### From Joule BYOA (A2A v0.3.0)

- Protocol: **JSON-RPC**, method `message/send`, message type `text` only
- Sync timeout: **60 seconds** — anything longer needs async
- Async: push notifications via webhook (IAS App2App trust required)
- Multi-turn: agent generates `contextId` and `taskId`, capability propagates them back on subsequent calls
- Empty `contextId/taskId` on first call = handled internally, no developer logic needed
- `response_context.description` MUST be ≤ 50 characters (Compiler-0190)
- DTA schema version ≥ 3.28.0 for BYOA features
- Capability YAML structure: `target.type=function` → function uses `agent-request` action with `system_alias` pointing to BTP destination

### From 4d-memory-armor-wrapper-knowledge

- **Armor 4 layers (NON-NEGOTIABLE order):**
  - L1 Validation — schema check, missing required fields rejected
  - L2 Permission — RiskLevel (LOW/MEDIUM/HIGH); HIGH auto-injects idempotency_key
  - L3 Execution + Recovery — circuit breaker; auto-retry (set `max_retries=0` to disable)
  - L4 Reflection + Self-Evolution — write to ReflectionMemory + HANA 4D footprint
- **Risk vs retry:**
  - READ → max_retries=2 (default)
  - COMPUTE → max_retries=0 (re-running expensive computation worse than reporting failure)
  - ACTION (writes) → max_retries=0~1
  - HIGH ACTION (irreversible) → max_retries=0 always
- **Async wrap:** `asyncio.to_thread(self.run, ...)` for blocking I/O. Don't write two impls — one sync + thin async wrapper.
- **L4 write is non-fatal:** wrap in try/except, log debug, never raise. Observability never breaks the agent.

### From Agent-Architecture-Selection

- **Quick test (verbatim):**
  - 1–3 lookups? → Single agent
  - Fixed sequence, small output each step? → Single + Skills
  - Any step has many tool calls / large intermediate data / own reasoning loop / parallel specialization? → **Multi-agent (that step becomes a sub-agent)**
- **Why multi-agent:** sub-agent keeps its own OTel span tree, returns ONLY the distilled answer to orchestrator. Main context window stays small and clean.
- **AppFND deployment unit:** single agent = one `pws_agent`; multi-agent = multiple `pws_agent` instances + A2A.

### From MAGMA 4 Dimensions

- 4 orthogonal dimensions = TEMPORAL + SEMANTIC + CAUSAL + ENTITY
- Each dimension captures something flat vector search or SQL cannot natively express
- TEMPORAL auto-created on every event (PRECEDES/SUCCEEDS/CONCURRENT, time_delta seconds)
- SEMANTIC: top-3 cosine similar events get bidirectional RELATED_TO links (MiniLM-L6-v2, 384-dim, local model)
- CAUSAL: async LLM inference + slow-path consolidation (LEADS_TO / BECAUSE_OF / ENABLES / PREVENTS / RESPONSE_TO)
- ENTITY: spaCy NER (en_core_web_trf transformer model, ~90% F1) + custom FP&A patterns (FX_PAIR, KPI, BUDGET_CODE)
- **Dual-stream ingestion:** fast path (temporal+vector, non-blocking) + slow path (causal inference, 2-hop, LLM)
- Keyword enrichment: TF-IDF keywords prepended before embedding so domain terms ("FX forecast JPY/USD") don't get diluted

### From MAGMA vs OpenTelemetry

> **OTel ≠ Memory.** OTel records spans/traces/latency for observability. MAGMA stores agent decisions and conversations as queryable natural-language memory across sessions.

The 4-layer FP&A agent memory architecture:
1. **In-context** — current conversation (LLM context window)
2. **MAGMA** — long-term semantic memory (queryable across sessions)
3. **OTel** — execution traces (debug + replay)
4. **HANA** — system of record (compliance + audit)

Each layer answers different questions. Don't try to make one do another's job.

## Cross-reference to my durable knowledge

| External (C:\AI\knowledge\) | My local (knowledge/) |
|---|---|
| `references\Joule Dev Guide — BYOA Code-Based Agents.md` | `patterns/00-a2a-foundation.md` (distilled, language-agnostic) |
| `4d-memory-armor-wrapper-knowledge.md` § Armor | `patterns/02-armor-wrapper.md` |
| `4d-memory-armor-wrapper-knowledge.md` § HANA 4D | `patterns/03-4d-memory-wrapper.md` |
| `concepts\MAGMA — 4 Orthogonal Memory Dimensions.md` | `patterns/03-4d-memory-wrapper.md` (the four-dimension theory) |
| `synthesis\Agent-Architecture-Selection.md` | `patterns/04-orchestrator-routing.md` (single vs multi decision) |
| `synthesis\Agent Memory Landscape — MAGMA vs OpenTelemetry.md` | `decisions/agent-composition-model.md` (5-layer model — properties of each layer) |
| (none — appFnd code) | `patterns/01-otel.md` (distilled from `app/observability.py`) |

## Source-of-truth rule

When my distilled patterns disagree with `C:\AI\knowledge\`, **the wiki wins** — it was written by the user, predates this session, and reflects their actual practice. My patterns are summaries; the wiki is authoritative.

## Session-start protocol update

`SESSION-START.md` should now also include this catalogue. When working on agent design questions, read order is:

```
1. knowledge/INDEX.md
2. knowledge/decisions/agent-composition-model.md   ← 5-layer model
3. knowledge/external-references.md                 ← THIS FILE: pointers to wiki
4. C:\AI\knowledge\<specific file>                  ← if deeper Q&A is needed
5. knowledge/patterns/00-a2a-foundation.md          ← my distilled patterns
6. knowledge/forge/INDEX.md                          ← Forge state
```

The wiki is the long-form Q&A. My `knowledge/` is the short-form working memory. Both stay in sync via this catalogue file.

## Provenance

User on 2026-05-22: *"Find the agent Q&A, there is a knowledge in your local — some principles."* — discovered via Grep over `C:/AI/knowledge` for `agent.*principle|Q.*A|Q&A|question.*answer`. 20+ files matched, 5 prioritized above.
