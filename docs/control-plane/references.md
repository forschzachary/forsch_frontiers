# Control Plane References

Use these before making architecture calls. Live state still wins over docs.

## External docs

### Frappe Framework REST API

https://frappeframework.com/docs/user/en/api/rest

Why it matters:

- Lists/gets DocTypes with `/api/resource/{doctype}`.
- Supports fields, filters, ordering, limits.
- Enough for most Control Plane cards.

Use for:

- CRM Lead/Deal summaries.
- Gameplan Project/Task summaries.
- Error Log summaries.

### Frappe UI

https://ui.frappe.io

Why it matters:

- Existing Vue component library used by Frappe apps.
- Avoid custom component bloat.

Use for:

- Cards, buttons, badges, resource calls if already present in CRM frontend.

### Frappe hooks

https://frappeframework.com/docs/user/en/python-api/hooks

Why it matters:

- Covers `doc_events`, scheduler, app includes, route hooks.
- Useful if Control Plane later needs reactive summary state.

Use for:

- Knowing when not to poll.
- Understanding existing Gameplan/agent sync hooks.

### Frappe Insights

https://docs.frappe.io/insights/introduction

Why it matters:

- Good reference for dashboard vocabulary: data source, query, chart, dashboard.
- Bad fit as the Control Plane itself.

Use for:

- Inspiration only. Do not install/build around it for v1.

## Local skills / notes

### `frappe-app-dev`

Loaded files:

- `references/frontend-vue.md`

Why it matters:

- Confirms the CRM frontend is Vue 3 + Vite + `frappe-ui` style.
- Explains SPA route pattern vs Desk page pattern.
- Gives `useCall`, `useList`, `useDoc` examples.

### `frappe-crm-ops`

Loaded files:

- `references/frappe-framework-capabilities.md`

Useful linked files to load when implementing:

- `references/probe-recipes.md` - API health probes.
- `references/doctype-naming.md` - CRM doctype naming gotchas.
- `references/agent-builder-ui-patterns.md` - existing Agent Builder route/proxy patterns.
- `references/box-json-api.md` - graph/box API details.

Why it matters:

- Captures local pitfalls: API auth, single doctypes, proxy CSRF, route differences.
- Confirms native Frappe features to use before custom code.

### `ponytail`

Why it matters:

- User explicitly asked for lazy/precise.
- Governs implementation: no dashboard engine, no stored layouts, no speculative backend.

### `ui-design`

Why it matters:

- Product surface should be restrained and clear.
- Cards should be useful surfaces, not boxed clutter.

## Local code to inspect before implementation

- `/opt/data/workspace/forsch_frontiers/forsch_frontiers/hooks.py`
  - Current app includes, fixtures, scheduler, doc events.
- `/opt/data/workspace/forsch_frontiers/forsch_frontiers/api/cockpit.py`
  - Existing CRM-authenticated proxy to Live Agent Graph.
- `/opt/data/workspace/forsch_frontiers/forsch_frontiers/api/_agent_box.py`
  - Shared box proxy helper.
- `/opt/data/workspace/forsch_frontiers/forsch_frontiers/api/agent_config.py`
  - Agent config proxy contract.
- `/opt/data/workspace/forsch_frontiers/forsch_frontiers/api/agent_factory.py`
  - Generate/verify proxy contract.
- `/opt/data/workspace/crm/frontend/`
  - Upstream/custom CRM Vue frontend routes and component patterns.

## Doctype names to verify live

Do not assume fields. Before coding cards, inspect schemas for:

- `CRM Lead`
- `CRM Deal`
- `GP Project`
- `GP Task`
- `Error Log`
- `FF Agent Task`

Use explicit fields in all list calls. Frappe rejects unknown fields.
