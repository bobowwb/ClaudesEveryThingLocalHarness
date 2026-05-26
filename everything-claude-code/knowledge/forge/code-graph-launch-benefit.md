# How code-graph Helps Forge Ship to Production

**Date:** 2026-05-22
**Status:** Concrete use cases mapped from upstream tool spec (`tools.ts`) to Forge's actual codebase + 5-layer architecture work.
**Source:** User on 2026-05-22: *"应该对我们这个产品上线会有帮助的"* (this should help our product ship)

## TL;DR

code-graph turns "I have to grep + Read 8 files to figure out what calls X" into "one MCP call returns the answer." For Forge specifically, it cuts the cost of the **5-layer wrapper composition** (A2A → Armor → 4D Memory → oTel → Orchestrator) by an estimated 60-70% in tool calls, because each layer needs to know what calls what across both the TS engine3d frontend AND the Python orchestrator backend.

Upstream benchmarks (Django, VS Code, Tokio, etc.):
- 35% cheaper
- 70% fewer tool calls
- 49% faster
- 59% fewer tokens

Forge falls in the "small-to-medium codebase" tier (~50-100 source files excluding `node_modules`/test fixtures). Per upstream's `getExploreBudget(fileCount)` table, Forge gets `1 explore call` budget and an **18,000-char output cap** per call — generous for a project this size, but it means I should ask precise questions, not "show me everything."

## Concrete production-shipping wins (mapped to current Forge bug + 5 layers)

### 1. The active bug: 2D/3D render missing

**Without code-graph:**
- Read `dashboard.html` (~1000 lines)
- Grep for `renderCanvas` across project
- Read `engine3d/blueprintEditor.js`, `engine3d/videoRenderer.js`
- Read `engine3d/types.ts`
- Re-read `dashboard.html` to cross-reference
- Estimated: 6-8 tool calls, 30k+ tokens

**With code-graph:**
```
codegraph_search("renderCanvas")          → location, kind, file
codegraph_callers("renderCanvas")         → who tries to draw to it (and why nothing shows)
codegraph_context("3D scene rendering")   → all the engine3d symbols, their callers/callees, and source
```
- Estimated: 3 tool calls, ~10k tokens
- Answer: "`renderCanvas` is hardcoded `display:none`; no callee of `mountThreeJSScene` ever exists"

### 2. Layer 1 — A2A-ifying each specialist agent (WR/EN/CH/LI/AU/ED/Render)

When I make `studio_orchestrator.py` into a real A2A caller (`_a2a_task` instead of in-process Python dispatch), I need to know:
- Where is each specialist's logic defined right now?
- What does the orchestrator currently call (so I can replace those call sites)?
- What's the input/output contract of each (so I can preserve it in the A2A skill schema)?

```
codegraph_search("dispatch")              → all dispatch points in studio_orchestrator
codegraph_callers("scenario_agent")       → caller pattern for one specialist (use as template for the other 5)
codegraph_callees("studio_orchestrator")  → exactly what gets called → maps 1:1 to A2A skill list
codegraph_impact("Movie3DBlueprint", 3)   → blast radius if I version-bump the type contract
```

**Production-grade benefit:** I won't break the existing API surface during the rewrite. `codegraph_impact` tells me which downstream files reference each contract type; I add an alias or migration step instead of breaking changes.

### 3. Layer 2 — Wrapping skills with Armor (L1→L4)

Each skill that goes into Armor needs:
- Its current call signature (input shape, return shape)
- Its current error paths (so I know what `try/except` to convert to `ArmorResult(success=False, error=...)`)
- Its current callers (to update them to handle `ArmorResult`)

```
codegraph_node("generate_video", includeCode=true)  → exact signature
codegraph_callers("generate_video")                 → all call sites that need to change
codegraph_callees("generate_video")                 → what tools the function uses (gives risk_level: ACTION)
```

**Production-grade benefit:** Armor won't introduce regressions. Every caller updated, every internal tool catalogued.

### 4. Layer 3 — 4D Memory wrapper integration

The `_with_4d_memory` closure pattern wraps each orchestrator stage. To wire it correctly:
- Where are the stage boundaries?
- What's the per-stage `(payload, ctx) -> {finding, agent}` contract today vs. what it needs to become?

```
codegraph_explore("orchestrator stages stage_fn dispatch handler")
  → returns the orchestrator dispatch area as one cohesive block of source
  → I see all stages at once, design the closure wrapper once
```

**Production-grade benefit:** I don't write the wrapper for one stage, deploy, then realize it doesn't fit the others. One `explore` shows the full pattern.

### 5. Layer 4 — oTel observability hookup

Forge's dashboard already has the oTel UI scaffolding (`#traceId`, `#orchScan`, agent rows). The job is connecting them to a real `forge_observability.py` trace store. To do that I need:
- Every place an A2A call happens (each becomes a `start_trace` or `add_step`)
- Every place a status changes (each becomes a `finish_step`)

```
codegraph_search("a2a", kind="function")  → all A2A entry points
codegraph_search("trace", kind="variable") → existing trace placeholders (already in dashboard)
codegraph_impact("traceId", depth=3)        → everything affected by the trace plumbing
```

**Production-grade benefit:** complete instrumentation in one pass. No "oh, I missed instrumenting the audio agent" 3 days into production.

### 6. Layer 5 — Orchestrator routing (LLM-first / keyword-fallback)

The current `promptToBlueprint.ts` uses keyword matching only and has the hardcoded astronaut/clock fallback bug. To replace with LLM-first/keyword-fallback (Pattern 04):
- Find every place that defaults to demo blueprint (the bug surface)
- Find every existing keyword rule (preserve them as fallback)

```
codegraph_search("astronaut", limit=20)       → finds the demo fallback insertion sites
codegraph_search("ENVIRONMENT_KEYWORDS")      → the existing keyword dictionary
codegraph_callers("getThemeForPrompt")        → all consumers of the current routing
codegraph_impact("promptToBlueprint")          → what depends on the current shape
```

**Production-grade benefit:** I can confidently replace the fallback knowing exactly which call sites and tests will need to update.

## Pre-launch / pre-deploy use cases

Beyond the build phase, code-graph helps after we ship:

### Code review before each release
```
codegraph_impact(<each-changed-symbol>, depth=2)
```
Generate a "blast radius report" automatically — "this PR changes 3 symbols, total downstream surface = 14 files, 22 callers." Reviewer sees the real impact in seconds.

### Hot-fix triage
```
codegraph_callers(<bug-symbol>) + codegraph_impact(<bug-symbol>)
```
"Production says scene rendering is broken." → 1 query → "27 callers across 4 files, here they are." Fix in minutes not hours.

### Onboarding new contributors / future Claude sessions
```
codegraph_context("how does Forge generate a movie")
```
Returns: WR → EN → CH → LI → AU → ED → Render dispatch chain + the data contracts between them, in one call. New contributor (or me-in-a-fresh-session) is productive immediately.

### Detecting orphaned code before shipping
Files where `codegraph_callers(<every-symbol>)` returns 0 = dead code candidate. Pre-launch dead-code sweep prevents shipping unused experimental routes.

## Cost benefit for Forge launch

| Phase | Without code-graph | With code-graph |
|---|---|---|
| **Bug fix (2D/3D render)** | ~6-8 calls, 30k tokens | ~3 calls, 10k tokens |
| **A2A-ify 7 specialists** | ~14 calls/agent × 7 = ~100 calls | ~5 calls/agent × 7 = ~35 calls |
| **Armor wrap 5 skills** | ~10 calls/skill × 5 = ~50 calls | ~3 calls/skill × 5 = ~15 calls |
| **oTel hookup full pass** | ~30 calls | ~10 calls |
| **Orchestrator rewrite** | ~25 calls | ~8 calls |
| **Per-PR impact analysis** | manual, ~15 min | 1 call, instant |

**Estimated cumulative savings to ship Forge v1: ~150 fewer tool calls, ~400k tokens, several hours of wall-clock time.**

These are the same magnitudes upstream benchmarked on Django/Tokio/VS Code at ~35% cheaper. Forge is smaller so absolute savings are smaller, but the **percentage win is the same.**

## Two things needed to unlock this

| What | Status | Who does it |
|---|---|---|
| **MCP server installed globally** (`npm i -g @colbymchenry/codegraph` or `npx`) | ❌ not done | User runs PowerShell |
| **`.codegraph/` index built for Forge** (`cd <forge-project>; codegraph init -i`) | ❌ not done | User runs PowerShell, OR grant me the permission |
| **Settings.json `mcpServers.codegraph` registered** | ❌ not done | User edits `~/.claude/settings.json` (or run `codegraph install --target=claude --yes`) |
| **Restart Claude Code** | ❌ not done | User restarts terminal |

Order: install global → register MCP → restart → init Forge index.

After these 4 steps, the `codegraph_*` tools appear in my MCP tool list and I can run any of the queries above for Forge work.

## What this means for the "ready to code" question

I'd been thinking of code-graph as a "nice to have." Re-reading the upstream benchmarks against Forge's actual file count and the 5-layer wrapper work ahead, it's actually a **prerequisite for fast/safe shipping**:

- Without it: A2A-ifying 7 specialists is a multi-day grep/read marathon with regression risk
- With it: A2A-ifying 7 specialists is a single afternoon of `codegraph_callers` + `codegraph_impact` checks before each rewrite

So when you ask "are we ready to code?" — code-graph being installed actually moves my readiness from 65% → ~85%. The remaining 15% is still your skills + test bundle + the 8 deployment-model gaps.

## Cross-references

- `knowledge/skills-inventory/code-graph/SKILL.md` — usage instructions
- `knowledge/skills-inventory/code-graph/install-log.md` — install record + PowerShell commands
- `knowledge/forge/INDEX.md` — Forge state (knows about the 5-layer plan)
- `knowledge/decisions/agent-composition-model.md` — the 5 layers in question
- Upstream: https://github.com/colbymchenry/codegraph
