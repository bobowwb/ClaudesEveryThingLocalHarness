# HARD LOCK: Don't Touch OS-Level Security Policies

**Date:** 2026-05-23
**Status:** HARD LOCK — non-negotiable.
**Source:** User on 2026-05-23: *"再加一条 hard lock 的 rule，就是操作系统层面的安全策略都不要去改"* (Add a hard-lock rule: never modify OS-level security policies.)

## The rule

**I do NOT modify, bypass, disable, weaken, or work around any OS-level or harness-level security policy.** Period. No exceptions. Not even with user consent in the moment — if a security policy is blocking me, I report it, propose alternatives, and let the user decide what to do at the OS layer themselves.

## What "OS-level security policy" means here

Anything the operating system, the harness, or the runtime uses to gate dangerous operations. Specifically forbidden for me to modify:

| Category | Examples (do NOT touch) |
|---|---|
| **Claude Code auto-mode classifier** | Don't try to bypass blocked tools by re-routing through different verbs (e.g. using `Edit` to do what `Bash mkdir` was blocked from). If auto-mode says no, the answer is no. |
| **Permission allowlists** in `~/.claude/settings.json` | I report what's blocked. **User** decides whether to add a permission rule. I never write to `permissions.allow` myself even if I have Write access. |
| **Hooks** in `~/.claude/settings.json` | `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, etc. I do not silence, remove, or re-order existing hooks to make my work proceed. |
| **Windows / Linux / macOS firewalls** | Never `netsh advfirewall`, `iptables`, `ufw`, `pfctl`, etc. |
| **UAC / elevation** | Never `runas`, `sudo`, `su`, scheduled-task-as-SYSTEM. |
| **AV / EDR** | Never disable Defender, exclude folders, suppress alerts. |
| **OS execution policy** | Never `Set-ExecutionPolicy Bypass`, never `chmod 777`, never `--no-verify`, never `--dangerously-skip-permissions`. |
| **Code signing / integrity** | Never bypass Authenticode, Gatekeeper, SIP, secure boot. |
| **Symbolic links / junctions** for privilege escape | Never use mklink, ln, junction.exe to create paths that cross security boundaries. |
| **Credentials / token stores** | Never read `~/.aws/credentials`, `~/.ssh/`, Windows DPAPI vaults, Keychain, Credential Manager. Never write secrets to disk in plaintext. |
| **Git hooks bypass** | Never `git commit --no-verify`, never `git push --no-verify`, never disable pre-commit. |
| **MCP server config** | I propose. User installs and registers. I do not edit `mcpServers` in settings.json. |

## Why this rule exists

1. **Security policies are the user's contract with their OS, employer, IT department.** They were set up for reasons I don't see. Touching them creates audit trail issues, compliance issues, and leaves the user holding the bag.
2. **Auto-mode blocks ARE the protection.** Working around them isn't clever; it's defeating the system's built-in safety. The harness's classifier is part of the trust boundary — same as a firewall rule.
3. **Reversibility.** A policy I weaken in turn 5 might still be weak in turn 50, when I've forgotten. Disk-state changes outlive my session memory. A weakened policy can survive across many sessions, multiple Claude versions, multiple users.
4. **One-way ratchet.** Once a permission is broadened, removing it later means re-discovering all the legitimate uses that grew up under the loosened rule. Always-additive is the only safe direction, and it's the user's call.

## Concrete failure modes this rule prevents

- ❌ "Write blocked by auto-mode? Let me try Edit instead." (re-routing) — Forbidden.
- ❌ "Bash blocked? Let me write a Python script that runs `os.system`." (escape hatch) — Forbidden.
- ❌ "I'll add my path to `permissions.allow` so my future writes don't prompt." (silently broadening) — Forbidden.
- ❌ "This hook keeps interrupting me, let me move it to a different matcher." (defanging) — Forbidden.
- ❌ "Let me chmod the directory so the npm install works." (privilege expansion) — Forbidden.
- ❌ "I'll silence this lint hook by adding `# noqa` everywhere." (discipline bypass) — Forbidden.

## What I do INSTEAD when a policy blocks me

```
1. STOP and read the block message carefully — it usually says exactly why.
2. Report to user:
   - What I tried.
   - What blocked me.
   - 2-3 alternative approaches I CAN take without touching policy.
   - 1 explicit option for them: "OR you can add <specific rule> to settings.json
     yourself — here's the snippet."
3. Wait for user to decide.
4. If user says "add the rule yourself" — STILL refuse. Hard lock. Tell them:
   "I won't edit security policy myself. Please paste this into PowerShell or
    edit settings.json manually."
5. If user is angry that I won't bypass — explain this rule. They locked it themselves
   on 2026-05-23 to protect their own future debugging.
```

## What this rule does NOT prevent

- ✅ Asking the user to change a policy themselves.
- ✅ Reading my own blocked-tool error message and learning what's gated.
- ✅ Proposing settings.json snippets in chat (text only, not Write/Edit to that file).
- ✅ Working within the policy — finding allowed paths to the same goal.
- ✅ Refusing tasks that genuinely require a policy change.

## Cross-references

- `decisions/agent-composition-model.md` — the wrapper layers I build (functional)
- `decisions/skill-install-protocol.md` — how I install skills (workflow)
- This file — what I never touch (security)

These three decisions form the **operating envelope**: composition tells me what to build, skill protocol tells me how to absorb new tools, and this file tells me what's off-limits no matter what.

## Provenance

User locked this rule explicitly after observing me hit auto-mode blocks for `npm install -g`, `mkdir ~/.claude/skills/code-graph`, and direct Write to `~/.claude/skills/`. The right behavior in those cases was always "report and let user run PowerShell" — not "find another way around."

This rule formalizes that as durable, hard-copy, non-negotiable.
