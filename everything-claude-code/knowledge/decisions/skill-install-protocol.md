# Decision: Skill Installation Protocol

**Date:** 2026-05-22
**Status:** LOCKED IN by user.
**Source:** User on 2026-05-22: *"我给你的卡帕西的这些 skill, 有些你是有的, 你装就行了. 像那个第一个什么 graph, 我看一下, 如果你没有的, 你直接搞找 GitHub 的地址, 然后 GitHub clone clone 到一个临时的文件里面, 然后你去 it 那个项目, 把那里面重要的东西拿过来用, 它就是你的 skill 了."*

## The rule

When the user gives me a skill (by name or photo):

```
1. Check  ~/.claude/skills/<skill-name>/SKILL.md
   ┌─────────────────────────────┐
   │ already installed?          │
   └─────────────────────────────┘
            │              │
          YES             NO
            │              │
            ▼              ▼
   Just enable it    Find on GitHub
   (already done)    (clone → distill → install)
```

## When the skill is missing — extraction recipe

```bash
# 1. Clone to scratch (NOT to ~/.claude/skills/ directly)
git clone <github-url> "C:/AI/everything-claude-code(miss_useOHnow)/everything-claude-code/tmp/skill-clone-<name>-YYYYMMDD/"

# 2. Inspect — find the "important parts":
#    - SKILL.md                  ← if it exists, that IS the skill
#    - README.md                 ← often has the principles
#    - examples/, guides/, rules/ ← extract patterns
#    - the 3-5 paragraphs of philosophy
#    - any prompt templates / behavioral rules
#    NOT to extract:
#    - LICENSE, .gitignore, node_modules, .git
#    - test fixtures, CI configs, build scripts (unless they ARE the skill)

# 3. Distill into ~/.claude/skills/<name>/SKILL.md
#    Format: YAML frontmatter (name, description, license) + body sections
#    Keep it tight — quote the important parts, drop the noise

# 4. Throw away the clone
rm -rf "C:/AI/everything-claude-code(miss_useOHnow)/everything-claude-code/tmp/skill-clone-<name>-YYYYMMDD/"
# (or leave it in tmp/ and let auto-cleanup handle it)

# 5. Log the install
# Write knowledge/skills-inventory/<name>.md with:
#   - source GitHub URL
#   - install date
#   - what was extracted
#   - what was dropped
#   - how I plan to use it
```

## Why this rule

- ⚡ Fast: don't reinvent skills that already exist locally
- 🧹 Clean: GitHub clones don't pollute `~/.claude/skills/` (which is curated)
- 🎯 Focused: extract the *idea* from the repo, drop the boilerplate
- 📓 Traceable: every install logged in `knowledge/skills-inventory/`
- 🔁 Reusable: once distilled, the skill is "mine" — same shape as built-in skills

## Existing skills inventory

`~/.claude/skills/` already contains hundreds of skills. Before any clone, I MUST:
```
glob C:/Users/I075354/.claude/skills/*/SKILL.md  → list installed
grep -l "<skill name>" ...                       → check exact match
```

If the user's named skill isn't a 1:1 match, check for variants:
- `karpathy-guidelines` ≠ `karpathy-rules` ≠ `karpathy-skills` — same idea, different names
- Use semantic match, not just exact filename

## Source folders to scan FIRST (before reaching for GitHub)

| Path | What's there |
|---|---|
| `~/.claude/skills/` | curated installed skills (~hundreds) |
| `~/.claude/plugins/cache/.../skills/` | superpowers + plugin-bundled skills |
| `C:/AI/andrej-karpathy-skills(miss)/skills/` | local karpathy skill source |
| `C:/AI/everything-claude-code(miss_useOHnow)/everything-claude-code/skills/` | ECC repo's skills (this project) |
| `C:/AI/obsidian-wiki/.skills/` | wiki-bundled skills |

Only after all five fail → go to GitHub.

## Per-install workflow

```
User: "I want skill X"
  ↓
Me: glob across all 5 source folders for X
  ↓
  ┌─────────────────────┐
  │ found locally?      │
  └─────────────────────┘
       │              │
      YES            NO
       │              │
       ▼              ▼
  Copy to        web_search_exa
  ~/.claude/     "github X karpathy"
  skills/X/      → find URL
                 → git clone to tmp/
                 → distill SKILL.md
                 → install
       │              │
       └──────┬───────┘
              ▼
  Write knowledge/skills-inventory/X.md
  (source, date, extracts, usage plan)
              ▼
  Confirm with user: "Installed X. Used it for: ___"
```

## What goes in `knowledge/skills-inventory/<skill>.md`

```markdown
# Skill: <name>

**Source:** <github-url> OR <local-path>
**Installed:** YYYY-MM-DD
**Type:** [extracted | as-is-copy]

## What it does
<1-2 sentences>

## Why I have it
<which user task / pattern this serves>

## What I extracted (if from GitHub clone)
- Kept: SKILL.md, references/<file>.md
- Dropped: tests/, .github/, examples/cookbook (too long)
- Distilled: 3 sections from README.md → 1 section in SKILL.md

## How I use it
- Trigger conditions: <when to invoke>
- Combines with: <other skills>
- Output shape: <what I produce>
```

## DON'T

- ❌ Auto-install skills the user didn't ask for
- ❌ Clone GitHub repos into `~/.claude/skills/` directly (pollutes curated set)
- ❌ Keep `node_modules/`, `.git/`, `tests/` from clones — only the idea
- ❌ Forget to log to `knowledge/skills-inventory/` (then I lose track)
- ❌ Re-extract a skill I already extracted last week (check inventory first)
