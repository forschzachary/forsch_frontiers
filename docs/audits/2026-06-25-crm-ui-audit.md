# CRM UI Audit & Navigation Architecture — June 25, 2026

**Performed by:** Hubert (browser E2E traversal)
**Status:** Audit complete. Architecture recommendations below.
**For:** Zach + another agent to review and implement.

---

## Part 1: Full UI Audit

Every button in the CRM sidebar and cockpit was clicked by a real browser session logged in as Zach. Here's what works and what doesn't.

### Sidebar navigation

| # | Button | Status | Notes |
|---|--------|--------|-------|
| 1 | Dashboard | ✅ Works | CRM dashboard with charts |
| 2 | Leads | ✅ Works | Lead list, filters, create |
| 3 | Deals | ✅ Works | Deal list, Paperclip AI deal visible |
| 4 | Contacts | ✅ Works | Contact list |
| 5 | Organizations | ✅ Works | Org list |
| 6 | Notes | ✅ Works | Note list |
| 7 | Tasks | ✅ Works | Task list |
| 8 | Calendar | ✅ Works | Calendar view |
| 9 | Call Logs | ✅ Works | Call log list with filters |
| 10 | Newsletters | ✅ Works | Listmonk iframe embed |
| 11 | Social | ✅ Works | Postiz iframe embed (shows sign-up page) |
| 12 | Gameplan | ✅ Works | Separate app at `/g`, "←CRM" back link |
| 13 | **Agent Builder** | ❌ **DEAD** | Click does nothing. No navigation, no error. |
| 14 | **Fullscreen Chat** | ❌ **DEAD** | Click does nothing. |
| 15 | **AI Assistant** | ❌ **DEAD** | Click does nothing. |
| 16 | **Apps** | ❌ **WRONG URL** | Goes to `frappeframework.com/blog` instead of `/crm/apps` |

### Cockpit toolbar (at `/api/method/forsch_frontiers.api.cockpit.embed`)

| Control | Status | Notes |
|---------|--------|-------|
| Agent dropdown | ✅ Works | Lists all 20 agents, switching works |
| Theme toggle | ✅ Works | Light/dark mode |
| **□ Box** | ⚠️ No feedback | Clicked, nothing visible happened |
| **↻ Refresh** | ⚠️ No feedback | Clicked, nothing visible happened |
| **▷ Run** | ⚠️ No feedback | Clicked, nothing visible happened |
| **Deploy** | ❌ **TIMEOUT** | Hung for 30s — likely backend issue |
| **Generate ›** | ⚠️ Not tested | Avoided (mutating action per your instructions) |
| Model dropdown | ✅ Works | Shows all LiteLLM models |
| Jacket dropdown | ✅ Works | "none" and "hubert-team-lead" |
| Instruction textarea | ✅ Works | Editable |
| Toolbox sidebar | ✅ Renders | All tools listed with ✎ buttons |
| Chat iframe | ✅ Renders | "Claude / Hubert chat" iframe |
| Notes textbox | ✅ Works | "jot anything" placeholder |

### Console errors

- **Gameplan notification error (on every page):** `frappe.exceptions.ValidationError: SQL functions are not allowed as strings in SELECT: count(name) as count` — Gameplan's `unread_notifications` API uses old SQL syntax incompatible with current Frappe. Fills console with tracebacks on every CRM page load.

### Session issues

- **Session expires quickly** — had to re-login 3 times during this audit. Cockpit 403s after a few minutes of inactivity.
- **No "New Agent" button in cockpit** — the agent dropdown only lists existing agents. A user has to know to type a new agent ID directly in the URL (`/crm/agents/<new-id>`).

---

## Part 2: Navigation Architecture — What Goes Where

### Current state

The CRM sidebar is a flat list mixing three categories:

1. **Native CRM items** (Dashboard → Call Logs) — these are real CRM views
2. **Embedded apps** (Newsletters, Social) — iframes inside CRM chrome
3. **Dead links** (Agent Builder, Fullscreen Chat, AI Assistant) — broken
4. **Gameplan** — a separate app on the same bench, accessed at `/g`, with its own UI

Gameplan is the model to follow. It's not an iframe — it's a full separate application on the same Frappe bench, sharing the same database and login. It has its own URL (`/g`), its own navigation, and a "←CRM" back link.

### Zach's preferences (from conversation)

- Remove the Gameplan sidebar button — use the flipper at the top instead
- Land in Gameplan by default if possible
- Agent Builder should probably be its own complete tab

### Recommendation: Three-tier navigation

```
┌─────────────────────────────────────────────────────────┐
│  [Gameplan]  [CRM]  [Agent Builder]  [Wiki]  [Drive]    │  ← top flipper
├─────────────────────────────────────────────────────────┤
│                                                         │
│  (CRM sidebar)                    (Agent Builder)        │
│  ├─ Dashboard                     ├─ Agent canvas        │
│  ├─ Leads                        ├─ Config panel        │
│  ├─ Deals                        ├─ Toolbox             │
│  ├─ Contacts                     ├─ Chat                │
│  ├─ Organizations                └─ Generate/Deploy      │
│  ├─ Notes                                                │
│  ├─ Tasks                        (Gameplan)              │
│  ├─ Calendar                     ├─ Discussions          │
│  ├─ Call Logs                    ├─ Projects             │
│  ├─ Newsletters (embed)          └─ Members              │
│  └─ Social (embed)                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Tier 1 — Top flipper:** Switches between major application planes. Each is a full app experience, not an iframe. This is the Frappe Desk pattern — modules at the top, sidebar within each module.

**Tier 2 — Per-app sidebar:** Each app has its own navigation. CRM keeps its native items + lightweight embeds. Agent Builder gets its own sidebar (or the cockpit's built-in nav).

**Tier 3 — Inline content:** The main content area for the active app.

### What moves where

| Current location | Recommendation | Why |
|-----------------|----------------|-----|
| **Gameplan** (sidebar) | → Top flipper, **default landing** | It's a full app. Zach wants to land here. Remove the sidebar link, keep `/g` as the app URL. |
| **Agent Builder** (sidebar, dead) | → Top flipper, **full tab** | The cockpit is a complete application (canvas, config, chat, deploy). It deserves its own space. Currently trapped in a dead sidebar link + hidden iframe URL. |
| **Fullscreen Chat** (sidebar, dead) | → **Remove** or merge into Agent Builder | Dead link. If this was meant to be a Hubert chat surface, the cockpit already has a chat iframe. |
| **AI Assistant** (sidebar, dead) | → **Remove** or merge into Agent Builder | Same — dead link, redundant with cockpit chat. |
| **Apps** (sidebar, wrong URL) | → Fix URL to `/crm/apps` or **remove** | Currently goes to Frappe blog. The app registry exists at `/crm/apps`. |
| **Newsletters** (sidebar) | → Stay in CRM sidebar | Lightweight Listmonk iframe. Works fine as a CRM sidebar item. |
| **Social** (sidebar) | → Stay in CRM sidebar | Lightweight Postiz iframe. Works fine. |
| **Native CRM items** | → Stay in CRM sidebar | Dashboard, Leads, Deals, etc. These ARE the CRM. |

### How to implement the flipper

The CRM fork (`forschzachary/crm`) already has custom frontend commits for the sidebar (Newsletters/Social links). The flipper would be another frontend change in that same fork.

**Option A — Frappe Desk top bar (native):** Frappe Desk already has a module switcher at the top. Gameplan, CRM, and Agent Builder could each be a Desk module with their own workspace. This is the most "Frappe-native" approach and would require zero custom flipper code — just workspace configuration.

**Option B — Custom flipper in CRM fork:** Add a top bar to the CRM frontend that switches between `/g` (Gameplan), `/crm` (CRM), and `/agent-builder` (Agent Builder). More control, more custom code.

**Recommendation: Option A (Desk modules).** It's already built. Gameplan already has a Desk workspace. CRM has one. Agent Builder has one (the "Agent Builder" Workspace with the URL shortcut). The Desk top bar IS the flipper. Just configure the default landing page to be Gameplan's workspace.

### Default landing: Gameplan

To make Gameplan the default landing page when visiting `crm.forschfrontiers.com`:

1. Set the default home page in Frappe site config to `/g` (or the Gameplan Desk workspace)
2. Or: configure the root `/` route to redirect to `/g`
3. Or: set Zach's user default workspace to Gameplan

This way: visit the CRM domain → land in Gameplan → use the Desk top bar to flip to CRM or Agent Builder.

### Agent Builder as a full tab

The Agent Builder cockpit is currently:
- A Web Page at `/agent-builder` (Frappe Custom HTML Block with an iframe)
- Reverse-proxied through `forsch_frontiers/api/cockpit.py` → `cockpit.forschfrontiers.com`
- The sidebar link is dead

To make it a proper tab:

**Short-term fix:** Fix the sidebar link to point to `/agent-builder`. The Web Page already exists and works. This is a one-line fix in the CRM fork's sidebar component.

**Long-term (recommended):** Follow the plan in `docs/agent-graph-native-rebuild.md` — rebuild the graph UI as a native Frappe Vue route. No iframe, no CDN dependency, no Cloudflare tunnel for the UI. The box stays as a JSON API only. This is a multi-day effort but eliminates the entire class of iframe/CDN/tunnel bugs.

**Middle-ground:** Keep the current iframe approach but give Agent Builder its own Desk workspace with a proper shortcut. The cockpit already works — it just needs a working nav link and better session management (the 403-after-inactivity problem).

---

## Part 3: Bug Backlog

### Critical (blocks user workflows)

1. **Agent Builder sidebar link is dead** — no route, no navigation. Users cannot discover the cockpit from the CRM UI.
2. **Fullscreen Chat sidebar link is dead** — same.
3. **AI Assistant sidebar link is dead** — same.
4. **Apps sidebar link goes to wrong URL** — should go to `/crm/apps`, goes to Frappe blog.
5. **Cockpit Deploy button hangs** — 30s timeout, likely backend issue on the box.
6. **Session expires too quickly** — cockpit 403s after a few minutes. Forces re-login mid-workflow.

### Important (degrades experience)

7. **Cockpit toolbar buttons (Box, Refresh, Run) have no visible feedback** — user clicks and nothing happens. No loading indicator, no status change, no error message.
8. **No "New Agent" button in cockpit** — can only select existing agents from dropdown. Must know the URL pattern to create one.
9. **Gameplan notification error on every CRM page** — `count(name) as count` SQL syntax incompatible with current Frappe. Fills console with tracebacks.
10. **Auto-spawn bug on first save** — when saving a new agent through the CRM UI (Frappe proxy path), the agent is not added to `agents.yaml`. Workaround: spawn via box API directly. (Documented in `docs/E2E-PROOF-HANDOFF.md`)

### Nice-to-have

11. **Cockpit Generate button not tested** — avoided per instructions, but should be verified.
12. **Postiz iframe shows sign-up page** — may need OIDC wiring so it recognizes the logged-in CRM user.

---

## Part 4: Implementation Sequence

### Quick wins (today, low risk)

1. **Fix the three dead sidebar links** — point Agent Builder to `/agent-builder`, remove or fix Fullscreen Chat and AI Assistant.
2. **Fix Apps link** — point to `/crm/apps`.
3. **Fix Gameplan SQL error** — update `count(name) as count` to use Frappe's query builder or raw SQL with proper escaping. This is in the `forschzachary/gameplan` repo, `develop` branch.

### This week

4. **Configure Desk modules as the flipper** — set up Gameplan, CRM, and Agent Builder as Desk workspaces with the top bar switcher.
5. **Set Gameplan as default landing** — configure site or user default.
6. **Fix cockpit session timeout** — investigate why the session cookie expires so quickly. May be a Frappe session config or the cockpit's token refresh.
7. **Add "New Agent" button to cockpit** — a "+" button in the agent dropdown that prompts for an ID and navigates to `/crm/agents/<new-id>`.

### Next sprint

8. **Cockpit toolbar feedback** — add loading states and status messages to Box, Refresh, Run, Deploy buttons.
9. **Fix auto-spawn bug** — ensure the Frappe proxy path triggers the same auto-spawn logic as direct box API calls.
10. **Wire Postiz OIDC** — so the iframe recognizes the logged-in CRM user instead of showing a sign-up page.

### Future (multi-day)

11. **Native Agent Graph rebuild** — per `docs/agent-graph-native-rebuild.md`. Eliminates the iframe, CDN dependency, and Cloudflare tunnel for the UI. The box becomes a pure JSON API.
12. **Agent Detail View** — per `docs/plans/dispatch-prompts.md`. A proper Frappe page for agent configuration with Config tab, Generate & Verify, status tracking.

---

## References

- CRM fork: `forschzachary/crm` (v16 branch) — sidebar is built here
- Custom app: `forsch_frontiers` — cockpit proxy, permissions, DocTypes
- Deploy: `forschzachary/frappe-crm-deploy` — Railway build, Dockerfile, apps.json
- Gameplan: `forschzachary/gameplan` (develop branch) — team-rooms app, has the SQL bug
- Cockpit proxy: `forsch_frontiers/api/cockpit.py` — reverse-proxies to `cockpit.forschfrontiers.com`
- Agent Graph rebuild plan: `forsch_frontiers/docs/agent-graph-native-rebuild.md`
- Agent Detail View plan: `forsch_frontiers/docs/plans/dispatch-prompts.md`
- E2E proof handoff: `adk/docs/E2E-PROOF-HANDOFF.md`
- Canonical facts: `canonical/business-stack/frappe-crm/CANONICAL-FACTS.md`
