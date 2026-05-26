# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ecc-universal` is a Claude Code plugin — a collection of production-ready agents, skills, hooks, commands, rules, and MCP configurations. It installs into Claude Code (and Cursor, Codex, Gemini, OpenCode) via the `ecc` CLI or `install.sh`/`install.ps1`.

## Commands

```bash
# Install all dependencies
yarn install

# Run the full test suite (CI validators + unit tests)
npm test
# or: node tests/run-all.js (unit tests only, skips CI validators)

# Run a single test file
node tests/hooks/hooks.test.js
node tests/lib/utils.test.js

# Lint JS + Markdown
npm run lint
# or individually:
eslint .
markdownlint '**/*.md' --ignore node_modules

# Coverage (requires 80% threshold)
npm run coverage

# Validate specific artifact types (fast, no Node runtime needed)
node scripts/ci/validate-agents.js
node scripts/ci/validate-skills.js
node scripts/ci/validate-hooks.js
node scripts/ci/validate-commands.js
node scripts/ci/validate-rules.js
node scripts/ci/validate-install-manifests.js
node scripts/ci/validate-no-personal-paths.js
node scripts/ci/check-unicode-safety.js
```

### The `ecc` CLI

```bash
npx ecc install [profile] [--target claude|cursor|codex|gemini|opencode]
npx ecc plan [profile]          # dry-run — show what would be installed
npx ecc catalog                 # list all profiles and component IDs
npx ecc consult "query"         # natural-language component recommender
npx ecc doctor                  # diagnose missing/drifted files
npx ecc repair                  # restore missing ECC-managed files
npx ecc list-installed          # inspect state files for current context
npx ecc auto-update             # pull latest ECC and reinstall
npx ecc status                  # SQLite state-store summary
npx ecc sessions                # list/inspect ECC sessions
```

Install profiles: `minimal`, `core`, `developer` (default), `security`, `research`, `full`.

## Architecture

### Code conventions (mandatory)

- **CommonJS only** — `require`/`module.exports`. No ESM (`import`/`export`) unless the file ends in `.mjs`.
- **Node ≥ 18**, no transpilation, plain `.js` throughout.
- Hook scripts must always `exit 0` on non-critical errors — a failing hook blocks Claude's tool execution.
- Keep hook scripts under 200 lines; extract helpers to `scripts/lib/`.

### Directory layout

| Path | Purpose |
|------|---------|
| `agents/` | Subagent `.md` files with YAML frontmatter (`name`, `description`, `tools`, `model`) |
| `skills/` | Curated skills, each a subdirectory with `SKILL.md` — these are shipped |
| `commands/` | Slash commands (`.md` files, require `description:` frontmatter) |
| `hooks/` | Hook JSON configs (matcher + command) |
| `rules/` | Always-on guidelines (`common/`, language layers, `zh/` translations) |
| `scripts/` | Node.js utilities; hooks live in `scripts/hooks/` |
| `scripts/lib/` | Shared helpers used by hooks and CLI |
| `scripts/ci/` | CI validators (not unit tests — run first in `npm test`) |
| `tests/` | Unit tests mirroring `scripts/` layout — `*.test.js` |
| `manifests/` | JSON manifests declaring what each install profile/module provides |
| `schemas/` | JSON Schema for manifests, hooks, state, provenance, etc. |
| `mcp-configs/` | MCP server configurations |

### Hook system

All hooks use `scripts/hooks/run-with-flags.js` as a wrapper so runtime gating works:

```bash
node scripts/hooks/run-with-flags.js <hookId> <relativeScriptPath> [profilesCsv]
```

Runtime control via env vars: `ECC_HOOK_PROFILE` (csv of active profiles), `ECC_DISABLED_HOOKS` (csv of hook IDs to skip).

### Install system

`manifests/install-modules.json` declares modules; `manifests/install-profiles.json` groups modules into named profiles. `scripts/lib/install-manifests.js` is the canonical resolver. All `paths` entries in modules must point to real repo paths — `validate-install-manifests.js` enforces this.

### Skill placement

| Type | Location | Shipped |
|------|----------|---------|
| Curated | `skills/<name>/SKILL.md` (repo) | Yes |
| Learned | `~/.claude/skills/learned/` | No |
| Imported | `~/.claude/skills/imported/` | No |
| Evolved | `~/.claude/homunculus/evolved/skills/` | No |

Learned/imported skills require a `.provenance.json` sibling. See `docs/SKILL-PLACEMENT-POLICY.md`.

## Adding Content

- **Agent**: add `agents/<name>.md` with YAML frontmatter; `validate-agents.js` checks format.
- **Skill**: add `skills/<name>/SKILL.md`; register the path in `manifests/install-modules.json`; `validate-skills.js` checks non-empty `SKILL.md` exists.
- **Command**: add `commands/<name>.md` with a `description:` frontmatter line.
- **Hook**: add to `hooks/` JSON; validate with `validate-hooks.js`.
- **Language rules**: add `rules/<lang>/` directory extending `rules/common/`; use `/add-language-rules` command.

File naming: **lowercase with hyphens** throughout (e.g., `python-reviewer.md`).

## CI Pipeline

`npm test` runs in this order:
1. `check-unicode-safety.js` — rejects non-ASCII identifiers in `.js` files
2. `validate-agents.js`, `validate-commands.js`, `validate-rules.js`, `validate-skills.js`, `validate-hooks.js`
3. `validate-install-manifests.js` — all manifest paths must exist
4. `validate-no-personal-paths.js` — no hardcoded home directories
5. `catalog:check` — sync check on catalog.json
6. `tests/run-all.js` — full unit test suite

All steps must pass. The coverage gate is 80% lines/functions/branches/statements.

## Key Skills for This Repo

| File(s) | Skill |
|---------|-------|
| `README.md` | `/readme` |
| `.github/workflows/*.yml` | `/ci-workflow` |
| Adding a new language ruleset | `/add-language-rules` |
| Database schema changes | `/database-migration` |
| Standard feature work | `/feature-development` |
