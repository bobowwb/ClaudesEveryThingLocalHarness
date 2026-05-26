# Forge — Target User & UX North Star

**Date:** 2026-05-25
**Status:** LOCKED — defines who 2D/3D renders are for.
**Source:** User on 2026-05-25, verbatim:
> *"Design step 4，渲染，就是最后产品的 2D 和 3D 图给谁看？就是给这个 prompt 的输入者看，这个输入者的角色是一个新兴的创业人，他有许多的脑洞，然后他要开发一些更好的产品，制造更多的需求，新产品创业."*

## The user

**新兴创业者 / Aspiring entrepreneur with many brainstorming ideas, building new products to manufacture new demand.**

NOT:
- ❌ Manufacturer (looking for CAD/spec)
- ❌ Investor (looking for pitch deck)
- ❌ End consumer (browsing to buy)
- ❌ Industrial designer (looking for engineering drawings)

YES:
- ✅ Solo founder / 2-person startup
- ✅ Has 10 product ideas, only one will become real
- ✅ Needs to SEE what they're imagining before committing
- ✅ Decides "is this idea worth pursuing?" based on the 2D / 3D outputs
- ✅ Iterates fast: type prompt → see → reject or refine → type again

## What this means for 2D/3D design

### The 2D images are NOT product photos
They are **founder-decision-aid renders**. The job is to answer the founder's question:

> "If I were to actually build this product, would it look... cool? viable? worth $89? worth $340? would I be proud to launch it?"

So images need:
- **Aspirational** — make the founder excited about their own idea
- **Distinct across 5 tiers** — visually obvious that lite / standard / premium / pro / master are different products at different price points
- **Photographic quality** — not concept sketches; founder needs to feel "this could be on Amazon next month"
- **Standalone product on neutral background** — no lifestyle scene, founder is evaluating THE PRODUCT

### The 3D is the "is this real" moment
After founder sees 2D and picks one tier, the 3D scene answers:

> "Wait, does this actually exist as an object I can rotate? Could a factory really make this? Am I imagining something physically possible?"

So 3D needs:
- **Orbital camera** so founder can spin and feel the volume / proportions
- **Material faithful** — if Design said "aluminum alloy", the splat actually looks metallic
- **Quick** — founder is on idea #7 of the day, can't wait 5 minutes per render
- **Confidence-building** — once they orbit it, they should think "OK, this is the one I'm going to build"

## What this kills (UI/UX assumptions I had wrong)

| ❌ Wrong assumption | ✅ Correct because of "founder-as-user" |
|---|---|
| "Show technical CAD spec" | NO — show product photography, founders aren't engineers |
| "Investor pitch overlay with margin / TAM" | NO — Finance/Strategy data shows in *separate* panels, not on the image itself |
| "Multi-angle product views (front/side/top)" | NO — single hero shot per tier; orbit comes later in 3D step |
| "Mood/lifestyle staging" | NO — no people, no kitchen, no lifestyle. Just the product. |
| "5 stylistic moods (cinematic/dreamy/aerial/retro/noir)" | NO — that was movie thinking. 5 *tiers* differ by material/process/feature, NOT by photography style |
| "Manufacturer-grade engineering details" | NO — founders are imagining, not specing for the factory |

## What this confirms (UI/UX choices that are correct)

| ✅ Choice | Why correct for founder user |
|---|---|
| 5-tier grid all visible at once | Founder compares "premium vs pro" instantly |
| Click one tier → 3D viewer | Mimics "let me hold this in my hand before I commit" |
| Cheap fast iteration on prompt | Founders try 10 ideas/day; can't wait |
| BOM + margin in *separate* panels (already in `payload.search.bom`, `payload.finance.margin_pct`) | Founder sees feasibility WITHOUT cluttering the image |
| Compliance block surfaces clearly (already in `pipeline_status: "blocked_by_compliance"`) | Founder fails fast on bad ideas |

## Concrete prompt template (Step 1 — fal.ai FLUX call)

For each of the 5 tiers in DesignOutput.tiers, build a prompt like:

```
Industrial product photo of {request.product_name},
made of {tier.primary_material},
manufactured via {tier.process_human_readable},
key feature: {tier.feature_highlights[0]},
studio lighting, white background, e-commerce style,
sharp focus, 4k, professional product photography,
single object centered, no people, no lifestyle.
```

Where `process_human_readable` = humanize "injection_molding" → "injection molding", etc.

Across the 5 tiers, the resulting images will *naturally* differ because:
- material differs (ABS plastic → aluminum → titanium)
- process differs (injection_molding → cnc_machining → hybrid)
- feature_highlights differ (basic → AI integration)

This delivers what the founder needs: **visual differentiation that maps to real product decisions**, not arbitrary mood swaps.

## Concrete 3D prompt (Step 2 — fal.ai LGM call)

Input to LGM: the chosen tier's `image_url` (from Step 1).
LGM returns: a `.splat` URL.
Frontend mounts on `#renderCanvas` (or its Next.js equivalent on `/forge/[run_id]`).
Auto-orbit speed: slow (~0.3 rad/s) — founder watches it spin without input first, then can grab.

## Cross-references

- `forge/PRODUCT-DEFINITION-OTO1.md` — definitive product = 5-tier industrial blueprint
- `forge/VERIFIED-architecture-2026-05-25.md` — verified pipeline, 7 agents, real data shapes
- This file — defines WHO the renders serve and WHY
- `decisions/agent-composition-model.md` — 5-layer architecture (still valid)
