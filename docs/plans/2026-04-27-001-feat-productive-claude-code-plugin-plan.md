---
title: Productive.io Claude Code Plugin
type: feat
status: active
date: 2026-04-27
deepened: 2026-04-27
---

# Productive.io Claude Code Plugin

## Overview

Build a public, one-click-installable Claude Code plugin for Productive.io (productive.io), modeled after the official Notion plugin (`makenotion/claude-code-notion-plugin`). The plugin bundles three integrated components:

1. **A custom local MCP server** (Python, stdio) that wraps Productive's REST API and exposes read + write tools for time entries, deals, services, tasks, people, and companies. (Productive calls what other tools call "projects" the **deal** resource — used consistently throughout this plan.)
2. **Slash commands** for the most common daily workflows (`setup`, `search`, `find`, `create-task`, `log-time`, `project-status`, `weekly-report`).
3. **Productive Skills** that teach Claude how to use Productive intelligently for time tracking and project status reporting.

The repo doubles as a Claude Code plugin marketplace — a single GitHub URL gives any user `/plugin marketplace add` + `/plugin install` parity with the Notion plugin.

---

## Problem Frame

The existing `productive` skill at `~/.dotfiles/config/claude/skills/productive` works for personal queries but has three blockers for daily-driver use and broader sharing:

1. **Token is hardcoded** in `scripts/productive_api.py` — unsafe to publish, and tied to one org.
2. **No native tool surface for Claude** — every interaction shells out to scripts and parses JSON:API by hand. Claude can't compose Productive operations the way it composes Notion MCP tools.
3. **Read-only and AP3-specific** — no write surface (log time, create tasks), no easy install path for other Productive users.

The Notion plugin has shown the shape that solves this: bundle MCP server + skills + commands behind a one-click install. Productive.io needs the same primitive, adapted to the fact that Productive has no hosted MCP — we ship a local stdio server instead.

---

## Requirements Trace

- R1. Any Claude Code user can install the plugin via `/plugin marketplace add <repo>` + `/plugin install` and have a working Productive integration after providing two env vars (`PRODUCTIVE_API_TOKEN`, `PRODUCTIVE_ORGANIZATION_ID`).
- R2. The MCP server exposes both read and write tools covering time entries, deals, services, tasks, people, companies, and custom field values.
- R3. The MCP server enforces auth, pagination, rate-limit backoff, and never logs or persists the API token.
- R4. Slash commands cover the core daily workflows: a one-time setup pre-flight, searching/listing entities, creating tasks, logging time, summarizing project status, and producing a weekly time report.
- R5. Bundled skills teach Claude high-level Productive workflows (time tracking discipline, project status summaries) so commands compose well with conversational use.
- R6. The plugin is publishable to a public GitHub repo and works as both a plugin and a marketplace (mirrors the Notion plugin's repo layout).
- R7. The existing personal `productive` skill keeps working unchanged during plugin development so daily AP3 work isn't disrupted.

---

## Scope Boundaries

- Not building a hosted MCP server. The MCP server runs locally over stdio, launched by Claude Code per the `.mcp.json` declaration.
- Not implementing OAuth. Productive only supports Personal Access Tokens; the plugin requires the user to create one and supply it via env var.
- Not covering the full Productive API surface in v1.
- Not migrating the user's existing `~/.dotfiles/config/claude/skills/productive` skill into the plugin; the two coexist until the plugin is feature-equivalent.
- Not shipping CI, release automation, or a published npm/PyPI package in v1.

### Deferred to Follow-Up Work

- **Invoices, budgets, expenses endpoints**: covered by the API but not part of v1 daily-driver scope. Defer until there's a clear command-level use case.
- **Reports endpoints**: separate, much tighter rate limit (10 req / 30 s) — requires a different client strategy. Defer to v2.
- **Custom fields tools** (`productive_get_custom_field`, `productive_set_custom_field_value`): no v1 command or skill invokes them and the user has not stated a custom-field use case. Add when a workspace-specific helper actually needs them.
- **Invoice-prep skill**: removed from v1. Invoice endpoints are deferred and there is no v1 command to back the skill — shipping it would teach Claude a workflow it cannot execute.
- **Webhooks**: signed HMAC delivery, retry semantics, requires a hosted endpoint to be useful. Out of scope for a stdio plugin.
- **Bulk operations** (`Content-Type: application/vnd.api+json; ext=bulk`): no v1 command needs them.
- **Migrating the personal `productive` skill** into the plugin and deleting the dotfile version: do once the plugin proves out for >2 weeks of real use.
- **Publishing to the official Anthropic plugin marketplace**: ship to a personal/AP3 marketplace first, evaluate quality, then submit upstream.
- **PyPI publishing of `productive-mcp`**: install path uses `uvx --from git+...` in v1 so users avoid a manual publish/release cycle. Switch to PyPI when a stable 1.0 ships.

---

## Context & Research

### Relevant Code and Patterns

- **Existing personal Productive skill** (reference, not modified):
  - `~/.dotfiles/config/claude/skills/productive/SKILL.md` — endpoint reference, JSON:API field guide.
  - `~/.dotfiles/config/claude/skills/productive/scripts/productive_api.py` — pagination logic worth porting.
  - `~/.dotfiles/config/claude/skills/productive/scripts/fetch_time_entries.py` — concrete example of the include-and-resolve pattern (time entries → services → deals → companies).
  - These are outside the plugin repo but informed the API client design.
- **Notion plugin** (architectural template, cloned locally at `~/.claude/plugins/marketplaces/notion-plugin-marketplace/`):
  - `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.mcp.json` — exact plugin/marketplace shape to mirror.
  - `commands/*.md` — frontmatter conventions (`description`, `argument-hint`, `args`), skill+MCP composition patterns.
  - `skills/notion/*/SKILL.md` — skill structure: instructional, references MCP tools by name, ships with examples and reference docs.

### Institutional Learnings

- The user's existing skill hardcodes the API token in committed Python — the plugin must never repeat this. Token comes from `PRODUCTIVE_API_TOKEN` env var; the MCP server fails fast with a helpful error if missing.
- The user's existing skill assumes AP3 ApS (org `34915`) — the plugin must accept any `PRODUCTIVE_ORGANIZATION_ID`.

### External References

- Productive Developer Documentation: https://developer.productive.io/
- Productive API Access (Personal Access Tokens): https://help.productive.io/en/articles/5440689-api-access
- Productive Webhooks (deferred): https://developer.productive.io/webhooks.html
- Productive Custom Fields: https://developer.productive.io/custom_fields.html
- Community MCP servers (read for ideas, not bundled):
  - `berwickgeek/productive-mcp` (Node/TS, read-write, npm-published).
  - `druellan/Productive-Simple-MCP` (Python/FastMCP, read-only, token-efficiency patterns).
- Official Productive Ruby client (resource-model reference): https://github.com/productiveio/api_client
- Anthropic Claude Code plugin docs: structure of `.claude-plugin/`, `.mcp.json`, `commands/`, `skills/` (already understood from the Notion plugin example).

---

## Key Technical Decisions

- **Language: Python 3.10+ for the MCP server**. Matches the user's existing Productive scripts, avoids introducing a Node/TS toolchain to the repo, and the Anthropic Python MCP SDK is mature.
- **Distribution: `uvx --from git+...` invocation in `.mcp.json`**, with `uv` documented as a one-time prereq in the README (`brew install uv` on macOS). This avoids a PyPI publish loop in v1 while still giving users zero-config startup once `uv` is on PATH. Concrete `.mcp.json` shape:

  ```json
  {
    "mcpServers": {
      "productive": {
        "command": "uvx",
        "args": [
          "--from",
          "git+https://github.com/<owner>/Productive-Skill.git#subdirectory=mcp_server",
          "productive-mcp"
        ]
      }
    }
  }
  ```

  Fallback for users who already have a Python toolchain: documented `pip install -e mcp_server/` + `python -m productive_mcp` in `docs/troubleshooting.md`. **Note:** unlike the Notion plugin (HTTP MCP, zero client-side runtime), this design imposes a `uv` dependency on the user. The trade-off and its alternatives are tracked under Risks.
- **Transport: stdio MCP**. Productive has no hosted MCP. stdio matches Claude Code's local-MCP launch model and is what both community Productive MCP servers chose.
- **Auth: env vars only**. `PRODUCTIVE_API_TOKEN` (required), `PRODUCTIVE_ORGANIZATION_ID` (required), `PRODUCTIVE_USER_ID` (optional, used by "current user" defaults). Server validates both required vars at startup and exits with an actionable error if missing. The `/productive:setup` command (U5) provides a pre-flight check that a user can run *before* any other command to surface missing vars without an opaque "MCP failed to start" message.
- **Tool naming convention: `productive_<verb>_<resource>`**. Examples: `productive_search_time_entries`, `productive_create_task`, `productive_get_deal`, `productive_update_task`. Verb prefixes (`search`, `list`, `get`, `create`, `update`, `set`) make the read/write split greppable. There is no `productive_write_*` umbrella prefix. There are no `productive_delete_*` tools in v1.
- **Slash command vs MCP tool namespaces are distinct**: slash commands use `/productive:` (colon, conversational interface); MCP tools use `productive_` (underscore, programmatic interface). They do not collide.
- **Skill names are namespaced**: bundled skills use frontmatter `name: productive-time-tracking` and `name: productive-project-status`, mirroring the Notion plugin's `notion-knowledge-capture` pattern. This avoids any collision with the user's existing `name: productive` dotfile skill (R7).
- **Pagination short-circuits at `max_results`**. The client fetches pages until either `links.next` is absent or the accumulated record count reaches `max_results`, whichever comes first. Tools that produce reports (e.g. weekly-report, project-status) aggregate inside the tool and never return raw entry rows to Claude when the result set could exceed a few dozen.
- **Rate limit + retry handling lives in `client.py`**, not a separate `ratelimit.py` module. v1 traffic is one user, one tool call at a time over stdio — no concurrency. Implementation: HTTP 429 triggers exponential backoff up to 3 retries; otherwise surface a clear tool error. Lift to a dedicated module only if real usage shows contention.
- **No persistent state on disk**. The MCP server is stateless across calls; no caching files written to the user's machine in v1.
- **Repo doubles as marketplace**. `.claude-plugin/marketplace.json` lives at the repo root so the README can use a single `/plugin marketplace add <user>/<repo>` command. The marketplace `name` field is pinned to `productive-skill-marketplace` and the plugin `name` to `productive-workspace-plugin` — these are the exact strings used in `/plugin install productive-workspace-plugin@productive-skill-marketplace` (mirrors the Notion plugin's two-string pattern).

---

## Open Questions

### Resolved During Planning

- *Read-only or read-write?* — Resolved: read + write (per user choice). Daily-driver use needs at least time-entry creation.
- *Public OSS or private?* — Resolved: public OSS (per user choice). Follows the Notion plugin's distribution shape exactly.
- *Personal access token vs OAuth?* — Resolved: personal access token. OAuth isn't supported by Productive; we document how to mint a PAT in the README.
- *Build fresh vs fork an existing community MCP server?* — Resolved with a hard gate at the start of U2: a 1–2 hour spike catalogues the tool surfaces of `berwickgeek/productive-mcp` (Node/TS) and `druellan/Productive-Simple-MCP` (Python/FastMCP) against this plan's tool list (lines under "High-Level Technical Design"). If overlap is ≥80% on either, fork it instead of starting fresh; if not, build fresh in Python. The from-scratch default is no longer asserted — the spike's findings are recorded in U2's verification.

### Deferred to Implementation

- **Exact Python MCP SDK package and entry-point conventions** at the time of build. Pin once dependencies are installed; the `.mcp.json` shape under Key Technical Decisions documents the agreed invocation form.
- **Whether the build-vs-fork spike (U2 entry gate) tilts the plan toward a fork** — if so, U2's "Files" list collapses to a fork branch + customisations rather than fresh modules.
- **Custom fields shape per AP3 workspace**. Out of v1 (deferred); revisit when a command needs it.
- **Whether the `weekly-report` and `project-status` commands need server-side aggregation tools** (e.g. `productive_summarize_time_entries`) instead of pulling raw entries and aggregating in-conversation. Decide during U5 once typical query sizes are observed.

### Deferred to Implementation

- **Exact Python MCP SDK package and entry-point conventions** at the time of build. Pin once dependencies are installed; pseudocode in this plan uses the SDK's documented patterns.
- **Whether `uvx` or a thin `python -m` invocation works better** as the `.mcp.json` `command`. Pick during U2 once the package layout is concrete.
- **Custom fields shape per AP3 workspace**. The MCP server exposes generic custom-field tools; the slash commands stay agnostic until we hit a use case that demands a workspace-specific helper.
- **Rate limiter sharing strategy across concurrent tool calls** within a single Claude Code session. Start with a process-wide token-bucket limiter; revisit if real usage shows contention.

---

## Output Structure

```
Productive-Skill/
├── .claude-plugin/
│   ├── marketplace.json          # name: productive-skill-marketplace
│   └── plugin.json               # name: productive-workspace-plugin
├── .mcp.json                     # uvx --from git+... productive-mcp
├── README.md                     # install + uv prereq + PAT setup
├── LICENSE                       # MIT
├── commands/
│   ├── setup.md                  # /productive:setup pre-flight check
│   ├── search.md
│   ├── find.md
│   ├── log-time.md
│   ├── create-task.md
│   ├── project-status.md
│   └── weekly-report.md
├── skills/
│   └── productive/
│       ├── time-tracking/
│       │   ├── SKILL.md          # name: productive-time-tracking
│       │   └── examples/
│       └── project-status/
│           ├── SKILL.md          # name: productive-project-status
│           └── reference/
├── mcp_server/
│   ├── pyproject.toml            # entry point: productive-mcp = productive_mcp.__main__:main
│   ├── productive_mcp/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── server.py             # MCP server bootstrap, tool registration
│   │   ├── client.py             # REST client: auth, pagination, 429 retry/backoff
│   │   ├── tools/
│   │   │   ├── time_entries.py
│   │   │   ├── deals.py
│   │   │   ├── services.py
│   │   │   ├── tasks.py
│   │   │   ├── people.py
│   │   │   └── companies.py
│   │   └── formatting.py         # JSON:API → compact dict shapes
│   └── tests/
│       ├── conftest.py           # vcrpy cassettes + scrubbing filter
│       ├── test_client.py
│       ├── test_tools_time_entries.py
│       ├── test_tools_deals.py
│       └── test_tools_tasks.py
└── docs/
    ├── install.md                # written during U6 (final-polish unit)
    ├── troubleshooting.md
    └── plans/
        └── 2026-04-27-001-feat-productive-claude-code-plugin-plan.md  (this file)
```

The implementer may adjust this layout if Python packaging conventions or the chosen MCP SDK suggest a better shape — per-unit `**Files:**` sections remain authoritative.

---

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```
┌──────────────────────────────────────────────────────────────────────┐
│  Claude Code session                                                 │
│                                                                      │
│  ┌──────────────┐   ┌──────────────────┐   ┌──────────────────────┐ │
│  │ Slash cmds   │──▶│ Skills           │──▶│ MCP tool calls       │ │
│  │ /productive: │   │ productive-time- │   │ productive_*         │ │
│  │  setup, …    │   │ tracking,        │   │                      │ │
│  │              │   │ productive-      │   │                      │ │
│  └──────────────┘   │ project-status   │   └──────────┬───────────┘ │
│                     └──────────────────┘              │             │
└───────────────────────────────────────────────────────┼─────────────┘
                                                        │ stdio
                                ┌───────────────────────▼──────────────┐
                                │  productive_mcp (local Python MCP)   │
                                │                                      │
                                │  server.py — registers tools         │
                                │     │                                │
                                │     ▼                                │
                                │  tools/*  — one module per resource  │
                                │     │                                │
                                │     ▼                                │
                                │  client.py — HTTP, auth, pagination, │
                                │              429 retry/backoff       │
                                │     │                                │
                                │     ▼                                │
                                │  formatting.py — compact tool output │
                                └───────────────────────┬──────────────┘
                                                        │ HTTPS
                                          ┌─────────────▼────────────┐
                                          │ api.productive.io/api/v2 │
                                          └──────────────────────────┘
```

Tool surface sketch (directional, exact signatures TBD):

```
# read tools
productive_search_time_entries(after, before, person_id?, deal_id?, max_results=200)
productive_list_deals(filter?, include?, max_results=50)
productive_get_deal(id, include?)
productive_list_services(deal_id?, max_results=50)
productive_list_tasks(deal_id?, status?, assignee_id?, max_results=50)
productive_list_people(filter?)
productive_list_companies(filter?)

# write tools
productive_create_time_entry(date, person_id, service_id, minutes, billable_minutes?, note?, task_id?)
productive_update_time_entry(id, **fields)
productive_create_task(deal_id, title, description?, assignee_id?, due_date?)
productive_update_task(id, **fields)
productive_create_task_comment(task_id, body)

# operational
productive_health()  # returns { ok, organization_id, base_url, token_scope_hint }
```

Custom-field tools (`productive_get_custom_field`, `productive_set_custom_field_value`) are deferred to follow-up work — see Scope Boundaries.

---

## Implementation Units

- [ ] U1. **Plugin scaffolding and marketplace definition**

**Goal:** Stand up the repo as both a Claude Code plugin and a single-plugin marketplace, mirroring the Notion plugin's exact file layout so `/plugin marketplace add` + `/plugin install` work end-to-end. README is a stub here; full content lands in U6.

**Requirements:** R1, R6

**Dependencies:** None.

**Files:**
- Create: `.claude-plugin/plugin.json` (`name: "productive-workspace-plugin"`)
- Create: `.claude-plugin/marketplace.json` (`name: "productive-skill-marketplace"`)
- Create: `.mcp.json`
- Create: `README.md` (stub: install commands + "see docs/install.md for details", filled out in U6)
- Create: `LICENSE` (MIT)
- Create: `.gitignore` (ignores `.env`, `__pycache__`, `*.pyc`, `.venv/`)

**Approach:**
- `.claude-plugin/plugin.json`: `{ name: "productive-workspace-plugin", version: "0.1.0", description, author, repository, license: "MIT" }`.
- `.claude-plugin/marketplace.json`: single-entry marketplace named `productive-skill-marketplace` declaring `productive-workspace-plugin` sourced from `github:<owner>/Productive-Skill`.
- `.mcp.json`: declares one stdio MCP server named `productive`. Invocation: `command: "uvx"`, `args: ["--from", "git+https://github.com/<owner>/Productive-Skill.git#subdirectory=mcp_server", "productive-mcp"]`. The server entry-point name `productive-mcp` matches the `[project.scripts]` entry that lands in `mcp_server/pyproject.toml` in U2.
- `README.md` stub: title, one-paragraph description, install commands (`/plugin marketplace add <repo>` then `/plugin install productive-workspace-plugin@productive-skill-marketplace`), placeholder for full README content built in U6.

**Patterns to follow:**
- `~/.claude/plugins/marketplaces/notion-plugin-marketplace/.claude-plugin/plugin.json`
- `~/.claude/plugins/marketplaces/notion-plugin-marketplace/.claude-plugin/marketplace.json`
- `~/.claude/plugins/marketplaces/notion-plugin-marketplace/README.md`

**Test scenarios:**
- Test expectation: none — pure scaffolding. Verified by per-unit smoke checks during U2–U6 and final polish in U6.

**Verification:**
- `cat .claude-plugin/plugin.json | jq .name` returns `"productive-workspace-plugin"`.
- `cat .claude-plugin/marketplace.json | jq .name` returns `"productive-skill-marketplace"`.
- `.mcp.json` declares exactly one MCP server named `productive`.
- Install string `productive-workspace-plugin@productive-skill-marketplace` matches both pinned names.

---

- [ ] U2. **Build-vs-fork spike, then Productive REST client foundation**

**Goal:** Resolve the build-vs-fork question with a short, evidence-based spike, then build (or fork) the Python REST client that every tool will share — auth headers, pagination with short-circuit, 429 retry, JSON:API flattening — plus the MCP server bootstrap exposing only a `productive_health` tool.

**Requirements:** R3

**Dependencies:** U1.

**Files:**
- Create: `docs/decisions/0001-build-vs-fork-mcp-server.md` (spike findings, ≤1 page)
- Create: `mcp_server/pyproject.toml` (entry point: `productive-mcp = productive_mcp.__main__:main`)
- Create: `mcp_server/productive_mcp/__init__.py`
- Create: `mcp_server/productive_mcp/__main__.py`
- Create: `mcp_server/productive_mcp/server.py`
- Create: `mcp_server/productive_mcp/client.py`
- Create: `mcp_server/productive_mcp/formatting.py`
- Test: `mcp_server/tests/conftest.py` (vcrpy cassettes + scrubbing filter)
- Test: `mcp_server/tests/test_client.py`

**Approach:**
- **Spike first (1–2 hours):** catalogue the tool surfaces of `berwickgeek/productive-mcp` and `druellan/Productive-Simple-MCP` against the tool list under "High-Level Technical Design". Write findings into `docs/decisions/0001-build-vs-fork-mcp-server.md` covering: tool overlap %, code quality assessment, license compatibility, willingness to merge upstream, customisation cost. If overlap on one is ≥80% **and** license is compatible **and** the project is alive, fork it; otherwise build fresh. The rest of U2 below assumes the build-fresh path; the fork path collapses files to a fork branch + targeted edits.
- **Build-fresh path:**
  - Bootstrap the MCP server using the Anthropic Python MCP SDK over stdio.
  - `client.py`: `ProductiveClient` class. Reads `PRODUCTIVE_API_TOKEN` and `PRODUCTIVE_ORGANIZATION_ID` at init; raises `ConfigError` with actionable message naming the missing var if either is absent. `get(endpoint, params, max_results=None)` handles JSON:API decoding, paginates via `links.next`, **short-circuits when accumulated record count reaches `max_results`** (never fetches a page only to throw it away). `post/patch/delete` for write paths. HTTP 429 triggers exponential backoff up to 3 retries; HTTP 401/403/404/5xx surface as typed errors with the API's message body, **with `X-Auth-Token` redacted from any logged context**.
  - `formatting.py`: helpers to flatten JSON:API `data` + `included` into compact dicts so tool output stays token-cheap.
  - `server.py`: registers a single `productive_health` tool returning `{ ok: true, organization_id, base_url, token_scope_hint }` (token scope hint inferred from a HEAD/`/people/me` ping to detect read-only tokens early).
  - **Fixture scrubbing**: `conftest.py` uses `vcrpy` with a `before_record_request` filter that strips `X-Auth-Token` + `X-Organization-Id` headers, and a `before_record_response` filter that scrubs URL-embedded tokens from `links.self` fields. Cassettes are committed.

**Patterns to follow:**
- `~/.dotfiles/config/claude/skills/productive/scripts/productive_api.py` (pagination loop, with the new short-circuit modification).
- Anthropic MCP Python SDK examples (stdio transport).
- `druellan/Productive-Simple-MCP` for token-efficient JSON output shaping.

**Test scenarios:**
- Happy path: `ProductiveClient.get("/people")` returns combined `data` + `included` from a recorded multi-page cassette.
- Happy path: `formatting.flatten_jsonapi` turns a recorded response into the expected compact dict.
- Edge case: `get(..., max_results=10)` returns exactly 10 records and stops fetching after the first 10 are accumulated, even when subsequent pages exist (verified via cassette page-count assertion).
- Edge case: missing `PRODUCTIVE_API_TOKEN` raises `ConfigError` with the env var name in the message.
- Edge case: missing `PRODUCTIVE_ORGANIZATION_ID` raises `ConfigError` with the env var name in the message.
- Edge case: pagination terminates when `links.next` is absent or empty.
- Error path: HTTP 401 surfaces "check your `PRODUCTIVE_API_TOKEN`" verbatim.
- Error path: HTTP 403 with a read-only token message surfaces a "token is read-only" hint.
- Error path: HTTP 429 triggers exponential backoff up to 3 retries; persistent 429 surfaces a rate-limit error to the tool caller.
- Error path: HTTP 500 surfaces the API's error body **without** leaking the token (assert via cassette of a synthesized 500 with token in headers — token must not appear in the raised error string).
- Integration: launching `productive-mcp` (via `uvx --from .` in the test) connects over stdio and `productive_health` returns a payload containing the configured `organization_id`.

**Verification:**
- `docs/decisions/0001-build-vs-fork-mcp-server.md` exists and concludes with one of: "build fresh" or "fork <repo>".
- `pytest mcp_server/tests/` passes.
- Cassettes in `mcp_server/tests/` contain no occurrences of any real PAT (CI-style grep check, easy to run locally).
- Manual: `uvx --from ./mcp_server productive-mcp` starts and `productive_health` returns the expected payload.

---

- [ ] U3. **Read-side MCP tools**

**Goal:** Expose the read surface Claude needs for daily Productive queries: time entries, deals, services, tasks, people, companies. Custom-field tools are deferred (see Scope Boundaries).

**Requirements:** R2 (read half), R3

**Dependencies:** U2.

**Files:**
- Create: `mcp_server/productive_mcp/tools/time_entries.py`
- Create: `mcp_server/productive_mcp/tools/deals.py`
- Create: `mcp_server/productive_mcp/tools/services.py`
- Create: `mcp_server/productive_mcp/tools/tasks.py`
- Create: `mcp_server/productive_mcp/tools/people.py`
- Create: `mcp_server/productive_mcp/tools/companies.py`
- Modify: `mcp_server/productive_mcp/server.py` (register the new tools)
- Test: `mcp_server/tests/test_tools_time_entries.py`
- Test: `mcp_server/tests/test_tools_deals.py`
- Test: `mcp_server/tests/test_tools_tasks.py`

**Approach:**
- Each tool is a thin function over `ProductiveClient.get` with JSON-schema input validation and `formatting.flatten_jsonapi` output.
- Naming: `productive_search_time_entries`, `productive_list_deals`, `productive_get_deal`, `productive_list_services`, `productive_list_tasks`, `productive_list_people`, `productive_list_companies`.
- Every list tool accepts `max_results` (default 50, hard cap 500) so Claude can self-cap output. The cap is enforced via the client's pagination short-circuit, not by post-fetch truncation.
- Tools accept structured filter objects, not raw query strings — the function builds `filter[...]` params internally.

**Patterns to follow:**
- Existing skill's include-and-resolve example for time entries (`scripts/fetch_time_entries.py`).

**Test scenarios:**
- Happy path: `productive_search_time_entries(after="2026-04-01", before="2026-04-30")` returns a list of compact entries with `date`, `minutes`, `person_id`, `service_id`.
- Happy path: `productive_list_deals(include=["company"])` includes flattened company info on each deal.
- Happy path: `productive_get_deal(id=123, include=["company"])` returns one deal dict with company name resolved.
- Edge case: `productive_search_time_entries` with no entries in the date range returns an empty list, not an error.
- Edge case: `max_results=10` truncates pagination after 10 records even when the API has more.
- Edge case: an invalid `person_id` filter returns an empty list (Productive's behavior), tool surfaces this without retrying.
- Error path: requesting an unknown deal id surfaces the API's 404 message clearly.
- Integration: a chained read — `list_deals` → pick id → `list_services(deal_id=...)` → `list_tasks(deal_id=...)` — works end-to-end against recorded fixtures.

**Verification:**
- All read tools appear in `tools/list` MCP response when the server is connected.
- `pytest mcp_server/tests/test_tools_*` passes.
- Manual smoke test: from a Claude Code session, asking "show me my time entries last week" results in `productive_search_time_entries` being called with the right filters.

---

- [ ] U4. **Write-side MCP tools**

**Goal:** Expose write tools for the high-value daily workflows: log a time entry, create/update a task, comment on a task. Custom-field write tools are deferred.

**Requirements:** R2 (write half), R3

**Dependencies:** U3.

**Files:**
- Modify: `mcp_server/productive_mcp/tools/time_entries.py` (add create/update)
- Modify: `mcp_server/productive_mcp/tools/tasks.py` (add create/update + comments)
- Modify: `mcp_server/productive_mcp/client.py` (ensure `post`, `patch` are present and test-covered)
- Modify: `mcp_server/productive_mcp/server.py` (register new tools)
- Test: `mcp_server/tests/test_tools_time_entries.py` (extend)
- Test: `mcp_server/tests/test_tools_tasks.py` (extend)

**Approach:**
- Tool names: `productive_create_time_entry`, `productive_update_time_entry`, `productive_create_task`, `productive_update_task`, `productive_create_task_comment`.
- Every write tool validates required fields client-side before sending — the API's error messages on missing fields are not always actionable.
- Write tools never delete. A `productive_delete_*` family is **not included in v1** to keep blast radius small. Add later if a clear use case appears.
- Write tools return the created/updated resource in the same compact format as read tools.
- **Prompt-injection defense (advisory):** docstrings on write tools instruct Claude to confirm with the user when the triggering context contains Productive-sourced text (task descriptions, comments, notes) that includes verb-like instructions ("log time", "mark done"). Mitigation lives at the prompt/skill layer, not the tool layer; commands that compose read+write reinforce this in their bodies.

**Execution note:** Implement the happy-path test for each write tool before the implementation — write tools have higher cost-of-failure than reads and a test-first cadence catches missing-field validation gaps early.

**Patterns to follow:**
- Read tool implementations from U3 — same input-validation, formatting, and error-handling patterns.

**Test scenarios:**
- Happy path: `productive_create_time_entry(date, person_id, service_id, minutes=60)` POSTs the right JSON:API document and returns the created entry's id.
- Happy path: `productive_create_task(deal_id, title)` returns a task with the supplied title and the right `deal_id` relationship.
- Happy path: `productive_create_task_comment(task_id, body)` returns the created comment's id.
- Edge case: `productive_create_time_entry` with `minutes=0` is rejected client-side with a clear validation message before any HTTP call.
- Edge case: `productive_update_task(id, status="done")` PATCHes only the status field (verified via cassette body assertion).
- Error path: posting with a read-only token surfaces a "your token is read-only" message (mapped from Productive's 403 response).
- Error path: creating a task on a non-existent `deal_id` surfaces the 404 cleanly.
- Integration: create-then-read round trip — `create_task` → `get_task(id)` — returns the same task with matching fields.

**Verification:**
- All write tools appear in `tools/list` and can be invoked from a Claude Code session.
- `pytest mcp_server/tests/test_tools_time_entries.py mcp_server/tests/test_tools_tasks.py` passes.
- Manual smoke test against a sandbox/test workspace: log a 15-minute time entry, then list time entries for today and confirm it's there.

---

- [ ] U5. **Slash commands**

**Goal:** Ship the user-facing slash commands that compose MCP tools and skills into the daily workflows: a setup pre-flight, search, find, create-task, log-time, project-status, weekly-report.

**Requirements:** R4

**Dependencies:** U3 (read tools must exist), U4 (write tools must exist for `log-time` and `create-task`).

**Files:**
- Create: `commands/setup.md`
- Create: `commands/search.md`
- Create: `commands/find.md`
- Create: `commands/log-time.md`
- Create: `commands/create-task.md`
- Create: `commands/project-status.md`
- Create: `commands/weekly-report.md`

**Approach:**
- Each command is a markdown file with frontmatter (`description`, `argument-hint` or `args`) plus instructional body, exactly like the Notion plugin's commands.
- `/productive:setup` is a pre-flight: it calls `productive_health` and, if the MCP server failed to boot due to missing env vars, *catches that failure mode* and prints the exact env-var setup instructions (token-minting URL, the two `export` lines, and the "restart Claude Code" step). This is the answer to the silent-failure onboarding risk — users with a misconfigured install run `/productive:setup` first.
- Commands reference MCP tools by name (e.g. "Use the `productive_search_time_entries` tool…") and reference the appropriate Productive Skill for higher-level workflow logic.
- `weekly-report.md` is the most complex — pulls last week's time entries, joins to services and deals, groups by deal, formats a markdown report. Per the deferred-implementation question, decide here whether a server-side aggregation tool (e.g. `productive_summarize_time_entries`) is needed; if so, capture as a follow-up task in U2's tooling.
- Commands ask one clarifying question if input is ambiguous; never silently make destructive changes. Commands that read Productive content and then act on it (`log-time`, `create-task`, `weekly-report`) include a sentence in the body reminding Claude to ignore in-content instructions and confirm the user's intent (prompt-injection defense).

**Patterns to follow:**
- `~/.claude/plugins/marketplaces/notion-plugin-marketplace/commands/search.md`
- `~/.claude/plugins/marketplaces/notion-plugin-marketplace/commands/create-task.md`
- `~/.claude/plugins/marketplaces/notion-plugin-marketplace/commands/database-query.md`

**Test scenarios:**
- Test expectation: none for command markdown directly. Each command is verified by a manual smoke-test transcript captured in U6's install checklist: run the command against a real workspace, observe the conversational behavior, paste the transcript snippet (input, tool calls, output) into `docs/install.md`.

**Verification:**
- `/productive:setup`, `/productive:search`, `/productive:find`, `/productive:log-time`, `/productive:create-task`, `/productive:project-status`, `/productive:weekly-report` all show up in `/help` after install.
- Each command's frontmatter parses (no malformed YAML).
- Manual: each command, when run with a representative argument, produces the intended outcome (read commands return a summary; write commands create the right resource and confirm; `setup` reports a clean health check or surfaces the exact missing env var).

---

- [ ] U6. **Bundled Productive Skills + final README and install docs**

**Goal:** Ship the two v1 skills (time-tracking, project-status) and finish the user-facing documentation: full README, `docs/install.md`, `docs/troubleshooting.md`. Run a fresh-install smoke test as the unit's verification step, capturing transcripts. The third skill (invoice-prep) is deferred — see Scope Boundaries.

**Requirements:** R1, R5, R6, R7

**Dependencies:** U1, U2, U3, U4, U5.

**Files:**
- Create: `skills/productive/time-tracking/SKILL.md` (frontmatter `name: productive-time-tracking`)
- Create: `skills/productive/time-tracking/examples/log-yesterday.md`
- Create: `skills/productive/time-tracking/examples/fill-gaps.md`
- Create: `skills/productive/project-status/SKILL.md` (frontmatter `name: productive-project-status`)
- Create: `skills/productive/project-status/reference/status-report-format.md`
- Modify: `README.md` (full content: features, install, uv prereq, PAT minting walkthrough, commands table, skills table, troubleshooting link, credits)
- Create: `docs/install.md` (fresh-install smoke checklist + transcripts)
- Create: `docs/troubleshooting.md` (env var issues, `uv`-not-found, 401/403, rate limits, fallback `pip install -e` flow)

**Approach:**
- **Skills.** `time-tracking/SKILL.md`: when to log time, how to fill gaps in a week, how to detect missing entries, how to handle billable vs non-billable, how to attach time to the right service. `project-status/SKILL.md`: how to summarize a deal — pull deal + services + tasks + recent time entries, group by service, surface budget burn if visible, format as a status report. Both skills follow the Notion plugin's `SKILL.md` structure: frontmatter (`name`, `description`), Quick Start, Workflow, Common Issues, Examples links. Frontmatter `name` values are namespaced (`productive-time-tracking`, `productive-project-status`) so they cannot collide with the user's existing personal `productive` skill (R7).
- **README.** Mirror the Notion plugin's README structure: Features, Install (3 steps + `uv` prereq note), Authentication (PAT minting), Configuration (env var reference), Commands table, Skills table, Troubleshooting link, Credits.
- **Install doc.** Fresh-install smoke checklist plus pasted transcripts from each command (`setup`, `search`, `find`, `log-time`, `create-task`, `project-status`, `weekly-report`) run against a real workspace. Each transcript snippet is short — input, tool calls observed, summary output.
- **Troubleshooting doc.** Env-var-missing failure, `uv: command not found` failure, read-only-token 403, 429 rate limits, fallback `pip install -e mcp_server/` + manual `python -m productive_mcp` invocation in `.mcp.json`.
- **R7 verification.** Confirm the existing `~/.dotfiles/config/claude/skills/productive` skill still triggers and runs alongside the plugin without conflict.

**Patterns to follow:**
- `~/.claude/plugins/marketplaces/notion-plugin-marketplace/skills/notion/knowledge-capture/SKILL.md`
- `~/.claude/plugins/marketplaces/notion-plugin-marketplace/skills/notion/research-documentation/SKILL.md`
- `~/.claude/plugins/marketplaces/notion-plugin-marketplace/README.md`

**Test scenarios:**
- Each `SKILL.md` parses with valid frontmatter, namespaced `name`, and a clear `description`.
- Both skills appear in the available-skills list when the plugin is installed.
- Integration: fresh install on a machine with no prior Productive plugin state — `/plugin marketplace add <repo>` → `/plugin install productive-workspace-plugin@productive-skill-marketplace` → restart → `/productive:setup` → all commands run successfully against a real workspace.
- Edge case: install with `PRODUCTIVE_API_TOKEN` unset — `/productive:setup` surfaces the exact missing-env-var error with actionable next steps; `/help` still surfaces commands.
- Edge case: install with a read-only token — read commands work; write commands surface the "your token is read-only" error from U4 cleanly.
- Edge case: install on a machine without `uv` — `/productive:setup` surfaces a "uv not found" hint pointing to `docs/troubleshooting.md`.
- Integration (R7): existing `~/.dotfiles/config/claude/skills/productive` still triggers and runs alongside the plugin without conflict (verified by asking "show my time entries last week" both before and after plugin install — output should be equivalent).

**Verification:**
- `docs/install.md` smoke checklist is fully green and contains transcripts for every command.
- README's "five minutes to first call" path is followed literally by someone who hasn't seen the repo before (the user, on a clean machine or with `unset PRODUCTIVE_API_TOKEN`).
- A grep for any real PAT against the entire repo returns nothing.

---

## System-Wide Impact

- **Interaction graph:** Three call layers — slash commands → skills (instructional) → MCP tools (effectful) → Productive REST API. Skills do not call each other directly; commands may invoke multiple skills' guidance via the conversational layer.
- **Error propagation:** REST errors (401, 403, 404, 429, 5xx) are mapped to actionable tool errors at `client.py`; tools surface them verbatim to Claude; commands convert tool errors into user-facing prose. The token must never appear in any error path or any logged context.
- **State lifecycle risks:** Write tools have no rollback. A failed `create_time_entry` halfway through a batch leaves earlier entries in place. Commands that loop over creates must track per-iteration success and report partial completions.
- **API surface parity:** Read and write tools must follow the same naming, input-shape, and output-shape conventions so Claude can compose them predictably. A change to one resource's tool shape forces a sweep across all resource modules.
- **Integration coverage:** Unit tests with vcrpy cassettes will not catch API-shape drift. U6's manual smoke tests against a real workspace are load-bearing and need to be repeated whenever the Productive API version changes.
- **Unchanged invariants:**
  - The user's existing `~/.dotfiles/config/claude/skills/productive` skill (frontmatter `name: productive`) must keep working unchanged during plugin development (R7). The plugin's bundled skills use namespaced frontmatter `name` values (`productive-time-tracking`, `productive-project-status`) so Claude Code's skill loading (which resolves by frontmatter `name`, not directory path) cannot collide.
  - The plugin's MCP server uses environment variables (`PRODUCTIVE_API_TOKEN`, `PRODUCTIVE_ORGANIZATION_ID`); the personal skill hardcodes its token in a Python script. There is no env-var collision; both can coexist indefinitely.
  - No file in the personal-skill directory tree is read or modified by the plugin.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Token leakage via logs, errors, or test fixtures | `client.py` redacts `X-Auth-Token` and `X-Organization-Id` from any logged context; tests use `vcrpy` with `before_record_request`/`before_record_response` filters that strip those headers and scrub URL-embedded tokens from `links.self`; cassettes are committed only after the scrubbing filter is in place; U6's verification grep for any real PAT against the repo is a hard gate. |
| Prompt injection from Productive content into write tools | Write-tool docstrings instruct Claude to confirm with the user when triggering context contains Productive-sourced text with verb-like instructions; commands that compose read+write reinforce this in their bodies; the `weekly-report` and `project-status` commands do not call write tools at all. |
| Supply-chain risk of public OSS plugin holding a high-privilege PAT | README documents pinning to a release tag (or a known commit SHA in `.mcp.json`'s `git+` URL) instead of `HEAD`; deferred work item adds release signing once 1.0 ships; users are advised to use a read-only token for evaluation runs. |
| Rate-limit thrashing under heavy use | 429 retry with exponential backoff in `client.py` (cap 3 retries); commands aggregate inside the tool when result sets are large; reports endpoints (tighter limit) deferred to v2; troubleshooting doc covers what the user sees when the limiter trips. |
| Productive API JSON:API shape drift | vcrpy cassettes make breakage visible at test time; U6's manual smoke tests catch shape changes cassettes don't; client validation is liberal-on-input, strict-on-output. |
| Write operations doing the wrong thing (e.g. logging time on the wrong day) | Write tools require explicit fields (no defaults that could pick the wrong service or person); commands ask one clarifying question on ambiguity; no v1 delete tools. |
| MCP server failing to start silently breaks all Productive commands | `/productive:setup` slash command runs `productive_health` and surfaces missing-env-var, `uv`-not-found, and 401 errors as actionable text; users hit setup before any other command in the README's onboarding flow; troubleshooting doc covers each failure mode. |
| `uv` not on PATH on a fresh user's machine | README pins `uv` as a one-time prereq with a `brew install uv` line; troubleshooting doc documents a fallback `pip install -e mcp_server/` path with the alternate `.mcp.json` shape; consider rewriting the server in Node/TS in a future major version if `uv` adoption blocks users. |
| Existing personal Productive skill breaks during plugin development | Plugin's bundled skills use namespaced frontmatter `name` values (`productive-time-tracking`, `productive-project-status`) so the dotfile skill (`name: productive`) keeps loading; R7 explicitly tested in U6. |
| Confusion between two Productive integrations after install | README's "Migration from the personal skill" section explains coexistence; deferred work item to consolidate once plugin is feature-equivalent. |

---

## Documentation / Operational Notes

- **README sections required:** Features, Install (3 steps mirroring the Notion plugin), Authentication (PAT minting walkthrough with link to Productive's PAT docs), Configuration (env var reference), Commands (table mirroring the Notion plugin's), Skills (one-line description each), Troubleshooting (link to `docs/troubleshooting.md`), Credits.
- **No CI in v1.** Tests run locally with `pytest`. Add CI when there's a second contributor or before publishing 1.0.
- **Versioning:** start at `0.1.0`; bump to `0.2.0` for additive features, `0.x.0` until the API is stable.
- **License:** MIT, matching the Notion plugin and most Anthropic plugin examples.

---

## Review Findings Integrated (2026-04-27 deepening)

The post-write confidence check ran five reviewer agents (coherence, feasibility, scope, security, adversarial). Findings classified as high-confidence corrections were integrated directly into this plan; the remaining open strategic question is surfaced below for the user.

**Integrated:**
- **Coherence:** dropped the `productive_write_*` umbrella prefix language; pinned marketplace name to `productive-skill-marketplace` and plugin name to `productive-workspace-plugin`; replaced "projects/deals" with "deals" everywhere; clarified slash-command (`/productive:`) vs MCP tool (`productive_`) namespaces.
- **Feasibility:** changed `.mcp.json` invocation to `uvx --from git+...` with `uv` documented as a prereq (avoids the zero-runtime trap); added pagination short-circuit semantics so `max_results` is enforced during pagination, not after; pinned skill frontmatter `name` values to `productive-time-tracking` / `productive-project-status` to prevent collision with the dotfile skill.
- **Scope:** dropped the `invoice-prep` skill (no v1 commands back it); dropped custom-fields tools (no v1 use case); folded `ratelimit.py` into `client.py`; restructured U7 — smoke testing and final docs now land in U6 alongside skills, eliminating the standalone "publish + verify" unit.
- **Security:** specified `vcrpy` with explicit `before_record_*` filters for fixture scrubbing; added prompt-injection defense at the write-tool docstring + command-body layer; added supply-chain mitigation (pin to release tag/SHA, deferred release signing).
- **Adversarial / build-vs-fork:** removed the from-scratch assertion. U2 now starts with a 1–2 hour spike that catalogues `berwickgeek/productive-mcp` and `druellan/Productive-Simple-MCP` against this plan's tool surface and writes findings to `docs/decisions/0001-build-vs-fork-mcp-server.md`. The implementer follows whichever path the spike justifies.
- **Onboarding failure mode:** added a `/productive:setup` slash command (U5) that catches the env-var-missing failure mode and surfaces actionable next steps, rather than letting users hit an opaque "MCP server failed to start" error.

**Open strategic question for the user (does not block planning):**
- The adversarial reviewer pointed out that the three v1 skills were guesses without a Productive Cookbook lineage equivalent to Notion's. The plan now ships only two skills (time-tracking, project-status) and defers invoice-prep. If the user wants to validate skill content with real Productive workflow material before U6, that's a useful sequencing detour — but it's not a blocker.

---

## Sources & References

- Notion plugin (architectural template): https://github.com/makenotion/claude-code-notion-plugin
- Productive Developer Documentation: https://developer.productive.io/
- Productive PAT minting: https://help.productive.io/en/articles/5440689-api-access
- Productive Custom Fields: https://developer.productive.io/custom_fields.html
- Existing personal Productive skill: `~/.dotfiles/config/claude/skills/productive/`
- Reference community MCPs (not bundled): `berwickgeek/productive-mcp`, `druellan/Productive-Simple-MCP`
- Anthropic Python MCP SDK (entry-point and stdio patterns to be pinned during U2)
