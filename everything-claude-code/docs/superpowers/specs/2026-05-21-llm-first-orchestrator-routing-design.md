# LLM-First Orchestrator Routing — Design Spec

Date: 2026-05-21
Status: locked (user approval recorded in session 2026-05-20/21)
Scope: appFnd chat NLP routing for free-form prompts that miss the 14 button-locked routes

---

## 1. Problem

Today, when a user types a free-form prompt (e.g. "show me return-related operations"), the request goes:

1. `chat_routes._normalize_chat_task_type` → `_BUTTON_LOCKED` check
2. fall through to `LTMSemanticRouter._stage1` → hardcoded keyword substring match
3. on miss → `task_type="nlp_unknown"` → red "✗ NO_MATCH" card

This is brittle. `ltm_hdb` already understands "return" (BUSINESS_TERM "product return"), but the router never asks. Hardcoded keywords are the disease — we are about to delete them.

## 2. Hard constraints from user

- Hardcode is the LAST thing we do, not the first.
- Never hand a raw red error to the user. Degrade to amber, never red.
- For free-form NLP, route to **orchestrator first** (with LLM + predefined data structure + knowledge index), not to a keyword router.
- 14 button-locked routes stay strict (no LLM in the path).
- Ambiguity policy: if multi options remain, double-confirm; if truly unclear, ask user to refine, **max 3 retries per turn**.
- Persist raw + lemmatized tokens. Some NLP terms become business terms over time.
- LLM never writes SQL. LLM picks tool name + args; middle layer filters/cleans; dedicated SQL writer agent composes SQL.
- Pydantic typed contracts at every A2A boundary, with `contract_version`.
- Spans + 4D edges = chat turn replay. Every UI action wrapped in 4D.
- Idempotency on side-effects keyed by `trace_id + ui_element_id + click_seq`.

## 3. Two-track routing

### Track A — Button-locked (deterministic)

- 14 buttons → `_BUTTON_LOCKED` → direct dispatch.
- No orchestrator, no LLM, no router.
- Same as today. Untouched.

### Track B — Free-form NLP (LLM-first)

```
user prompt
  → normalize → not in _BUTTON_LOCKED
  → SKIP keyword router (delete _stage1 for free-form path)
  → NLPFallbackOrchestrator (Plan-Execute-Replan)
       1. extract trace (raw + lemma + entities)   [spaCy en_core_web_sm]
       2. recall 4D memory (RRF over LTM_MEMORY_EVENTS, top_k=20)
       3. classify with LLM:
            input  = raw_query, lemmas, entities, recall_hits, tool_catalog
            output = NLPClassifyOutput {
              intent, tool_name, tool_args,
              candidates, confidence,
              contract_version: "nlp_classify.v1"
            }
       4. branch:
            confidence >= threshold (default 0.75) AND len(candidates) == 1:
              → dispatch to LTMArmoredOrchestrator.<tool>(args)
            multiple high-confidence candidates:
              → render double-confirm card (top 3–5)
            confidence < threshold:
              → render clarify card (LLM-generated question, 4D recall hits as hint chips)
       5. on user response: replay loop, increment retry_count (max 3)
       6. on retry exhaustion: amber "we couldn't understand, here's what we tried" card
          (NEVER a red error)
```

## 4. Components

### 4.1 NLPFallbackOrchestrator (new)

- Replaces the role currently played by `LTMSemanticRouter._stage1` for free-form prompts.
- Plan-Execute-Replan pattern (per Q11 of MULTI_AGENT_QA_REFERENCE).
- Wraps `LTMArmoredOrchestrator`. Does not bypass armor.
- Lives at `app/ltm_nlp_orchestrator.py` (new file).
- Exposes `async classify_and_dispatch(query, session_id, retry_count) -> NLPDispatchResult`.

### 4.2 Tool catalog (Layer-2 typed tools)

LLM picks one of these tool names. LLM never composes SQL.

| tool_name | dispatched to | purpose |
|---|---|---|
| `MEMORY_SEARCH` | `LTMArmoredOrchestrator.memory_search` | RRF recall over 4D memory |
| `FORECAST` | `LTMArmoredOrchestrator.forecast` | KPI forecasting path |
| `HOVER_ACTION` | `LTMArmoredOrchestrator.hover_action` | LTM hover detail expansion |
| `DECISION_SEARCH` | `ltm_decision_search.search` | causal-chain / decision lookup |
| `MULTI_AGENT` | `ltm_multi_agent.run_analysis` | multi-agent analysis |
| `CLARIFY` | render clarify card | ambiguity / refine prompt |

After `tool_name + tool_args` are picked, a **middle mapping layer**:

1. Validates `tool_args` with Pydantic.
2. Cleans/filters (drops nulls, normalizes entity values, applies `tenant_id` + `tier_level` checks).
3. Hands cleaned args to a **dedicated SQL writer agent** (for tools that need DB queries) or the typed tool directly.
4. SQL writer agent composes parameterized SQL. LLM is not in this step.

### 4.3 Pydantic contracts

```python
class NLPClassifyInput(BaseModel):
    contract_version: Literal["nlp_classify.v1"] = "nlp_classify.v1"
    raw_query: str
    lemmas: list[str]
    entities: dict[str, list[str]]
    recall_hits: list[RecallHit]   # top_k from 4D memory
    tool_catalog: list[ToolDescriptor]

class NLPClassifyOutput(BaseModel):
    contract_version: Literal["nlp_classify.v1"] = "nlp_classify.v1"
    intent: str
    tool_name: ToolName            # enum
    tool_args: dict
    candidates: list[Candidate]
    confidence: float
    rationale: str
```

Validated by `contract_validation_middleware` at every A2A boundary.

### 4.4 LTM_NLP_TRACES (persistence)

Already designed. DDL string in `ltm_nlp_fallback.py`. Stores:

- `trace_id` (PK)
- `story_id`
- `raw_query`
- `tokens_json` (raw → lemma + `is_stop` + `is_punct`, no full POS/DEP)
- `entities_json`
- `enriched_query`
- `intent`
- `created_at`

Separate from orchestrator schema. Persistence is non-fatal.

### 4.5 4D wrapping for UI actions

Every accept / postpone / clarify-reply click on a fallback card emits a 4D edge:

- subject: `trace_id`
- verb: `UI_ACCEPT` | `UI_POSTPONE` | `UI_CLARIFY_REPLY`
- object: `candidate_id` or `refined_prompt`
- `ts`, `session_id`, `span_id`, `idempotency_key` (trace_id + ui_element_id + click_seq)

Hooked once at the UI boundary so accept/postpone are symmetric and replay-safe.

### 4.6 Step-level SSE events

| event | meaning |
|---|---|
| `nlp.lemmas_extracted` | spaCy trace done |
| `memory.recall_done` | 4D RRF complete |
| `orchestrator.classified` | LLM classify returned |
| `scenario.rendering` | dispatching to chosen tool |
| `ui.action_recorded` | 4D edge persisted |

## 5. Deletions

- `LTMSemanticRouter._stage1` keyword scan: **removed** for free-form path.
- The hand-rolled `_MANIFEST` keyword list: **removed**.
- The red "✗ NO_MATCH" template in `chat_routes` frontend JS: **replaced** with amber degraded card.
- `_stage1` stays only as deterministic backup behind a feature flag during rollout, then deleted entirely after eval gate passes.

## 6. Ambiguity / failure handling

| state | UI |
|---|---|
| 1 high-confidence candidate | dispatch immediately, normal card |
| 2–5 candidates above threshold | double-confirm card, top N as buttons |
| < threshold and recall hits exist | clarify card with LLM question + recall hits as hint chips |
| < threshold and no recall hits | clarify card with example refinements |
| `retry_count >= 3` | amber "we tried X, Y, Z. None matched. Pick a button or rephrase." |
| true `system_failure` (LLM down, DB down) | amber **structured** card, NEVER red text |

## 7. Idempotency

- Every external side-effect (UI accept / postpone, dispatch, replay) keyed by `trace_id + ui_element_id + click_seq`.
- Replays return the cached outcome; never re-execute.
- Counter for `retry_count` attached to `trace_id` span (not envelope).

## 8. Observability

Every span carries: `trace_id`, `parent_span_id`, `agent_name`, `contract_version`, `cost_usd`, `latency_ms`, `status`, `tool_name`. Visible in Trace Replay UI (deferred to v1.5 per appFnd plan).

## 9. Eval gate

- Golden set = curated prompts including the "show return related operations" regression.
- Release gate: classify accuracy >= 0.85 on golden set, RRF avg relevance >= 0.79 (appFnd baseline).
- Bug-gate: 0 P0/P1 before ship.

## 10. Open items / deferred

- Trace Replay UI is v1.5+; for v0.9 raw spans suffice.
- Adaptive confidence threshold tuning from 4D memory hits is a v1.1 follow-up; v0.9 ships fixed `0.75`.
- LiteLLM cost dashboard is Pro-tier feature, deferred.

## 11. Cross-references

- `MULTI_AGENT_QA_REFERENCE.md` (12 Q&A + 7 cross-cutting principles)
- `app/ltm_armored.py` (`LTMArmoredOrchestrator`)
- `app/ltm_nlp_fallback.py` (trace + persistence + fallback card)
- `app/ltm_hdb.py` (RRF, business terms, `_canonical_terms`)
- `agents/pws_agent/a2a_app.py` (A2AEnvelope shape)
- `docs/agent-armor-4d-memory-guide.md` (4D memory)
- `docs/ltm-5d6d-extension-plan.md` (memory roadmap)
