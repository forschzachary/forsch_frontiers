# Cerebras Dispatch — Tasks 1, 3, 5 (Phase 1 Scaffolds)

You are scaffolding Phase 1 of an ADK agent builder cockpit. Three independent tasks, each producing typed stubs/skeletons with no real logic yet. Every task has a VERIFY line — run it before declaring done.

## Canonical references (read in every task)
- Contract + gaps: `/opt/data/workspace/forsch_frontiers/docs/specs/factory-reconciliation.md` (source of truth for all JSON shapes)
- Roadmap: `/opt/data/workspace/forsch_frontiers/docs/plans/2026-06-25-agent-detail-view-implementation.md`
- Spec: `/opt/data/workspace/forsch_frontiers/docs/specs/agent-detail-view.md`
- Dispatch prompts (this context): `/opt/data/workspace/forsch_frontiers/docs/plans/dispatch-prompts.md`
- ADK docs: https://google.github.io/adk-docs/
- Frappe docs: https://docs.frappe.io/framework

## Task 1 — Box JSON API stubs

**Goal:** Add 4 new routes to the existing box HTTP server as typed stubs returning the exact contracted JSON shapes. No real Factory calls yet.

**Read first (cite file:line in output):**
- `/opt/data/workspace/forsch_frontiers/docs/specs/factory-reconciliation.md` → Section 4 "Box JSON API Contract" (authoritative for all request/response shapes)
- `/opt/data/workspace/adk/spikes/live-agent-graph/serve.py` → follow its existing authenticated-handler style (do_GET/do_POST, X-Graph-Secret check pattern, JSON responses via `_json_response`)
- `/opt/data/workspace/adk/builder/src/forsch/adk_builder/canvas_api.py` → existing models/toolbox discovery (line 67-134)
- `/opt/data/workspace/adk/builder/src/forsch/adk_builder/editor.py` → existing update_agent (line 32-90)
- `/opt/data/workspace/adk/factory/src/forsch/adk_factory/cli.py` → existing apply (line 111-135)

**Create/edit:** `/opt/data/workspace/adk/spikes/live-agent-graph/serve.py`

Add these routes to the existing do_GET and do_POST handlers:

```
GET  /agent-config?agent_id=<id>     → get_config (read-only, no secret required)
POST /agent-config                    → save_config (X-Graph-Secret required)
GET  /agent-tools                     → list_tools (read-only)
GET  /agent-models                    → list_models (may already exist; stub if not)
POST /agent-generate                  → generate (X-Graph-Secret required)
GET  /agent-verify?agent_id=<id>     → verify (read-only)
```

Each must return the EXACT JSON shape from the reconciliation contract Section 4. Use realistic fake data (e.g. for agent-config, return the shelby agent's real fields). NO list_connections (Phase 2). NO real Factory calls (Task 2). Follow serve.py's existing pattern: check secret for mutating routes, _json_response for all responses.

**VERIFY:**
```bash
cd /opt/data/workspace/adk
# Start the server (it binds 127.0.0.1:8888)
# Then curl each route:
curl -s http://127.0.0.1:8888/agent-config?agent_id=shelby | python3 -m json.tool | head -5
curl -s http://127.0.0.1:8888/agent-tools | python3 -m json.tool | head -5
curl -s http://127.0.0.1:8888/agent-verify?agent_id=shelby | python3 -m json.tool | head -5
curl -s http://127.0.0.1:8888/agent-models | python3 -m json.tool | head -5
# POST routes need the secret header — just verify they accept POST and return 401 without secret
curl -s -X POST http://127.0.0.1:8888/agent-config -d 'agent_id=shelby' | python3 -m json.tool | head -3
curl -s -X POST http://127.0.0.1:8888/agent-generate -d 'agent_id=shelby' | python3 -m json.tool | head -3
```
All return valid JSON matching the contracted shape. Cite serve.py line refs you patterned after.

---

## Task 3 — Frappe proxy stubs

**Goal:** Create two new Frappe API files that proxy JSON calls to the box. Stubs with the REAL auth/role/secret structure, placeholder forwarding logic.

**Read first (cite file:line in output):**
- `/opt/data/workspace/forsch_frontiers/docs/specs/factory-reconciliation.md` → Section 4 (the 6 endpoints)
- `/opt/data/workspace/forsch_frontiers/forsch_frontiers/api/cockpit.py` → COPY this pattern: graph_embed() (line 78-137) is the reference for reverse-proxy + X-Graph-Secret attached server-side + Frappe role gating + error handling (502 on box unreachable)
- Frappe @frappe.whitelist — https://docs.frappe.io/framework (whitelisting, frappe.session, frappe.get_roles)

**Create:**

### File 1: `/opt/data/workspace/forsch_frontiers/forsch_frontiers/api/agent_config.py`
```python
"""Frappe-auth'd JSON proxy for agent configuration (box API)."""
# @frappe.whitelist methods: get, save, tools, models
# Pattern: role-check → build request → attach X-Graph-Secret server-side → forward to box → return Response
# Mutating (save) gated to System Manager / FF Ops
# BOX_API_BASE from env, defaults to http://127.0.0.1:8780
# tools param comes as comma-separated string; parse to list before forwarding
# Error handling: box unreachable → 502 (same as cockpit.py line 132-137)
```

### File 2: `/opt/data/workspace/forsch_frontiers/forsch_frontiers/api/agent_factory.py`
```python
"""Frappe-auth'd JSON proxy for agent generation + verification (box API)."""
# @frappe.whitelist methods: generate, status
# Same proxy pattern as agent_config.py
# Both role-gated (System Manager / FF Ops)
```

**Rules:**
- Follow cockpit.py graph_embed() EXACTLY for the proxy pattern (line 78-137)
- Never expose GRAPH_SECRET to the browser — attach server-side only
- BOX_API_BASE defaults to `http://127.0.0.1:8780` (the builder cockpit port)
- Module docstrings cite the reconciliation contract

**VERIFY:**
```bash
cd /opt/data/workspace/forsch_frontiers
python3 -m py_compile forsch_frontiers/api/agent_config.py && echo "agent_config: OK"
python3 -m py_compile forsch_frontiers/api/agent_factory.py && echo "agent_factory: OK"
# Verify the methods are importable
python3 -c "from forsch_frontiers.api.agent_config import get, save, tools, models; print('config imports: OK')"
python3 -c "from forsch_frontiers.api.agent_factory import generate, status; print('factory imports: OK')"
```

---

## Task 5 — Vue Config-tab skeleton

**Goal:** Scaffold the Agent Detail View route + Config tab component in the CRM Vue frontend. Static UI only, no data binding. Tools from the list_tools endpoint (ADK components), NOT agent_tools.yaml.

**Read first (cite file:line in output):**
- `/opt/data/workspace/forsch_frontiers/docs/specs/agent-detail-view.md` → Phase 1 section (lines 11-168), especially "Tab 1: Config" layout and field details
- `/opt/data/workspace/forsch_frontiers/docs/specs/factory-reconciliation.md` → Section 4.1 (get_config response shape — the field list)
- The CRM repo at `forschzachary/crm` → follow its existing Vue component conventions. Cite the component you pattern after.
- ADK GenerateContentConfig — https://google.github.io/adk-docs/ (temperature / max_tokens / top_p). Cite the doc so fields match real ADK params.

**Create:** A Vue route/component for the agent detail view with the Config tab skeleton:

```
Name:           [text input, disabled — read-only identifier]
Model:          [dropdown: gemini-2.5-flash, gpt-5.5, glm-5.2, deepseek-v4-pro, ...]
Temperature:    [range slider 0.0-1.0 with labeled zones:
                  0.0-0.2 "Precise" | 0.3-0.6 "Balanced" | 0.7-1.0 "Creative"]
                Default: 0.3
Max Tokens:     [number input] Default: 500
Top-p:          [number input, under collapsible "Advanced"] Default: 0.95
System Instruction: [textarea, multiline, auto-expanding]
Tools:          [list of chips/badges with names + remove button]
                [+ Add Tool] button (dropdown of available tools)
                Warning at 5: "⚠ 5 of 7 tool slots used"
                Block at 7: "7+ tools degrades reliability. Consider a sub-agent."
Sub-Agents:     [read-only: "none wired"]
Parent:         [read-only text]
Status:         [pill: gray=blank, yellow=building, green=built, red=error]
Buttons: [Save] (disabled when clean)  [⚡ Generate & Verify]  [🗑 Delete] (collapsed)
Breadcrumb: ← Back to Project    Project: {cluster} > agent: {agent_id}
```

**Rules:**
- Phase 1 scope: Config tab ONLY. No chat/evals/connections/animation.
- Tool palette is from the list_tools endpoint (ADK components toolbox) — do NOT use agent_tools.yaml.
- Static/mock data only. Mark `TODO` seams where Task 6 will wire the Frappe proxies.
- Match the existing CRM styling. If the CRM uses a dark theme for the graph sidebar, use that; otherwise follow CRM defaults.
- Temperature slider must show labeled zone markers.

**VERIFY:**
- The route renders in the CRM shell with all fields visible
- No console errors in the browser
- Temperature slider shows labeled zones (Precise/Balanced/Creative)
- Tool list shows placeholder chips (hardcoded: ["check_schedule", "book_event"])
- Status pill renders all 5 states correctly
- "Advanced" section collapses/expands on click
- Take a screenshot and confirm

---

## Rules for all tasks
- Cite file:line references in your output for every claim
- If something is unclear, say "unverified" rather than inventing
- Each task produces independently commitable code
- VERIFY lines are mandatory — run them before declaring done
- Commit each task separately with a descriptive message
