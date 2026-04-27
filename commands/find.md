---
description: Quickly find a specific Productive deal, task, person, or company by name.
argument-hint: name or keyword
---

Use the Productive MCP tools to locate the resource whose name matches `$ARGUMENTS`.

Behavior:

- Treat `$ARGUMENTS` as a fuzzy name. Decide which resource type fits best from the wording:
  - Looks like a project/client name → `productive_list_deals` (with `include=["company"]`) and/or `productive_list_companies`.
  - Looks like a person → `productive_list_people` (try the `email` filter first if it looks like an email).
  - Looks like a task title → `productive_list_tasks`.
- Prefer precision over recall: 3–5 best matches is better than 50 noisy ones. Use `max_results=10` unless the user asked for more.

Return:

- A short list of the best matches with id, name/title, and one-line context (e.g. parent deal for tasks, company for deals).
- If nothing is found, say so clearly and suggest alternative search terms.
- If the search target type is genuinely ambiguous, ask the user one question before fanning out across resource types.
