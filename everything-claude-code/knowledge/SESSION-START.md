# Session Start Protocol

**Purpose:** Steps future-me follows on every new session to bootstrap from disk instead of relying on dead RAM.
**Last updated:** 2026-05-22

## On every new session

```
1. Read   knowledge/INDEX.md                                       ← directory map + rules
2. Read   knowledge/decisions/hard-lock-no-os-security-changes.md  ← 🔒 the no-OS-policy-changes lock
3. Read   knowledge/decisions/agent-composition-model.md            ← 5-layer model
4. Read   knowledge/forge/INDEX.md                                  ← what we're working on
5. Read   knowledge/forge/<active-bug>.md                           ← current task
6. Skim   knowledge/patterns/INDEX.md                               ← available architectural pillars
7. Skim   knowledge/skills-inventory/                                ← what skills are installed
8. Glance knowledge/decisions/                                       ← recent design choices
```

Total cost: ~8 file reads ≈ 8k tokens. Cheap.

## What this replaces

| Old (broken) | New (durable) |
|---|---|
| Hope session summary captured the right things | Read disk |
| Re-derive context from chat history | Read disk |
| Re-explore appFnd to remember patterns | Read `knowledge/patterns/` |
| Re-locate Forge folder by trial-and-error globbing | Read `knowledge/forge/INDEX.md` |
| Re-diagnose the same bug | Read `knowledge/forge/ui-bug-2d-3d-render.md` |

## When to UPDATE the knowledge base (write discipline)

| Trigger | Action |
|---|---|
| User states a hard rule | Add/update appropriate `knowledge/*/INDEX.md` |
| Bug diagnosed | Write `knowledge/forge/<bug-name>.md` |
| Bug fixed | Update bug file with FIX section + close it |
| New architectural pattern learned | Write `knowledge/patterns/NN-<name>.md` |
| Decision made (e.g. SQLite vs JSON, polling vs websocket) | Write `knowledge/decisions/<topic>.md` with WHY |
| Skill installed by user | Write `knowledge/skills-inventory/<skill-name>.md` |
| Forge folder structure changes | Update `knowledge/forge/INDEX.md` |

## What NEVER goes into knowledge/

- ❌ Test stubs / spike code → `tmp/`
- ❌ Half-formed thoughts → don't write yet
- ❌ Real Forge code → `C:\Users\I075354\.accio\accounts\7087759244\agents\DID-2799F4-...\project\`
- ❌ Long verbatim code copies — capture the IDEA, not the syntax (idea memory)

## Self-check questions (before writing into knowledge/)

1. Will this still be true in 3 days? (yes → durable)
2. Does it answer a question I'd otherwise have to re-derive? (yes → durable)
3. Could a future session do the wrong thing without this? (yes → durable)
4. Is it longer than 400 lines? (yes → split it)

If any "no" → don't write here. Either skip or put in `tmp/`.

## Forbidden actions

- Never delete `knowledge/` files without user permission
- Never edit reference projects (`C:/EPM_ACCUMULATION/appFnd/`)
- Never copy Forge code into `knowledge/` — abstract it instead
- Never put secrets, tokens, API keys, real user data into `knowledge/`

## Why this protocol exists

> User on 2026-05-22: "Not in the RAM not in the RAM in hard copy I give you the right to write down the markdown or any format to do accumulation of your knowledge."

Session memory is unreliable. Compaction strips nuance. The harness can lie about my model version. Files on disk don't lie. Read disk first.
