# Forge = OTO1 — DEFINITIVE PRODUCT DEFINITION

**Date:** 2026-05-25
**Status:** LOCKED. This is the ONLY correct definition. All prior interpretations are wrong.
**Source:** User on 2026-05-25, verbatim:
> *"我们这个项目跟 story to movie 没有关系，Zero relation. 我们这个项目就是 zero two o, 然后名字叫 forge, 就是做产品的，根据一个 prompt 能生成 5-6 个根据 prompt design 的一个产品."*

## The one sentence

**Forge = OTO1 (Zero-to-One). Input one prompt → output 5-6 product designs.**

## What this means concretely

- **Product type:** physical/industrial product designs (e.g. "industrial mop with 500k rotation durability for EU market" → 5-6 different mop designs)
- **NOT a movie / video / scene generator**
- **NOT** a "Story2Movie AI"
- **NOT** about cinematic mood variants (Cinematic / Dreamy / Aerial / Retro / Noir — DROP these)
- **The 5-6 outputs ARE products** — different design approaches to the same product brief

## What "5-6 products from one prompt" means

Each output is a different product *design*, NOT a different mood/tone of the same scene. Examples of how 5-6 designs might differ for the mop prompt:

| Variant axis | Example outputs |
|---|---|
| Material composition | aluminum alloy / stainless / composite / recycled plastic / titanium |
| Form factor | telescopic / fixed / folding / multi-head / robotic |
| Use case optimization | hospital-grade / industrial floor / outdoor / wet+dry / chemical-resistant |
| Manufacturing tier | premium / mid / value / eco / professional |
| Market positioning | EU compliance focus / China cost focus / US safety focus / global universal / niche specialty |

The Design Agent decides which axes to vary based on the prompt. **NOT pre-baked stylistic moods.**

## What's correct from prior knowledge work (KEEP)

✅ **Architecture is right:** 5-layer (A2A core + Armor + 4D Memory + oTel + Orchestrator) — applies to ANY agent system, including OTO1
✅ **`https://project-mu-two-13.vercel.app/studio`** — confirmed live URL
✅ **Backend stack visible in screenshot:** spaCy v3.7 NLP + MAGMA 4D memory + A2A Orchestrator v1.2
✅ **Wizard 4 stages:** GATING → MARKET → PSYCHE → DESIGN
✅ **Visible agents:** Compliance Agent, Strategy Engine (more from Accio)
✅ **MAGMA 4D matches user's existing wiki** at `C:\AI\knowledge\concepts\MAGMA — 4 Orthogonal Memory Dimensions.md`

## What was wrong (DROP / OBSOLETE)

❌ "Story2Movie" — wrong product
❌ "Movie blueprint / Movie3DBlueprint" — wrong domain
❌ WR / EN / CH / LI / AU / ED agent set — that was a movie pipeline (writer/environment/character/lighting/audio/editor)
❌ Cinematic / Dreamy / Aerial / Retro / Noir variants — wrong axis
❌ `agents/DID-2799F4-.../project/` as the source — that's a different (legacy?) Vercel project (`story2movie-ai`), NOT `project-mu-two-13`
❌ fal.ai HunyuanVideo for video — wrong service
❌ Director's Blueprint pane — wrong UI

## What I still need from Accio (5 questions) — REVISED 2026-05-25 evening

User clarification: *"所有这些流都是通过 agent，一个一个 agent 跑出来的，**之前定义的**"*

Translation: the agents already exist and were defined before. I just need to use them, NOT invent them.

### My HYPOTHESIS (await Accio confirmation)

The real source code for `project-mu-two-13` is at:
```
C:\Users\I075354\.accio\accounts\7087759244\agents\DID-DB9653-10DB9653U1778493-5199-FB4AC4\project\
```

Evidence:
- Has `src/backend/agents/` with ~13 agent Python files
- Has `0TO1_PRD.md`, `0TO1_AGENT_CARD.md` — directly named OTO1
- Has `MASTER_EXECUTION_BLUEPRINT.md`, `SHORTEST_PATH_MANUFACTURING.md` — product/manufacturing direction
- Has `tests/test_5_new_product_baselines.py` — **"5 new product baselines"** matches "5-6 products" requirement
- Has `tests/screenshots/product_1.png` ... `product_5.png` — 5 product screenshots already
- Has `tests/screenshots/global_product_1.png` ... `global_product_5.png` — global variants
- Has `tests/screenshots/drilldown_1.png` ... `drilldown_5.png` — per-product drilldowns
- Has `tests/screenshots/ux_resumption_1.png` ... `ux_resumption_5.png` — wizard resumption flows

### The agent roster (from `DID-DB9653/project/src/backend/agents/`)

| File | Agent role |
|---|---|
| `compliance_agent.py` | Compliance Agent (visible in screenshot ✓) |
| `strategy_agent.py` | Strategy Engine (visible in screenshot ✓) |
| `macro_strategic_agent.py` | Macro Strategic Agent |
| `design_agent.py` | **Design Agent** — likely runs DESIGN step 4 (the 5-6 products) |
| `search_agent.py` | Search Agent |
| `humanity_agent.py` | Humanity Agent (Psyche?) |
| `labs_agent.py` | Labs Agent |
| `labs_agent_bridge.py` | Labs Agent Bridge |
| `finance_agent.py` | Finance Agent |
| `testcase_agent.py` | Test Case Agent |
| `cm_log_agent.py` | CM Log Agent |
| `memory_agent.py` (root level) | 4D MAGMA memory |

### A2A contracts (from `src/backend/a2a/contracts/`)

Each agent has a versioned contract — confirms 5-layer model is already real:
- `compliance_v1.py`, `strategy_v1.py`, `design_v1.py`, `humanity_v1.py`,
  `labs_v1.py`, `finance_v1.py`, `testcase_v1.py`, `search_v1.py`,
  `orchestrator_v1.py`

These are the A2A skill schemas (Pattern 00). Already defined.

### So what I actually need (revised)

1. **Confirm DID-DB9653/project IS `project-mu-two-13`** (yes/no)
2. **Confirm the 13 agents listed above are the OTO1 set** (yes/no)
3. **For DESIGN step 4 specifically** — which agent(s) compose the 5-6 product designs? Just `design_agent.py` or also Strategy + Market chained in?
4. **Where in the existing code is the prompt → 5-6 products flow currently broken** (since the screenshot shows "API Unreachable")?
5. **Should the 5-6 products show as 2D images (fal.ai render) or as concept cards (text+spec) or both?**

I am NOT inventing. I am asking which existing pieces to assemble.

## Code-level next steps (after Accio answers)

The 5-6 product designs likely flow:

```
User prompt: "industrial mop with 500k rotation durability for EU market"
   ↓
Compliance Agent:  EU regulatory check → pass / fail / requires-modification
   ↓
Market Agent:      EU mop market size, key players, price points
   ↓
Psyche Agent:      buyer persona, brand positioning options
   ↓
Strategy Engine:   geopolitical / supply chain / macro risk
   ↓
DESIGN Agent (the step 4 work):
   ↓
   For each of 5-6 design axes:
     - Compose design brief (axis-specific)
     - Call image gen (fal.ai FLUX or similar) for industrial render
     - Optionally: call 3D gen (fal.ai LGM / TripoSR) for mesh/splat
     - Build product spec card (materials, dimensions, features, est. cost)
   ↓
   Return: [
     { id: 'd1', axis: 'premium-aluminum',  image_url, spec, ... },
     { id: 'd2', axis: 'value-composite',   image_url, spec, ... },
     { id: 'd3', axis: 'eco-recycled',      image_url, spec, ... },
     { id: 'd4', axis: 'modular-telescopic',image_url, spec, ... },
     { id: 'd5', axis: 'robotic-assist',    image_url, spec, ... },
     { id: 'd6', axis: 'hospital-grade',    image_url, spec, ... },
   ]
   ↓
User picks one → continues to Supply Chain / Global Scale steps
```

But this is **my hypothesis**, not Accio truth. Confirm before coding.

## Hard rule for me going forward

> Until Accio answers the 5 questions, I do NOT write product code. I can write architecture/pattern documentation that's domain-independent (already done). I can NOT write OTO1-specific specs that assume product semantics I haven't verified.

This file is the anchor. Every future spec must cite this file's "Definitive Product Definition" section.
