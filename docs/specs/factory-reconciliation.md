# Factory Reconciliation — What Exists vs What Phase 1 Needs

**Date:** 2026-06-25
**Purpose:** Ground the cockpit-as-ADK-builder build in what the Agent Factory ALREADY does, so we integrate instead of rebuild. Every claim cites a real file:line or ADK doc URL.

---

## 1. What render_agent_package(spec) Accepts and Emits

### Input: AgentSpec (models.py:15-37)

```python
class AgentSpec(BaseModel):
    id: str                                    # line 18 — stable agent ID (e.g. "ops")
    package: str                               # line 19 — Python import path (e.g. "forsch.agent_ops.agent")
    attr: str = "root_agent"                   # line 20 — export attribute name
    adk_name: str                              # line 21 — ADK runtime agent name (e.g. "ops_agent")
    agent_class: str = "LlmAgent"             # line 22 — ADK agent class
    description: str = ""                      # line 23 — human-readable description
    model_code: str                            # line 24 — fully-qualified model import path
    instruction: str = ""                      # line 25 — system instruction text
    group: Optional[str] = None                # line 28 — preamble component group
    model: Optional[str] = None                # line 31 — LiteLLM model pin (None = shared default)
    web_entrypoint: Optional[str] = None       # line 32 — web_agents/<name> path
    discord_channels: list[str] = []           # line 33 — bridge channel routing
    safety_level: str = "read_only"            # line 34 — safety classification
    purpose: str = ""                          # line 35 — purpose description
    tools: list[str] = []                      # line 36 — FQ tool names (e.g. "forsch.adk_components.tools.get_crm_health_snapshot")
    smoke_prompts: list[str] = []              # line 37 — test prompts for smoke testing
```

### What render_agent_package emits (renderer.py:82-106)

For agent ID `ops`, it writes **one file**:

```
agents/ops/src/forsch/agent_ops/agent.py
```

The rendered content (from `agent.py.j2`) includes:
- `import os` + `from google.adk import Agent` + `from google.adk.models.lite_llm import LiteLlm`
- Tool imports from `forsch.adk_components.tools`
- LiteLLM model construction with env-based config
- `root_agent = Agent(name=..., model=..., description=..., instruction=..., tools=[...])`
- `agent = root_agent` (ADK Web compatibility alias)

### What render_agent emits (renderer.py:70-79)

If `spec.web_entrypoint` is set, it writes:

```
web_agents/<name>/root_agent.yaml
```

The YAML contains: `agent_class`, `name`, `description`, `instruction`, `model_code.name`, `tools` (list of `{name: ...}`).

### What the full apply() writes (cli.py:111-135)

`apply()` calls `plan()` which calls both `render_agent` + `render_agent_package`, so a full generate writes **2 files**:
1. `agents/<id>/src/forsch/agent_<id>/agent.py` (the runtime)
2. `web_agents/<id>/root_agent.yaml` (the ADK Web surface)

Plus it runs `validate_agent_tools` + `check_deploy_gate` before writing (cli.py:123-131).

---

## 2. What canvas_api.py ALREADY Exposes

### Routes (canvas_api.py:102-134)

The builder cockpit (`app.py`) calls `build_view(workspace_root)` which returns:

```python
{
    "agents": [...],     # list of agent dicts with id, name, description, model, group, safety, instruction, tools, channels, smoke_prompts, rendered_yaml
    "toolbox": [...],    # drawers of tools/clients/agents for the wire panel
    "models": [...],     # available LiteLLM model IDs (live from proxy, fallback to static list)
    "groups": [...],     # preamble group names from preambbles/<group>.md
}
```

### What editor.py ALREADY exposes (editor.py:32-90)

`update_agent(workspace_root, agent_id, patch)` accepts a patch dict with optional keys:
- `instruction` (str) — updates system instruction
- `tools` (list[str]) — updates tool list (auto-prefixes `forsch.adk_components.tools.`)
- `model` (str) — pins/unpins LiteLLM model
- `group` (str) — selects/removes preamble jacket

It writes to `agent_specs/agents.yaml` (round-trip safe via ruamel), then regenerates both `root_agent.yaml` and `agent.py`.

Returns:
```python
{
    "ok": True,
    "agent": agent_id,
    "tools": [...],        # leaf tool names
    "model": "...",        # pinned model or ""
    "group": "...",        # group or ""
    "written": [...],      # absolute paths of written files
    "rendered_yaml": "...", # contents of root_agent.yaml
}
```

### Phase 1 Needs vs What Exists

| Phase 1 Endpoint | Method | What It Needs | What Exists | Gap |
|---|---|---|---|---|
| `get_config` | GET | Read agent config from agents.yaml | `build_view()` returns agent data but NOT the full config (missing `package`, `attr`, `model_code`, `safety_level`, `purpose`, `smoke_prompts`) | **Partial.** `build_view` strips fields. Need a dedicated config reader. |
| `save_config` | POST | Write config to agents.yaml + regenerate | `update_agent()` does exactly this | **Exists.** Can be wrapped directly. |
| `list_tools` | GET | Return available tools from library | `build_view()` → `toolbox` returns tools via AST parsing of components | **Exists.** Already returns tool names + summaries. |
| `generate` | POST | Run Factory to produce agent package | `cli.apply()` does exactly this | **Exists.** Can be wrapped directly. |
| `verify_status` | GET | Check if generation succeeded | No dedicated endpoint. `apply()` returns `written` paths. | **Missing.** Need to check if files exist + are importable. |
| `list_connections` | GET | Show parent/child relationships | `build_view()` doesn't return wiring info | **Missing.** Need to read cluster YAML or graph JSON. |
| `list_models` | GET | Return available models | `build_view()` → `models` already queries LiteLLM | **Exists.** |

---

## 3. Verify/Smoke Step — Does It Exist?

### What exists today

1. **`adk-factory validate`** (cli.py:188-196) — runs `validate_agent_tools(spec)` which checks:
   - Tool imports succeed
   - Tool docstrings exist
   - Authsome liveness (BehavioralValidator, validation.py:283-337)
   - API reachability per tool's auth provider
   - Per-tool smoke tests (if defined in tool metadata)

2. **`adk-factory smoke`** mentioned in AGENT_FACTORY_SPEC.md:195 but **NOT implemented in cli.py**. The CLI only has `apply`, `plan`, and `validate` commands (cli.py:160).

3. **`smoke_prompts`** field exists in AgentSpec (models.py:37) and is populated in agents.yaml, but no code actually runs these prompts against the agent.

4. **No `adk web` boot check** — nothing verifies the generated package actually starts. The AGENT_FACTORY_SPEC.md describes this as a desired feature (line 381: "Optional live Runner turn works when credentials are present") but it's not implemented.

### What's missing for "Generate & Verify"

The spec (agent-detail-view.md:107-112) requires:
1. Write config to agents.yaml ✅ (`update_agent`)
2. Trigger Factory to generate package ✅ (`cli.apply`)
3. **Smoke test: `adk web` starts, responds to one test message, exits clean** ❌ NOT IMPLEMENTED
4. Flip status to built or error ❌ No status tracking exists

### Where smoke should slot

After `cli.apply()` writes the files, add a verification step:

```python
# Pseudocode for the verify step
def verify_agent(agent_id, workspace_root):
    """Import the generated agent and optionally run a smoke prompt."""
    # 1. Import check: can we import root_agent?
    # subprocess: python -c "from forsch.agent_{id}.agent import root_agent; print(root_agent.name)"
    
    # 2. Name check: does root_agent.name match adk_name?
    
    # 3. Optional: run one smoke prompt via ADK Runner
    # This requires the ADK runtime + LiteLLM proxy to be available
    # Should be a lightweight subprocess call, not an in-process import
```

This should be a new function in `validation.py` or a new `smoke.py` module, callable both from the CLI and from the Frappe API proxy.

---

## 4. The Box JSON API Contract — 6 Endpoints

### 4.1 GET /agent-config

**Read an agent's full config from agents.yaml.**

Request:
```
GET /agent-config?agent_id=ops
Headers: X-Graph-Secret: <secret>
```

Response (200):
```json
{
  "ok": true,
  "agent": {
    "id": "ops",
    "adk_name": "ops_agent",
    "description": "Infrastructure and operations lead for Forsch.",
    "model": "glm-5.2",
    "model_code": "forsch.agent_ops.agent.ops_model",
    "instruction": "You are the ops team lead for Forsch...",
    "tools": ["get_crm_health_snapshot", "list_recent_crm_leads"],
    "safety_level": "read_only",
    "purpose": "Infrastructure and operations lead for Forsch.",
    "group": "",
    "smoke_prompts": ["Introduce yourself and describe your role for Forsch."],
    "package": "forsch.agent_ops.agent",
    "web_entrypoint": "web_agents/ops",
    "discord_channels": ["#team-ops"],
    "status": "built"
  }
}
```

Response (404):
```json
{"ok": false, "error": "unknown agent: ops"}
```

**Implementation:** Read `agent_specs/agents.yaml` with PyYAML/ruamel, return the agent block + derived status (check if `agents/<id>/src/forsch/agent_<id>/agent.py` exists → "built", else "blank").

### 4.2 POST /agent-config

**Save an agent's config to agents.yaml + regenerate package.**

Request:
```
POST /agent-config
Headers: X-Graph-Secret: <secret>, Content-Type: application/x-www-form-urlencoded
Body: agent_id=ops&instruction=New+instruction&tools=get_crm_health_snapshot,list_recent_crm_leads&model=glm-5.2
```

Response (200):
```json
{
  "ok": true,
  "agent": "ops",
  "tools": ["get_crm_health_snapshot", "list_recent_crm_leads"],
  "model": "glm-5.2",
  "group": "",
  "written": [
    "/opt/data/workspace/adk/agents/ops/src/forsch/agent_ops/agent.py",
    "/opt/data/workspace/adk/web_agents/ops/root_agent.yaml"
  ],
  "rendered_yaml": "agent_class: LlmAgent\nname: ops_agent\n..."
}
```

**Implementation:** Wrap `editor.update_agent()`. The editor already handles ruamel round-trip, preamble composition, and dual-file regeneration.

### 4.3 GET /agent-tools

**List available tools from the components library.**

Request:
```
GET /agent-tools
Headers: X-Graph-Secret: <secret> (or unauthenticated — read-only)
```

Response (200):
```json
{
  "ok": true,
  "tools": [
    {
      "name": "get_crm_health_snapshot",
      "summary": "Get a snapshot of CRM health metrics",
      "file": "/opt/data/workspace/adk/components/src/forsch/adk_components/tools/crm_tools.py",
      "wireable": true
    },
    {
      "name": "list_recent_crm_leads",
      "summary": "List recent CRM leads",
      "file": "/opt/data/workspace/adk/components/src/forsch/adk_components/tools/crm_tools.py",
      "wireable": true
    }
  ]
}
```

**Implementation:** Already exists in `canvas_api._toolbox()` (canvas_api.py:67-99). Extract the tools drawer. Note: the current implementation uses AST parsing to discover tools — it returns ALL functions from components, not just the ones in `agent_tools.yaml`. These are two different tool registries:
- **ADK components** (canvas_api.py toolbox): real Python functions the Factory can import
- **agent_tools.yaml** (our spec): conceptual tool definitions with parameter schemas and risk levels

For Phase 1, use the ADK components toolbox (it's what the Factory actually validates against). The `agent_tools.yaml` is a UI-layer concern for the Config tab's "+ Add Tool" palette.

### 4.4 POST /agent-generate

**Trigger Factory generate + verify for an agent.**

Request:
```
POST /agent-generate
Headers: X-Graph-Secret: <secret>, Content-Type: application/x-www-form-urlencoded
Body: agent_id=ops
```

Response (200, immediate):
```json
{
  "ok": true,
  "agent": "ops",
  "status": "building",
  "job_id": "ops-20260625-001"
}
```

Response (500):
```json
{
  "ok": false,
  "error": "deploy gate blocked: 1 red tool(s)",
  "details": "..."
}
```

**Implementation:** This is the NEW piece. It needs to:
1. Call `cli.apply()` (which validates + writes files)
2. Call a new `verify_agent()` function (import check + optional smoke)
3. Return status

The async pattern (job_id + polling) is specified in the spec but may be overkill for Phase 1 — `apply()` + verify typically completes in <5 seconds. Consider making it synchronous with a 30s timeout, falling back to async only if needed.

### 4.5 GET /agent-verify

**Check the verification status of an agent.**

Request:
```
GET /agent-verify?agent_id=ops
Headers: X-Graph-Secret: <secret>
```

Response (200):
```json
{
  "ok": true,
  "agent": "ops",
  "status": "built",
  "package_exists": true,
  "import_ok": true,
  "smoke_ok": true,
  "last_verify": "2026-06-25T00:15:00Z",
  "files": [
    "agents/ops/src/forsch/agent_ops/agent.py",
    "web_agents/ops/root_agent.yaml"
  ]
}
```

Response (200, not built):
```json
{
  "ok": true,
  "agent": "ops",
  "status": "blank",
  "package_exists": false,
  "import_ok": false,
  "smoke_ok": null,
  "last_verify": null,
  "files": []
}
```

**Implementation:** New function. Checks:
1. Does `agents/<id>/src/forsch/agent_<id>/agent.py` exist?
2. Can we import it? (subprocess: `python -c "from forsch.agent_<id>.agent import root_agent"`)
3. Does `root_agent.name` match `adk_name`?
4. Optional: run smoke prompt

### 4.6 GET /agent-connections

**List wiring relationships for agents in a cluster.**

Request:
```
GET /agent-connections?cluster=demo
Headers: X-Graph-Secret: <secret>
```

Response (200):
```json
{
  "ok": true,
  "cluster": "demo",
  "connections": [
    {
      "source": "primary_assistant",
      "target": "calendar_specialist",
      "type": "delegates_to"
    },
    {
      "source": "primary_assistant",
      "target": "shopping_specialist",
      "type": "delegates_to"
    }
  ]
}
```

**Implementation:** New endpoint. Read `clusters/<name>/cluster.yaml` + `agent-graph-v2.json` to derive parent/child relationships. The graph JSON already has edges; extract the sub-graph for depth-1.

---

## 5. GAP LIST — What's Missing for Phase 1

### Must-Have (blocking Phase 1 build)

| # | Gap | Effort | Notes |
|---|---|---|---|
| G1 | **`GET /agent-config` endpoint** — full config reader | Small | `build_view()` exists but strips fields. Need a dedicated reader that returns ALL AgentSpec fields + derived status. |
| G2 | **`POST /agent-generate` endpoint** — wrap `cli.apply()` + verify | Medium | `cli.apply()` exists but has no verify step. Need to add `verify_agent()` (import check) and wire it as a JSON endpoint. |
| G3 | **`verify_agent()` function** — import check + optional smoke | Small | New function. Subprocess import check is straightforward. Smoke prompt execution needs ADK Runner — defer to Phase 2 if complex. |
| G4 | **`GET /agent-verify` endpoint** — status check | Small | New. Check file existence + importability. |
| G5 | **Box-side HTTP handler for new endpoints** | Medium | `serve.py` needs 4 new routes (`/agent-config`, `/agent-generate`, `/agent-verify`, `/agent-connections`). Currently uses `http.server` with manual routing (serve.py:541-799). Add to `do_GET` and `do_POST` handlers. |
| G6 | **Frappe proxy endpoints** — `forsch_frontiers/api/agent_config.py` + `agent_factory.py` | Medium | New files. Frappe-auth'd JSON proxy to box endpoints. Same pattern as `cockpit.py:graph_embed()` but returning JSON instead of HTML. |
| G7 | **Status tracking** — blank/building/built/error per agent | Small | Derived from file existence + import check. No persistent state needed — compute on read. |

### Can Defer (Phase 2+)

| # | Gap | Phase | Notes |
|---|---|---|---|
| G8 | Canvas zoom animation | Phase 3 | Functional sidebar swap is Phase 1. |
| G9 | Chat tab | Phase 2 | Needs SSE/WebSocket streaming from box. |
| G10 | Evals tab | Phase 2 | Needs `adk eval` integration on box. |
| G11 | Connections tab (full) | Phase 2 | Basic read-only connections is Phase 1 (G5). Editable wiring is Phase 2. |
| G12 | HITL approval UI | Phase 4 | Tool `risk_level` flag stored now; approval flow is Phase 4. |
| G13 | Gradio surface | Phase 4 | Stubbed button only. |
| G14 | `agent_tools.yaml` parameter schemas in UI | Phase 2 | Phase 1 uses ADK components toolbox (names + summaries only). |

### Integration Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | **Two tool registries** — `agent_tools.yaml` (UI concepts) vs ADK components (real imports) | Phase 1 uses ADK components only. `agent_tools.yaml` is a Phase 2 UI concern for parameter editing. |
| R2 | **`serve.py` is a 800-line monolith** — adding 4 more routes makes it worse | Acceptable for Phase 1. The native rebuild (agent-graph-native-rebuild.md) will replace this with clean JSON proxies. |
| R3 | **No persistent status** — status is computed on read, so rapid generate→check races are possible | Acceptable for single-user cockpit. Add optimistic UI (show "building" immediately, verify on next read). |
| R4 | **Factory Python path** — `FACTORY_PYTHON` in serve.py may not match the factory venv | Verify `FACTORY_PYTHON` points to the correct venv with `forsch-adk-factory` installed. |

---

## ADK Doc References

- Agent + sub_agents: https://google.github.io/adk-docs/agents/agents-and-models/
- GenerateContentConfig (temperature, top_p, max_output_tokens): https://google.github.io/adk-docs/agents/models/
- `adk web` CLI: https://google.github.io/adk-docs/agents/web-ui/
- `adk eval` CLI: https://google.github.io/adk-docs/evaluation/
- Tools (atomic design): https://google.github.io/adk-docs/tools/

---

## File References

| File | Lines | What |
|---|---|---|
| `factory/src/forsch/adk_factory/models.py` | 15-37 | AgentSpec definition |
| `factory/src/forsch/adk_factory/models.py` | 40-44 | Manifest definition |
| `factory/src/forsch/adk_factory/renderer.py` | 70-79 | render_agent (web surface) |
| `factory/src/forsch/adk_factory/renderer.py` | 82-106 | render_agent_package (runtime) |
| `factory/src/forsch/adk_factory/cli.py` | 35-63 | plan() dry-run |
| `factory/src/forsch/adk_factory/cli.py` | 66-108 | write_files() with backup/rollback |
| `factory/src/forsch/adk_factory/cli.py` | 111-135 | apply() with deploy gate |
| `factory/src/forsch/adk_factory/validation.py` | 283-337 | BehavioralValidator |
| `builder/src/forsch/adk_builder/canvas_api.py` | 67-99 | toolbox discovery |
| `builder/src/forsch/adk_builder/canvas_api.py` | 102-134 | build_view() |
| `builder/src/forsch/adk_builder/editor.py` | 32-90 | update_agent() |
| `agent_specs/agents.yaml` | 1-221 | Current manifest (7 agents) |
| `spikes/live-agent-graph/serve.py` | 541-799 | Current box HTTP handler |
| `docs/AGENT_FACTORY_SPEC.md` | 1-555 | Factory design spec |
| `docs/specs/agent-detail-view.md` | 1-282 | Agent detail view spec |
| `docs/agent-graph-native-rebuild.md` | 1-183 | Native Frappe rebuild plan |
