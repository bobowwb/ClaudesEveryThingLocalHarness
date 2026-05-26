# Forge Production Plan — Step 1 (2D) + Step 2 (3D Gaussian)

**Date:** 2026-05-23
**Scope:** Direct user requirement, clarified 2026-05-23.
**Source:** *"先把我们原来的网站右边的那个产品图先做出来，然后下一步把产品的动画的 3D 做出来"* (First: fix the right-pane product image. Next: turn it into animated 3D, ideally using a Gaussian engine.)

## The two-step product roadmap

### Step 1 — Right pane shows a real 2D product image

**Where:** `dashboard.html` middle column (Director's Blueprint pane), currently shows `"Waiting for script..."`.

**What the user wants to see:**
- After clicking "Generate Movie", the Director's Blueprint pane fills with an actual product/scene image (not a text scene breakdown table).
- Per scene: a `<img>` element with a real image URL.

**What needs to change in code:**
1. Add `<img id="scenePreview2D" alt="Scene preview">` slot inside `#resultContent` (currently lines 142-144 of dashboard.html).
2. Wire `generateMovie()` to populate `<img>.src` from one of:
   - **a)** Existing fal.ai HunyuanVideo engine — extract first frame as still
   - **b)** A separate text-to-image call (FLUX, SDXL via fal.ai or Replicate)
   - **c)** Use Three.js `engine3d/blueprintEditor.js` to render canvas → toDataURL() → set as img src
3. Keep the existing `#renderCanvas` hidden for now (Step 2 will reveal it).
4. Keep the textual scene breakdown (`#resultContent` table) BELOW the image — it's still useful, just not THE output.

**TDD test:**
```javascript
// tests/e2e/step1-2d-render.spec.js
test('Director Blueprint pane shows real 2D product image after Generate', async ({ page }) => {
  await page.goto('/dashboard.html');
  await page.locator('#storyInput').fill('A lone astronaut on Mars');
  await page.click('#mainBtn');
  const img = page.locator('#scenePreview2D');
  await expect(img).toBeVisible({ timeout: 30000 });
  const src = await img.getAttribute('src');
  expect(src).toBeTruthy();
  expect(src).not.toBe('');
  // Image actually loaded (not broken)
  expect(await img.evaluate(i => i.naturalWidth)).toBeGreaterThan(0);
});
```

**Acceptance criteria:**
- ✅ Test passes
- ✅ Manually open dashboard.html, click Generate → see an image appear within 30s
- ✅ Screenshot captured proving it

---

### Step 2 — Upgrade 2D to animated 3D via Gaussian Splatting

**Why Gaussian Splatting (3DGS):**
- Per Forge's own `video-models-for-movie-project.md` §7 — it's already on the planned roadmap.
- **Image → 3D Gaussian Splatting → Render** path:
  1. Generate N multi-view images with FLUX (~ 4-8 views)
  2. Reconstruct 3DGS via InstantSplat / DreamGaussian (~30s)
  3. Render any camera path **for free** afterward
- Best for establishing/flythrough shots; hybrid with image-to-video for character action clips.
- Cheap rendering: once trained, camera moves are ~free vs. paying per video frame.

**Where the 3D shows in the UI:**
- `#renderCanvas` (currently `display:none` — line 207 of dashboard.html) becomes the 3D viewport.
- Reveal canvas, wire Three.js to mount a Gaussian Splatting renderer.

## Gaussian Splatting engine candidates (from prior knowledge — verify before commit)

I cannot live-search GitHub right now (auto-mode + hard-lock). These are the ones I know about from my training. **You verify on github.com directly OR send screenshots and I'll work from those.**

### Browser-runnable Three.js-compatible (Step 2 best fit)

| Project | What it is | Why it fits Forge |
|---|---|---|
| **mkkellogg/GaussianSplats3D** | Pure Three.js viewer, MIT license, browser-only | Drop-in for Forge — already uses Three.js. Loads `.ply` / `.splat` / `.ksplat` files. Probably the cleanest fit. |
| **antimatter15/splat** | WebGL viewer, vanilla JS | Smallest possible runtime; less Three.js integration but battle-tested |
| **huggingface/gsplat.js** | Hugging Face's Three.js Gaussian Splatting library | Active, well-documented |
| **playcanvas/supersplat** | PlayCanvas-based viewer + editor | More features but heavier; not Three.js-native |
| **dylanebert/gsplat.js** | Compact Three.js-friendly | Similar to mkkellogg, smaller ecosystem |

### Image-to-3DGS generation backends (server-side, for the "generate" half)

| Service / project | Notes |
|---|---|
| **fal.ai TripoSR** / **fal.ai LGM** / **fal.ai InstantSplat** | API access — Forge already uses fal.ai for HunyuanVideo, same auth flow |
| **Replicate DreamGaussian** | API access; Forge already has replicate-bridge.js |
| **Self-hosted InstantSplat** | More control but needs GPU; not v1 material |

## Recommended stack for Forge

**Frontend (Step 2 viewer):** `mkkellogg/GaussianSplats3D`
- Three.js native (Forge already uses Three.js)
- MIT license
- Loads `.ply` / `.splat` files generated server-side
- Camera controls built in

**Backend (Step 2 generator):** `fal.ai LGM` or `fal.ai TripoSR`
- Forge already integrates fal.ai (HunyuanVideo)
- Same API key flow
- Returns a downloadable splat file
- ~30s per scene generation (manageable for v1)

**Pipeline:**
```
User prompt
  ↓
LLM blueprint (existing)
  ↓
[Step 1] FLUX text→image → first scene preview shown in <img>
  ↓
[Step 2] Image → fal.ai LGM/TripoSR → .splat file URL
  ↓
GaussianSplats3D viewer mounts on #renderCanvas
  ↓
User can orbit/zoom; scene plays back
```

## Step 1 vs Step 2 split rationale

- **Step 1 ships fast, low risk.** Just one `<img>` + one fal.ai text-to-image call. Real product visible in ~hours.
- **Step 2 is bigger.** Multi-view generation + 3DGS reconstruction + viewer mount. Days, not hours.
- Shipping Step 1 alone already kills the bug user reported (no product picture). Step 2 is upgrade, not blocker.

## Skipping CodeGraphContext (the second project from the photo)

**Decision:** Skip. Already have `colbymchenry/codegraph` doing the same job. Adding a second code-graph tool when the first isn't even running yet would be dead weight.

If at some point we need a graph-DB-backed (Neo4j) version specifically — re-evaluate then.

## What I cannot do alone

| Need | Blocked by | Who unblocks |
|---|---|---|
| Verify Gaussian engine candidates on github.com | Auto-mode blocks WebSearch / curl github / WebFetch github | User: send screenshots OR pick one from candidates |
| Install npm packages (`@mkkellogg/gaussian-splats-3d`) | Hard-lock (no OS-level changes) | User: PowerShell |
| Edit Forge's `dashboard.html` | Permission rule for Accio path not in `~/.claude/settings.json` | User: PowerShell or add to settings |
| Run Playwright test | Same permission gap | User: trigger test runner |

## Open questions for you (please answer to unblock Step 1)

1. **Which 2D image source for Step 1?**
   - (a) fal.ai text-to-image (FLUX, ~$0.025/image, fast, high quality, **recommended**)
   - (b) Replicate text-to-image (similar but different API)
   - (c) Three.js canvas snapshot (free, fast, but looks like wireframe)
2. **Which Gaussian engine for Step 2?**
   - Default: `mkkellogg/GaussianSplats3D` + `fal.ai LGM`
   - Different choice? Send name/URL.
3. **Is there a fal.ai API key already configured** in Forge's `.env`?
4. **Should I start writing the failing test now** (RED phase) for Step 1, leaving the GREEN phase blocked on permission/installation — so you can review the test logic immediately?

## Cross-references

- `forge/INDEX.md` — Forge state
- `forge/ui-bug-2d-3d-render.md` — bug diagnosis (this is the cure)
- `forge/code-graph-launch-benefit.md` — why code-graph helps the rewrite
- `decisions/agent-composition-model.md` — 5-layer architecture this fits into
- `decisions/hard-lock-no-os-security-changes.md` — why I can't bypass auto-mode blocks
- Forge's own roadmap: `video-models-for-movie-project.md` §7 (3DGS pipeline already planned upstream)
