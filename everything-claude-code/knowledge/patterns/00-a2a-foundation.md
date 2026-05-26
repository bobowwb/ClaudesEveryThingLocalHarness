# Pattern 00 — A2A Protocol Foundation

> Reference distilled from `C:\EPM_ACCUMULATION\appFnd\app\routes\a2a_outer.py`, `agents\render_agent\a2a_app.py`, `agents\pws_agent\a2a_app.py`, `sampleJson\A2A *.json`.
> **Idea, not code.** To be re-implemented in Forge in its own way.
> **This is the foundation. Patterns 01-04 (oTel, Armor, 4D Memory, Orchestrator) are wrappers built ON TOP OF A2A.**

## The core principle

> User on 2026-05-22: *"All the wrapper should based on A2A"*

Every agent in the system is **A2A-compliant by construction**. There are no "internal" function-call agents that someone later wraps in A2A. An agent IS its A2A endpoints + agent card from day one. Wrappers (Armor, 4D Memory, oTel) decorate A2A-compliant agents — they never replace the protocol.

## What A2A is (in one paragraph)

A2A (Agent-to-Agent) is **JSON-RPC 2.0 over HTTP** with a discovery card. An agent publishes a single `/.well-known/agent.json` (the card) describing its name, version, skills, capabilities, and endpoints. Any other agent can discover those skills, then send a JSON-RPC `tasks/send` (or `message/send`) call to execute one. Responses carry a `result.status.state` (completed / submitted / failed) and a `result.status.message` containing structured `parts`. Trace IDs and skill IDs flow through `metadata`. That's the whole protocol.

## The two endpoints every A2A agent MUST expose

```
GET  /.well-known/agent.json   ← discovery (the agent card)
POST /                         ← JSON-RPC 2.0 method dispatch
       (or POST /a2a depending on convention)
```

That's it. Two endpoints. Anything else (health checks, debug routes, dashboards) is auxiliary.

## The agent card shape

```json
{
  "name": "render_agent",
  "description": "EPM FP&A Render Agent",
  "url": "http://localhost:5000",
  "version": "1.1.0",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false
  },
  "defaultInputModes":  ["text"],
  "defaultOutputModes": ["text"],
  "skills": [
    {
      "id":          "render_html_outer",
      "name":        "Render Outer Dashboard",
      "description": "Rich HTML popup with SVG charts"
    }
  ]
}
```

Required keys: `name`, `version`, `skills[]` (each with `id`, `name`, `description`). Everything else has sensible defaults.

## The JSON-RPC request shape

```json
{
  "jsonrpc": "2.0",
  "method":  "tasks/send",
  "id":      "req-uuid",
  "params": {
    "id": "task-uuid",
    "message": {
      "role": "user",
      "parts": [
        { "type": "text", "text": "<json-stringified payload>" }
      ]
    },
    "metadata": {
      "trace_id": "<correlation>",
      "skill_id": "<which skill to invoke>"
    }
  }
}
```

Method names: `tasks/send` (start a task, blocking) or `message/send` (one-shot message). Skill is selected via `metadata.skill_id`. Domain payload goes inside `message.parts[].text` as a JSON string (so the protocol stays text-shaped for future modality flexibility).

## The JSON-RPC response shape

```json
{
  "jsonrpc": "2.0",
  "id":      "req-uuid",
  "result": {
    "id": "task-uuid",
    "status": {
      "state": "completed",
      "message": {
        "messageId": "msg-uuid",
        "role": "agent",
        "parts": [
          { "type": "text", "text": "<json-stringified result>" }
        ]
      }
    }
  }
}
```

Or on error:

```json
{
  "jsonrpc": "2.0",
  "id": "req-uuid",
  "error": { "code": -32601, "message": "Method not found" }
}
```

States: `submitted | working | completed | failed | canceled`.

## Discovery flow (Need 1 in appFnd's "completeness")

Before sending a task to an agent, the orchestrator FIRST calls `GET /.well-known/agent.json` and logs:

```
- a2a_agent_name        (from card.name)
- a2a_agent_version     (from card.version)
- a2a_protocol_version  ("jsonrpc-2.0")
- agent_card_url        ("<url>/.well-known/agent.json")
- skills_available      [s.id for s in card.skills]
- agent_card_fetched_at (ISO timestamp)
- latency_ms            (round-trip ms)
```

This is logged as a `step("agent_card_discovered", ...)` event. The orchestrator now KNOWS the agent's identity and capabilities before invoking any skill — no hardcoded assumptions.

## The "A2A completeness" 6 fields per task call

Every task hop logs these:

| # | Field | Source |
|---|---|---|
| 1 | `agent_card_discovered` | step before first call (see above) |
| 2 | `a2a_target_url` | URL the JSON-RPC POST went to |
| 3 | `a2a_protocol_version` + `a2a_agent_name` | from agent card |
| 4 | `http_status_code` + `latency_ms` | from HTTP response |
| 5 | `a2a_task_state` | `result.status.state` (completed/failed/...) |
| 6 | `a2a_skill_id` | the skill being invoked |

These six fields make any A2A call **self-describing in logs**. The oTel layer (Pattern 01) reads them straight into `add_step()` — that's how the two layers compose.

## The orchestrator side (caller pattern)

```python
def _a2a_task(url, skill_id, payload, trace_id, agent_name, protocol_version):
    body = {
        "jsonrpc": "2.0", "method": "tasks/send", "id": str(uuid.uuid4()),
        "params": {
            "id": str(uuid.uuid4()),
            "message": {"role": "user",
                        "parts": [{"type": "text", "text": json.dumps(payload)}]},
            "metadata": {"trace_id": trace_id, "skill_id": skill_id}
        }
    }
    t0 = time.perf_counter()
    resp = httpx.post(f"{url}/", json=body, timeout=60)
    latency = round((time.perf_counter() - t0) * 1000)
    http_status = resp.status_code         # capture BEFORE raise_for_status
    resp.raise_for_status()
    data = resp.json()

    result_obj = data.get("result", {})
    state      = result_obj.get("status", {}).get("state", "unknown")
    parts      = result_obj.get("status", {}).get("message", {}).get("parts", [])
    text       = next((p["text"] for p in parts if p.get("type") == "text"), "{}")
    result     = json.loads(text)

    meta = {
        "a2a_target_url": f"{url}/",
        "a2a_protocol_version": protocol_version,
        "a2a_agent_name": agent_name,
        "http_status_code": http_status,
        "latency_ms": latency,
        "a2a_task_state": state,
        "a2a_skill_id": skill_id,
    }
    return result, meta
```

**Two key tricks:**
1. Capture `http_status` BEFORE `raise_for_status()` — so error responses still log the status
2. Return `(result, meta)` tuple — caller gets domain data + observability fields in one call

## The agent side (callee pattern)

```python
@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card():
    return jsonify(AGENT_CARD)

@app.route("/", methods=["POST"])              # or /a2a
def handler():
    body = request.get_json(force=True) or {}
    req_id = body.get("id", "1")
    method = body.get("method", "")

    if method != "message/send" and method != "tasks/send":
        return jsonify({
            "jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }), 404

    params  = body.get("params", {})
    message = params.get("message", {})
    parts   = message.get("parts", [])
    user_text = next((p.get("text", "") for p in parts if p.get("type") == "text"), "")

    # Extract skill_id from metadata; dispatch to the right skill handler
    skill_id = params.get("metadata", {}).get("skill_id", "")
    payload  = json.loads(user_text) if user_text.startswith("{") else {"text": user_text}

    result_text = _dispatch_skill(skill_id, payload)

    return jsonify({
        "jsonrpc": "2.0", "id": req_id,
        "result": {
            "id": str(uuid.uuid4()),
            "status": {
                "state": "completed",
                "message": {
                    "messageId": str(uuid.uuid4()),
                    "role": "agent",
                    "parts": [{"type": "text", "text": result_text}]
                }
            }
        }
    })
```

Two endpoints. Method dispatcher. Skill router. ~40 lines for a real A2A-compliant agent.

## Why this is the foundation

| Wrapper | Reads from A2A | Writes to A2A |
|---|---|---|
| **oTel (Pattern 01)** | every `add_step` records `a2a_*` fields from the call meta | trace store reflects the A2A call graph 1:1 |
| **Armor (Pattern 02)** | `ToolSchema.name` ≡ A2A `skill_id`. `_dispatch` calls `_a2a_task`, not raw functions | uniform `ArmorResult` returned to upstream A2A caller |
| **4D Memory (Pattern 03)** | `_with_4d_memory` wraps a stage that ITSELF makes A2A calls. memory_id keys off `(trace_id, skill_id, agent_name)` | persists to memory tables alongside A2A logs |
| **Orchestrator (Pattern 04)** | The orchestrator IS just a chained sequence of A2A calls. classify → fetch_context → run_forecast → render via `_a2a_task` each time | every middleware (audit/telemetry/guardrail/memory/cost/eval) wraps an A2A call |

**Translation:** if someone asks "what's the agent boundary?" the answer is always "the A2A endpoint." Wrappers add cross-cutting concerns; they never substitute for the protocol.

## How agents are CREATED to be naturally A2A-compliant

Don't write "a function that does X" then bolt A2A onto it. Write it the other way around:

### Step 1 — Define the agent card FIRST

Before any business logic, write the card:

```python
AGENT_CARD = {
    "name": "forge_environment_agent",
    "description": "Picks environment / set design for a Story2Movie scene",
    "url": "http://localhost:7100",
    "version": "1.0.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "defaultInputModes":  ["text"],
    "defaultOutputModes": ["text"],
    "skills": [
        {"id": "pick_environment",     "name": "Pick environment for scene",
         "description": "Given scene prompt + persona DNA, return environment spec"},
        {"id": "list_alternatives",    "name": "List 3 alternative environments",
         "description": "Used when user asks for re-render"},
    ],
}
```

The card is the agent's **public contract**. Skills listed here are the only externally-callable functions. Anything else is an internal helper.

### Step 2 — Make every skill independently dispatchable

Skills are routed by `metadata.skill_id`:

```python
SKILL_HANDLERS = {
    "pick_environment":  _pick_environment,
    "list_alternatives": _list_alternatives,
}

def _dispatch_skill(skill_id, payload):
    handler = SKILL_HANDLERS.get(skill_id)
    if not handler:
        return json.dumps({"error": f"Unknown skill: {skill_id}"})
    result = handler(payload)
    return json.dumps(result)
```

A skill handler:
- Takes a single dict (`payload`)
- Returns a single dict (becomes JSON-stringified for the response part)
- Raises on irrecoverable error (caught at HTTP layer → returns `state: failed`)

### Step 3 — One file, two endpoints, run as a service

```python
# agents/forge_environment/a2a_app.py
app = Flask(__name__)

@app.route("/.well-known/agent.json", methods=["GET"])
def card(): return jsonify(AGENT_CARD)

@app.route("/", methods=["POST"])
def handler(): return _handle_a2a(request.get_json(force=True) or {})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7100)))
```

The agent is now a real network service. It can be:
- Run locally (`python a2a_app.py`)
- Run in Vercel as a serverless function
- Discovered by any orchestrator on the network
- Replaced by a different language/framework as long as the card and JSON-RPC shape match

### Step 4 — Wrap with Armor / 4D Memory only AFTER A2A works

Order of construction:
1. Card + handlers + skills → A2A-compliant (Pattern 00, this doc)
2. Wrap skill handlers in `AgentArmor.execute(skill_id, payload)` → safety pipeline (Pattern 02)
3. Wrap the orchestrator's `_a2a_task` calls in `_with_4d_memory` → auto-RAG + auto-persist (Pattern 03)
4. Every `_a2a_task` call writes oTel record with the 6 completeness fields (Pattern 01)
5. Orchestrator routes by intent → A2A target agent (Pattern 04)

If A2A works at step 1, the wrappers compose. If A2A is bolted on at step 5, every wrapper has to special-case "is this an A2A call or a function call?" — that's the bug-factory.

## Forge mapping

Forge currently has `studio_orchestrator.py` doing **in-process Python dispatch** to specialist agents (WR, EN, CH, LI, AU, ED). That is NOT A2A-compliant. To fix:

### Each Forge specialist becomes an A2A service

```
agents/forge_writer/a2a_app.py         (port 7100, skill: write_scene)
agents/forge_environment/a2a_app.py    (port 7101, skill: pick_environment)
agents/forge_character/a2a_app.py      (port 7102, skill: design_character)
agents/forge_lighting/a2a_app.py       (port 7103, skill: design_lighting)
agents/forge_audio/a2a_app.py          (port 7104, skill: design_audio)
agents/forge_editor/a2a_app.py         (port 7105, skill: edit_timeline)
agents/forge_render/a2a_app.py         (port 7106, skills: render_2d, render_3d, render_video)
```

Each has a card at `/.well-known/agent.json`. Each speaks JSON-RPC 2.0 at `/`.

### The orchestrator becomes an A2A caller

`forge_orchestrator.py` (replacing `studio_orchestrator.py`) does:
1. Discover each specialist's card at startup (cache the skills list)
2. For each scene: `_a2a_task(env_url, "pick_environment", payload, trace_id)` etc.
3. Compose results, call `forge_render` agent's `render_2d` and `render_3d` skills
4. Persist trace IDs back to the dashboard (which polls `list_recent_traces`)

### The dashboard becomes an A2A consumer

`dashboard.html` calls a single `/api/orchestrate` endpoint (Vercel function) that internally fans out as A2A calls. The dashboard's A2A Studio panel rows (WR/EN/CH/LI/AU/ED) come alive because each is now a real agent with a real `a2a_task_state` from a real `_a2a_task` call.

**This is what makes the Director's Blueprint pane fill instead of staying "Waiting for script..."** — the panes are just A2A trace views.

## Don't over-design

- v1: skills can return text-as-JSON-string (per the spec); typed protobuf later if needed
- v1: localhost ports — no service discovery / DNS / k8s
- v1: blocking `tasks/send` only; streaming/`pushNotifications=false` for now
- v1: no auth — add bearer tokens once two services need to talk across networks
- The agent card is the SOURCE OF TRUTH for skills. If you find yourself adding a skill in code without updating the card, stop. Update the card first; add the handler second.

## Cross-references

- Pattern 01 (oTel) — reads A2A's 6 completeness fields into trace records
- Pattern 02 (Armor) — wraps skill handlers; `ToolSchema.name == skill_id`
- Pattern 03 (4D Memory) — keys off `(trace_id, skill_id, agent_name)` from A2A meta
- Pattern 04 (Orchestrator) — chains A2A calls per intent classification
- Sample call shapes: `appFnd/sampleJson/A2A *.json` (Single, Inner, Outer, Discover-and-Call)


