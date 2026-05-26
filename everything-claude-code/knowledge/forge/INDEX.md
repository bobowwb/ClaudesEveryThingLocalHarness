# Forge — Project State Memory

**⚠️ 2026-05-25 CORRECTION:** Earlier session work mis-identified the product as "story2movie / video generation." That was wrong. The real product is **OTO1 / Smart OTO1 Wizard** (Zero-to-One product lifecycle wizard). All `story2movie` spec files are now OBSOLETE.

**Purpose:** Single source of truth on the product's location, structure, current state, and next steps.
**Last updated:** 2026-05-25

## Identity (CORRECTED)

| Field | Value |
|---|---|
| **Product name** | **OTO1 / Smart OTO1 Wizard** (NOT "story2movie") |
| **Tagline** | Zero-to-One product lifecycle wizard |
| **Live URL** | **`https://project-mu-two-13.vercel.app/studio`** |
| **Backend stack** | spaCy v3.7 (NLP) + MAGMA 4D (memory) + A2A Orchestrator v1.2 |
| **4 wizard stages** | GATING → MARKET → PSYCHE → **DESIGN** (current) → (Supply Chain / Global Scale) |
| **Visible agents in UI** | Compliance Agent, Strategy Engine, (more — verify with Accio) |
| **Example user prompt** | "Industrial mop with 500k rotation durability, made for EU market" |

## What "Forge" originally meant in this knowledge base

Sessions before 2026-05-25 referred to "Forge" as the product name and assumed `dashboard.html` in `agents/DID-2799F4-.../project/` was the live product. That assumption was wrong. The `.vercel/project.json` there says `story2movie-ai` — a different (possibly demo / legacy) Vercel project, NOT `project-mu-two-13`.

## What I now need to learn (DO NOT GUESS)

User on 2026-05-25: *"具体的你要去问 Accio"* — Accio platform is the single source of truth.

Open questions (must be answered by Accio, NOT inferred from filesystem globbing):

1. **Which agent folder under `C:\Users\I075354\.accio\accounts\7087759244\agents\` contains the real source code for `project-mu-two-13`?**
2. **What does Design step 4 actually need to render** — 3-5 industrial design images of the product, or 3-5 positioning cards (function / premium / eco / value / innovative), or both?
3. **What role does 3D Gaussian splatting play** — user-facing product preview, manufacturer CAD, or investor demo?
4. **What are the actual agent names in OTO1?** Visible from screenshot: Compliance Agent, Strategy Engine. Likely there are more. NOT the WR/EN/CH/LI/AU/ED set I previously invented.
5. **Where is the API for the existing orchestrator? Why is it currently "API Unreachable"?**

## OBSOLETE files (story2movie misdirection — DO NOT use as reference)

- `production-spec-step1-2d-variants.md` — written for movie scene mood variants, wrong domain
- `production-spec-step2-3d-gaussian-and-deploy.md` — Gaussian splat for 3D scene, wrong domain
- `apply-step1-step2-powershell-guide.md` — points to wrong Vercel project (`story2movie-ai`, prj_sf0Pn7pjUiAzUea2xy4mWkYyjvaf)
- `code-graph-launch-benefit.md` — used WR/EN/CH/LI/AU/ED agents (movie pipeline), wrong agent set
- `production-plan-step1-2d-step2-3d.md` — same wrong frame
- `ui-bug-2d-3d-render.md` — diagnosed `#renderPlaceholder` in dashboard.html, but that's the wrong codebase

These remain on disk for audit trail (so future-me sees the mistake) but **must not be used as reference** for OTO1 work.

## What's still valid from earlier work

- ✅ `decisions/agent-composition-model.md` — 5-layer (A2A core + Armor + 4D Memory + oTel + Orchestrator) is architecture-level, applies to OTO1 too
- ✅ `decisions/skill-install-protocol.md` — how I install skills, domain-independent
- ✅ `decisions/hard-lock-no-os-security-changes.md` — operational rule, applies always
- ✅ `patterns/00-a2a-foundation.md` through `04-orchestrator-routing.md` — language-agnostic patterns, apply to any agent system
- ✅ `external-references.md` — pointers to user's wiki, MAGMA 4D matches what's visible in OTO1 screenshot
- ✅ `skills-inventory/code-graph/` — generic code-graph skill, useful for any project

## Reference projects (DO NOT EDIT)

| Path | Role |
|---|---|
| `C:\EPM_ACCUMULATION\appFnd\` | Architectural reference for oTel + 4D Memory + Armor + Orchestrator. Still valid as pattern source. |
| `C:\AI\knowledge\` | User's Obsidian wiki — authoritative on agent principles |
| `C:\AI\everything-claude-code(miss_useOHnow)\everything-claude-code\` | This repo. ECC plugin. Holds my `tmp/`, `knowledge/`, `.claude/` state. |

## Next step (HARD STOP)

**I do not write code or specs until Accio answers the 5 questions above.** Per user 2026-05-25: *"具体的你要去问 Accio"*.

User's job:
1. Open Accio (the platform UI)
2. Get the 5 answers above
3. Send to me
4. Then I plan Design step 4 implementation against the REAL product

My job in the meantime: nothing. Stand by. No speculative writing.

## Cross-references

- `decisions/agent-composition-model.md` — still valid 5-layer architecture
- `decisions/hard-lock-no-os-security-changes.md` — why I don't auto-discover by file globbing
- `patterns/INDEX.md` — wrapper layer patterns, valid for OTO1
- `external-references.md` — Obsidian wiki pointers (MAGMA 4D shown in OTO1 UI)

## Identity

| Field | Value |
|---|---|
| **Product name** | Forge / Story2Movie AI |
| **Tagline** | "Turn Your Stories Into 3D Movies in Seconds" |
| **Pitch line** | "World's first AI-powered movie blueprint engine. Powered by DeepSeek V4 — 90% cheaper than traditional animation pipelines." |
| **Pricing** | $29 lifetime (Founder's Special), 50 generations, commercial license |

## Path

**Project root** (real code lives here):
```
C:\Users\I075354\.accio\accounts\7087759244\agents\DID-2799F4-442799F4U1778493-5197-43E0D8\project\
```

**Account root:**
```
C:\Users\I075354\.accio\accounts\7087759244\
```

**Sibling agents under same account:**
| Agent DID | Role |
|---|---|
| DID-F456DA-13F456DAU1778493-5192-1958B7 | (purpose unknown — has agent-core) |
| DID-0D58EF-500D58EFU1778493-5196-E1956B | (purpose unknown — has agent-core) |
| DID-2799F4-442799F4U1778493-5197-43E0D8 | **← Forge product agent** |
| DID-DB9653-10DB9653U1778493-5199-FB4AC4 | **Skills + tests toolbox agent** (has `my_skills.md`, `tests/test_5_new_product_baselines.py`, `tests/e2e/test_forge_e2e.py`) |

## Reference projects (DO NOT EDIT)

| Path | Role |
|---|---|
| `C:\EPM_ACCUMULATION\appFnd\` | Architectural reference for oTel + 4D Memory + Armor + Orchestrator. Distilled into `knowledge/patterns/`. |
| `C:\AI\everything-claude-code(miss_useOHnow)\everything-claude-code\` | This repo. ECC plugin. Holds my `tmp/`, `knowledge/`, `.claude/` state. |

## Directory layout (Forge)

```
project/
├── index.html              ← marketing landing (no 2D/3D)
├── dashboard.html          ← THE PRODUCT UI — has #renderCanvas, #aiVideo, #videoContainer, #placeholder
├── arch.html               ← architecture diagram page
├── resume-demo.html        ← demo page
├── CLAUDE.md               ← Forge's own claude config (says it's Story2Movie AI)
│
├── src/engine3d/
│   ├── types.ts / types.js                  ← Movie3DBlueprint type contract
│   ├── promptToBlueprint.ts/.js             ← keyword-matching → blueprint (HARDCODED astronaut/clock fallback bug)
│   ├── blueprintEditor.js                   ← Three.js scene editor
│   ├── editCommandParser.js                 ← edit-mode command parser
│   └── videoRenderer.js                     ← video render orchestrator
│
├── api/                                     ← Vercel serverless
│   ├── generate-video.js
│   ├── llm-proxy.js
│   ├── magic-hour.js
│   ├── veo-bridge.js
│   └── replicate-bridge.js
│
├── *.py (Python pipeline)
│   ├── story_to_movie.py                    ← CLI: text → blueprint via DeepSeek/LiteLLM
│   ├── studio_orchestrator.py               ← multi-agent dispatcher (oTel-simulated)
│   ├── memory_agent.py                      ← BM25 + Ebbinghaus + RRF
│   └── harmonize_delta.py                   ← re-render only changed segment
│
├── Phase2/
│   ├── schemas/director_persona.schema.json ← .dpdna persona DNA file
│   ├── Planning/A2A_Marketplace_API.md
│   ├── Planning/Strategy_Phase2.md
│   ├── Coding/refactor_notes.md
│   ├── Testing/Audit/Audit_Report.md
│   ├── Testing/verification_report.md
│   └── Summary_Phase2.md
│
├── tests/
│   ├── test_keyword_logic.js                ← JS unit
│   ├── verify_phase2.py                     ← Python integration (plain assert, no pytest)
│   ├── ui_verification.md                   ← Playwright spec — INSUFFICIENT (see bug doc)
│   └── player_verification_report.md
│
├── test-results/                            ← Playwright failure screenshots
│   ├── story2movie-T3-fal-ai-ge-... (failed: video src not valid)
│   ├── story2movie-T4-replicate-engine-generates-video (failed)
│   ├── story2movie-T7-video-src-mixed-content-prevention (failed)
│   ├── story2movie-T9-single-scene-without-MediaRecorder (failed)
│   └── story2movie-T10-error-state-fal-ai-error (failed)
│
├── playwright.config.js
├── playwright-report/
├── docs/
│   ├── plan-b-engines.md
│   ├── handover-claude-code.md
│   ├── image-to-video-pipeline.md
│   ├── TDD-handover.md
│   └── video-generation-model-research.md
└── .vercel/
```

## Stack

| Layer | Tech |
|---|---|
| Frontend | static HTML + Tailwind CDN, vanilla JS modules |
| 3D engine | Three.js (in `src/engine3d/`) |
| Backend | Vercel serverless (Node) for API endpoints |
| Python pipeline | DeepSeek V4 / LiteLLM proxy → blueprint JSON |
| Video models | fal.ai HunyuanVideo (active), Replicate ZeroScope (free), Veo 3.1 (quota full) |
| Memory | BM25 + Ebbinghaus decay + RRF (in-process) |
| Schema | `.dpdna` (Director Persona DNA) — JSON Schema for trainable personas |

## Key concepts

- **Movie3DBlueprint** — typed JSON: world spec, characters, shots, timeline events, lighting, camera plan, telemetry. Shared contract between TS frontend and Python backend.
- **A2A Studio** — agent-to-agent dispatcher with simulated oTel trace. Six specialist agents: WR (writer), EN (environment), CH (character), LI (lighting), AU (audio), ED (editor).
- **Re-Harmonize Delta** — when user "hacks" prompt mid-production, only re-render the changed segment using `harmonize_delta.py`.
- **Director Persona DNA (`.dpdna`)** — sellable persona file: prompt_dna + distilled_memory + optional LoRA adapter_weights.

## Current state — open bug

See `forge/ui-bug-2d-3d-render.md` for the headline issue.

## What is missing vs. appFnd

| appFnd has | Forge missing |
|---|---|
| **A2A-compliant specialist agents** with `/.well-known/agent.json` + JSON-RPC POST | `studio_orchestrator.py` does in-process Python dispatch — NOT A2A. Specialists (WR/EN/CH/LI/AU/ED) need to become real network services. |
| `app/observability.py` SQLite trace store with 6 A2A completeness fields | no real oTel — UI only simulates trace |
| Agent Armor L1→L4 wrapping all skill calls | tools called raw from JS — no validate/permit/retry |
| `_with_4d_memory` per-stage closure | memory_agent.py exists but not wired into stages |
| LLM-first / keyword-fallback intent classifier | `promptToBlueprint.ts` is keyword-only; falls back to hardcoded astronaut/clock demo |
| `_persist_query_event` for every chat input | no chat persistence layer |
| Middleware chain (audit/telemetry/guardrail/memory/cost/eval) | no middleware concept |

## Application order (when work resumes)

Per `knowledge/patterns/INDEX.md` plan — **A2A FIRST**:

1. **A2A-ify each Forge specialist** → `agents/forge_<role>/a2a_app.py`. Card + JSON-RPC handler. Replace `studio_orchestrator.py` in-process dispatch with `_a2a_task` calls. (Pattern 00)
2. Port observability → `forge_observability.py`. Wire 6 A2A completeness fields → `#traceId`, `#orchestratorMsg`, `#orchScan`, agent rows. (Pattern 01)
3. Wrap one A2A skill with armor → start with `render_3d` (cheapest). (Pattern 02)
4. Replace `promptToBlueprint.ts` with LLM-first intent classifier; surface `nlp_unknown` instead of demo fallback. (Pattern 04)
5. Add `_with_4d_memory` wrapper around each orchestrator stage. (Pattern 03)

## Next step (now)

Awaiting user's skills + composed test cases bundle (per session 2026-05-22 conversation).

## Permissions reminder

`~/.claude/settings.json` permissions.allow does NOT yet include the Accio path. When edits to Forge are needed, either:
- Approve each Write/Edit prompt as it pops up, OR
- Add: `"Write(C:/Users/I075354/.accio/accounts/7087759244/**)"`, `"Edit(C:/Users/I075354/.accio/accounts/7087759244/**)"`

## Related knowledge

- `../patterns/INDEX.md` — the four architectural patterns to apply
- `../patterns/01-otel.md` ... `../patterns/04-orchestrator-routing.md` — pattern details
- `ui-bug-2d-3d-render.md` — the active bug (renders text rows instead of 2D/3D)
- `code-graph-launch-benefit.md` — how code-graph cuts ~150 tool calls / ~400k tokens off Forge launch work
- `production-plan-step1-2d-step2-3d.md` — **the active plan**: Step 1 = right-pane 2D image, Step 2 = upgrade to Gaussian Splatting 3D
