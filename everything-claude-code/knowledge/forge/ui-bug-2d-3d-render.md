# Forge UI Bug — No 2D/3D Product Render

**Purpose:** Locked-in diagnosis of the active Forge UI bug. Survives context resets.
**Last updated:** 2026-05-22
**Status:** Diagnosed. Not yet fixed (awaiting user's skills + tests bundle).

## User report

> "There's no product picture generate, it is a very plain table with line items and with a button."

## Diagnosis (confirmed by code read + test-failure screenshot)

The Forge dashboard renders **scaffolding only** (sidebar + 3 columns + button + agent rows + telemetry log). The slot where a 2D image or 3D scene should appear stays empty.

### Why — three concrete causes in `dashboard.html`:

1. **`#renderCanvas` is hardcoded `style="display:none"`** (line 207).
   ```html
   <canvas id="renderCanvas" class="absolute inset-0 w-full h-full" width="1280" height="720" style="display:none"></canvas>
   ```
   The 3D canvas is *defined* but **never made visible**. Three.js in `engine3d/blueprintEditor.js` and `videoRenderer.js` cannot paint to a hidden canvas.

2. **`#videoContainer` starts `class="hidden"`** (line 204). It un-hides only after `generateMovie()` succeeds — but only the `<video>` plays, the `<canvas>` underneath stays `display:none` regardless.

3. **No `<img>` element** for a 2D still preview anywhere on the page.

4. **`#placeholder` stays as "Waiting for script..."** because the generation path goes straight to `<video>` and skips the 2D step.

5. **`#resultContent` (Director's Blueprint pane)** shows a *textual scene breakdown* (lines 142-144) — that's the "plain table with line items" the user described.

### Why the existing test misses this

`tests/ui_verification.md` only asserts:
- `#mainBtn` visible ✅
- `#orchestratorMsg` says "Orchestrating" ✅
- `#videoContainer` becomes visible ✅

It **never asserts**:
- ❌ `#renderCanvas` is visible (display ≠ none)
- ❌ `#renderCanvas` has nonzero painted pixels
- ❌ `<img>` shows a real 2D preview
- ❌ `#aiVideo` has a non-empty `src` after generation

So the test passes while the user sees an empty box.

### Existing test-failure screenshots (already on disk)

In `tests/test-results/`:
- T3 — `fal-ai generates video and src is a valid video URL` — FAILED
- T4 — `replicate engine generates video` — FAILED
- T7 — `video src mixed-content-prevention` — FAILED
- T9 — `single scene without MediaRecorder concat` — FAILED
- T10 — `error state when fal.ai returns an error` — FAILED

The dashboard view in those screenshots = exactly the user's complaint (3 columns of scaffolding + no visual product).

## Fix plan (TDD, when work resumes)

### RED — write failing tests
Add Playwright assertions:
```
canvas = page.locator('#renderCanvas')
expect(canvas).toBeVisible()                              // not display:none
expect(await canvas.evaluate(c => c.width > 0))           // has size
expect(await canvas.evaluate(c => {
    const ctx = c.getContext('2d') || c.getContext('webgl')
    // verify non-blank: any non-transparent pixel exists
}))

img = page.locator('img.scene-preview-2d')                 // new element
expect(img).toBeVisible()
expect(await img.evaluate(i => i.naturalWidth > 0))        // real image
```

### GREEN — minimal code changes in dashboard.html + engine3d
1. Remove `style="display:none"` from `#renderCanvas` (or toggle it on after blueprint exists).
2. Add `<img id="scenePreview2D" class="scene-preview-2d" alt="Scene preview">` slot inside Director's Blueprint pane.
3. Wire `engine3d/blueprintEditor.js` to mount Three.js scene to `#renderCanvas` immediately when blueprint object is built (don't wait for video).
4. Wire `videoRenderer.js` (or a new helper) to paint the first frame as a 2D still onto `#scenePreview2D` while 3D loads.
5. Add fallback chain: 3D paint fails → 2D image; 2D fails → log to orchestrator + retry route.

### REFACTOR — apply patterns
Once green:
- Wrap `generate_blueprint`, `render_3d_scene`, `generate_video` with **Agent Armor** (knowledge/patterns/02).
- Wire **oTel** (knowledge/patterns/01) so dashboard's `#traceId`, `#orchestratorMsg`, `#orchScan` reflect real trace.
- Add **`_with_4d_memory`** (knowledge/patterns/03) around each stage.
- Replace `promptToBlueprint.ts` keyword-only with **LLM-first / keyword-fallback** classifier (knowledge/patterns/04). Surface `nlp_unknown` rather than silent astronaut/clock demo.

## Constraint reminder

- Real edits → only into `C:\Users\I075354\.accio\accounts\7087759244\agents\DID-2799F4-...\project\`
- Scratch tests / spike code → ECC `tmp/`
- DO NOT touch `C:\EPM_ACCUMULATION\appFnd\` — reference only

## Related knowledge

- `INDEX.md` — Forge project state
- `../patterns/INDEX.md` — architectural patterns to apply
- Failing test screenshots: `tests/test-results/*/test-failed-1.png` (in Forge project)
