# Forsch Frontiers Project Discipline

This repo is the custom Frappe app for the Forsch Frontiers CRM.

## GitHub discipline

- Durable work happens on a branch, not directly on `main`.
- Branch names should say the intent: `feat/...`, `fix/...`, `docs/...`, `chore/...`.
- Commit as you go at natural checkpoints. A finished document, a working UI slice, or a verified fix gets its own commit.
- Keep commits reviewable. Do not mix documentation staging, UI implementation, and deployment plumbing in one commit unless the change is inseparable.
- Use conventional commit messages: `docs: ...`, `feat: ...`, `fix: ...`, `chore: ...`.
- Before committing, run `git status -sb` and review the exact files staged.
- Push branches to GitHub when work should survive the box.
- Use PRs for anything that changes production behavior. Small docs-only commits may land directly only when Zach asks for it.
- Do not leave important work local-only. If it matters, it gets committed and pushed.

## Documentation discipline

- Update docs in the same branch as the work they describe.
- If live state changes, update the relevant doc before calling the task done.
- Put planning/staging docs under `docs/plans/`, `docs/specs/`, `docs/audits/`, or a feature folder under `docs/`.
- Docs must distinguish confirmed facts from intended design.
- Include evidence paths: API endpoint, source file, command, route, or live URL.
- Do not write secrets into docs. Name credential locations or Authsome key names only.
- If docs disagree with live state, live state wins; fix the doc or mark it stale.

## Branch workflow

1. Start clean or explicitly inventory unrelated dirty files.
2. Create a branch from current `main`:
   `git checkout -b docs/example-topic`
3. Make the smallest coherent change.
4. Verify the change with the smallest real check available.
5. Stage only related files:
   `git add <paths>`
6. Commit:
   `git commit -m "docs: stage example topic"`
7. Push when the work should be durable:
   `git push -u origin HEAD`
8. Open a PR for code or production-facing behavior changes.

## Control Plane notes

The Control Plane staging docs live at `docs/control-plane/`.

The intended implementation posture is lazy and mostly frontend:

- Existing CRM Vue route first.
- Existing Frappe REST and existing graph/box proxies first.
- One read-only summary endpoint only if frontend-only becomes brittle.
- No dashboard builder, no Insights install, no custom dashboard DocTypes in v1.
