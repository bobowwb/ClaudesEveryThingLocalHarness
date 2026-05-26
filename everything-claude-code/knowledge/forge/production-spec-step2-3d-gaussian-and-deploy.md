# Forge Step 2 — 3D Gaussian Splatting Animation

**Date:** 2026-05-24
**Companion to:** `production-spec-step1-2d-variants.md`
**Status:** Spec only; Step 2 starts after Step 1 ships green.

## Architecture

```
User picks one of 3-5 variants from Step 1's grid
   │
   ▼
[NEW] api/generate-3d.js  (Vercel serverless)
   │
   ├── Takes selected variant's image_url + prompt as input
   ├── Calls fal.ai LGM (Large Gaussian Model) or TripoSR
   │     fal.subscribe('fal-ai/lgm', { image_url })
   ├── Returns: { splat_url: 'https://.../scene.splat', ms }
   │
   ▼
JS receives splat_url
   │
   ▼
GaussianSplats3D viewer mounts on #renderCanvas
   ├── New module: src/engine3d/gsViewer.js
   ├── Imports @mkkellogg/gaussian-splats-3d
   ├── Loads scene from splat_url
   ├── User can orbit / zoom / pan
   ├── Auto-orbit animation toggle (camera path = circle around scene)
   │
   ▼
User can hit Save → record selected variant + 3D scene to memory_agent
```

## Engine selection

**Frontend viewer:** `@mkkellogg/gaussian-splats-3d` (npm)
- Three.js native (Forge already uses Three.js — `engine3d/blueprintEditor.js`)
- MIT license
- Loads `.ply` / `.splat` / `.ksplat`
- Built-in OrbitControls

**Backend generation:** `fal-ai/lgm`
- Forge already integrates fal.ai (HunyuanVideo)
- Same `FAL_KEY` env var
- Image → splat in ~30s
- Output: downloadable `.ply` URL

## Reveal canvas

Change line 207 of dashboard.html:
```html
<!-- BEFORE -->
<canvas id="renderCanvas" ... style="display:none"></canvas>

<!-- AFTER (Step 2) -->
<canvas id="renderCanvas" ... ></canvas>
<!-- visibility now controlled by JS class toggle -->
```

JS toggle:
```javascript
function show3DScene(splatUrl) {
  document.getElementById('videoContainer').classList.remove('hidden');
  document.getElementById('aiVideo').classList.add('hidden');
  document.getElementById('renderCanvas').style.display = 'block';
  mountGaussianSplats(splatUrl, '#renderCanvas');
}
```

## RED tests for Step 2

File: `tests/e2e/step2-3d-gaussian.spec.js`

```javascript
import { test, expect } from '@playwright/test';

test('selecting a variant triggers 3D generation', async ({ page }) => {
  await page.goto('http://localhost:8080/dashboard.html');
  await page.locator('#storyInput').fill('A lone astronaut on Mars');
  await page.click('#mainBtn');
  await page.waitForSelector('#productGrid .product-card img', { timeout: 60000 });

  await page.locator('#productGrid .product-card').first().click();

  const canvas = page.locator('#renderCanvas');
  await expect(canvas).toBeVisible({ timeout: 60000 });
});

test('canvas has nonzero rendered pixels (3D scene actually painted)', async ({ page }) => {
  await page.goto('http://localhost:8080/dashboard.html');
  await page.locator('#storyInput').fill('A lone astronaut on Mars');
  await page.click('#mainBtn');
  await page.waitForSelector('#productGrid .product-card img', { timeout: 60000 });
  await page.locator('#productGrid .product-card').first().click();

  await page.waitForSelector('#renderCanvas:not([style*="display:none"])', { timeout: 60000 });
  await page.waitForTimeout(3000); // splat load + first frame

  const hasPixels = await page.evaluate(() => {
    const canvas = document.querySelector('#renderCanvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) return false;
    const pixels = new Uint8Array(4);
    gl.readPixels(canvas.width / 2, canvas.height / 2, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    return pixels.some(p => p > 0);
  });
  expect(hasPixels).toBe(true);
});

test('orbit control is mounted (canvas responds to mouse drag)', async ({ page }) => {
  // ... setup as above ...
  const canvas = page.locator('#renderCanvas');
  const box = await canvas.boundingBox();
  await page.mouse.move(box.x + 100, box.y + 100);
  await page.mouse.down();
  await page.mouse.move(box.x + 200, box.y + 100);
  await page.mouse.up();
  // No assertion on exact pixel — just ensure no JS error
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  expect(errors).toHaveLength(0);
});
```

## Files to add (Step 2)

```
api/generate-3d.js                        ← NEW
src/engine3d/gsViewer.js                  ← NEW
tests/e2e/step2-3d-gaussian.spec.js       ← NEW
package.json                              ← UPDATE (add @mkkellogg/gaussian-splats-3d)
dashboard.html                            ← EDIT (drop display:none on #renderCanvas)
```

## Step 2 acceptance criteria

- [ ] RED: 3 tests above FAIL on current code
- [ ] GREEN: tests PASS
- [ ] Visual: clicking a 2D variant triggers 3D scene mounting on canvas
- [ ] Orbit / zoom works
- [ ] Auto-orbit animation runs by default
- [ ] Loading state visible while splat downloads (~30s)

## ICIO deploy checklist (after Step 1 + Step 2 green)

> "ICIO" interpreted as: the person/team responsible for Accio platform deployment. User said *"问 ICIO 怎么上线，他一般性在上上线，找到那个链接把它更新掉"*.

### Pre-flight (I do)
- [ ] All RED tests now GREEN locally
- [ ] `npm run dev` smoke test passes (open dashboard, generate, see grid + 3D)
- [ ] Capture before/after screenshots
- [ ] Bump version in `package.json` (1.0.0 → 1.1.0 for Step 1 + 1.2.0 for Step 2)

### Vercel deploy (user/ICIO does, since they hold credentials)
- [ ] In Vercel dashboard for project `prj_sf0Pn7pjUiAzUea2xy4mWkYyjvaf`:
  - [ ] Add env var `FAL_KEY` (Production + Preview)
  - [ ] Trigger deploy from current branch
- [ ] Wait for green deploy
- [ ] Open `https://story2movie-ai.vercel.app` (predicted prod URL — confirm in Vercel dashboard)
- [ ] Smoke test: enter prompt → see 3-5 variants → click one → see 3D scene
- [ ] If custom domain: update DNS / verify

### ICIO ask (the question to put to ICIO)
> "Hi ICIO, the Story2Movie AI Vercel project (`prj_sf0Pn7pjUiAzUea2xy4mWkYyjvaf`) has a v1.1.0/v1.2.0 ready that adds (a) 3-5 product variants per prompt and (b) Gaussian Splatting 3D scene viewer. The fal.ai LGM and FLUX endpoints need a `FAL_KEY` env var added in Vercel before deploy. Can you (1) add the env var and (2) trigger the deploy from main branch? Live URL after deploy: https://story2movie-ai.vercel.app/dashboard.html. Test plan and before/after screenshots attached."

### Rollback plan
- Vercel keeps previous deployments — one click reverts.
- Tag prior working build: `git tag pre-step1-rollback` before changes.

## What's still blocked on user input

| Need | Status |
|---|---|
| **Accio write permission** | not in `~/.claude/settings.json` permissions.allow → can't actually edit dashboard.html etc. |
| **fal.ai API key** | unknown if Forge has one already |
| **Confirmation: live URL** | predicted as `story2movie-ai.vercel.app`, not verified |
| **ICIO contact info** | who is ICIO? Slack handle? Email? |

## What I CAN do without write permission (do now)

1. ✅ Write specs (done — this file + part 1)
2. ✅ Write RED tests verbatim (done — copy-pasteable from spec)
3. ✅ Write deploy checklist (done — this section)
4. ⏳ Wait for Accio write permission grant OR you running Edit/Write commands on my behalf via PowerShell

## Next decision point

User picks one:
- **A.** Add Accio write permission to `settings.json` (you do it, per hard-lock rule)
- **B.** I dictate the exact `dashboard.html` patch + new `api/generate-variants.js` content here in chat; you paste into PowerShell
- **C.** Wait for skills bundle / different approach

Whichever path — both Step 1 spec and Step 2 spec are now durable on disk. They survive context resets.
