---
description: Verify the Productive MCP server is connected and the environment is configured. Run this first after install.
---

You are running a pre-flight check for the Productive plugin.

Steps:

1. Call the `productive_health` MCP tool with no arguments.
2. Interpret the response:
   - **`{"ok": true, ...}`** — confirm to the user with the configured `organization_id`, the API base URL, the version, and the `token_scope_hint`. Tell them they're ready to use the other `/productive:*` commands.
   - **`{"ok": false, "error": "...PRODUCTIVE_API_TOKEN..."}` or similar** — the MCP server reached `productive_health` but Productive rejected the request. Most likely causes: an invalid token, a wrong organization id, or a token from a different workspace. Surface the error verbatim, then point the user to:
     - Mint a Personal Access Token at https://app.productive.io/settings/api-token
     - Confirm their organization id from the Productive URL or settings page
     - Export both vars, then restart Claude Code

3. **If the `productive_health` tool is not available at all** (e.g. Claude reports "no such tool" or the MCP server failed to start), the most likely cause is missing environment variables before Claude Code launched. Walk the user through:

   ```bash
   export PRODUCTIVE_API_TOKEN=<your token>
   export PRODUCTIVE_ORGANIZATION_ID=<your org id>
   ```

   Tell them to add those exports to their shell profile (`~/.zshrc` or equivalent) and restart Claude Code so the MCP server picks them up. Also remind them `uv` must be on `PATH` (`brew install uv` on macOS).

Keep the response short and action-oriented — this is the first command a new user sees, so clarity matters more than breadth.
