# VibeWiredHarness

> AI Agent Orchestration Harness - Wire and manage a full fleet of Claude-powered
> agents with MCP, hooks, commands and infrastructure services.

## Quick Start — one line after clone

```powershell
git clone https://github.wdf.sap.corp/i075354/VibeWiredHarness.git C:\AI\VibeWiredHarness
cd C:\AI\VibeWiredHarness
.\install.ps1
```

`install.ps1` does everything in one shot:
1. `npm install` for the harness and ECC
2. Adds `claude-l` to your user PATH (no admin needed)
3. Installs ECC agents, skills, hooks into `~/.claude/`
4. Runs vibestart preflight (checks MAMGA, browser-harness, etc.)

Then just launch Claude:

```powershell
# from anywhere inside this repo:
claude-l

# or from the ECC subfolder directly:
cd everything-claude-code
claude-l
```

**First time:** edit `.env` and set `ANTHROPIC_API_KEY` (or `HYPERSPACE_PROXY_KEY` for the SAP Hyperspace proxy).

**Update:** `git pull` from the repo root — updates both the harness and ECC in one pull.

## Architecture

```
  You -> Claude Code/Codex (loads agents/*.md as instruction context)
              | MCP protocol
              v
+-------------------------------------------------------------+
|  LAYER 1 - MCP Observer, default :3100 (vibestart/vibestop)|
|                                                             |
|  44 Harness Agents  (stateless, on-demand per call)        |
|  architect | code-reviewer | planner | security-reviewer   |
|  tdd-guide | rust-reviewer | go-reviewer | + 37 more       |
|                                                             |
|  GAN Loop Agents  (plan -> generate -> evaluate -> repeat)  |
|  gan-planner | gan-generator | gan-evaluator               |
|  builds apps iteratively until eval score >= 7.0           |
|                                                             |
|  MCP Tool Connectors (bridges to Layer 2)                  |
|    memory_store/recall -----> MAMGA :7788                  |
|    browser_action      -----> browser-harness (PATH)       |
|    wiki_lookup         -----> obsidian-wiki (files)        |
+-------------------------------------------------------------+
              |
+-------------------------------------------------------------+
|  LAYER 2 - External Services  (independent lifecycle)       |
|  NOT managed by vibestart/vibestop - manage separately     |
|                                                             |
|  MAMGA memory    :7788  [PERSISTENT STATE - survives restart]|
|  browser-harness PATH   [browser automation binary]        |
|  agent-browser   C:\AI\agent-browser\  [UI test guides]    |
|  Obsidian wiki   C:\AI\obsidian-wiki\ [knowledge base]     |
|  PlanDB          internal [optional task splitter]         |
|  Evolver         internal [code evolution, review only]    |
+-------------------------------------------------------------+
```

### Runtime Model

| | Layer 1: Harness Agents | Layer 2: Infrastructure |
|---|---|---|
| Examples | architect, code-reviewer, gan-* | MAMGA, browser-harness, wiki |
| Count | 44 in agents/*.md | 6 in services/*.md |
| State | Stateless | Stateful (MAMGA) or file/binary |
| Lifecycle | vibestart / vibestop | Independent - manage separately |
| Port | MCP observer default :3100; confirmed by `/ping` | MAMGA :7788, others PATH/files |

## Start / Stop

```powershell
# START (ensure MAMGA is running first - Layer 2)
.\scripts\vibestart.ps1
.\scripts\vibestart.ps1 -Verbose   # list all agents
# Dashboard/health URLs are printed only after /ping responds.

# STOP Layer 1 only - MAMGA and Layer 2 NOT affected
.\scripts\vibestop.ps1

# STATUS - checks both layers
.\scripts\vibestatus.ps1
```

## Recommended Folder Structure

```
C:\AI\VibeWiredHarness\              <- this repo (clone here)
+-- claude-l.cmd                     <- launch Claude from repo root
+-- install.ps1                      <- one-line setup
+-- agents\                          <- 44 AI agent definitions (Layer 1)
+-- services\                        <- 6 external service docs (Layer 2)
+-- commands\                        <- slash-command definitions
+-- hooks\                           <- pre/post event hooks
+-- rules\                           <- guardrails and policies
+-- everything-claude-code\          <- ECC agents, skills, hooks
|   +-- scripts\
|   |   +-- claude-l.cmd             <- Claude launcher (Hyperspace proxy aware)
|   |   +-- vibestart.ps1            <- START services
|   |   +-- vibestop.ps1             <- STOP services
|   +-- agents\  commands\  skills\  <- ECC content wired to ~/.claude/
+-- .codex\config.toml
|
C:\AI\
+-- agent-browser\          <- Layer 2: UI test guide project
+-- obsidian-wiki\          <- Layer 2: knowledge base vault
(MAMGA running at http://127.0.0.1:7788 - Layer 2: persistent memory)
```

## Typical Usage

```powershell
# Code review
claude --agent agents/code-reviewer.md "review all TypeScript in src/"

# Slash commands (in Claude Code session)
/plan "add OAuth2 login"
/tdd "write tests for payment module"
/feature-dev "dark mode toggle"
/build-fix

# GAN build loop - full app from one prompt
/gan-build "todo app with drag-and-drop and dark mode"
# gan-planner expands spec -> gan-generator builds -> gan-evaluator scores
# loops until score >= 7.0 or max iterations

# List all wired agents
Get-ChildItem agents\ -Filter "*.md" | Select-Object BaseName | Format-Table
```

## Agents (44 total - Layer 1, MCP observer default :3100)

| Category | Agents |
|---|---|
| Architecture | architect, code-architect, planner, chief-of-staff |
| Code Review | code-reviewer, typescript-reviewer, python-reviewer, java-reviewer, rust-reviewer, go-reviewer, cpp-reviewer, kotlin-reviewer, csharp-reviewer, flutter-reviewer, database-reviewer, healthcare-reviewer |
| Build/Fix | build-error-resolver, java-build-resolver, rust-build-resolver, go-build-resolver, kotlin-build-resolver, cpp-build-resolver, pytorch-build-resolver, dart-build-resolver |
| Quality | tdd-guide, e2e-runner, performance-optimizer, security-reviewer, refactor-cleaner, code-simplifier |
| Analysis | code-explorer, comment-analyzer, conversation-analyzer, silent-failure-hunter, type-design-analyzer, pr-test-analyzer |
| GAN Loop | gan-planner, gan-generator, gan-evaluator |
| Ops | harness-optimizer, loop-operator, doc-updater, docs-lookup |
| Open Source | opensource-forker, opensource-packager, opensource-sanitizer |
| Other | seo-specialist |

## External Services (6 - Layer 2, independent lifecycle)

| Service | Where | State | Notes |
|---|---|---|---|
| MAMGA | :7788 | Persistent | Start before harness; NOT stopped by vibestop |
| browser-harness | PATH | Stateless | Must be on PATH |
| agent-browser | C:\AI\agent-browser\ | File-based | UI test guides for gan-evaluator |
| Obsidian wiki | C:\AI\obsidian-wiki\ | File-based | Knowledge base |
| PlanDB | internal | Stateless | Optional task splitter |
| Evolver | internal | Stateless | Review/manual mode only |

See `services/*.md` for full docs.

## Configuration

```toml
[model]
default = "claude-sonnet-4-5"
fast    = "claude-haiku-3-5"

[agents]
auto_load = true
directory = "agents"

[mcp]
enabled = true
port    = 3100

[hooks]
enabled   = true
directory = "hooks"
```

## License

[MIT](LICENSE)
