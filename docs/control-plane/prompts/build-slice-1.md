# Prompt: Build Control Plane Slice 1

You are working in `/opt/data/workspace/forsch_frontiers`.

Task: implement Slice 1 from `docs/control-plane/implementation-slices.md`.

Read first:

- `/opt/data/workspace/AGENTS.md`
- `docs/control-plane/README.md`
- `docs/control-plane/spec.md`
- `docs/control-plane/wireframe.md`
- `docs/control-plane/implementation-slices.md`
- `docs/control-plane/references.md`

Constraints:

- Mostly frontend.
- Do not add new DocTypes.
- Do not install Frappe Insights.
- Do not create a dashboard builder.
- Do not add a backend endpoint unless Slice 1 cannot exist without it.
- Use existing CRM/Frappe UI patterns.
- Every placeholder must be visibly static/unwired, not fake-live.

Goal:

- Add a native CRM route/page for Control Plane.
- Render the shell: header, attention strip, Revenue/Work/Agents/Ops lanes, 8 cards.
- Use realistic static placeholder data.
- Make links point to existing routes where known, otherwise mark disabled.

Verification:

- Run the smallest build/check available for the frontend.
- If a browser can be used, load the page and check console errors.
- Report exact files changed and exact command output.
