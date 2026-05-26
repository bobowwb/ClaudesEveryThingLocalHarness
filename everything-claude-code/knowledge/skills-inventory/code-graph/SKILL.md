---
name: code-graph
description: Use when working in any sizable codebase to answer "where is X / what calls Y / what does Y call / what would changing Z break / show me X's source / give me focused context for an area." Built on the CodeGraph MCP server (tree-sitter knowledge graph + SQLite FTS5). Saves ~35% cost / ~70% tool calls vs grep+read exploration. PREFER over native search for any STRUCTURAL question (callers, callees, impact, signature, definition). Use grep/Read only for literal text (string contents, comments) or after a specific file is already open.
license: MIT
source: https://github.com/colbymchenry/codegraph (v0.9.2, MIT)
distilled: 2026-05-22
---

# code-graph — Code Intelligence over an Indexed Knowledge Graph

A pre-built tree-sitter AST + symbol/edge/file index, exposed via MCP tools. Reads sub-millisecond. Use BEFORE writing or editing code, not during.

## Core principle (from upstream)

> "Codegraph IS the pre-built search index. Delegating the lookup to a separate file-reading sub-task/agent — or running your own grep + read loop — repeats work codegraph already did and costs more for the same answer."

Translation: **answer directly using 2-3 codegraph calls, not by spawning an explore agent.**

## Tool selection (by intent)

| Question | Tool |
|---|---|
| "Where is X defined?" / "Find symbol named X" | `codegraph_search` |
| "What's the deal with this task / feature / area?" | `codegraph_context` ← **PRIMARY**, composes search + node + callers + callees in one call |
| "What calls function Y?" | `codegraph_callers` |
| "What does Y call?" | `codegraph_callees` |
| "What would break if I changed Z?" | `codegraph_impact` |
| "Show me Y's signature / source / docstring" | `codegraph_node` |
| "Show me several related symbols' source / survey an area" | `codegraph_explore` ← ONE capped call; prefer over many node/Read |
| "What's in directory X?" | `codegraph_files` |
| "Is the index ready / what's its size?" | `codegraph_status` |

## Exact tool schemas (from upstream `src/mcp/tools.ts`)

All tools accept an optional `projectPath` to query a different project's `.codegraph/` index — useful when working across multiple repos.

### `codegraph_search` — quick symbol lookup
```
required: query (string)              e.g. "auth", "signIn", "UserService"
optional: kind (enum)                 function | method | class | interface | type | variable | route | component
          limit (number, default 10)
          projectPath
returns:  locations only (no code)
```

### `codegraph_context` — PRIMARY tool, comprehensive task context
```
required: task (string)               description of task/bug/feature
optional: maxNodes (default 20)
          includeCode (default true)  include code snippets for key symbols
          projectPath
returns:  composed search+node+callers+callees in ONE call
```

### `codegraph_callers` — find callers
```
required: symbol (string)
optional: limit (default 20)
          projectPath
```

### `codegraph_callees` — find callees
```
required: symbol (string)
optional: limit (default 20)
          projectPath
```

### `codegraph_impact` — blast radius
```
required: symbol (string)
optional: depth (default 2)           how many levels of dependencies to traverse
          projectPath
```

### `codegraph_node` — single symbol details
```
required: symbol (string)
optional: includeCode (default false) ← off by default to minimize context
          projectPath
returns:  for container kinds (class/struct/interface/trait/protocol/enum/namespace/module),
          includeCode=true returns a STRUCTURAL OUTLINE (member names + signatures + line numbers),
          NOT the full body — saves context on large classes
```

### `codegraph_explore` — survey an area
```
required: query (string)              symbol names, file names, short code terms
                                       e.g. "AuthService loginUser session-manager"
                                       e.g. "GraphTraverser BFS impact traversal.ts"
optional: maxFiles (default 12)       max files to include source from
          projectPath
returns:  capped output — output budget scales with project size:
          <500 files:    18000 chars,  5 files default,  3800 chars/file
          <5000 files:   13000 chars,  6 files default,  2500 chars/file
          <15000 files:  35000 chars, 12 files default,  7000 chars/file
          ≥15000 files:  38000 chars, 14 files default,  7000 chars/file
note:     Use `codegraph_search` FIRST to find names, then explore them in one call
```

### `codegraph_files` — file structure (REQUIRED for file/folder exploration, faster than Glob)
```
optional: path (string)               filter to files under directory
          pattern (string)            glob filter, e.g. "*.tsx", "**/*.test.ts"
          format (enum)               tree (default) | flat | grouped (by language)
          includeMetadata (default true)
          maxDepth (number)
          projectPath
```

### `codegraph_status` — index health
```
optional: projectPath
returns:  indexed file count, node count, edge count, backend (native sqlite vs wasm fallback)
```

## Critical defaults to remember

- `codegraph_node` defaults `includeCode=false` — opt in when you want source
- `codegraph_node` on a CLASS returns outline, not body, even with `includeCode=true` (intentional anti-bloat)
- `codegraph_explore` budget scales with project size — small project (<500 files like Forge) = 5 files, 18k chars; query precisely
- `codegraph_impact` defaults depth=2 — bump to 3 for deep type refactors, 1 for quick "direct callers only"
- Index lags writes ~500ms-1s — don't query immediately after editing
- All tools accept `projectPath` — use to query a different project's index without `cd`

## Common chains

- **Onboarding a codebase** → `codegraph_context` first. If still unclear, `codegraph_explore` for breadth, then `codegraph_node` on specific symbols.
- **Refactor planning** → `codegraph_search` → `codegraph_callers` → `codegraph_impact`. Blast-radius answer comes from `impact`, not from walking callers manually.
- **Debugging a regression** → `codegraph_callers` of suspected symbol; widen with `codegraph_impact` if an unexpected call appears.
- **"How does X work?" / architecture trace** → `codegraph_context` then ONE `codegraph_explore` for the source. Stop. Usually 0 file reads needed.

## Anti-patterns (DON'T)

| Don't | Do |
|---|---|
| Grep first to find a symbol by name | `codegraph_search` (faster, returns kind+location+signature in one call) |
| Re-verify codegraph results with grep | Trust them — they came from a full AST parse |
| Chain `codegraph_search` + `codegraph_node` for context | One `codegraph_context` call |
| Loop `codegraph_node` over many symbols | One `codegraph_explore` call (returns all grouped by file, capped) |
| Query the index immediately after editing a file | Wait next turn — watcher debounces ~500ms |
| Spawn an Explore sub-agent for "how does X work" | Answer directly with 2-3 codegraph calls |

## When NOT to use code-graph

- Looking for **literal text** — string contents, log messages, comments → `Grep` is correct.
- Reading a **specific file you already opened** → `Read` is correct.
- The index says "not initialized" → ask user: *"This project doesn't have CodeGraph initialized. Run `codegraph init -i`?"*
- File just edited in same turn → wait, don't re-query.

## When code-graph helps Forge work specifically

The Forge project (`C:\Users\I075354\.accio\accounts\7087759244\agents\DID-2799F4-...\project\`) has:
- TS/JS frontend (engine3d, dashboard.html, api/)
- Python backend (story_to_movie.py, studio_orchestrator.py, memory_agent.py, harmonize_delta.py)
- 19+ language support means both halves are indexable

Likely uses for code-graph during Forge work:
- "Where is `generateMovie()` defined?" -> `codegraph_search`
- "What calls `studio_orchestrator.dispatch()`?" -> `codegraph_callers`
- "If I refactor `Movie3DBlueprint` type, what breaks?" -> `codegraph_impact`
- "Map the WR/EN/CH/LI/AU/ED agent dispatch area" -> `codegraph_context`
- "Show me all 6 specialist agent functions at once" -> `codegraph_explore`

## Setup state

This skill describes how to USE code-graph when the MCP server is configured. To install the server itself in a project:

```bash
# Install (auto-detects Claude Code / Cursor / Codex / opencode)
npx @colbymchenry/codegraph

# Or explicit
codegraph install --target=claude --yes

# Per-project index
cd <project>
codegraph init -i
```

After install, the MCP server tools `codegraph_*` appear automatically. If they don't appear, the MCP server isn't running — restart the agent client.

## Limitations

- Index lags file writes by ~1 second.
- Cross-file resolution is best-effort name matching; ambiguous calls may return multiple candidates.
- No live correctness validation — that's still TypeScript compiler / test suite / linter's job.
- Frameworks recognized: Django, Flask, FastAPI, Express, NestJS, Laravel, Drupal, Rails, Spring, Gin/chi/gorilla/mux, Axum/actix/Rocket, ASP.NET, Vapor, React Router, SvelteKit. Other frameworks fall back to plain symbol resolution.

## Provenance

- Upstream repo: https://github.com/colbymchenry/codegraph
- Distilled from: upstream `README.md`, `CLAUDE.md`, `.cursor/rules/codegraph.mdc`, `src/mcp/server-instructions.ts`
- Distilled by: claude on 2026-05-22 per `knowledge/decisions/skill-install-protocol.md`
- Dropped from upstream (boilerplate, not the idea): TypeScript implementation, build scripts, installer logic, test fixtures, `package.json`, framework-specific TS extractors, MCP transport code
