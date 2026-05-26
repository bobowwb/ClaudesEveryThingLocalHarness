# Knowledge Base — Persistent Hard-Copy Memory

**Owner:** User granted explicit write permission on 2026-05-22 for durable knowledge accumulation.
**Rule:** This folder is **NOT scratch**. Files here persist across sessions, context resets, and model upgrades. Read this INDEX first on every session start.

## Why this exists

User said: *"Not in the RAM not in the RAM in hard copy I give you the right to write down the markdown or any format to do accumulation of your knowledge."*

Session memory dies at compaction. Session summaries lose nuance. The only durable knowledge layer is **files on disk that I write and re-read**.

## Directory map

```
knowledge/
├── INDEX.md                 ← you are here. read first every session.
├── patterns/                ← architectural patterns (idea-level, language-agnostic)
│   ├── INDEX.md
│   ├── 00-a2a-foundation.md ← THE BEDROCK. Read FIRST. All wrappers sit on this.
│   ├── 01-otel.md           ← oTel observability pattern (from appFnd)
│   ├── 02-armor-wrapper.md  ← Agent Armor L1→L4 (from appFnd)
│   ├── 03-4d-memory-wrapper.md  ← 4D memory closure pattern (from appFnd)
│   └── 04-orchestrator-routing.md  ← intent classify + middleware (from appFnd)
├── forge/                   ← Forge project specifics
│   ├── INDEX.md             ← Forge state, paths, current bug, next steps
│   ├── ui-bug-2d-3d-render.md   ← the actual bug we're fixing
│   └── (more as work proceeds)
├── skills-inventory/        ← user's installed skills + how I should use them
│   └── (populated when user delivers skills bundle)
└── decisions/               ← architectural decisions, with WHY
    └── (populated as we make choices)
```

## Hard rules

1. **Real Forge code** → only in `C:\Users\I075354\.accio\accounts\7087759244\agents\DID-2799F4-...\project\`
2. **Scratch / throwaway / spike code** → `tmp/` (this repo) — auto-deletable
3. **Durable knowledge** → THIS folder (`knowledge/`) — never auto-delete
4. **Reference (read-only)** → `C:\EPM_ACCUMULATION\appFnd\` — never edit
5. Any session start → read this INDEX, then `forge/INDEX.md`, then resume

## Source of truth on each topic

| Topic | Source of truth |
|---|---|
| **🔒 PRODUCT DEFINITION (read FIRST)** | `forge/PRODUCT-DEFINITION-OTO1.md` ← Forge = OTO1, prompt → 5-6 product designs, **NOT** story2movie |
| **🔒 TARGET USER & UX north star** | `forge/TARGET-USER-and-UX.md` ← user is **新兴创业者** (aspiring founder), 2D/3D 服务于 founder 决策 |
| **🔒 VERIFIED architecture** | `forge/VERIFIED-architecture-2026-05-25.md` ← read source, confirmed 7 agents + Next.js + 5-tier blueprint |
| **🔒 HARD LOCK: never modify OS-level security policies** | `decisions/hard-lock-no-os-security-changes.md` ← read first |
| **External Q&A (Obsidian wiki)** — agent principles, A2A, MAGMA, etc. | `external-references.md` ← catalogue + pointers to `C:\AI\knowledge\` |
| **The agent composition model (5 layers)** | `decisions/agent-composition-model.md` ← read first |
| **Skill install protocol (local-first, then GitHub clone+distill)** | `decisions/skill-install-protocol.md` |
| **What is A2A and how do agents conform?** | `patterns/00-a2a-foundation.md` ← read first |
| What is appFnd's oTel design? | `patterns/01-otel.md` |
| What is Agent Armor? | `patterns/02-armor-wrapper.md` |
| What is 4D Memory? | `patterns/03-4d-memory-wrapper.md` |
| How does orchestrator routing work? | `patterns/04-orchestrator-routing.md` |
| Where does Forge live? | `forge/INDEX.md` |
| What's the current Forge bug? | `forge/ui-bug-2d-3d-render.md` ← OBSOLETE (story2movie misdirection) |
| What skills did the user provide? | `skills-inventory/` |
| Why did we choose X over Y? | `decisions/` |

## Update discipline

When I learn something durable:
- ✅ Bug pattern + fix → `decisions/<topic>.md`
- ✅ A new appFnd-style pattern I should remember → `patterns/NN-<name>.md`
- ✅ Forge state change (file added, agent renamed) → update `forge/INDEX.md`
- ✅ Skill installed or used → log in `skills-inventory/<skill-name>.md`
- ❌ Quick test, throwaway probe, ad-hoc script → `tmp/`, NOT here

## Conventions

- File naming: lowercase-hyphenated, optional NN- prefix for ordering
- Every file starts with: 1-line `**Purpose:**`, 1-line `**Last updated:**`
- Every claim sourced (where it came from): `> reference: appFnd/app/observability.py`
- Pseudo-code over real code (this is idea memory, not implementation)
- One concept per file. Split when a file passes 400 lines.

## Status

| Area | Status |
|---|---|
| `patterns/` | ✅ 5 patterns (00-04) + INDEX. A2A is foundation. |
| `forge/INDEX.md` | ✅ updated with A2A-first ordering |
| `forge/ui-bug-2d-3d-render.md` | ✅ written — diagnosis locked |
| `decisions/agent-composition-model.md` | ✅ 5-layer composition model locked in |
| `skills-inventory/` | ⏳ awaiting user's skills bundle |
| `decisions/` (other) | (will populate as choices are made) |
