---
name: productive-project-status
description: Summarize the status of a Productive deal — services, open tasks, recent time activity, and budget burn signals. Triggers on "project status", "deal status", "how is X going", "summarize the project", "status report", or any request to roll up a deal's current state. Composes productive_get_deal, productive_list_services, productive_list_tasks, and productive_search_time_entries.
---

# Productive Project Status

This skill teaches Claude how to produce a clear, scannable status summary for a Productive deal — the kind a project manager would copy into a client email or a Monday standup.

## When to use this skill

- "Give me a status on the Acme deal."
- "What's open on project X?"
- "How are we doing on the Foo redesign?"
- "Status report for last two weeks on deal 42."
- Any request that names a deal and asks for current state, progress, or a roll-up.

## MCP tools you compose

| Tool | Use it for |
|---|---|
| `productive_list_deals` | Resolving a deal name to an id (use `include=["company"]`). |
| `productive_get_deal` | Fetching the deal header. |
| `productive_list_services` | The structural breakdown of the deal. |
| `productive_list_tasks` | What's open, by status and assignee. |
| `productive_search_time_entries` | Recent activity with `deal_id` filter. |

## Workflow

1. **Resolve the deal.**
   - If the user gave a numeric id, skip lookup.
   - Otherwise `productive_list_deals(extra_filters={"name_contains": <query>}, include=["company"])`. If multiple match, present a one-line list and ask which one.

2. **Pull supporting data.** When possible, fan these calls out (the underlying client respects rate limits):
   - `productive_get_deal(deal_id, include=["company"])` — header.
   - `productive_list_services(deal_id, max_results=50)` — deliverable structure.
   - `productive_list_tasks(deal_id, max_results=100)` — open work.
   - `productive_search_time_entries(after=<period start>, before=<period end>, deal_id=<id>, include=["service"], max_results=500)` — recent activity. Default the period to **the last 14 days** unless the user specified one.

3. **Aggregate before formatting.** Don't pass raw entry rows to the user. For time, compute totals per service and a daily/weekly trend line. For tasks, count by status and by assignee.

4. **Format as markdown.** Follow [reference/status-report-format.md](reference/status-report-format.md). Sections, in order:
   - Header (deal name, company, period covered)
   - Services snapshot
   - Open tasks
   - Recent time activity
   - Flags & follow-ups

5. **End with a focused question** — not a generic "anything else?" but something tied to the data, e.g. "Two tasks are unassigned — want to triage them?" or "Time on Service X dropped 40% vs the prior fortnight; investigate?".

## Anti-patterns

- **Dumping raw JSON.** The whole point of this skill is curated output.
- **Pulling 500 time entries and listing them.** Aggregate; the period summary belongs in totals, not rows.
- **Showing tasks with status = Done.** The status snapshot is about *open* work unless the user asked for completed.
- **Omitting the period.** Always state the date range covered. If the deal was created last week, say so — "deal is 7 days old, period covers the entire deal life."

## Common issues

- **"There are too many tasks to summarise."** Group by assignee and show counts; offer to drill into one assignee.
- **"The deal has 30 services."** Roll up by service category (use the `service_type_id` if exposed via custom filters; otherwise keep the list compact).
- **"Time data is empty for this deal."** Say so explicitly; suggest the user check whether time entries exist on a parent deal or alternate service.

## Reference

- [Status report format](reference/status-report-format.md)
