# Agent Detail View — Implementation Roadmap (executor-divided)

> **For agentic workers:** Phase 1 tasks are execution-ready after Task 0 (reconciliation). Each
> task is tagged with its executor and carries a verify line. Steps use `- [ ]` for tracking.
> Bite-sized TDD steps per task are authored by the executor when they pick it up (the exact
> Factory code can't be finalized until Task 0 reveals the existing interfaces).

**Goal:** Make the cockpit/line-graph a visual ADK builder whose Config view generates a *real,
verified* google-ADK package — the "build one real agent" MVP — then layer chat, evals,
connections, animation, and Gradio on top.

**Architecture:** UI native in Frappe/CRM (Vue), agent control plane stays on the box as a JSON
API, Frappe-auth'd proxies bridge them. The Factory (`render_agent_package`) + canvas API +
`agents.yaml` already exist on the box — Phase 1 is mostly **integration + a verify gate**, not
greenfield.

**Tech stack:** google-adk (box), Frappe v16 + Vue (CRM/Railway), Jinja templates (Factory),
LiteLLM (models), Cloudflare tunnel (box JSON API).

---

## Executors (locked)
- **⚡ Cerebras** — Scaffolder. Fast first-draft boilerplate from a precise spec: stubs, skeletons, schemas, test scaffolds.
- **🤖 Hubert (MiMo 2.5)** — Long-horizon builder + box operator. 1M context, agentic tool-calling, lives on the box. Owns reconciliation, the Factory integration + verify loop, and box-side execution/testing.
- **🔵 Claude** — Frappe/CRM front-end (Vue), cross-repo proxy glue, commits/Railway deploys, and reviewer of all output.

## Repos / surfaces touched
- **Box** `/root/.hermes/workspace/adk`: `factory/` (exists), `builder/…/canvas_api.py` (exists, extend), `agent_specs/agents.yaml` (exists, extend schema), NEW verify wrapper, the box JSON API.
- **forsch_frontiers** (Frappe app, Railway): `api/agent_config.py` + `api/agent_factory.py` (NEW proxies), `agent_tools.yaml` (exists), `docs/specs/agent-detail-view.md` (the spec).
- **crm** (Vue): Agent Detail View route + Config tab component.
- **Cloudflare tunnel**: expose the box JSON API (JSON only, Frappe-auth proxied).

## File structure (Phase 1)
| File | Repo | Responsibility | Executor |
|---|---|---|---|
| `agent_specs/agents.yaml` (extend) | box | manifest schema: + temperature, max_tokens, instruction, tools[], per-tool risk | 🤖 |
| `builder/…/canvas_api.py` or `agent_api.py` (new/extend) | box | the 6 JSON endpoints: get/save config, generate, verify-status, list-connections, models | ⚡ scaffold → 🤖 implement |
| Factory verify wrapper | box | render → write package → `adk web` smoke → built/error | 🤖 |
| `api/agent_config.py` | forsch_frontiers | Frappe-auth proxy: get/save config, models, connections | ⚡ scaffold → 🔵 implement |
| `api/agent_factory.py` | forsch_frontiers | Frappe-auth proxy: generate + verify-status (role-gated, X-Graph-Secret server-side) | ⚡ scaffold → 🔵 implement |
| Agent Detail View route + Config tab | crm | the Vue UI: fields, tool palette, Generate&Verify, status, dirty state | ⚡ skeleton → 🔵 implement |

---

## Phase 1 — MVP: Config tab + Generate & Verify (independently shippable)

**Definition of done:** in the live CRM, configure an agent (name/model/temp/max_tokens/instruction/3–5 atomic tools), click **Generate & Verify**, the box renders a real ADK package + smoke-tests it with `adk web`, and the node status flips to **built only after a verified run** (or **error**). No chat/evals/animation.

### Task 0 — Reconciliation (gate) · 🤖 Hubert (MiMo 2.5)
**Files:** read `factory/src/forsch/adk_factory/renderer.py`, `…/cli.py`, `…/models.py`, `builder/src/forsch/adk_builder/canvas_api.py`, `agent_specs/agents.yaml`, `docs/AGENT_FACTORY_SPEC.md`. Write `docs/specs/factory-reconciliation.md`.
- [ ] Map what `render_agent_package(spec)` accepts (AgentSpec fields) and emits (paths/contents).
- [ ] Map what `canvas_api.py` already exposes (routes, payloads) vs the 6 endpoints we need.
- [ ] Determine whether any verify/smoke step exists today; if not, note where it slots.
- [ ] Produce the **box JSON API contract** (exact request/response for the 6 endpoints) + a gap list (what's missing for Phase 1).
**Verify:** `factory-reconciliation.md` committed; 🔵 Claude reviews it before any Factory task starts. **This unblocks Tasks 1, 2, 4.**

### Task 1 — Scaffold the box JSON API · ⚡ Cerebras (then 🤖 owns)
**Files:** `builder/…/canvas_api.py` (extend) or new `agent_api.py`.
- [ ] From Task 0's contract, scaffold the 6 endpoint handlers as typed stubs returning shaped fake JSON (get_config, save_config, generate, verify_status, list_connections, list_models).
**Verify:** `curl` each stub returns the contracted JSON shape.

### Task 2 — Generate & Verify backbone · 🤖 Hubert (MiMo 2.5)
**Files:** the verify wrapper + `generate`/`verify_status` handlers from Task 1; `agents.yaml` writes.
- [ ] save_config writes the agent's entry into `agents.yaml` (extended schema).
- [ ] generate runs `render_agent_package(spec)` → writes `web_agents/<id>/` package.
- [ ] verify runs an `adk web` smoke (boot the package, confirm it loads + the agent responds to a trivial turn); capture pass/fail + logs.
- [ ] status flips to **built** only on smoke-pass; **error** (with the log) on fail. (Phantom-fix gate.)
**Verify:** generate the existing `shelby` agent end-to-end on the box → smoke passes → status=built; break the instruction → status=error with a real log line.

### Task 3 — Scaffold Frappe proxies · ⚡ Cerebras (then 🔵 owns)
**Files:** `forsch_frontiers/api/agent_config.py`, `forsch_frontiers/api/agent_factory.py`.
- [ ] Scaffold 6 `@frappe.whitelist` methods mirroring the box endpoints; mutating ones role-gated (FF Ops / System Manager); attach `X-Graph-Secret` server-side; call the box JSON API base.
**Verify:** `python -m py_compile` both; methods import in a Frappe console.

### Task 4 — Implement Frappe proxies · 🔵 Claude
**Files:** same as Task 3.
- [ ] Real HTTP to the box JSON API; Frappe session auth → role map → secret; error handling (box down, 4xx/5xx surfaced cleanly).
**Verify:** from the CRM, a logged-in FF-Ops user round-trips get/save/generate to the box; a non-privileged user is 403'd on generate; secret never appears in browser traffic.

### Task 5 — Scaffold the Config tab · ⚡ Cerebras (then 🔵 owns)
**Files:** `crm` — Agent Detail View route + Config tab component skeleton.
- [ ] Fields: name, model dropdown, temperature slider (labeled zones), max_tokens, instruction textarea, tools list + "Add Tool", status pill, Generate&Verify button, Save.
**Verify:** route renders in the CRM shell with the static skeleton, no console errors.

### Task 6 — Implement the Config tab · 🔵 Claude
**Files:** same as Task 5; reads `forsch_frontiers/agent_tools.yaml`.
- [ ] Bind fields to the Frappe proxies (load/save config). Tool palette sourced from `agent_tools.yaml` with the soft-cap-5/hard-cap-7 warning. Dirty-state dot. Generate&Verify calls the proxy, streams/polls status, renders built/error with the log.
**Verify:** e2e in the live CRM — configure `shelby` → Generate&Verify → status flips to **built** (backed by the real box smoke), tools capped, dirty state correct.

### Task 7 — MVP end-to-end verification · 🔵 Claude + 🤖 Hubert · **★ MVP MILESTONE — shippable**
- [ ] Full loop in the live CRM: configure → Generate&Verify → built, with box-side evidence (the `adk web` smoke log) and a UI screenshot. Confirm error path too.
**Verify:** documented evidence (UI + box log) that a real, verified ADK package was produced from the cockpit. Ship/announce here.

---

## Phase 2 — Chat · Connections · Evals · live status (mapped)
**Objective:** make the agent usable + governed from its detail view.
- **Chat tab** 🤖(box chat proxy: isolated conversation with the agent, tool calls inline, "Save to Evalset") + 🔵(Vue).
- **Connections tab** 🤖(sub_agents wiring writes to `agents.yaml` → regenerate) + 🔵(Vue).
- **Evals tab** 🤖(`adk eval` on the box, JSON run+stream endpoint, trajectory+response scores, diff) + 🔵(Vue list/diff). *Open Q resolved: evals run `adk eval` on the box, never the browser.*
- **Live status promotion** 🤖 (what makes an agent "live" = deployed to a surface; define + wire).
Each sub-tab gets its own bite-sized plan when Phase 1 lands.

## Phase 3 — Canvas zoom + sub-graph + shortcuts + mobile (mapped) · 🔵 Claude
**Objective:** the 600ms zoom transition, depth-1 local sub-graph, keyboard shortcuts, mobile fallback. Pure front-end polish; depends on Phase 1+2 data being real. Depth strictly **depth-1** (per review).

## Phase 4 — Gradio surface · HITL approval · production eval flywheel (mapped)
**Objective:** one-click Gradio surface for a built agent (+ Discord-from-Gradio path) 🤖+🔵; HITL approve/reject UI driven by the per-tool risk flags already stored 🔵; production eval flywheel (extract real failures → regression evals) 🤖. Gradio is first-class here per the canonical wiki.

---

## Sequencing & dependencies
```
Task 0 (recon, 🤖) ──unblocks──▶ Task 1 (⚡) ──▶ Task 2 (🤖) ─┐
                    └──────────▶ Task 3 (⚡) ──▶ Task 4 (🔵) ─┤
                                  Task 5 (⚡) ──▶ Task 6 (🔵) ─┴──▶ Task 7 (★ MVP)
                                                          then ▶ Phase 2 → 3 → 4
```
- Cerebras scaffolds (1,3,5) can run **in parallel** right after Task 0.
- Box backbone (2) and Frappe proxies (4) can proceed in parallel once their scaffolds land.
- Config tab (6) integrates last; Task 7 proves the loop.

## Open items to confirm during Task 0
- Exact `AgentSpec` schema vs our Config fields (any gaps to add to `agents.yaml`).
- Whether `canvas_api.py` is the right host for the 6 endpoints or a new `agent_api.py`.
- How the box JSON API is exposed (reuse the Cloudflare tunnel, JSON-only).
