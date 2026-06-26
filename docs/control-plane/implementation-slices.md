# Control Plane Implementation Slices

Build this in thin slices. Stop each slice with a visible result.

## Slice 0 - Preflight

Goal: verify the data sources and route location.

Steps:

1. Inspect CRM frontend router in `/opt/data/workspace/crm/frontend/`.
2. Confirm where custom routes from `forsch_frontiers` are currently injected, if at all.
3. Fetch schemas for `CRM Lead`, `CRM Deal`, `GP Project`, `GP Task`, `Error Log`.
4. Probe graph proxy paths through CRM auth if testing against production.

Output:

- Confirmed route target.
- Field list for v1 cards.
- Decision: frontend-only or one summary endpoint.

## Slice 1 - Static page shell

Goal: make the page exist with real layout and fake-but-obviously-static data.

Files likely touched:

- CRM frontend route/component files, exact path after router inspection.
- Maybe `forsch_frontiers` frontend/page files if this app owns the route.

Content:

- Header.
- Attention strip.
- Four lanes: Revenue, Work, Agents, Ops.
- 8 placeholder cards.

Verification:

- Page loads in CRM.
- No console errors.
- Links are either real or visibly disabled.

## Slice 2 - Frappe REST cards

Goal: replace placeholders with real CRM/Gameplan/Error Log data.

Cards:

- Leads needing follow-up.
- Open deals.
- Active projects.
- Tasks due/stale.
- Error Log last 24h.

Implementation:

- Use existing frontend resource helpers if available.
- Otherwise use same fetch pattern as current CRM frontend.
- Query explicit fields only.
- Each card handles loading/error/empty.

Verification:

- Compare counts to direct API calls.
- Logged-out state does not show fake data.

## Slice 3 - Graph/agent cards

Goal: show graph and agent status without new backend if possible.

Cards:

- Live Agent Graph health.
- Agent/cluster count.
- Agents needing verify/eval attention, if endpoint exists.

Implementation:

- Use existing `graph_embed` proxy for read-only endpoints.
- Use existing agent config/factory proxy methods only after confirming names.
- If eval/verify state is absent, show "not wired" honestly.

Verification:

- `/pulse` and `/clusters` agree with direct graph probe.
- Failures display as unavailable, not green.

## Slice 4 - Optional summary endpoint

Only if frontend-only gets ugly.

Endpoint:

`forsch_frontiers.api.control_plane.summary`

Rules:

- `@frappe.whitelist(methods=["GET"])`
- Login required.
- Read-only.
- Fast timeouts per external check.
- Compact JSON grouped by lane.
- Never returns secrets.

Use it for:

- LiteLLM/Authsome/ADK bridge health.
- Cross-origin/service checks browser cannot safely make.

Do not use it for:

- Basic DocType counts that Frappe REST already handles.

## Slice 5 - Landing behavior

Goal: decide whether this becomes the default place Zach lands.

Options:

1. CRM router default sends `/crm` to `/crm/control-plane`.
2. Frappe `desktop:home_page` lands on CRM, and CRM lands on Control Plane.
3. Add top nav item only, keep existing landing.

Recommended:

- Make it a route first.
- Use it for a week.
- Then set landing.

## Slice 6 - Polish

Goal: make it feel like a control plane, not an admin report.

Tasks:

- Tighten spacing/alignment.
- Remove any low-signal cards.
- Add last refreshed timestamp.
- Add single refresh action.
- Add empty states that are quiet, not celebratory.

## Things not to build yet

- Drag/drop card layout.
- Saved user preferences.
- Custom dashboard DocTypes.
- Chart builder.
- External write actions.
- Full deploy controls.
- Notifications.

If any of those suddenly feel necessary, write the reason down first. Then probably don't build it anyway.
