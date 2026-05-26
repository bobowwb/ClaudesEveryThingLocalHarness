# Skill: code-graph

**Source:** https://github.com/colbymchenry/codegraph (v0.9.2, MIT license)
**Installed:** 2026-05-22
**Type:** extracted (clone+distill)
**SKILL.md:** `knowledge/skills-inventory/code-graph/SKILL.md`

## What it does

A pre-built tree-sitter AST + symbol/edge/file knowledge graph, exposed as MCP tools (`codegraph_search`, `codegraph_context`, `codegraph_callers`, `codegraph_callees`, `codegraph_impact`, `codegraph_node`, `codegraph_explore`, `codegraph_files`, `codegraph_status`). Saves ~35% cost / ~70% tool calls vs raw grep+Read exploration on real codebases (verified on VS Code, Excalidraw, Django, Tokio, OkHttp, Gin, Alamofire).

100% local, SQLite FTS5 backend, file-watcher-driven sync. Supports 19+ languages including TS/JS/Python/Go/Rust/Java/C#/PHP/Ruby/Swift/Kotlin (which covers everything Forge uses).

## Why I have it

User on 2026-05-22 explicitly named this as a skill they want me to install. "code-graph" 是他列出的 skills 之一，flagged as a newer GitHub project I don't already have.

Direct fit for Forge work:
- Forge has dual-language codebase (TS/JS frontend + Python backend)
- I'll need to navigate it heavily during the 5-layer wrapper composition (A2A → Armor → 4D Memory → oTel → Orchestrator)
- Without code-graph: every "what calls X" question = grep + multi-file Read = expensive
- With code-graph: same question = one `codegraph_context` call

## What I extracted

**Kept (the idea):**
- Tool selection table by intent (which `codegraph_*` for which question type)
- Common chains (onboarding / refactor / debug / "how does X work")
- Anti-patterns (don't grep first, don't re-verify, don't loop node, don't chain search+node)
- When NOT to use it (literal text → grep; opened file → Read; uninitialized → ask user)
- Setup commands (`npx @colbymchenry/codegraph`, `codegraph init -i`)
- Limitations (index lag ~1s, name matching ambiguity, no live correctness)
- Specific Forge mapping (likely usage scenarios)

**Dropped (boilerplate, not the idea):**
- TypeScript implementation (`src/`, `__tests__/`, `package.json`, `package-lock.json`)
- Build scripts (`scripts/build-bundle.sh`, `pack-npm.sh`, etc.)
- Multi-agent installer code (`src/installer/targets/*`)
- Tree-sitter grammar `.wasm` files
- Test fixtures
- `.git/` (1.4MB pack file)
- Release / changelog logic
- Cursor MCP working-directory quirk handling

## Source files I distilled from

| Upstream file | What I took |
|---|---|
| `README.md` | Benchmark numbers, framework support list, setup commands, "Why CodeGraph" pitch |
| `CLAUDE.md` (theirs) | Architecture overview, NodeKind/EdgeKind enum, MCP transport notes |
| `.cursor/rules/codegraph.mdc` | Tool intent table, rules of thumb, anti-patterns (this is the most important file — it's the user-facing skill instructions) |
| `src/mcp/server-instructions.ts` | "Answer directly — don't delegate exploration" core principle, common chains |

The `.mdc` and `server-instructions.ts` are the canonical instructions. Everything else is implementation noise.

## Install state

⚠️ **Not yet installed to `~/.claude/skills/code-graph/`.** Auto-mode classifier blocks Write to `~/.claude/skills/`. The distilled SKILL.md is currently at:
```
C:\AI\everything-claude-code(miss_useOHnow)\everything-claude-code\knowledge\skills-inventory\code-graph\SKILL.md
```

To complete install, user runs in PowerShell:
```powershell
# Create destination + copy SKILL.md
New-Item -ItemType Directory -Force -Path "C:\Users\I075354\.claude\skills\code-graph" | Out-Null
Copy-Item -Path "C:\AI\everything-claude-code(miss_useOHnow)\everything-claude-code\knowledge\skills-inventory\code-graph\SKILL.md" -Destination "C:\Users\I075354\.claude\skills\code-graph\SKILL.md" -Force

# Verify
Test-Path "C:\Users\I075354\.claude\skills\code-graph\SKILL.md"
```

OR allow auto-mode to write to `~/.claude/skills/`:
```powershell
# Add to settings.json permissions.allow
"Write(C:/Users/I075354/.claude/skills/**)",
"Edit(C:/Users/I075354/.claude/skills/**)"
```

Then I can install future skills directly without PowerShell.

## How I use it (when active)

**Trigger conditions:**
- Working in any sizable codebase (>50 files)
- Question shape: "where is X / what calls Y / what does Y call / what would changing Z break / show me X / give me context for area"
- BEFORE writing code, not during

**Combines with:**
- `code-explorer` (skill) → use code-graph for structure, then code-explorer for narrative
- `code-architect` (skill) → use code-graph to discover existing patterns before designing new ones
- `tdd-workflow` (skill) → use code-graph to find affected callers before writing failing test
- `subagent-driven-development` → DO NOT spawn an explore sub-agent if code-graph is available (the upstream literally warns against this)

**Output shape:**
- Tool returns symbol/file/signature/source — direct answer, no further exploration needed in most cases
- For Forge specifically: maps the 6 specialist agent dispatch area in one `codegraph_context` call

## Cleanup

Temp clone folder will be auto-deletable:
```
C:\AI\everything-claude-code(miss_useOHnow)\everything-claude-code\tmp\skill-clone-code-graph-20260522\
```

Keeping it for now in case I need to re-distill if the skill description proves too thin in actual use. If unused for 7 days, delete.

## Open questions

1. **Should I install the actual MCP server too** (`npx @colbymchenry/codegraph` + `codegraph init -i` in Forge project)? **YES — this is now blocking.** See `knowledge/forge/code-graph-launch-benefit.md` for why it's a prerequisite for fast Forge shipping, not a nice-to-have.
2. **Does Forge already have `.codegraph/` directory?** Confirmed NO via Glob 2026-05-22.

## Hands-on learning notes (2026-05-22)

After clone+distill, attempted to actually USE code-graph on Forge. Findings:

1. **MCP server is NOT yet registered** in `~/.claude/settings.json` `mcpServers`. The clone gives me the upstream code; it does NOT auto-install the running MCP server.
2. **Tool schemas extracted** from `src/mcp/tools.ts` — added the 9 tools' precise input schemas to SKILL.md so I know parameter names, defaults, enum values, and the size-tiered explore output budget.
3. **Output budget scales with project size:** Forge (~50-100 source files) sits in the smallest tier — `codegraph_explore` returns max 18k chars / 5 files / 3800 chars per file. Query precisely.
4. **Container kinds get an outline, not body:** `codegraph_node` on a class/interface/trait with `includeCode=true` returns member names + signatures + line numbers, NOT the full source. This is intentional (prevents context bloat).
5. **`codegraph_files` REPLACES `Glob`** for project file structure once the index is built — faster, includes metadata (language, symbol count). The upstream calls this "REQUIRED for file/folder exploration."
6. **The `.cursor/rules/codegraph.mdc` file is the canonical user-facing skill** — not the README. It's terser, more directive, and matches what gets loaded into the agent's context.

## Cross-references

- `SKILL.md` (this folder) — the distilled usage doc
- `../../forge/code-graph-launch-benefit.md` — concrete Forge launch wins
- `../../decisions/skill-install-protocol.md` — the install rules I followed
