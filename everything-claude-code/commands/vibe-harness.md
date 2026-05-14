# Vibe Harness

Run the local ECC preflight before a Cline or Codex coding session:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\vibe-harness.ps1 -ForCline
```

Use this when you want Cline and Codex to share the same engineering harness:

- MAMGA is long-horizon memory at `http://127.0.0.1:7788`.
- Obsidian wiki is local coding knowledge at `C:\AI\obsidian-wiki\CLINE.md`.
- `browser-harness` is the preferred browser-control path; `agent-browser` is the Cline workflow fallback.
- PlanDB is optional and only needed for large task splitting.
- Evolver is review-only unless tests prove a repeatable failure pattern.

Evidence priority:

1. Local test results and runtime observations.
2. Official docs.
3. MAMGA memory.
4. Obsidian wiki.
5. Other notes or web material.
