# Forge — Apply Step 1 & 2 (PowerShell deploy guide)

**Date:** 2026-05-24
**Status:** All code staged in ECC tmp/. User runs PowerShell to copy + install + test + deploy.
**Reason:** Hard-lock rule (2026-05-23) forbids me from modifying OS-level security policies, including the auto-mode classifier blocking writes to Accio path. So I stage in ECC tmp/ (allowed); user copies to Accio.

## What's staged at `C:\AI\everything-claude-code(miss_useOHnow)\everything-claude-code\tmp\forge-staging-20260524\`

```
api\generate-variants.js          (Step 1 — fal.ai FLUX, 3-5 variants)
api\generate-3d.js                (Step 2 — fal.ai LGM, 2D image -> 3DGS splat)
src\engine3d\gsViewer.js          (Step 2 — Three.js + GaussianSplats3D viewer)
tests\e2e\step1-2d-variants.spec.js  (Step 1 RED tests)
```

Still TODO (in this same staging dir, before user runs deploy):
```
tests\e2e\step2-3d-gaussian.spec.js   (Step 2 RED tests)
patches\dashboard.html.patch          (UI diff)
patches\env.example.patch             (FAL_KEY add)
patches\package.json.patch            (deps add)
```

## PowerShell deploy script — user runs ONE TIME

```powershell
# === 0. Set paths ===
$ECC = "C:\AI\everything-claude-code(miss_useOHnow)\everything-claude-code"
$STAGE = "$ECC\tmp\forge-staging-20260524"
$FORGE = "C:\Users\I075354\.accio\accounts\7087759244\agents\DID-2799F4-442799F4U1778493-5197-43E0D8\project"

# === 1. Stamp current Forge (rollback safety) ===
cd $FORGE
git tag pre-step1-rollback 2>$null
git status

# === 2. Install npm deps ===
npm install @fal-ai/serverless-client @mkkellogg/gaussian-splats-3d three

# === 3. Copy staged files into Forge ===
Copy-Item -Path "$STAGE\api\generate-variants.js" -Destination "$FORGE\api\generate-variants.js" -Force
Copy-Item -Path "$STAGE\api\generate-3d.js"       -Destination "$FORGE\api\generate-3d.js"       -Force
New-Item -Path "$FORGE\src\engine3d" -ItemType Directory -Force | Out-Null
Copy-Item -Path "$STAGE\src\engine3d\gsViewer.js" -Destination "$FORGE\src\engine3d\gsViewer.js" -Force
New-Item -Path "$FORGE\tests\e2e" -ItemType Directory -Force | Out-Null
Copy-Item -Path "$STAGE\tests\e2e\step1-2d-variants.spec.js" -Destination "$FORGE\tests\e2e\step1-2d-variants.spec.js" -Force

# === 4. Add FAL_KEY to .env.example (manual edit recommended) ===
# Add this line to $FORGE\.env.example :
#   FAL_KEY=your-fal-ai-key-here

# === 5. Set local FAL_KEY for dev (you provide the value) ===
# Edit $FORGE\.env.local (gitignored):
#   FAL_KEY=fal-xxx-your-real-key-xxx

# === 6. Run dev server in one terminal ===
cd $FORGE
npm run dev    # http://localhost:8080

# === 7. Run RED tests in another terminal — should FAIL initially ===
cd $FORGE
npx playwright test tests/e2e/step1-2d-variants.spec.js
# Expected: ALL 5 tests FAIL because dashboard.html not yet patched (no #productGrid)

# === 8. Apply dashboard.html patch (see patches\dashboard.html.patch) ===
# I will dictate exact changes in chat once you confirm steps 1-7 complete

# === 9. Re-run RED tests — should PASS now ===
npx playwright test tests/e2e/step1-2d-variants.spec.js

# === 10. Manual smoke test ===
# Open http://localhost:8080/dashboard.html
# Type "A lone astronaut on Mars" -> click Generate -> see 3-5 image cards in middle column

# === 11. Capture screenshot ===
npx playwright codegen http://localhost:8080/dashboard.html
# OR use snipping tool — save to $ECC\knowledge\forge\screenshots\step1-after-2026-05-24.png

# === 12. Commit ===
cd $FORGE
git add api/generate-variants.js api/generate-3d.js src/engine3d/gsViewer.js tests/e2e/step1-2d-variants.spec.js .env.example package.json package-lock.json dashboard.html
git commit -m "feat: step1 — render 3-5 product 2D variants per prompt + step2 scaffolding"

# === 13. Push (Vercel auto-deploys) ===
git push origin main
```

## Vercel env var add — required before deploy works

```
Vercel dashboard -> story2movie-ai project -> Settings -> Environment Variables
  Add: FAL_KEY = <your fal.ai key>
  Scopes: Production + Preview + Development
```

## Live URL (predicted, please confirm in Vercel dashboard)

```
https://story2movie-ai.vercel.app
https://story2movie-ai.vercel.app/dashboard.html  (the actual UI)
```

If the project has a custom domain attached, that's the real URL. Vercel dashboard Project -> Settings -> Domains shows it.

## ICIO ask — exact wording to send

> Hi ICIO,
>
> The Story2Movie AI Vercel project (`story2movie-ai`, project ID `prj_sf0Pn7pjUiAzUea2xy4mWkYyjvaf`, team `team_fyCVc5ZFmCjvATtGFnXoyUGS`) has a v1.1.0 update ready that:
>
> 1. Adds `/api/generate-variants` endpoint — generates 3-5 product 2D variants per user prompt using fal.ai FLUX Schnell.
> 2. Adds `/api/generate-3d` endpoint — generates a 3D Gaussian Splatting scene from any chosen 2D variant using fal.ai LGM.
> 3. Updates `dashboard.html` to show a variant grid in the Director's Blueprint pane (instead of "Waiting for script..." placeholder).
> 4. Mounts `@mkkellogg/gaussian-splats-3d` viewer on `#renderCanvas` for the 3D scene.
>
> Before you trigger the deploy:
> 1. Please add `FAL_KEY` env var to the Vercel project (Production + Preview), value from our shared 1Password / secret store entry "fal.ai Story2Movie".
> 2. Trigger a fresh deploy from main (`vercel --prod` or via dashboard).
>
> Smoke test plan after deploy:
> - Open `https://<live-url>/dashboard.html`
> - Type "A lone astronaut on Mars" → click Generate
> - Verify: 3-5 image cards appear in middle column within ~30s
> - Click any card → verify 3D scene renders on the right canvas within ~60s
>
> Rollback: previous Vercel deployment can be redeployed in 1 click; we also have git tag `pre-step1-rollback` locally.
>
> Estimated user-facing improvement: replaces empty "Waiting" state with real product imagery on every Generate click. Direct fix to the user complaint that "the dashboard renders only a plain table with line items, no product picture."

## Cross-references

- `production-spec-step1-2d-variants.md` — full Step 1 spec
- `production-spec-step2-3d-gaussian-and-deploy.md` — full Step 2 spec + deploy
- `decisions/hard-lock-no-os-security-changes.md` — why I can't run PowerShell myself
- `forge/INDEX.md` — Forge state of the world
