# Agent Detail View — Dispatch Prompts (Phase 1)

Self-contained prompts for each executor. Every prompt references the canonical docs and
requires cited, evidence-based output. **Sequencing:** Task 0 (✅ done) → Cerebras scaffolds
(Tasks 1, 3, 5 — parallel) → Hubert backbone (Task 2) → Claude implements (Tasks 4, 6) → Task 7.

**Canonical references (read in every task):**
- Contract + gaps: `forsch_frontiers/docs/specs/factory-reconciliation.md` ← source of truth
- Roadmap: `forsch_frontiers/docs/plans/2026-06-25-agent-detail-view-implementation.md`
- Spec: `forsch_frontiers/docs/specs/agent-detail-view.md`
- ADK: https://google.github.io/adk-docs/ · Frappe: https://docs.frappe.io/framework

**Phase-1 endpoint set (6, locked):** `get_config`, `save_config`, `list_tools`, `list_models`,
`generate`, `verify`. (`list_connections` is Phase 2.) **Tools come from the ADK components
toolbox (`_toolbox`/`list_tools`), NOT `agent_tools.yaml` (Phase 2).**

---

## Task 0 — Reconciliation · 🤖 Hubert ✅ COMPLETE
Output: `docs/specs/factory-reconciliation.md` (verified against box code 2026-06-25). Findings:
Factory does ~80%; `save_config`/`generate` wrap existing fns; net-new = G1 config reader, G3
`verify_agent`, G7 status. Box host = `serve.py`. Tools = ADK components toolbox.

---

## Task 1 — Box JSON API stubs · ⚡ Cerebras
```
Scaffold the box JSON API for the cockpit ADK-builder — typed stubs returning shaped fake JSON,
no real logic yet.

READ FIRST:
- forsch_frontiers/docs/specs/factory-reconciliation.md → §4 "Box JSON API Contract" (authoritative)
- box: spikes/live-agent-graph/serve.py → follow its existing authenticated-handler style
  (do_GET/do_POST, the X-Graph-Secret check, JSON responses)

TASK: add 4 new routes to serve.py implementing the 6 Phase-1 endpoints as stubs returning the
contracted JSON shapes with realistic fake data:
  GET  /agent-config?agent_id=   → get_config
  POST /agent-config             → save_config
  GET  /agent-tools              → list_tools
  GET  /agent-models             → list_models   (may already exist via build_view; stub if not)
  POST /agent-generate           → generate
  GET  /agent-verify?agent_id=   → verify
Match the contract field-for-field. NO list_connections (Phase 2). NO real Factory calls yet
(Task 2). Mutating routes (/agent-config POST, /agent-generate) require X-Graph-Secret like the
existing mutating handlers; read-only ones follow the existing CORS-pinned pattern.

VERIFY: `curl` each route returns the contracted shape. Cite serve.py line refs you patterned after.
```

---

## Task 2 — Generate & Verify backbone · 🤖 Hubert (MiMo 2.5)
```
Implement the real logic behind the Task-1 stubs. The reconciliation proved most of this WRAPS
existing functions — wrap, don't rebuild.

READ FIRST (cite file:line):
- forsch_frontiers/docs/specs/factory-reconciliation.md → §2, §3 (what exists), the gap list
- box: builder/src/forsch/adk_builder/editor.py:32 (update_agent), canvas_api.py (_toolbox/build_view)
- box: factory/src/forsch/adk_factory/cli.py:111 (apply), validation.py (validate_agent_tools)
- ADK Runner / adk web — https://google.github.io/adk-docs/ (cite for the smoke turn)

TASK:
- save_config  → wrap editor.update_agent() (already writes agents.yaml + regenerates both files).
- generate     → wrap cli.apply() (already validates + deploy-gates + writes the 2 files).
- get_config   → G1: NEW config reader. build_view strips package/safety_level/purpose/smoke_prompts
                 — read the full agent block straight from agent_specs/agents.yaml (ruamel).
- list_tools   → return the ADK components toolbox via canvas_api._toolbox() (real importable fns).
- verify_agent → G3: NEW (new factory/.../smoke.py or extend validation.py). Subprocess import
                 check: `python -c "from forsch.agent_<id>.agent import root_agent; print(root_agent.name)"`.
                 Then a best-effort smoke_prompts turn via the ADK Runner IF creds/proxy present
                 (graceful skip otherwise). Must be subprocess, NOT in-process.
- status (G7)  → derive: blank (no package) / built (package exists AND verify passed) /
                 error (verify failed; keep the log). Status flips to built ONLY on a passing
                 verify — NEVER on save. This is the phantom-fix gate.

VERIFY (new evidence, not assertions): generate the existing `shelby` agent end-to-end →
import-check passes → status=built, with the captured log line. Then break its instruction or a
tool name → status=error with the real failure log. Paste both logs in your report.
```

---

## Task 3 — Frappe proxy stubs · ⚡ Cerebras
```
Scaffold the Frappe-side proxies bridging the CRM to the box JSON API. Stubs with the REAL
auth/role/secret structure (copy the existing pattern), placeholder data otherwise.

READ FIRST:
- forsch_frontiers/docs/specs/factory-reconciliation.md → the 6-endpoint contract
- forsch_frontiers/api/cockpit.py → COPY this: reverse-proxy + X-Graph-Secret attached
  server-side + Frappe role gating (graph_embed is the reference)
- Frappe @frappe.whitelist — https://docs.frappe.io/framework (whitelisting, frappe.session, frappe.get_roles)

TASK: create
- forsch_frontiers/api/agent_config.py  → @frappe.whitelist methods: get_config, save_config,
  list_tools, list_models
- forsch_frontiers/api/agent_factory.py → @frappe.whitelist methods: generate, verify
Mutating ones (save_config, generate) role-gated (System Manager / FF Ops), attaching
X-Graph-Secret server-side, calling the box JSON API base from env (GRAPH_BASE-style). Module
docstrings cite the contract + cockpit.py. NO list_connections (Phase 2).

VERIFY: `python -m py_compile` both; the @whitelist methods import. No logic beyond the proxy
skeleton (Claude implements in Task 4).
```

---

## Task 5 — Vue Config-tab skeleton · ⚡ Cerebras  *(CORRECTED: tools from list_tools, not agent_tools.yaml)*
```
Scaffold the Agent Detail View route + Config tab skeleton in the CRM Vue frontend (static UI,
no data binding yet).

READ FIRST:
- forsch_frontiers/docs/specs/agent-detail-view.md → "Tab 1: Config" (fields/layout) + Phase-1
  scope (Config tab ONLY — no chat/evals/connections/animation)
- crm (forschzachary/crm) → follow its existing Vue component + routing conventions; cite the
  example component you patterned after
- ADK GenerateContentConfig — https://google.github.io/adk-docs/ (temperature / max_tokens / top_p);
  cite the doc so the fields match real ADK params

TASK: a route component for the agent detail view with the Config tab skeleton:
  name, model dropdown, temperature slider (zones Precise/Balanced/Creative), max_tokens,
  system instruction textarea, tools list + "Add Tool", status pill, "Generate & Verify" button, Save.
The tool palette is sourced from the `list_tools` endpoint (the ADK components toolbox) — DO NOT
use agent_tools.yaml (that's a Phase-2 enrichment). Static/mock data only; mark TODO seams where
Task 6 wires the Frappe proxies.

VERIFY: the route renders in the CRM shell, no console errors. Scope = Config tab ONLY.
```

---

## Claude (🔵) — Tasks 4, 6, 7
- **Task 4:** implement the Frappe proxies (real HTTP to the box, Frappe session→role→secret, error handling).
- **Task 6:** implement the Config tab (bind to proxies, `list_tools` palette + 5/7 count cap, dirty state, Generate&Verify → poll `verify` → render built/error).
- **Task 7:** e2e verification in the live CRM (configure → Generate&Verify → built, with box log + screenshot). ★ MVP milestone.
