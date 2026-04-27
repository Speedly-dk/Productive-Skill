---
description: Produce a weekly time report grouped by deal — last week's hours, billable split, and top notes.
argument-hint: optional week (e.g. "last week", "2026-W17", "2026-04-20 to 2026-04-26")
---

You are producing a weekly time report from Productive time entries.

Steps:

1. Resolve the report period from `$ARGUMENTS`:
   - Default to **last week** (Mon–Sun in the user's locale) when no argument is given.
   - Accept ISO week strings like `2026-W17`, explicit ranges like `2026-04-20 to 2026-04-26`, or relative phrases like "this week", "last week".
   - State the resolved period (`Mon 2026-04-20 → Sun 2026-04-26`) before pulling data.

2. Pull entries with `productive_search_time_entries`:
   - `after` and `before` from the resolved period (inclusive).
   - `include=["service", "task"]` so you can group without a separate fetch.
   - `person_id` filter only if the user asked for a specific person; otherwise leave it open.
   - Cap `max_results` at 500 (the hard cap) and warn the user if the response hits the cap so they can narrow the period.

3. Resolve service → deal → company:
   - Collect unique `service_id` values from the entries.
   - Call `productive_list_services` with `extra_filters={"id": "<csv-of-ids>"}` and `include=["deal"]` to get deal ids.
   - Call `productive_list_deals` with `extra_filters={"id": "<csv-of-deal-ids>"}` and `include=["company"]` to flesh out names.

4. Aggregate and render a markdown report:
   - **Header:** the resolved period and total minutes.
   - **By deal:** a table with deal name, company, total minutes, billable minutes.
   - **Top notes:** up to 5 entries with the longest or most descriptive notes — useful for invoicing context. Strip HTML before showing.
   - **Gaps:** if any weekday has zero entries, list it as a flag for the user to fill.

Do not dump raw entry rows into the response. If the user wants drill-down, offer a follow-up like "want me to show all entries on deal X?".
