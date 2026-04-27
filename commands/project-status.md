---
description: Summarize the status of a Productive deal — services, open tasks, and recent time activity.
argument-hint: deal name or id (optional date range)
---

You are producing a project status summary for a Productive deal using the read-side MCP tools.

Steps:

1. Identify the deal from `$ARGUMENTS`:
   - If the user gave a numeric id, treat it as the deal id directly.
   - Otherwise look it up with `productive_list_deals` (`include=["company"]`). If multiple match, ask the user to choose.

2. Pull the supporting data in parallel where possible:
   - `productive_get_deal(deal_id, include=["company"])` for the deal header.
   - `productive_list_services(deal_id=...)` for the deliverable structure.
   - `productive_list_tasks(deal_id=..., max_results=50)` to see open work.
   - `productive_search_time_entries(after=<period start>, before=<period end>, deal_id=...)` for recent time activity. Default the period to the last 14 days unless the user specified one.

3. Format the output as a markdown status report with these sections:
   - **Deal** — name, company, deal type, status.
   - **Services** — short table of services with name and id.
   - **Open tasks** — table grouped by status (or by assignee if status grouping is sparse).
   - **Recent time** — total minutes per service for the period, plus the top 5 most recent entries.

Aggregate inside the tool call when the time-entry list is large — don't dump raw entries into the response. If you need to call `productive_search_time_entries` with `max_results` higher than 200, ask the user to confirm a tighter date range first.
