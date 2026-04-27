---
description: Search Productive for time entries, deals, tasks, people, or companies matching a natural-language query.
argument-hint: query terms
---

Use the Productive MCP tools to search the user's Productive workspace for content related to `$ARGUMENTS`.

Behavior:

- Interpret `$ARGUMENTS` as a natural-language search query (e.g. "time logged on Acme last week", "open tasks assigned to me", "all deals with company Foo").
- Pick the most appropriate MCP tool(s) for the query:
  - Time-related queries → `productive_search_time_entries` with date filters.
  - Project/client queries → `productive_list_deals` (sometimes with `productive_list_companies` to resolve a company id first).
  - Task queries → `productive_list_tasks`.
  - Person queries → `productive_list_people`.
- For multi-step queries (e.g. "all open tasks on the Acme project"), chain calls: list deals to find the id, then list tasks scoped to that deal.
- Default to a token-cheap result set: pass `max_results=20` for entity lists when the user did not specify.

When you answer:

- Return a human-readable summary, not raw JSON.
- For lists, use a compact table-like layout with the key fields (e.g. id, name, status, owner, date).
- If multiple resources match, ask one clarifying question rather than dumping everything.
- If nothing matches, say so clearly and suggest a refinement.
