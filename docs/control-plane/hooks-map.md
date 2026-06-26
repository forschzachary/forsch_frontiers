# Control Plane Hooks Map

This is the working map of what the Control Plane can hook into without turning into a yak farm.

Difficulty scale:

- **Easy** - frontend can call existing Frappe REST or existing endpoint.
- **Medium** - needs one small read-only summary endpoint or schema verification.
- **Hard** - needs credentials, external API wiring, or new persistent state. Avoid in v1.

## Frappe / CRM

| Need | Source | Hook | Difficulty | Notes |
|---|---|---|---|---|
| Leads | `CRM Lead` | Frappe REST `/api/resource/CRM Lead` | Easy | Verify fields before coding. Use explicit fields. |
| Deals | `CRM Deal` | Frappe REST `/api/resource/CRM Deal` | Easy | Stage fields likely useful, but verify schema. |
| Contacts/orgs | CRM doctypes | Frappe REST | Easy | Secondary; don't include in v1 unless needed. |
| Error count | `Error Log` | Frappe REST `/api/resource/Error Log` | Easy | Good ops card. Needs date filter. |
| Current user/roles | Frappe boot/session | Existing CRM context / `frappe.auth.get_logged_user` | Easy | Use only for "mine/all" if assignment data is clean. |
| Default landing | System Settings + `desktop:home_page` | Frappe settings/defaults | Medium | We know this can be controlled; don't touch until page exists. |

## Gameplan

| Need | Source | Hook | Difficulty | Notes |
|---|---|---|---|---|
| Projects | `GP Project` | Frappe REST | Easy | Already installed and used. |
| Tasks | `GP Task` | Frappe REST | Easy | Good for due/stale lane. |
| Agent task sync | `FF Agent Task` / hooks | Frappe REST + existing `doc_events` | Medium | Useful later for agent work visibility. |

## Agent Builder / Live Agent Graph

| Need | Source | Hook | Difficulty | Notes |
|---|---|---|---|---|
| Graph health | graph server | CRM proxy `forsch_frontiers.api.cockpit.graph_embed?path=/pulse` | Easy | Already exists behind login. |
| Clusters/nodes | graph server | CRM proxy `graph_embed?path=/clusters` or graph JSON path | Easy | Read-only. |
| Agent config | box API | Existing `agent_config.py` proxy endpoints | Easy/Medium | Verify exact method names before implementation. |
| Generate/verify state | box API / factory | Existing `agent_factory.py` proxy endpoints | Medium | Use honest unavailable if no status artifact. |
| Eval state | graph server `.eval_runs` / future endpoints | Medium | Plan has `GET /agent-evals`, `POST /agent-eval-run`; don't fake it. |

## Ops services

| Need | Source | Hook | Difficulty | Notes |
|---|---|---|---|---|
| LiteLLM readiness | `http://litellm:4000/health/readiness` or public proxy | Server-side summary endpoint | Medium | Browser should not hold API keys. |
| Authsome health | `http://authsome:7998/health` | Server-side summary endpoint | Medium | Same-origin summary endpoint avoids CORS/secrets. |
| ADK bridge health | container/bridge endpoint | Server-side summary endpoint | Medium | Exact endpoint to verify. |
| Docker/container health | host Docker | Hard | Do not expose raw Docker to CRM. Maybe summary later. |
| Railway deploy state | Railway API | Hard | Needs Authsome credentials and scope. Later. |

## Content systems

| Need | Source | Hook | Difficulty | Notes |
|---|---|---|---|---|
| Listmonk campaigns/subscribers | Listmonk API / CRM proxy | Medium/Hard | Later. Useful but not landing-page critical. |
| Postiz queue/status | Postiz API | Medium/Hard | Later. |
| Newsletter sync state | existing scheduled jobs/logs | Medium | Add only when data path is known. |

## Recommended v1 hook strategy

Frontend-only first:

1. Frappe REST for `CRM Lead`, `CRM Deal`, `GP Project`, `GP Task`, `Error Log`.
2. Existing graph proxy for `/pulse` and `/clusters`.
3. Links to existing routes.

Add one backend endpoint only if needed:

`forsch_frontiers.api.control_plane.summary`

Responsibilities:

- Read-only.
- Return compact JSON for health cards.
- Hide secrets and cross-origin service details.
- Timeout fast and return per-service unavailable states.

Do not add:

- Dashboard DocTypes.
- Card layout persistence.
- External service write actions.
- Long-running checks.
