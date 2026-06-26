# Prompt: Probe Control Plane Data Sources

You are working in `/opt/data/workspace/forsch_frontiers`.

Task: complete Slice 0 data-source preflight for the Control Plane.

Read first:

- `/opt/data/workspace/AGENTS.md`
- `docs/control-plane/hooks-map.md`
- `docs/control-plane/references.md`
- `docs/control-plane/implementation-slices.md`

Probe live CRM using the admin token helper, but do not print secrets:

```bash
TOKEN=$(bash /opt/data/scripts/frappe-token.sh --admin-raw)
```

Verify schemas for:

- `CRM Lead`
- `CRM Deal`
- `GP Project`
- `GP Task`
- `Error Log`
- `FF Agent Task`

For each, collect:

- doctype exists?
- useful fields for cards
- date/status/owner/assignment fields
- sample count query
- safe route to link to

Also probe graph through the existing production-safe path if possible:

- graph health/pulse
- clusters/nodes summary

Output:

- Write findings to `docs/control-plane/data-source-preflight.md`.
- Include exact API paths and field names.
- Mark each source: ready / needs endpoint / defer.

Constraints:

- Read-only.
- No writes.
- No deploys.
- No guessed field names in final notes.
