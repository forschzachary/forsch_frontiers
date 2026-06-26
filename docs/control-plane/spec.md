# Control Plane Spec

## One-sentence spec

A custom CRM landing page that shows the smallest useful operating picture across revenue, work, agents, and system health, with every item linking to the real place to act.

## User promise

Open CRM. Know what is healthy, what is stale, what needs action, and where to click next.

## Design posture

- Dashboard-like, but not dashboard-builder-like.
- Dense enough to be useful, calm enough to be a home base.
- Cards are summaries and launchpads, not mini-apps.
- Prefer text, counts, status chips, and links over charts.
- One primary action: **Review attention items**.

## Information architecture

### 1. Attention strip

Purpose: top-level triage.

Possible cards:

- Deals needing follow-up.
- Open high-priority Gameplan tasks.
- Agents with failing/stale verify or eval state.
- CRM errors in the last 24h.
- Scheduler/bridge/model health problems.

Card behavior:

- Each card has label, count/state, short reason, target link.
- Empty state is quiet: "nothing urgent".

### 2. Revenue lane

Purpose: CRM pulse.

Possible widgets:

- New leads this week.
- Deals by stage, text list not chart in v1.
- Follow-ups due today/overdue.
- Recent high-value contacts/deals.

Likely sources:

- `CRM Lead`
- `CRM Deal`
- Frappe CRM activities/tasks, exact doctype to verify before implementation.

### 3. Work lane

Purpose: operational/project work.

Possible widgets:

- Gameplan projects in progress.
- Tasks due/overdue.
- Recently updated tasks.
- Zach/Shelby assigned work, if assignment fields are clean.

Likely sources:

- `GP Project`
- `GP Task`

### 4. Agent lane

Purpose: builder/runtime status.

Possible widgets:

- Live Agent Graph health.
- Agent count by project/cluster.
- Agents failing verify.
- Agents with stale evals.
- Quick links: graph, focused agent, generate/verify.

Likely sources:

- Existing graph server via CRM proxy.
- Existing agent config/factory endpoints.
- Existing eval/verify JSON once wired.

### 5. Ops lane

Purpose: boring health, surfaced before it bites.

Possible widgets:

- CRM `Error Log` recent count.
- Scheduler status.
- LiteLLM readiness/model route status.
- Authsome health.
- ADK bridge health.
- Railway deploy state, later only if easy.

Likely sources:

- Frappe REST for Error Log.
- Existing Frappe whitelisted ops endpoints where present.
- Public/internal health endpoints via a small server-side summary endpoint if needed.

### 6. Content lane

Purpose: optional marketing/content pulse.

Possible widgets:

- Listmonk campaign/subscriber status.
- Postiz queue status.
- Newsletter sync state.

Status: later. Keep out of v1 unless the data is already trivial.

## V1 card set

Smallest useful v1 should be 8 cards:

1. CRM leads needing follow-up.
2. Open deals.
3. Gameplan tasks due or stale.
4. Active Gameplan projects.
5. Live Agent Graph health.
6. Agents needing verify/eval attention.
7. CRM Error Log last 24h.
8. LiteLLM/Authsome/ADK bridge health, summarized as one ops card.

## V1 interaction model

- Click card -> navigate to existing CRM/Gameplan/Agent Builder surface.
- Refresh button reloads all summaries.
- No drag/drop.
- No saved layouts.
- No user personalization.
- No filters except maybe "mine/all" if assignment data is clean.

## Visual direction

- Full-width CRM page.
- Header: title, last refreshed, refresh action.
- Attention strip: horizontal cards, slightly stronger contrast.
- Lanes: two-column responsive grid below.
- Cards: flush surface, subtle borders, status chip, count, 1-line explanation, link.
- Use existing CRM/frappe-ui tokens. Do not invent a design system.

## Acceptance criteria

- Runs as a CRM Vue route inside existing app shell.
- Loads without new backend code if possible.
- If backend code is required, it is one read-only summary endpoint.
- All cards either show real data or an honest unavailable state.
- Every non-empty card links to the relevant existing route.
- No fake green statuses.
