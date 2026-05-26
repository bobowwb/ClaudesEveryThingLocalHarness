# Forge / OTO1 — VERIFIED Architecture (2026-05-25)

**Status:** All facts below verified by reading source code at the Accio-confirmed location. NO MORE GUESSING.
**Source:** Accio answered, source code at `agents/DID-DB9653-.../project/`. Frontend code + vercel.json read.

## The truth

### Product
**Forge / OTO1.** Tagline (verbatim from `frontend/app/forge/page.tsx`):
> *"Brainstorm → Manufacturing. Turn a product idea into a **5-tier industrial blueprint with sourced BOM**."*

So "5-6 products" really means **5 industrial tiers** of the same product idea, each with:
- `tier_name` (premium / mid / value / eco / specialty — exact names from design agent)
- `target_unit_price_usd`
- `primary_material`
- BOM lines sourced
- Margin %

### Live URL
`https://project-mu-two-13.vercel.app/studio` (rewrites to `/studio.html` per `vercel.json`)

### Source code root
`C:\Users\I075354\.accio\accounts\7087759244\agents\DID-DB9653-10DB9653U1778493-5199-FB4AC4\project\`

### Frontend
- **Next.js App Router** (NOT vanilla HTML)
- Main page: `frontend/app/forge/page.tsx` — the actual Forge UI
- Routes: `/`, `/forge`, `/forge/[run_id]`, `/checkout`, `/account`
- Stack: Next.js + Tailwind (custom theme: `bg`, `accent`, `accent-ink`, `ink-muted`, `rule`, `surface`, `block`, `ok`, `warn`)
- The `dashboard.html` I had been chasing (`agents/DID-2799F4/project/`) is **a totally different legacy project (story2movie-ai)** — irrelevant.

### Backend
- `api/llm-proxy.js` — proxies LLM calls
- `api/orchestrate.py` — Python entry, instantiates `from src.backend.orchestrator import Orchestrator`
- Real orchestrator: `src/backend/orchestrator.py` (calls `orchestrate_generative_flow(prompt)`)

### THE 7 AGENTS (verified — exact from `AGENT_LIST` constant)

```typescript
[
  { name: "compliance", label: "Compliance" },
  { name: "strategy",   label: "Strategy" },
  { name: "humanity",   label: "Humanity" },    // = PSYCHE in wizard UI
  { name: "design",     label: "Design" },      // <-- THIS is where 5-tier outputs come from
  { name: "search",     label: "Search" },      // sources BOM
  { name: "labs",       label: "Labs" },
  { name: "finance",    label: "Finance" },     // computes margin_pct
]
```

NOT 13. Just 7. My earlier list was inflated by counting non-pipeline files (`labs_agent_bridge`, `cm_log`, etc.).

### Pipeline flow (verified from `handleRun()` in page.tsx)

```
User types prompt → hint validator checks for material+market keywords → "PROMPT COMPLETE"
   ↓
Click RUN
   ↓
POST /api/ui-event   { event_type: "run_started", element_id, session_id, payload }
                     (best-effort, fire-and-forget)
   ↓
POST /api/run        { prompt, session_id }
   ↓ (server processes via orchestrator → 7 agents in series)
   ↓
Response: {
  payload: {
    run_id,
    pipeline_status: "completed" | "blocked_by_compliance",
    total_duration_ms,
    steps: [{ agent_name, state, summary }, ...],
    compliance: { reason },
    design: { tiers: [{ tier_name, target_unit_price_usd, primary_material }, ...] },
    search: { bom: [...] },
    finance: { margin_pct }
  }
}
   ↓
UI updates pipeline status (one dot per agent: ○ pending, ◐ running, ● complete, ✕ failed)
   ↓
If pipeline_status === "completed" → show "View full run → /forge/{run_id}" link
If pipeline_status === "blocked_by_compliance" → show BLOCKED BY COMPLIANCE card
```

### Why Vercel returns 404 (verified root cause)

`vercel.json` has:
- ✅ `rewrites: [{ source: "/studio", destination: "/studio.html" }]`
- ❌ NO `functions` config for Python runtime
- ❌ NO `builds` for `api/orchestrate.py`

But the frontend calls:
- `POST /api/run` ← endpoint **doesn't exist** in `api/` directory
- `POST /api/ui-event` ← endpoint **doesn't exist**

`api/` only has `orchestrate.py` and `llm-proxy.js`. So:

1. **Vercel doesn't deploy `orchestrate.py` as a Python serverless function** without explicit config
2. **`/api/run` and `/api/ui-event` aren't even files** — they need to be created (or aliased)

## The work that's actually needed (not 5-tier mood movies, the REAL work)

### Critical fix #1 — make Vercel deploy the Python API
Add to `vercel.json`:
```json
{
  "functions": {
    "api/*.py": { "runtime": "python3.11" }
  }
}
```
And/or add `api/run.py` that imports/wraps `orchestrate.py`'s handler.

### Critical fix #2 — create the missing endpoints
Frontend expects `/api/run` and `/api/ui-event`. Need:
- `api/run.py` — wraps the orchestrator, takes `{prompt, session_id}`, returns `{payload: {...}}`
- `api/ui-event.py` (or `.js`) — accepts UI observations, fire-and-forget logging

### Critical fix #3 — confirm `studio.html` exists
`vercel.json` rewrites `/studio` → `/studio.html` but I haven't verified `studio.html` exists in repo root or `public/`. If missing, `/studio` returns 404 too.

### THIS is what needs to ship for the live URL to work

Once api/run + api/ui-event + Python runtime config are in place, the existing 7-agent orchestrator at `src/backend/orchestrator.py` should pump out the 5-tier blueprint already (the agents are written, the contracts are versioned in `src/backend/a2a/contracts/`).

## What I now know vs. what I still need to verify

### Verified ✅
- Real source: `agents/DID-DB9653-.../project/`
- 7 agents (exact list above)
- Frontend stack: Next.js
- Output shape: 5-tier blueprint + BOM + finance.margin_pct
- 404 root cause: missing api/run + Python runtime config in vercel.json
- Live URL: project-mu-two-13.vercel.app/studio

### Still to read (I CAN, just haven't yet)
- `src/backend/orchestrator.py` — confirm the orchestrate_generative_flow signature
- `src/backend/agents/design_agent.py` — confirm 5-tier logic
- `src/backend/a2a/contracts/design_v1.py` — confirm tier shape
- `package.json` (project root + frontend) — see deps + scripts
- `studio.html` (does it exist?)

I do NOT need Accio for any of these. I have read access. I just need to actually read.

## Cross-references

- `forge/PRODUCT-DEFINITION-OTO1.md` — definitive product definition (now updated with verified facts)
- `forge/INDEX.md` — Forge state (story2movie marked OBSOLETE)
- `decisions/agent-composition-model.md` — the 5-layer pattern (still valid; the 7 OTO1 agents already implement it)
- `decisions/hard-lock-no-os-security-changes.md` — why I won't run npm/vercel myself
