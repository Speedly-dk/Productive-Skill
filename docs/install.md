# Install & smoke-test checklist

This is the canonical "five minutes to first call" walkthrough plus a checklist you can use to verify a fresh install end-to-end.

## Prerequisites

- Claude Code installed and authenticated.
- A Productive.io account with permission to mint a Personal Access Token.
- macOS, Linux, or WSL (Windows native is not currently exercised).

## One-time setup

### 1. Install `uv`

```bash
# macOS
brew install uv

# Linux / WSL
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Confirm:

```bash
uv --version
# uv 0.10.x (or newer)
```

### 2. Mint a Productive Personal Access Token

1. Visit <https://app.productive.io/settings/api-token>.
2. Click **Create token**.
3. Pick **read-write** scope unless you only want the read commands.
4. Copy the token. You won't see it again.

### 3. Find your Organization ID

In Productive's URL, the path looks like `/organizations/12345/...`. The number is your organization id. You can also find it in **Settings → API → Organization ID**.

### 4. Export env vars

Add to `~/.zshrc` (or your shell's profile equivalent):

```bash
export PRODUCTIVE_API_TOKEN="your-token-here"
export PRODUCTIVE_ORGANIZATION_ID="12345"
```

Reload your shell (`exec $SHELL -l` or open a new terminal).

### 5. Add the plugin marketplace and install

In Claude Code:

```text
/plugin marketplace add Speedly-dk/Productive-Skill
/plugin install productive-workspace-plugin@productive-skill-marketplace
```

Restart Claude Code so it picks up the new MCP server and the env vars.

## Smoke checklist

After install, walk through these in order. Each should produce the noted outcome.

### ✅ `/productive:setup`

- **Expected:** A success report with `ok: true`, your `organization_id`, the Productive API base URL, and `token_scope_hint: valid`.
- **If you see `ok: false`:** the error message tells you what's wrong (token, org id, or network). See [`troubleshooting.md`](troubleshooting.md).
- **If the tool isn't available at all:** the MCP server didn't start. Most common cause: env vars weren't set before Claude Code launched. Set them, restart Claude Code, retry.

### ✅ `/productive:find Acme`

- **Expected:** A short list of deals/companies whose name matches "Acme" (or "no matches" if none — try one of your real client names instead).

### ✅ `/productive:search time entries last week`

- **Expected:** A summary of last week's time entries, grouped by deal or service. Empty is fine if you didn't log anything; an error is not.

### ✅ `/productive:project-status <a deal you know>`

- **Expected:** A markdown report with deal header, services, open tasks, and recent time activity. Should land in under a few seconds for a typical deal.

### ✅ `/productive:weekly-report`

- **Expected:** Last week's hours grouped by deal. Aggregated; no raw entry rows in the response.

### ✅ `/productive:log-time` *(skip if your token is read-only)*

- Run `/productive:log-time 15min on <some deal> testing the plugin install`.
- **Expected:** Claude resolves the deal and service, asks for confirmation, then creates the entry. Verify the entry exists in Productive's UI.
- **Cleanup:** delete the test entry from Productive's UI when you're satisfied.

### ✅ Existing personal `productive` skill still works

If you also have `~/.claude/skills/productive/SKILL.md`, ask Claude something it would normally trigger ("show me my time entries from last month"). Both skills should continue to work — the plugin's bundled skills use namespaced names (`productive-time-tracking`, `productive-project-status`) so they don't collide.

## When everything is green

Capture a copy of this checklist with timestamps and your environment (Claude Code version, OS, `uv` version) the first time it goes green on a clean machine. That artifact is the v0.1.0 release sign-off.
