# 0001 — Build vs. fork the Productive MCP server

- **Date:** 2026-04-27
- **Status:** Decided
- **Decision:** Build fresh in Python.
- **Plan unit:** [U2 in `docs/plans/2026-04-27-001-feat-productive-claude-code-plugin-plan.md`](../plans/2026-04-27-001-feat-productive-claude-code-plugin-plan.md)

## Why this decision was on the table

The plan's adversarial review flagged that "build fresh" was asserted without evidence. The plan's deepening pass added a hard gate at the start of U2: catalogue the two known community Productive MCP servers against the plan's v1 tool surface, and fork one if overlap ≥80% with a compatible license and recent activity. Otherwise, build fresh.

## Candidates evaluated

### A. `berwickgeek/productive-mcp` (TypeScript / Node, npm)

- **Repo:** https://github.com/berwickgeek/productive-mcp
- **License:** ISC (MIT-equivalent, fork-compatible)
- **Activity:** last commit 2026-04-01, actively merged PRs through April 2026, npm-published v1.2.0
- **Stars / issues:** 11 / 2 open
- **Tests:** none (`"test": "echo Error: no test specified"`)
- **Tool surface:** 60+ tools across `src/tools/*.ts` (22 files)

### B. `druellan/Productive-Simple-MCP` (Python / FastMCP)

- **Repo:** https://github.com/druellan/Productive-Simple-MCP
- **License:** MIT
- **Activity:** last commit 2026-04-19, rapid recent iteration
- **Stars / issues:** 0 / 0
- **Tests:** none
- **Tool surface:** 22 read-only tools in a single `tools.py`

## Overlap with the plan's v1 surface (13 tools)

| Plan tool | berwickgeek (A) | druellan (B) |
|---|---|---|
| `productive_search_time_entries` | `list_time_entries` ✓ | `list_time_entries` ✓ |
| `productive_list_deals` | `list_project_deals` ✓ | MISSING |
| `productive_get_deal` | MISSING | MISSING |
| `productive_list_services` | `list_services` ✓ | MISSING |
| `productive_list_tasks` | `list_tasks` ✓ | `get_tasks` ✓ |
| `productive_list_people` | MISSING (only `whoami`) | `get_people` ✓ |
| `productive_list_companies` | `list_companies` ✓ | MISSING |
| `productive_create_time_entry` | `create_time_entry` ✓ | read-only — MISSING |
| `productive_update_time_entry` | MISSING | read-only — MISSING |
| `productive_create_task` | `create_task` ✓ | read-only — MISSING |
| `productive_update_task` | split into `update_task_details` + `update_task_assignment` + `update_task_status` ✗ | read-only — MISSING |
| `productive_create_task_comment` | `add_task_comment` ✓ | read-only — MISSING |
| `productive_health` | MISSING | MISSING |
| **Overlap** | **8/13 = 62%** | **3/13 = 23%** |

Neither candidate clears the 80% threshold the plan set.

## Other factors

- **berwickgeek** is in TypeScript; forking would force the rest of the plugin into Node/TS or maintain a polyglot repo. The plan's stated language preference (Python, matching the user's existing Productive scripts) would be violated. Refactoring its split `update_task_*` tools into a unified `productive_update_task` is non-trivial. No tests means every behavioural change is unverified.
- **druellan** is the right language but read-only — adding the five v1 write tools is effectively a fresh build of the write half of the server, plus the four missing read endpoints. The good ideas to borrow as prior art are its response-filtering utilities (HTML stripping, field pruning, optional TOON output) and its centralized error handler — both small enough to reimplement directly.

## Decision

**Build fresh in Python.** Rationale, in order of weight:

1. **Neither candidate clears the 80% gate.** 62% on berwickgeek is the upper bound, and that's after accepting a language switch and a unification refactor.
2. **Language preference.** Python matches the user's existing Productive scripts and the plan's stated default. Forking berwickgeek would force a Node toolchain into a Python-aligned repo.
3. **Test coverage starts at zero in both forks.** A from-scratch build with `vcrpy` cassettes from day one (per the plan) is more credible than retrofitting tests onto either fork.
4. **Customisation surface.** The plan calls out specific behaviours that don't exist in either fork — `productive_health` with token-scope detection, pagination short-circuit at `max_results`, prompt-injection-aware docstrings on write tools, fixture scrubbing — and adding them cleanly is easier in code we own than in code we'd be patching.

## What we'll borrow as prior art (not fork)

- **From druellan:** centralized API error handler pattern, response field pruning for token efficiency, optional compact output formats. Reference its `productive_client.py` and `tools.py` while writing our `client.py` and `formatting.py`.
- **From berwickgeek:** confirmation pattern on destructive writes, helper functions like `resolvePersonName` / `resolveWorkflowStatus` for ID-to-name resolution. Reference its `src/tools/time-entries.ts` and `src/tools/tasks.ts` while writing our equivalent tools in U3 and U4.

Both repos remain useful as cross-references during U2–U4, but neither becomes a dependency.
