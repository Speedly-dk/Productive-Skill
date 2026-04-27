# Productive Plugin for Claude Code

A Claude Code plugin that bundles a local [Productive.io](https://productive.io) MCP server, slash commands, and skills for time tracking, project status, and the rest of the daily Productive workflow.

This plugin gives Claude first-class tools for Productive: log time, query deals and services, create and update tasks, summarise a project, and produce a weekly time report — all without leaving your editor.

> **Status:** v0.1.0 foundation. The MCP server, all 13 read/write tools, the seven slash commands, and two skills are in place. Real-workspace smoke testing happens once you publish to the `Speedly-dk` GitHub org.

---

## Features

### Local Productive MCP server (Python, stdio)

Exposes 13 native MCP tools across the daily Productive surface:

| Resource | Tools |
|---|---|
| Time entries | `productive_search_time_entries`, `productive_create_time_entry`, `productive_update_time_entry` |
| Deals | `productive_list_deals`, `productive_get_deal` |
| Services | `productive_list_services` |
| Tasks | `productive_list_tasks`, `productive_create_task`, `productive_update_task`, `productive_create_task_comment` |
| People | `productive_list_people` |
| Companies | `productive_list_companies` |
| Operational | `productive_health` |

Pagination short-circuits at the requested `max_results`, HTTP 429 triggers exponential backoff with up to 3 retries, and your `PRODUCTIVE_API_TOKEN` is scrubbed from any error message that surfaces to Claude.

### Slash commands

| Command | Description |
|---|---|
| `/productive:setup` | Pre-flight: verify the MCP server is connected and your env is configured. Run this first. |
| `/productive:search` | Natural-language query across the read tools. |
| `/productive:find` | Quick lookup by name (deal, task, person, company). |
| `/productive:log-time` | Log a time entry with name-to-id resolution and a confirmation step. |
| `/productive:create-task` | Create a task on a deal, with assignee and due-date resolution. |
| `/productive:project-status` | Roll up a deal's services, open tasks, and recent time activity. |
| `/productive:weekly-report` | Last week's hours grouped by deal, with billable splits and gap flagging. |

### Skills

| Skill | What it teaches Claude |
|---|---|
| `productive-time-tracking` | When and how to log, fill gaps, audit, and fix time entries. |
| `productive-project-status` | How to produce a clean, scannable project status report. |

---

## Install

### 1. Add the marketplace

```bash
/plugin marketplace add Speedly-dk/Productive-Skill
```

### 2. Install the plugin

```bash
/plugin install productive-workspace-plugin@productive-skill-marketplace
```

### 3. Install `uv` (one-time prerequisite)

The MCP server is launched via `uvx`, which is part of [`uv`](https://github.com/astral-sh/uv).

```bash
# macOS
brew install uv

# Linux / other
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 4. Set environment variables

You need a Productive Personal Access Token and your Organization ID.

Mint a PAT at <https://app.productive.io/settings/api-token>. Choose **read-write** scope unless you only want read commands. Find your Organization ID in the Productive URL after you log in (it's the number after `/organizations/` or visible in **Settings → API**).

Add these to your shell profile (`~/.zshrc`, `~/.bashrc`, or equivalent):

```bash
export PRODUCTIVE_API_TOKEN="your-token-here"
export PRODUCTIVE_ORGANIZATION_ID="your-org-id"
```

### 5. Restart Claude Code

So the MCP server picks up the new env vars.

### 6. Verify

```text
/productive:setup
```

You should see your organization id, the API base URL, and a green health-check confirmation. If anything looks off, see [`docs/troubleshooting.md`](docs/troubleshooting.md).

---

## Configuration

| Variable | Required | Notes |
|---|---|---|
| `PRODUCTIVE_API_TOKEN` | Yes | Personal Access Token from Productive's API settings page. |
| `PRODUCTIVE_ORGANIZATION_ID` | Yes | Numeric organization id (visible in Productive's URLs and settings). |
| `PRODUCTIVE_USER_ID` | No | Your own person id. Lets `log-time` and similar commands default to "the current user" without an extra lookup. |

The MCP server reads these from the environment at launch and never persists them. The plugin's `.gitignore` excludes `.env` files so a stray local override won't accidentally commit.

---

## Migration from the personal `productive` skill

If you previously used a personal Productive skill at `~/.claude/skills/productive/` (or symlinked from a dotfile repo), this plugin coexists with it:

- The plugin's bundled skills use namespaced frontmatter names (`productive-time-tracking`, `productive-project-status`), so they don't collide with `name: productive` from a personal skill.
- The plugin's MCP server reads from `PRODUCTIVE_API_TOKEN` / `PRODUCTIVE_ORGANIZATION_ID` env vars; the personal skill typically hardcoded its token in a Python script.

You can run both for a few weeks while you decide whether the plugin replaces the dotfile skill entirely.

---

## License

[MIT](LICENSE)

---

## Credits

- **Plugin specification** by Anthropic.
- **Productive.io REST API** — see [developer.productive.io](https://developer.productive.io/).
- Inspired by the [Notion plugin for Claude Code](https://github.com/makenotion/claude-code-notion-plugin) — same shape, adapted to the fact that Productive has no hosted MCP server.
