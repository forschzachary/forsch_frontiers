# Agent Detail View — Spec

## Current State

This is the **full vision** spec. Phase 1 (the MVP) is carved out below. Later phases are explicitly labeled.

The graph lives at `forsch_frontiers/forsch_frontiers/public/graph/index.html`, served through the `graph_embed` proxy in `cockpit.py`. Agent state will live as YAML files on the cloud box, accessed through a Frappe-auth'd JSON API.

---

# Phase 1 — MVP: Config + Generate + Verify

**Goal:** From the cockpit graph, configure an agent, generate a real google-adk package, and verify it runs.

## 1.1 Entry Point: Zoom Transition (Phase 1 = minimal)

In Phase 1, the transition is **functional, not animated**:

- Double-click a node OR click "Configure" from the inspect panel
- The right sidebar swaps from project-level controls to the agent Config tab
- The graph stays visible (no zoom animation yet — that's Phase 3)
- A breadcrumb appears: `Project: demo > agent: calendar_specialist`
- "Back to Project" link returns to project-level sidebar

The full canvas zoom animation (camera pan, node expand, sibling fade, local sub-graph) is **Phase 3**.

## 1.2 Config Tab (the core of Phase 1)

The only tab in Phase 1. Full-screen or right-panel, whichever fits the current layout.

```
+------------------------------------------------------------------+
| ← Back to Project    Project: demo > calendar_specialist         |
+------------------------------------------------------------------+
|                                                                    |
|  Name:           calendar_specialist                              |
|  Model:          [gemini-2.5-flash ▾]                             |
|  Temperature:    [====●=====] 0.3                                |
|  Max Tokens:     [500]                                            |
|  Top-p:          [0.95]  (advanced, collapsed by default)        |
|                                                                    |
|  System Instruction:                                               |
|  ┌─────────────────────────────────────────────────────┐          |
|  │ You manage the family calendar. You are strictly    │          |
|  │ logical. Always confirm before booking.             │          |
|  │                                                     │          |
|  └─────────────────────────────────────────────────────┘          |
|                                                                    |
|  Tools:                                                            |
|  ┌─────────────────────────────────────────────────────┐          |
|  │ ✓ check_schedule  (check calendar for events)       │          |
|  │ ✓ book_event      (create calendar event)           │          |
|  │ [+ Add Tool]                                        │          |
|  │                                                     │          |
|  │ ⚠ 5 of 7 tool slots used (soft cap)                │          |
|  └─────────────────────────────────────────────────────┘          |
|                                                                    |
|  Sub-Agents:    (none wired)                                      |
|  Parent:        primary_assistant                                  |
|                                                                    |
|  Status:  ◎ built                                                 |
|                                                                    |
|  [💾 Save]  [⚡ Generate & Verify]  [🗑 Delete Agent]            |
|                                                                    |
+------------------------------------------------------------------+
```

### Field Details

| Field | Type | Notes |
|-------|------|-------|
| Name | text | unique within cluster, lowercase + underscores |
| Model | dropdown | populated from LiteLLM `/models` endpoint |
| Temperature | slider 0.0-1.0 | labeled zones: Precise (0-0.2), Balanced (0.3-0.6), Creative (0.7-1.0) |
| Max Tokens | number | default 500 |
| Top-p | number | collapsed under "Advanced", default 0.95 |
| System Instruction | textarea | multiline, auto-expanding |
| Tools | checklist + add | see Tool Library below |
| Sub-Agents | list | read-only in Phase 1, editable in Phase 2 |
| Parent | read-only | shows who delegates to this agent |

### Tool Library

When clicking "+ Add Tool", a dropdown/search appears listing available tools from a curated library. Each tool has:

```yaml
- name: check_schedule
  description: "Check calendar for events on a specific date"
  parameters:
    date: { type: string, required: true, description: "YYYY-MM-DD" }
  source: google_calendar  # which API/integration
  risk_level: low           # low = no approval needed
```

**Tool library lives in:** `forsch_frontiers/forsch_frontiers/api/agent_tools.yaml` on the repo. A flat YAML list of available atomic tools with descriptions, parameter schemas, source integrations, and risk levels.

**Soft cap:** warning at 5 tools, hard cap at 7. If someone tries to add an 8th, show: "7+ tools degrades reliability. Consider splitting into a sub-agent."

**Risk levels:** each tool has a `risk_level` field: `low`, `medium`, `high`. High-risk tools will require approval (HITL) — the flag is stored now even though the approval UI is Phase 2.

### Save vs Generate & Verify

Two distinct actions:

**Save** — writes the agent config to the YAML registry on the box. Does NOT generate a runnable package. Status stays at current state.

**Generate & Verify** — the real MVP action:
1. Writes the agent config to `agents.yaml` on the box
2. Triggers the Factory to generate a google-adk package (`root_agent.py` + `agents.yaml`)
3. Runs a smoke test: `adk web ./package_dir` starts, responds to one test message, exits clean
4. If smoke passes → status flips to **built** (green arc)
5. If smoke fails → status flips to **error** (red cross), error details shown in a collapsible panel

Status meanings:

| Status | Meaning |
|--------|---------|
| blank | newly spawned, no config saved yet |
| building | Generate & Verify is running |
| built | package generated and smoke-tested successfully |
| live | deployed to a surface (Gradio, Discord, etc.) — Phase 2 |
| error | last generate or eval failed |

**"built" is NOT achieved by Save alone.** This is the critical distinction.

## 1.3 Backend Contract (Phase 1)

The cockpit UI is a Frappe web page. The agent runtime lives on the cloud box. All communication goes through Frappe-auth'd proxy endpoints.

### Endpoints

| Action | Method | Frappe Endpoint | Box Target | Notes |
|--------|--------|----------------|------------|-------|
| Get agent config | GET | `forsch_frontiers.api.agent_config.get` | `agents/{id}/config.yaml` | Returns YAML as JSON |
| Save agent config | POST | `forsch_frontiers.api.agent_config.save` | writes `agents/{id}/config.yaml` | Validates schema before write |
| List available tools | GET | `forsch_frontiers.api.agent_tools.list` | `agent_tools.yaml` | Static library, cacheable |
| Generate & Verify | POST | `forsch_frontiers.api.agent_factory.generate` | triggers Factory on box | Async: returns job_id, polls for status |
| Check generate status | GET | `forsch_frontiers.api.agent_factory.status?job_id=X` | box job queue | Returns running/built/error + details |
| List agents in cluster | GET | `forsch_frontiers.api.agent_config.list?cluster=X` | `clusters/{name}/agents.yaml` | For graph rendering |

### Auth

All endpoints require logged-in Frappe user with System Manager or FF Ops role (same as `graph_embed`). The proxy attaches `X-Graph-Secret` server-side — token never reaches the browser.

### Data Flow

```
Browser (cockpit)
  → POST /api/method/forsch_frontiers.api.agent_factory.generate
    → Frappe checks auth + role
      → Box: reads config YAML, runs Factory, runs smoke test
        → Returns { status: "built", package_path: "..." }
  ← Browser updates node status ring
```

### Error Handling

- **Generate timeout** (>60s): return error with "generation took too long, check box logs"
- **Smoke test failure**: return the exact error output from `adk web` startup or test message
- **Box unreachable**: return 502 with error message (same pattern as `graph_embed`)

## 1.4 Commit to Git

The spec lives in the `forsch_frontiers` repo:
- `docs/specs/agent-detail-view.md` — this file
- `forsch_frontiers/api/agent_tools.yaml` — tool library
- `forsch_frontiers/api/agent_config.py` — config API endpoints
- `forsch_frontiers/api/agent_factory.py` — generate + verify endpoints

---

# Phase 2 — Chat + Connections + Eval Flywheel

**Goal:** Test agents directly, wire sub-agents, capture golden traces.

## 2.1 Chat Tab

Direct conversation with a specific agent in isolation. Bypasses the concierge.

- Tool calls visible inline with arguments and response
- "Save to Evalset" button captures conversation as a golden trace
- Model/temperature override dropdown for temporary testing (resets on reload)
- Streaming responses (SSE or WebSocket)

## 2.2 Connections Tab

- List of sub-agents (delegates to) and parents (delegated by)
- "+ Wire New Sub-Agent" opens wire panel
- Shared resource detection (same tool used by multiple agents)
- Clicking any listed agent transitions to its detail view

## 2.3 Evals Tab

- Eval set list with pass/fail history and scores
- "Run All Evals" triggers `adk eval` on the box
- Click into an eval to see expected vs actual trajectory diff
- "Add from Chat" captures current conversation as a new eval case
- Failure details highlight which step was skipped or hallucinated

## 2.4 Live Status Promotion

- "built" → "live" requires an explicit deploy action
- Deploy surfaces: Gradio chat, Discord bot, API endpoint
- Deploy action shows available surfaces, user picks one
- Status ring pulses green when live

---

# Phase 3 — Canvas Zoom Animation + Polish

**Goal:** The smooth, natural transition described in the original spec.

## 3.1 Full Canvas Zoom

The 3-phase animation (~600ms):
- Phase 1 (0-200ms): camera pans, siblings fade
- Phase 2 (200-450ms): node expands, sub-graph fans out
- Phase 3 (450-600ms): panel slides in, breadcrumb appears

Spring physics on node scale. cubic-bezier(0.4, 0, 0.2, 1) on all transitions.

## 3.2 Local Sub-Graph

When zoomed in, the graph shows ONLY this agent's depth-1 connections:
- Center node at 1.5x size with expanded status ring
- Parents to the left, children to the right
- Shared resources as small dots below
- Clicking a connected node flies to its detail view

## 3.3 Keyboard Shortcuts

| Action | Trigger |
|--------|---------|
| Zoom into agent | Double-click node or Enter |
| Back to project | Escape |
| Next connected agent | Tab |
| Previous connected agent | Shift+Tab |
| Save config | Ctrl+S |

## 3.4 Mobile / Narrow Viewport (< 1024px)

- Sub-graph becomes vertical list above control panel
- Tabs collapse into bottom sheet
- Double-click becomes long-press
- Escape becomes back-swipe

---

# Phase 4 — Gradio Surface + HITL

**Goal:** Gradio as first-class user-facing surface, human-in-the-loop approval.

## 4.1 Gradio Integration

- "Fullscreen Chat" button launches a Gradio chat instance for the zoomed agent
- Gradio app mounted on the box, served through Tailscale Funnel or CF tunnel
- Each agent gets its own Gradio endpoint: `/chat/{agent_id}`
- Gradio handles auth (Frappe session cookie or separate)

## 4.2 HITL Approval

- High-risk tools (from `risk_level` in tool library) trigger approval flow
- When agent tries to use a high-risk tool, execution pauses
- Approval notification surfaces in the cockpit and/or Gradio chat
- User approves/rejects, execution resumes or agent gets cancellation message

## 4.3 Eval Flywheel in Production

- Monitor live conversations for failures
- Extract failed prompts as regression evals
- One-click "Create Eval from Failure" in the Evals tab
- Evalset grows organically from real edge cases

---

# Decisions (from review)

1. **Depth:** strictly depth-1 in the detail sub-graph. Optional "expand neighbor" later.
2. **Chat persistence:** per-agent within session. Durable DB is later.
3. **Eval running:** `adk eval` on the box, never browser/Railway. Box exposes JSON endpoint, cockpit calls through Frappe proxy.
4. **Gradio:** stubbed button in Phase 2, full integration in Phase 4.
5. **"built" vs "live":** built = generate + smoke verify. live = deployed to a surface. Explicit deploy action required.
