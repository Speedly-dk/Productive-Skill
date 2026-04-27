# Status report format

Use this exact structure when producing a project status summary. Each section is a markdown header; tables are preferred over bullets for tabular data.

## Header

```markdown
## [Deal name] — [Company name]

- **Period:** [YYYY-MM-DD → YYYY-MM-DD]
- **Deal type:** [Internal | Client]
- **Status:** [from deal attributes]
```

## Services snapshot

```markdown
### Services

| Service | Type | Notes |
|---|---|---|
| Development | Time-based | Primary delivery |
| Project management | Time-based | Coordination |
```

Skip the table when there is only one service; mention it in prose instead.

## Open tasks

Group by status when there are 5+ tasks; otherwise list flat.

```markdown
### Open tasks (12)

**In progress (5)**
| Title | Assignee | Due |
|---|---|---|
| Implement OAuth | Alice | 2026-05-01 |

**Blocked (2)**
…
**To do (5)**
…
```

If the deal has zero open tasks, say "No open tasks." Don't fabricate empty tables.

## Recent time activity

Always show **totals per service**, then optionally the top 5 recent entries.

```markdown
### Time activity (period)

| Service | Total | Billable |
|---|---|---|
| Development | 32h 30min | 32h 30min |
| Project management | 4h 0min | 4h 0min |
| **Total** | **36h 30min** | **36h 30min** |

**Recent entries:**
- 2026-04-26 · 1h 30min · Development · Alice — "OAuth refactor"
- …
```

Use HH:MM or H h M min — pick one format and stick to it. Always strip HTML from notes (Productive sometimes stores them with `<p>`/`<br>`).

## Flags & follow-ups

Surface anything that warrants a human decision. Examples:

```markdown
### Flags

- **Two tasks unassigned** — "Update copy" and "Migrate billing flow". Triage?
- **No time logged on Project Management this period** — typo on service id, or scope shifted?
- **Three entries with empty notes** — back-fill before invoicing?
```

If there are no flags, omit the section. Don't pad the report.

## End the report with a focused question

Not "anything else?" — pick the most actionable signal from the data and ask about it directly. E.g.:

> Two tasks are unassigned. Want to assign them now?

This converts the status report into an action surface rather than a passive summary.
