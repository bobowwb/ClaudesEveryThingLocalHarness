# Forge Product Spec — Complete

**Date:** 2026-05-24
**Status:** Spec complete, awaiting Accio write permission to start RED-GREEN cycle.
**Source:** User on 2026-05-24: *"把产品写出来，每一个 prompt 要生成 3-5 个新的产品建议，然后问 ICIO 怎么上线，找到那个链接把它更新掉"*

## Discovered facts (read-only inspection of Forge project)

| Item | Value |
|---|---|
| **Vercel project ID** | `prj_sf0Pn7pjUiAzUea2xy4mWkYyjvaf` |
| **Vercel project name** | `story2movie-ai` |
| **Vercel team** | `team_fyCVc5ZFmCjvATtGFnXoyUGS` |
| **Predicted live URL** | `https://story2movie-ai.vercel.app` |
| **Right-pane Waiting element** | `#renderPlaceholder` (dashboard.html line 202) |
| **Existing canvas** | `#renderCanvas` line 207, currently `style="display:none"` |
| **Existing video** | `#aiVideo` line 206, fal.ai HunyuanVideo renderer |
| **`.env.example`** | Only LiteLLM proxy keys; no fal.ai/replicate keys |
| **dev start** | `npm run dev` → `http-server -p 8080` |
| **test runner** | Playwright (`tests/e2e/`) |

## Step 1 — Right pane shows 3-5 product 2D variants per prompt

### Where in the DOM
Replace `#renderPlaceholder` (line 202) with a grid container that holds 3-5 image cards.

### Target HTML structure
```html
<!-- Replaces #renderPlaceholder -->
<div id="productGrid"
     class="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-4"
     aria-label="Generated product variants">
  <!-- 3-5 cards injected by JS, each: -->
  <div class="product-card relative aspect-square bg-slate-900 rounded-xl
              border border-slate-800 overflow-hidden cursor-pointer
              hover:border-blue-500/50 transition group"
       data-variant-id="v1">
    <img class="w-full h-full object-cover"
         alt="Variant 1 — moody cinematic"
         loading="lazy"
         src="...">
    <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80
                via-black/40 to-transparent p-2">
      <p class="text-[9px] text-slate-300 truncate">Variant 1</p>
      <p class="text-[8px] text-slate-500 truncate">Moody cinematic</p>
    </div>
    <div class="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/10 transition" />
  </div>
  <!-- ...repeat ×3-5 -->
</div>

<!-- Below the grid: existing #videoContainer / #renderCanvas (untouched in Step 1) -->
```

### Generation flow

```
User clicks Generate
   │
   ▼
generateMovie() (existing, in dashboard.html)
   │
   ▼
[NEW] api/generate-variants.js  (Vercel serverless function)
   │
   ├── parses user prompt into PromptAnalysis (existing keyword logic OR LLM)
   ├── builds 3-5 variant prompts:
   │     v1 = base style          ("cinematic, dramatic lighting")
   │     v2 = mood swap           ("dreamy, warm tones")
   │     v3 = camera swap         ("wide aerial shot, golden hour")
   │     v4 = era swap            ("retro 80s vhs aesthetic")
   │     v5 = color swap          ("monochrome noir")
   ├── for each variant: call fal.ai FLUX text-to-image
   │     fal.subscribe('fal-ai/flux/schnell', { prompt, image_size: '1024x1024' })
   ├── returns: { variants: [{ id, label, mood, image_url, ms }] }
   │
   ▼
JS receives, populates #productGrid with cards
   │
   ▼
User clicks a card → that variant becomes the chosen one for Step 2 (3D)
```

### Pricing
- fal.ai FLUX Schnell: ~$0.003/image × 5 = ~$0.015 per Generate click
- Acceptable for v1; Founder's $29 tier supports ~2000 generates

### API key handling
- Add to Vercel project env: `FAL_KEY` (server-side only, NEVER client)
- `.env.example` updated with `FAL_KEY=your-fal-ai-key-here`
- Local dev: `.env.local` (already gitignored)

### Error handling per Pattern 02 (Armor)
```javascript
async function generateVariants(prompt) {
  try {
    const resp = await fetch('/api/generate-variants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    return { success: true, variants: data.variants };
  } catch (err) {
    // L4 reflection: log to oTel store
    console.error('[generateVariants] failed', err);
    return { success: false, error: err.message, variants: [] };
  }
}
```

If `success: false` → render an error card in the grid, NOT a JS exception. (Pattern 02 — never raise.)

## RED tests for Step 1

File: `tests/e2e/step1-2d-variants.spec.js`

```javascript
import { test, expect } from '@playwright/test';

test.describe('Step 1: 3-5 product 2D variants', () => {

  test('grid renders with 3-5 variant cards', async ({ page }) => {
    await page.goto('http://localhost:8080/dashboard.html');
    await page.locator('#storyInput').fill('A lone astronaut on Mars');
    await page.click('#mainBtn');

    const grid = page.locator('#productGrid');
    await expect(grid).toBeVisible({ timeout: 60000 });

    const cards = grid.locator('.product-card');
    const count = await cards.count();
    expect(count).toBeGreaterThanOrEqual(3);
    expect(count).toBeLessThanOrEqual(5);
  });

  test('each card has a real image (non-empty src, naturalWidth > 0)', async ({ page }) => {
    await page.goto('http://localhost:8080/dashboard.html');
    await page.locator('#storyInput').fill('A lone astronaut on Mars');
    await page.click('#mainBtn');

    await page.waitForSelector('#productGrid .product-card img', { timeout: 60000 });
    const imgs = page.locator('#productGrid .product-card img');

    for (let i = 0; i < await imgs.count(); i++) {
      const img = imgs.nth(i);
      const src = await img.getAttribute('src');
      expect(src).toBeTruthy();
      expect(src).not.toBe('');
      const w = await img.evaluate(el => el.naturalWidth);
      expect(w).toBeGreaterThan(0);
    }
  });

  test('each card has variant label and mood', async ({ page }) => {
    await page.goto('http://localhost:8080/dashboard.html');
    await page.locator('#storyInput').fill('A lone astronaut on Mars');
    await page.click('#mainBtn');
    await page.waitForSelector('#productGrid .product-card', { timeout: 60000 });

    const labels = page.locator('#productGrid .product-card p').first();
    await expect(labels).toContainText(/Variant \d/);
  });

  test('clicking a card marks it selected', async ({ page }) => {
    await page.goto('http://localhost:8080/dashboard.html');
    await page.locator('#storyInput').fill('A lone astronaut on Mars');
    await page.click('#mainBtn');
    await page.waitForSelector('#productGrid .product-card', { timeout: 60000 });

    await page.locator('#productGrid .product-card').first().click();
    const selected = page.locator('#productGrid .product-card[data-selected="true"]');
    await expect(selected).toHaveCount(1);
  });

  test('error state: API failure shows error card not JS exception', async ({ page }) => {
    // Block the API to simulate failure
    await page.route('**/api/generate-variants', route => route.fulfill({ status: 500, body: 'fail' }));

    await page.goto('http://localhost:8080/dashboard.html');
    await page.locator('#storyInput').fill('Test');
    await page.click('#mainBtn');

    const errorCard = page.locator('#productGrid .product-card.error');
    await expect(errorCard).toBeVisible({ timeout: 30000 });

    // No uncaught JS errors
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    expect(errors).toHaveLength(0);
  });

});
```

## Step 1 acceptance criteria

- [x] Spec written (this document)
- [ ] RED: 5 tests above all FAIL when run against current code
- [ ] GREEN: implement → all 5 tests PASS
- [ ] Visual: screenshot shows grid of 3-5 product images (no "Waiting..." text)
- [ ] Manual: click Generate → real images appear within 60s
- [ ] Per-variant labels visible on hover

## Files to add (Step 1)

```
api/generate-variants.js              ← NEW (Vercel serverless)
tests/e2e/step1-2d-variants.spec.js   ← NEW (RED tests)
.env.example                          ← UPDATE (add FAL_KEY=...)
dashboard.html                        ← EDIT (replace #renderPlaceholder, add JS handler)
```

## Files NOT to touch (Step 1)

```
#aiVideo, #renderCanvas, #videoContainer  ← Step 2 territory; leave hidden
src/engine3d/*                            ← Step 2 territory
studio_orchestrator.py                    ← later, when 5-layer composition begins
memory_agent.py                           ← later
```

This is the surgical-changes principle (Karpathy rule #3): touch only what Step 1 requires.

## Continued in part 2

- Step 2 (3D Gaussian) detail
- ICIO deploy checklist
- Cross-references

See `production-plan-step1-2d-step2-3d-PART2.md` (next file).
