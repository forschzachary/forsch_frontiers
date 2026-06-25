# Agent Graph → Native Frappe Rebuild — Scoping & Split Plan

**Status:** SCOPING (Part 1 of 2 — "take stock + split the current system")
**Date:** 2026-06-25
**Authors:** Zach + Claude (Opus 4.8). Hubert to contribute (Part 2 brainstorm).
**Repos in scope:** `forschzachary/live-agent-graph` (current server), `forschzachary/forsch_frontiers` (CRM app / target), `forschzachary/crm` (CRM Vue frontend), `forschzachary/frappe-crm-deploy` (Railway build).

> Part 2 (missing features / Google ADK direction) is a separate brainstorm with
> Zach + Hubert + Claude — placeholder at the bottom. This doc is **only** the
> take-stock + how-to-split-what-exists.

---

## 0. Why we're doing this

The agent graph today is an **external custom server stitched into Frappe through an
iframe + an HTML proxy + a public CDN.** Nearly every failure on 2026-06-24/25 traced to
that stack:
- force-graph loaded from `unpkg.com` → unreachable from the Browserbase browser (canvas stuck "Loading…").
- The `graph_embed` HTML-rewrite fix only helps if the iframe routes through it — the iframe is a runtime Frappe Custom HTML Block whose `src` may point straight at the tunnel, bypassing the rewrite.
- Two auth systems, a Cloudflare tunnel, a separate deploy, SameSite/CSP iframe friction.

Going native to Frappe deletes most of those moving parts. **But** the graph's backend
spawns/controls real agents that live **on the box**, so the split has a hard boundary.

---

## 1. Take stock — what we have now

### 1.1 Topology
```
Browser (CRM, Railway)
  └─ Agent Builder page  ── iframe ──▶ graph.forschfrontiers.com  (Cloudflare tunnel)
       (Frappe Custom HTML Block)            │
  └─ forsch_frontiers/api/cockpit.py         ▼
       graph_embed()  ── reverse-proxy ──▶  box: serve.py @127.0.0.1:8888
       (adds X-Graph-Secret, rewrites CDN)        │  (live-agent-graph)
                                                  ├─ reads box files (registry, clusters, graph json)
                                                  ├─ spawns/promotes agents on the box
                                                  ├─ _crm_post/_crm_get → CRM whitelisted API (admin key)
                                                  └─ /chat → Hubert (LLM)
```

### 1.2 Components
| Component | Where | Role |
|---|---|---|
| `serve.py` (~34KB) | box (live-agent-graph) | HTTP server: serves UI **and** the agent control API |
| `index.html` (~50KB) | box | the graph UI (force-graph canvas), loads CDN JS |
| `build_live_graph.py`, `spawn_agent.py`, `promote_agent.py` | box | graph generation + agent lifecycle |
| `forsch_frontiers/api/cockpit.py` → `graph_embed()` | CRM (Railway) | reverse-proxy: Frappe auth → box, + CDN rewrite (the stopgap) |
| `forsch_frontiers/permissions.py` | CRM | redirects to login so the iframe always has a session cookie |
| Cloudflare tunnel | box → `graph.forschfrontiers.com` | exposes the box server |
| Agent Builder page | CRM (runtime Custom HTML Block) | hosts the iframe |

### 1.3 API surface (serve.py)
**Read-only** (unauthenticated, CORS pinned to the CRM origin):
`/pulse` · `/clusters` · `/manifest` · `/models` (GET)

**Mutating** (require `X-Graph-Secret`, no CORS):
`/spawn` · `/wire` · `/save-agent` · `/promote` · `/new-cluster` · `/add-agent` · `/chat` · `/models` (POST)

`/chat` additionally enforces session ownership, rate-limits per principal, and audit-logs.

### 1.4 Data (authoritative on the box, file-based)
- `agent-graph-v2.json` — the rendered graph
- `registry/agents/agents.yaml` — agent registry
- `clusters/<name>/cluster.yaml` — cluster definitions
- `capabilities.json`, `.roundtrip_cache.json`
- `build_live_graph.py` regenerates `agent-graph-v2.json`

### 1.5 Integrations
- **CRM:** `_crm_post`/`_crm_get` call CRM whitelisted methods with an admin API key (box → CRM already exists).
- **authsome:** health probe at `127.0.0.1:7998`.
- **Hubert/LLM:** `/chat` proxies a model for graph-aware Q&A.

### 1.6 Auth model
- Mutating ops gated by `X-Graph-Secret` (box env / `$HERMES_HOME/graph-server-secret`).
- `graph_embed` maps Frappe roles → secret (FF Ops / System Manager required for mutating).
- Read-only open (CORS-pinned). The secret never reaches the browser.

### 1.7 Observed failure modes (the motivation)
1. CDN (`unpkg`) unreachable from some browsers → canvas dead.
2. HTML-proxy rewrite only works if the iframe uses `graph_embed` (it may not).
3. iframe cross-site cookie/CSP friction.
4. Two deploys (Railway CRM + box server) + a tunnel to keep in sync.

---

## 2. Target architecture — the split

**Principle:** the **UI becomes native Frappe**; the **agent control plane stays on the
box** (it must — it spawns/reads/writes the box's agent runtime + files); the box↔Railway
boundary **shrinks from "iframe a whole web app" to "fetch JSON."**

```
Browser (CRM, Railway)
  └─ Agent Builder = native CRM Vue route
       ├─ force-graph bundled as a CRM/app asset (NO CDN, NO iframe)
       └─ calls Frappe @whitelist methods  ───────────────┐
                                                           ▼
  forsch_frontiers/api/agent_graph.py  (Frappe-auth + roles)
       └─ thin JSON proxy ──▶ box: graph API (serve.py, JSON-only)
                                   (X-Graph-Secret server-side; same endpoints, no HTML)
```

### 2.1 What's deleted
- `index.html` (→ Vue route), all HTML-serving in `serve.py`.
- CDN dependency + the `graph_embed` CDN-rewrite stopgap.
- The iframe + the Custom HTML Block + `permissions.py` login-cookie hack.
- The tunnel **as a UI host** (may remain only as the JSON API path, or be replaced by a private link).

### 2.2 What stays (box-side, inherent)
- Agent lifecycle: spawn/wire/promote/new-cluster/add-agent (they touch the box's agent runtime + files).
- The file-based source of truth (registry/clusters/graph json) + `build_live_graph.py`.
- `/chat`.
- `X-Graph-Secret` — but now **only** between Frappe (server) and the box; never near a browser.

### 2.3 What's new
- A CRM Vue route (canvas) — ports `index.html`'s render + interactions.
- `forsch_frontiers/api/agent_graph.py` — whitelisted **data** methods (one per box endpoint), Frappe-auth + role-gated, returning JSON (replaces `graph_embed`'s HTML proxy).
- force-graph vendored as an app asset (Frappe build pipeline).

---

## 3. Port matrix

| Current (box `serve.py` / `index.html`) | Destination | Notes |
|---|---|---|
| `index.html` canvas + interactions | CRM Vue route (`crm` frontend) | rewrite in Vue; reuse force-graph data shape |
| force-graph CDN `<script>` | bundled app asset | kills the CDN class of bug entirely |
| `/pulse`, `/clusters`, `/manifest`, `/models` (read) | box JSON API → Frappe `@whitelist` GET proxies | Frappe session auth replaces CORS-open |
| `/spawn`, `/wire`, `/promote`, `/new-cluster`, `/add-agent`, `/save-agent` (mutating) | **stay on box**; Frappe `@whitelist` POST proxies (role-gated) | box owns agent runtime + files |
| `/chat` | stay on box; Frappe proxy | keep session-ownership + rate-limit + audit |
| `graph_embed()` HTML proxy + CDN rewrite | **delete**; replace with JSON proxies | |
| `permissions.py` iframe-cookie hook | **delete** (no iframe) | |
| registry/clusters/graph files | stay box-authoritative (Phase 5: optional DocType mirror) | |

---

## 4. Implementation plan (split CURRENT → native; phased, each with a verify line)

**Phase 0 — Stopgap to unblock the live E2E (optional, ~10 min).**
Self-host force-graph in `live-agent-graph` (vendor `force-graph.min.js`, point `index.html` at the local path) + redeploy the box graph server. *Verify:* canvas renders via the existing iframe with no external CDN call. *(This is throwaway once Phase 2 lands — only do it if the E2E can't wait.)*

**Phase 1 — Box: make `serve.py` a pure JSON API.**
Split UI from data. Keep all endpoints, drop HTML serving (or leave it dormant for rollback). Confirm every endpoint returns clean JSON + documents its schema. *Verify:* `curl` each endpoint (with secret for mutating) returns JSON; no HTML path needed by any consumer.

**Phase 2 — CRM: native graph route.**
Bundle force-graph as an app asset. Build the Vue route that renders the graph from the JSON API (port `index.html`'s canvas + interactions). *Verify:* the route renders the live graph in the CRM shell, no iframe, no CDN, Lighthouse/Network shows zero third-party JS.

**Phase 3 — Frappe: whitelisted JSON proxies.**
`forsch_frontiers/api/agent_graph.py` — one `@frappe.whitelist` method per box endpoint, Frappe-auth + role-gated (FF Ops / System Manager for mutating), attaching `X-Graph-Secret` server-side. *Verify:* the Vue route drives spawn/wire/promote end-to-end through Frappe auth; secret never in browser traffic.

**Phase 4 — Cutover + retire.**
Point the Agent Builder nav at the new Vue route. Delete the Custom HTML Block, `graph_embed` HTML proxy + CDN rewrite, `permissions.py` hook. Reduce the tunnel to the JSON API only (or a private link). *Verify:* old iframe path 404/removed; full E2E (design agent → spawn → materialize) green through the native route.

**Phase 5 — (Optional) Data into DocTypes.**
If we want native querying/permissions/reporting over agents/clusters, mirror registry/clusters into DocTypes (box files stay the build source, sync one-way). *Verify:* list/filter agents in Frappe; graph builds from DocTypes or files interchangeably.

---

## 5. Open decisions (resolve before/while building)
1. **Box JSON API exposure:** keep the Cloudflare tunnel (JSON-only) vs a private Railway↔box link vs Tailscale. (Today's tunnel works; least-change = keep it JSON-only.)
2. **Graph data home:** stay box-file-authoritative (simplest) vs mirror to Frappe DocTypes (Phase 5) for native query/permission/report.
3. **Does the agent runtime ever move to Railway?** If yes, the box backend could eventually collapse too — but that's a much larger shift (out of scope here).
4. **Vue route home:** in `forschzachary/crm` (fork) vs a `forsch_frontiers` page. Fork = native CRM nav; app page = decoupled from CRM upstream.
5. **Effort:** Phases 1–4 are a multi-day rewrite (50KB UI + proxy layer), not a patch. Sequence so the E2E stays demoable (Phase 0 stopgap covers the gap).

---

## 6. PART 2 (separate brainstorm — TBD with Zach + Hubert + Claude)
**Missing features / Google ADK direction.** Zach has been studying Google ADK; this section
captures the feature gaps + where ADK patterns (agents-as-config, tools, sessions, eval,
materialization) should shape the native rebuild. **Not yet filled** — to be brainstormed
together. Capture here so the rebuild is designed *for* the target feature set, not just a
1:1 port.

---

## 7. References
- Current server: `live-agent-graph/serve.py`, `index.html`, `build_live_graph.py`, `spawn_agent.py`, `promote_agent.py`
- Proxy + auth: `forsch_frontiers/api/cockpit.py` (`graph_embed`), `forsch_frontiers/permissions.py`
- The 2026-06-24/25 incident that motivated this: CDN-unreachable + iframe-bypass (see commit `192e16b` graph_embed rewrite + Railway deploy `323326b6`).
