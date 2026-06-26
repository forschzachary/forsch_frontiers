# Forsch Control Plane

Lazy, precise staging folder for a custom CRM landing page.

## Intent

Build one native CRM landing surface that answers: "what needs Zach's attention now?"

This is not a BI product, not an Insights clone, and not a second Frappe app. It is a mostly-frontend Vue route inside the existing CRM shell, backed by existing Frappe REST calls and a few already-existing proxy endpoints.

## Shape

Working name: **Control Plane**

Route target: `/crm/control-plane` or whatever the CRM router wants.

Primary layout:

1. **Attention strip** - 3-5 things that need action now.
2. **Revenue lane** - leads, deals, follow-ups.
3. **Work lane** - Gameplan projects, tasks, stale work.
4. **Agent lane** - graph status, agents, verify/eval state, deploy readiness.
5. **Ops lane** - CRM errors, scheduler, LiteLLM/Authsome/bridge health.
6. **Content lane** - newsletters/social, if useful later.

Each card should be a link or a tiny read-only summary. No custom workflow until the summary proves it deserves one.

## Ponytail rule

Use the first rung that holds:

- Existing CRM Vue route, not a new app.
- Existing Frappe REST / `frappe-ui` resources, not new backend code.
- Existing proxy endpoints for graph/agent box data.
- One small summary endpoint only if the frontend would otherwise make too many fragile calls.
- No stored dashboard config in v1.
- No chart library in v1 unless already available in the CRM bundle.

## Deliverables staged here

- `docs/control-plane/README.md` - this file.
- `docs/control-plane/spec.md` - product spec and widget inventory.
- `docs/control-plane/hooks-map.md` - what we can hook into, where it comes from, and how hard it is.
- `docs/control-plane/references.md` - docs and local notes to lean on.
- `docs/control-plane/implementation-slices.md` - smallest safe build sequence.
- `docs/control-plane/wireframe.md` - text wireframe and visual rules.
- `docs/control-plane/prompts/` - handoff prompts for future agents.

## Non-goals

- Installing Frappe Insights.
- Building a report builder.
- Creating new DocTypes for dashboards.
- Replacing CRM, Gameplan, Agent Builder, or Live Agent Graph.
- Making every card interactive on day one.

## Open decisions

- Final route name: `/crm/control-plane`, `/crm/home`, or replace current default CRM landing.
- Whether Control Plane becomes the actual Frappe `desktop:home_page` target directly, or the CRM app default route handles it.
- Which 8 cards make v1.
