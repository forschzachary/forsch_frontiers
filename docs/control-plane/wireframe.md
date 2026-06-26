# Control Plane Wireframe

Text wireframe for the first pass. Keep it boring on purpose.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Control Plane                                      refreshed 2 min ago [↻]   │
│ What needs attention across CRM, work, agents, and ops.                      │
├──────────────────────────────────────────────────────────────────────────────┤
│ [ 3 deals need follow-up ] [ 5 tasks stale ] [ graph healthy ] [ 2 errors ]  │
├───────────────────────────────────────────┬──────────────────────────────────┤
│ Revenue                                   │ Work                             │
│                                           │                                  │
│  Open deals                               │  Active projects                 │
│  14 active · 3 stale                      │  6 active · 2 quiet              │
│  → CRM deals                              │  → Gameplan projects             │
│                                           │                                  │
│  New leads                                │  Tasks due                       │
│  8 this week · 2 untouched                │  11 due · 5 overdue              │
│  → CRM leads                              │  → Gameplan tasks                │
├───────────────────────────────────────────┼──────────────────────────────────┤
│ Agents                                    │ Ops                              │
│                                           │                                  │
│  Live Agent Graph                         │  CRM errors                      │
│  healthy · 41 nodes · 29 links            │  2 in last 24h                   │
│  → Open graph                             │  → Error Log                     │
│                                           │                                  │
│  Verify / eval                            │  Service health                  │
│  1 stale eval · verify available          │  LiteLLM ok · Authsome ok        │
│  → Agent Builder                          │  → Ops notes                     │
└───────────────────────────────────────────┴──────────────────────────────────┘
```

## Visual rules

- No chart in v1 unless a list becomes unreadable.
- Counts are large enough to scan, not hero-stat huge.
- Status chips are restrained: ok, attention, unavailable.
- Cards align in lanes. Fixed-width status slot where repeated.
- Empty state copy: "nothing urgent", "no recent errors", "not wired yet".
- Unavailable state copy: "can't reach graph", "schema not verified", "health endpoint unavailable".
- No green unless a real check passed.

## Card content contract

Every card has:

- title
- value or status
- one-line reason
- target link
- state: `ok | attention | unavailable | unwired`

Example:

```json
{
  "title": "Live Agent Graph",
  "value": "healthy",
  "detail": "41 nodes, 29 links",
  "href": "/crm/agents",
  "state": "ok"
}
```

## Tweak panel, if prototyping visually

Only for design comparison during build, not production unless Zach likes it.

Useful toggles:

- Density: compact / relaxed.
- Grouping: 2-column lanes / single-column feed.
- Attention strip: cards / inline list.

Remove before production unless it earns its keep.
