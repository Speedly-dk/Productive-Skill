# Troubleshooting

When something doesn't work, run `/productive:setup` first. Most failure modes surface cleanly there. The rest of this document covers what to do when they don't.

## "Tool `productive_health` is not available"

**Cause:** The MCP server didn't start.

**Most likely reason:** the env vars weren't set when Claude Code launched. The server validates `PRODUCTIVE_API_TOKEN` and `PRODUCTIVE_ORGANIZATION_ID` at boot and exits with a clear message if either is missing — but you only see that message in the launcher's stderr, which Claude Code may not surface.

**Fix:**

1. Confirm both vars are exported in your shell:

   ```bash
   echo "$PRODUCTIVE_API_TOKEN" "$PRODUCTIVE_ORGANIZATION_ID"
   ```

2. Make sure they're in your shell profile (`~/.zshrc`, `~/.bashrc`, etc.) so future shells inherit them.
3. Restart Claude Code so it picks up the env.

**Other possible causes:**

- `uv` not on `PATH` (see below).
- Network blocked GitHub on the first `uvx --from git+...` resolve. Try running the command manually:

  ```bash
  uvx --from git+https://github.com/Speedly-dk/Productive-Skill.git#subdirectory=mcp_server productive-mcp
  ```

  The first run downloads and builds the package; subsequent runs are cached. If this fails, fix network/auth there first.

## "uv: command not found"

The MCP server is launched via `uvx`. Install `uv`:

```bash
# macOS
brew install uv

# Linux / WSL
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your shell so the new binary is on `PATH`. Confirm:

```bash
uv --version
```

If you really cannot install `uv` (corporate-managed machine, etc.), see "Fallback: pip-based install" below.

## "Productive returned 401 Unauthorized"

The token is wrong, expired, or for a different organization.

1. Mint a fresh token at <https://app.productive.io/settings/api-token>.
2. Update `PRODUCTIVE_API_TOKEN` in your shell profile.
3. Restart Claude Code.

If you have multiple Productive organizations, double-check that `PRODUCTIVE_ORGANIZATION_ID` matches the organization the token belongs to.

## "Productive returned 403: your token appears to be read-only"

You tried to call a write tool (`productive_create_*`, `productive_update_*`) with a read-only token.

Either:

- Mint a read-write Personal Access Token and replace `PRODUCTIVE_API_TOKEN`, **or**
- Stick to read-only commands (`/productive:search`, `/productive:find`, `/productive:project-status`, `/productive:weekly-report`).

## "Productive rate limit hit and retries exhausted"

The client retries HTTP 429 with exponential backoff up to 3 times before surfacing this error. Usually it means a single command pulled a lot of data — for example, a `weekly-report` over a quarter, or a `project-status` over a deal with thousands of time entries.

**Workarounds:**

- Narrow the date range. `weekly-report` defaults to last week; if you asked for a year, ask for a month instead and chain several calls.
- Wait 30 seconds and retry — the rate-limit window slides.

## "Productive returned 404"

The id you (or Claude) used doesn't exist in your organization. Two common cases:

- **Wrong organization** — check `PRODUCTIVE_ORGANIZATION_ID` is the org that contains the resource.
- **Bad id from a stale conversation** — start a fresh search rather than reusing an id from earlier in the conversation if the workspace state may have changed.

## Fallback: pip-based install (without `uv`)

If you can't install `uv`, you can run the MCP server with the standard Python toolchain:

```bash
git clone https://github.com/Speedly-dk/Productive-Skill.git
cd Productive-Skill
python -m venv .venv
source .venv/bin/activate
pip install -e mcp_server/
```

Then change your `.mcp.json` (or the plugin's installed copy) to:

```json
{
  "mcpServers": {
    "productive": {
      "command": "/absolute/path/to/Productive-Skill/.venv/bin/productive-mcp",
      "env": {
        "PRODUCTIVE_API_TOKEN": "${PRODUCTIVE_API_TOKEN}",
        "PRODUCTIVE_ORGANIZATION_ID": "${PRODUCTIVE_ORGANIZATION_ID}"
      }
    }
  }
}
```

This is brittle (the absolute path won't move with the repo) — prefer the `uvx` invocation when you can.

## Still stuck?

Open an issue at <https://github.com/Speedly-dk/Productive-Skill/issues> with:

- Output of `/productive:setup`
- Your `uv --version` (if installed)
- Your Claude Code version (`/version` or About dialog)
- Whether the personal `productive` skill (if any) still works

Don't paste your `PRODUCTIVE_API_TOKEN` into an issue — the plugin scrubs it from error messages before they surface, but a screenshot of your shell profile would defeat that.
