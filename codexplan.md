TASK: Configure local Codex to use my local Hyperspace AI / LiteLLM proxy.

Context:
- My local proxy is already running.
- Proxy URL from screenshot:
  http://localhost:6656/v1
- Proxy API key from screenshot:
  8a6ab847-a6aa-4b1e-b84f-629d2f905046
- I want Codex CLI / Codex IDE to use this local proxy.
- Do NOT commit API keys.
- Do NOT modify unrelated project files.
- Work in small steps and show diff.

Goal:
Create a safe local Codex configuration that can use the local proxy for coding tasks.

Important docs behavior:
- User-level Codex config is:
  %USERPROFILE%\.codex\config.toml
- Project-level config is:
  <repo>\.codex\config.toml
- CLI and IDE extension share config layers.
- API key should be referenced through an environment variable, not hardcoded in config.toml.

Step 1: Inspect current Codex config
Run read-only commands only:

PowerShell:
  echo $env:USERPROFILE
  if (Test-Path "$env:USERPROFILE\.codex") { Get-ChildItem "$env:USERPROFILE\.codex" } else { "No .codex folder yet" }
  if (Test-Path "$env:USERPROFILE\.codex\config.toml") { Get-Content "$env:USERPROFILE\.codex\config.toml" } else { "No config.toml yet" }

Step 2: Create Codex config folder if missing

PowerShell:
  New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex"

Step 3: Create or update global Codex config

File:
  %USERPROFILE%\.codex\config.toml

Use this content:

  model = "gpt-5-mini"
  model_provider = "hyperspace"
  model_reasoning_effort = "medium"

  [model_providers.hyperspace]
  name = "Hyperspace Local LiteLLM Proxy"
  base_url = "http://localhost:6656/v1"
  env_key = "HYPERSPACE_API_KEY"
  wire_api = "responses"

Notes:
- Do not put the real API key inside config.toml.
- The env_key value must be the name of an environment variable.
- Use gpt-5-mini first for cheaper/smaller coding tasks.
- Current Codex requires wire_api = "responses"; the local shim provides the Responses endpoint and forwards to the 6655 chat proxy.

Step 4: Set Windows user environment variable

PowerShell:
  setx HYPERSPACE_API_KEY "8a6ab847-a6aa-4b1e-b84f-629d2f905046"

Important:
- After setx, restart VS Code / terminal / Codex app so the env var is visible.
- For current terminal only, also run:
  $env:HYPERSPACE_API_KEY="8a6ab847-a6aa-4b1e-b84f-629d2f905046"

Step 5: Test Codex with local proxy

Run:

  codex -c model_provider=hyperspace -c model=gpt-5-mini

Inside Codex, ask:

  Say hello only. Do not inspect files. Do not edit files.

Expected:
- Hyperspace proxy window should show a POST request to:
  /litellm/v1/chat/completions
- Codex should answer.

Step 6: Add project-local config only if needed

If I want only this repo to use local proxy, create:

  <repo>\.codex\config.toml

with:

  model = "gpt-5-mini"
  model_provider = "hyperspace"
  model_reasoning_effort = "medium"

  [model_providers.hyperspace]
  name = "Hyperspace Local LiteLLM Proxy"
  base_url = "http://localhost:6656/v1"
  env_key = "HYPERSPACE_API_KEY"
  wire_api = "responses"

Do not create project-local config unless I explicitly confirm this repo should use proxy by default.

Step 7: Add safety AGENTS.md

Create or update:

  %USERPROFILE%\.codex\AGENTS.md

Content:

  # Global Codex Rules

  - First inspect the repo before editing.
  - Do not scan the whole repo unless necessary.
  - Prefer one-file or small-step changes.
  - Show plan before editing.
  - Show diff after editing.
  - Run safe validation after changes.
  - Ask before install, deploy, delete, reset, service start/stop, or config mutation.
  - Do not change ports unless explicitly requested.
  - Do not commit secrets or auth files.
  - Do not edit .env, auth.json, config files containing secrets unless explicitly requested.

Step 8: Verify final state

Run:

  Get-Content "$env:USERPROFILE\.codex\config.toml"
  Get-Content "$env:USERPROFILE\.codex\AGENTS.md"
  echo $env:HYPERSPACE_API_KEY

Do not print the full API key in final response. Mask it like:
  8a6a...5046

Step 9: Final report

Return:
- Files created/changed
- Exact config used
- Whether proxy logs showed Codex traffic
- Whether codex test succeeded
- Any fallback tried
- How to revert

Revert instructions:
- Remove or rename:
  %USERPROFILE%\.codex\config.toml
- Or change model_provider back to OpenAI/default.
- Remove env var manually from Windows Environment Variables if needed.



$env:HYPERSPACE_API_KEY="8a6ab847-a6aa-4b1e-b84f-629d2f905046"

codex `
  -c model_provider=hyperspace `
  -c model=gpt-5-mini `
  -c model_providers.hyperspace.name="Hyperspace Local LiteLLM Proxy" `
  -c model_providers.hyperspace.base_url="http://localhost:6656/v1" `
  -c model_providers.hyperspace.env_key="HYPERSPACE_API_KEY" `
  -c model_providers.hyperspace.wire_api="responses"

  Use one command per launch with -c override.

Use local proxy
codex -c model_provider=hyperspace -c model=gpt-5-mini
Use normal OpenAI / ChatGPT Codex
codex -c model_provider=openai -c model=gpt-5-mini

If your local proxy provider is not already saved in ~\.codex\config.toml, use this full one-line proxy command:

codex -c model_provider=hyperspace -c model=gpt-5-mini -c model_providers.hyperspace.name="Hyperspace Local LiteLLM Proxy" -c model_providers.hyperspace.base_url="http://localhost:6656/v1" -c model_providers.hyperspace.env_key="HYPERSPACE_API_KEY" -c model_providers.hyperspace.wire_api="responses"

Best shortcut:

function codex-local { codex -c model_provider=hyperspace -c model=gpt-5-mini }
function codex-openai { codex -c model_provider=openai -c model=gpt-5-mini }

Then you can switch with:

codex-local

or:

codex-openai

---

## Setup Summary (completed 2026-05-09)

All steps executed successfully.

### Files Created/Modified

- %C:\Users\I075354%\.codex\config.toml - Updated with hyperspace provider
- %C:\Users\I075354%\.codex\AGENTS.md - Created with global safety rules
- Windows env HYPERSPACE_API_KEY - Set via setx (persisted)

### Final config.toml

  model = "gpt-5-mini"
  model_provider = "hyperspace"
  model_reasoning_effort = "medium"

  [model_providers.hyperspace]
  name = "Hyperspace Local LiteLLM Proxy"
  base_url = "http://localhost:6656/v1"
  env_key = "HYPERSPACE_API_KEY"
  wire_api = "responses"

### Key: 8a6a...5046 (masked)

### IMPORTANT: Restart VS Code and Codex app after setup.

### Quick commands

  codex -c model_provider=hyperspace -c model=gpt-5   # use local proxy
  codex -c model_provider=openai -c model=gpt-5.5        # use OpenAI

### Revert

  Remove or edit %C:\Users\I075354%\.codex\config.toml
  Delete HYPERSPACE_API_KEY from Windows Environment Variables

---

## One-command route switch (added 2026-05-09)

PowerShell profile now provides these commands:

```powershell
codex-route status   # show current Codex model/model_provider
codex-route local    # switch default Codex route to local Hyperspace LiteLLM proxy
codex-route openai   # switch default Codex route back to OpenAI
codex-local          # switch to local proxy, then start Codex
codex-openai         # switch to OpenAI, then start Codex
```

Local proxy route uses:

```toml
model_provider = "hyperspace"
base_url = "http://localhost:6656/v1"
env_key = "HYPERSPACE_API_KEY"
wire_api = "responses"
```

The API key is stored in the Windows user environment variable `HYPERSPACE_API_KEY`; do not hardcode it in Codex commands.

After editing the profile, open a new PowerShell window or run:

```powershell
. $PROFILE
```

Then use one command:

```powershell
codex-local
```

or switch back with:

```powershell
codex-openai
```


### Local Responses shim note

Current Codex requires `wire_api = "responses"`. The Hyperspace local proxy on `6655` exposes chat completions but not `/responses`, so `codex-route local` starts this shim automatically:

```powershell
C:\tmp\codex_responses_shim.py
```

Codex calls `http://localhost:6656/v1/responses`; the shim forwards to `http://localhost:6656/v1/chat/completions`.


