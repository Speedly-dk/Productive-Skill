# Productive Plugin for Claude Code

A Claude Code plugin that bundles a local Productive.io MCP server, slash commands, and skills for working with [Productive.io](https://productive.io) — time tracking, projects/deals, services, tasks, people, and companies.

> **Status:** v0.1.0 foundation in progress. See [`docs/plans/`](docs/plans/) for the implementation plan.

---

## Install

> Full install instructions land alongside v0.1.0 in `docs/install.md`. Stub steps below.

```bash
# 1. Add this plugin's marketplace
/plugin marketplace add Speedly-dk/Productive-Skill

# 2. Install the plugin
/plugin install productive-workspace-plugin@productive-skill-marketplace

# 3. Restart Claude Code
```

You also need:

- `uv` on your `PATH` (the MCP server is launched via `uvx`).
  - macOS: `brew install uv`
- A Productive Personal Access Token and your Organization ID, exported as:
  - `PRODUCTIVE_API_TOKEN`
  - `PRODUCTIVE_ORGANIZATION_ID`

After install, run `/productive:setup` to verify the MCP server can talk to Productive.

---

## License

[MIT](LICENSE)
