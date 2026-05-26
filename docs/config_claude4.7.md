# Configure Claude Code to Use `anthropic--claude-4.7-opus` via a Local LiteLLM (Hyperspace) Proxy

This guide walks any vibe-coding teammate through wiring **Claude Code** (the official `claude` CLI) so it can talk to your **local LiteLLM proxy** (e.g. SAP Hyperspace at `http://localhost:6655/litellm/v1`) and use models like `anthropic--claude-4.7-opus`.

Follow it top-to-bottom and you'll get a working `claude-l` command that defaults to 4.7-opus.

---

## 1. Why a translator is needed (read this first)

There are two API "shapes" at play:

| Tool                                  | API shape it speaks                              | Endpoint it expects                                 |
| ------------------------------------- | ------------------------------------------------ | --------------------------------------------------- |
| **Cline / Continue / OpenAI clients** | OpenAI Chat Completions (`/v1/chat/completions`) | `http://localhost:6655/litellm/v1` ✅              |
| **Claude Code (`claude` CLI)**        | Anthropic Messages API (`/v1/messages`)          | Needs an Anthropic-compatible endpoint              |

The Hyperspace LiteLLM proxy only exposes the **OpenAI shape** (`/litellm/v1`). Pointing Claude Code's `ANTHROPIC_BASE_URL` directly at LiteLLM will always fail with:

> There's an issue with the selected model (anthropic--claude-4.7-opus). It may not exist or you may not have access to it. Run /model

Even though Cline works fine using exactly the same URL, key, and model id. The model id is correct; the protocol is wrong.

**Fix:** put a tiny **Anthropic ⇄ OpenAI translator** between Claude Code and LiteLLM. We use [`claude-code-router`](https://www.npmjs.com/package/@musistudio/claude-code-router) (`ccr`), a local Node process that listens on `127.0.0.1:3456`.

```text
   Claude Code  (Anthropic API)
            |
            v
   ccr      (127.0.0.1:3456)         <-- Anthropic <-> OpenAI translator
            |
            v
   LiteLLM / Hyperspace proxy
   http://localhost:6655/litellm/v1/chat/completions
```

---

## 2. Prerequisites

| Tool                   | Minimum  | Check                                                                                       |
| ---------------------- | -------- | ------------------------------------------------------------------------------------------- |
| Node.js                | 18+      | `node -v`                                                                                   |
| npm                    | 9+       | `npm -v`                                                                                    |
| Claude Code CLI        | latest   | `claude --version`                                                                          |
| LiteLLM proxy running  | -        | `curl http://localhost:6655/litellm/v1/models -H "Authorization: Bearer <KEY>"` returns JSON |

You also need:

- The **API key** the LiteLLM proxy expects (in Hyperspace's UI it's the "API Key" field, e.g. `8a6ab847-…-905046`).
- The exact **model ids** the proxy registers. For Hyperspace they look like:
  - `anthropic--claude-4.7-opus`
  - `anthropic--claude-4.6-opus`
  - `anthropic--claude-4.5-opus`
  - `anthropic--claude-4.6-sonnet`
  - `anthropic--claude-4.5-sonnet`
  - `anthropic--claude-4-sonnet`
  - `anthropic--claude-4.5-haiku`

Confirm them once via the model dropdown in your Cline / Continue settings, or:

```powershell
curl.exe -s -H "Authorization: Bearer <KEY>" http://localhost:6655/litellm/v1/models
```

---

## 3. Install `claude-code-router`

```powershell
npm i -g @musistudio/claude-code-router
ccr -v
# claude-code-router version: 2.0.0  (or newer)
```

If `ccr` isn't on PATH afterwards, restart the terminal so the global npm bin is picked up.

---

## 4. Create the ccr config

Path: `%USERPROFILE%\.claude-code-router\config.json` (create the folder if it doesn't exist).

```json
{
  "LOG": false,
  "HOST": "127.0.0.1",
  "PORT": 3456,
  "APIKEY": "",
  "Providers": [
    {
      "name": "hyperspace-litellm",
      "api_base_url": "http://localhost:6655/litellm/v1/chat/completions",
      "api_key": "REPLACE_WITH_YOUR_HYPERSPACE_KEY",
      "models": [
        "anthropic--claude-4.7-opus",
        "anthropic--claude-4.6-opus",
        "anthropic--claude-4.5-opus",
        "anthropic--claude-4.6-sonnet",
        "anthropic--claude-4.5-sonnet",
        "anthropic--claude-4-sonnet",
        "anthropic--claude-4.5-haiku"
      ]
    }
  ],
  "Router": {
    "default":      "hyperspace-litellm,anthropic--claude-4.7-opus",
    "background":   "hyperspace-litellm,anthropic--claude-4.5-haiku",
    "think":        "hyperspace-litellm,anthropic--claude-4.7-opus",
    "longContext":  "hyperspace-litellm,anthropic--claude-4.7-opus",
    "longContextThreshold": 60000,
    "webSearch":    "hyperspace-litellm,anthropic--claude-4.7-opus"
  }
}
```

Field guide:

- `api_base_url` — must end in `/chat/completions`. ccr appends nothing.
- `api_key` — bearer token forwarded to LiteLLM. **Replace with your own key.** The file is local-only; do NOT commit it.
- `models` — every model id you want available.
- `Router.default` — used for normal requests.
- `Router.background` — used for Claude Code's auto-summarisation; cheap model is fine.
- `Router.think` — used when Claude Code requests extended thinking.
- `longContext` + `longContextThreshold` — switch model when prompt exceeds N tokens.

> Security tip: if you don't want the key on disk, omit `api_key` and set the env var `OPENAI_API_KEY` before launching `ccr`.

---

## 5. The `claude-l` launcher (Windows)

Use the launcher already shipped in this repo:

- Repo copy:    `everything-claude-code/scripts/claude-l.cmd`
- Installed copy (active on PATH): `C:\Users\<you>\.local\bin\claude-l.cmd`

What it does:

1. Verifies `claude` and `ccr` are on PATH (graceful errors otherwise).
2. Wipes any stale `ANTHROPIC_*` env vars (so old shells can't leak the wrong base URL).
3. Lets you pick a model interactively, or accepts the default `anthropic--claude-4.7-opus`.
4. Calls `ccr code %*` so Claude Code talks to the local router.

Install it once into your user-level bin (so PowerShell finds it):

```powershell
# from this repo root
$dst = "$env:USERPROFILE\.local\bin\claude-l.cmd"
New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
Copy-Item -Force everything-claude-code\scripts\claude-l.cmd $dst
# Make sure %USERPROFILE%\.local\bin is on PATH
[Environment]::GetEnvironmentVariable("PATH","User") -split ';' | Select-String "\.local\\bin$"
```

If the last command prints nothing, add `%USERPROFILE%\.local\bin` to your user PATH and restart the terminal.

> Watch out: if you have an older `claude-l.cmd` in BOTH `%USERPROFILE%\.local\bin\` AND the repo root, Windows uses whichever is found first on PATH. Always overwrite the one in `.local\bin` after pulling repo changes (the snippet above does this).

---

## 6. First run

```powershell
claude-l
```

Expected output before Claude Code starts:

```
[claude-l] Routing through ccr -> http://localhost:6655/litellm/v1
[claude-l] Model: anthropic--claude-4.7-opus
```

Then Claude Code's UI loads, talks to ccr, and you're chatting against `anthropic--claude-4.7-opus`.

---

## 7. How to verify it's actually 4.7-opus

LLMs cannot self-report their version reliably. Use one of these instead:

1. Inside Claude Code: type `/model` — it shows the active model id from your ccr config.
2. Watch your **Hyperspace dashboard** (Total Requests / Cost numbers tick up as you chat) — proves the request hit the proxy with the configured model.
3. Enable ccr logging: set `"LOG": true` in `~\.claude-code-router\config.json`, restart `claude-l`, then tail:

   ```powershell
   Get-Content -Wait "$env:USERPROFILE\.claude-code-router\claude-code-router.log"
   ```

   You'll see each request's resolved provider + model, e.g. `hyperspace-litellm/anthropic--claude-4.7-opus`.

---

## 8. Troubleshooting

| Symptom                                                                | Cause                                                                                              | Fix                                                                                                                                                                          |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "model doesn't exist or you may not have access"                       | Claude Code is hitting a non-Anthropic endpoint directly (no translator).                          | Make sure you launched via `claude-l`, not bare `claude`. Check the `[claude-l] Routing through ccr -> ...` banner appears.                                                  |
| Same error AND no banner                                                | Old shim on PATH. Two `claude-l.cmd` files exist; the wrong one wins.                              | `where claude-l` — overwrite each result with the new launcher (Section 5).                                                                                                  |
| `claude-code-router (ccr) not found on PATH`                           | npm global bin not on PATH.                                                                        | Restart terminal; or add `npm config get prefix` output to PATH.                                                                                                             |
| `ccr code` exits with `EADDRINUSE`                                     | Another ccr instance already on port 3456.                                                         | `ccr stop` then retry; or change `PORT` in the config.                                                                                                                       |
| 401 / "Missing Authorization header" upstream                          | Wrong / missing `api_key` in `~\.claude-code-router\config.json`.                                  | Paste the exact bearer key from your Hyperspace UI. Test directly: `curl -H "Authorization: Bearer <KEY>" http://localhost:6655/litellm/v1/models`.                          |
| MCP servers fail with red errors at start                              | Some hook MCP servers (`npx`-launched) race with ccr startup.                                      | Optional: prefix `claude-l` with `--no-mcp` (if your Claude Code build supports it), or remove unused MCP entries from `~/.claude/settings.json`. Doesn't affect chat.        |
| "Low effort  ← / →  to adjust" status hint in Claude Code              | Reasoning-effort selector. Not an error.                                                            | Click the status item, press Right Arrow to bump Low → Medium → High → Max. Whether it actually changes behaviour depends on whether your LiteLLM proxy passes through `thinking.budget_tokens` / `reasoning_effort`. |

---

## 9. Optional: Linux / macOS shell version

Same idea as Section 5, in bash. Save as `~/bin/claude-l` and `chmod +x` it.

```bash
#!/usr/bin/env bash
set -euo pipefail

command -v claude >/dev/null 2>&1 || { echo "claude CLI not on PATH"; exit 127; }
command -v ccr    >/dev/null 2>&1 || { echo "ccr not on PATH; npm i -g @musistudio/claude-code-router"; exit 127; }

unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL ANTHROPIC_CUSTOM_HEADERS

: "${ANTHROPIC_MODEL:=anthropic--claude-4.7-opus}"
export ANTHROPIC_MODEL CLAUDE_MODEL="$ANTHROPIC_MODEL"

echo "[claude-l] Routing through ccr -> http://localhost:6655/litellm/v1"
echo "[claude-l] Model: $ANTHROPIC_MODEL"

exec ccr code "$@"
```

---

## 10. Quick recap (for impatient teammates)

```powershell
# 1. Translator
npm i -g @musistudio/claude-code-router

# 2. Config (replace KEY)
mkdir "$env:USERPROFILE\.claude-code-router" -Force | Out-Null
@"
{ "LOG": false, "HOST":"127.0.0.1","PORT":3456,"APIKEY":"",
  "Providers":[{"name":"hyperspace-litellm",
    "api_base_url":"http://localhost:6655/litellm/v1/chat/completions",
    "api_key":"REPLACE_WITH_YOUR_HYPERSPACE_KEY",
    "models":["anthropic--claude-4.7-opus","anthropic--claude-4.5-haiku"]}],
  "Router":{"default":"hyperspace-litellm,anthropic--claude-4.7-opus",
            "background":"hyperspace-litellm,anthropic--claude-4.5-haiku"} }
"@ | Set-Content "$env:USERPROFILE\.claude-code-router\config.json"

# 3. Launcher
Copy-Item -Force everything-claude-code\scripts\claude-l.cmd `
                 "$env:USERPROFILE\.local\bin\claude-l.cmd"

# 4. Run
claude-l
```

If `[claude-l] Routing through ccr -> ...` shows up before Claude Code starts, you're done.
