# Cross-harness agent registration

This plugin keeps **canonical agent definitions** in:

- `geeky-orchestration/agents/*.md`

Because Codex, Claude, Copilot, and Cursor use different discovery paths and/or schemas, we project these canonical files into harness-specific locations.

## Sync command

Two equivalent implementations ship side-by-side — use whichever runtime is available:

**Python (3.8+, no dependencies):**
```bash
python scripts/sync-agents.py
```

**Node.js (any modern version, no dependencies):**
```bash
node scripts/sync-agents.js
```

Both accept the same flags:

```bash
# preview only
python scripts/sync-agents.py --dry-run
node   scripts/sync-agents.js --dry-run

# subset of targets
python scripts/sync-agents.py --targets claude,copilot,codex
node   scripts/sync-agents.js --targets claude,copilot,codex

# scoped projection
python scripts/sync-agents.py --agents geeky-orchestrator
node   scripts/sync-agents.js --agents geeky-orchestrator

# harness-neutral fallback
python scripts/sync-agents.py --targets generic --agents geeky-orchestrator
node   scripts/sync-agents.js --targets generic --agents geeky-orchestrator

# explicit project root
python scripts/sync-agents.py --project-root "C:/path/to/repo"
node   scripts/sync-agents.js --project-root "C:/path/to/repo"

# machine-readable output
python scripts/sync-agents.py --json
node   scripts/sync-agents.js --json
```

## Installed-cache use

Both sync scripts default to the current working directory, independent of where the plugin is installed. Run from the intended project root, or pass `--project-root` explicitly. Use `--dry-run --json` first and inspect every output path. Limit `--agents` and `--targets` to the definitions being updated; preserve custom user definitions.

For Codex, parse the resulting TOML and check the live role catalog. File generation alone does not prove runtime registration. Use the exact callable role name; do not repeatedly try namespaced guesses after an unavailable-role error. If a valid projection is absent from the catalog, inspect harness diagnostics and verify discovery in a fresh session before claiming it is fixed. Task dispatch may use the canonical-instructions fallback in the execution protocol unless the user requires that registered role.

## Generated outputs

Default output paths (relative to `--project-root`):

- Claude: `.claude/agents/<name>.md`
- Copilot/VS Code: `.github/agents/<name>.agent.md`
- Codex CLI: `.codex/agents/<name>.toml`
- Cursor (best effort): `.cursor/agents/<name>.md`
- Generic Markdown: `.agents/<name>.md`

## Harness notes

### Claude Code

- Supports markdown subagent definitions with YAML frontmatter.
- Plugin `agents/` is already a valid source for plugin-provided subagents.
- Projection into `.claude/agents/` is still useful when you want workspace-local overrides or testing outside plugin packaging.

### Codex CLI

- Custom agents are TOML files under `.codex/agents/` (project) or `~/.codex/agents/` (user).
- Required fields are emitted by the sync script:
  - `name`
  - `description`
  - `developer_instructions`

Codex resolves a role by its TOML `name`, not the filename. Keep names unique within a scope and match filenames to names. Check both user and workspace definitions when a role is missing or behaves differently.

Custom subagents inherit the parent provider. A `model_provider` setting in an agent file does not override it; selecting a third-party model there can still send it through the parent's provider and fail. Use a separately configured provider session or an explicit provider wrapper for cross-provider work. See [Codex custom-agent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents). A successful spawn followed by a provider error is an execution failure, not a TOML parsing failure.

### Copilot (VS Code custom agents)

- Workspace custom agents are discovered from `.github/agents/` and use `.agent.md` files.
- This script emits compatibility-safe files preserving `name`, `description`, and instructions body.

### Cursor

- Cursor capabilities around file-based custom agent registration have changed across versions.
- This script emits best-effort `.cursor/agents/*.md` projections.
- Validate behavior in your installed Cursor build and fall back to `.cursor/rules`, `.cursor/skills`, and SDK-based definitions when needed.

### Generic Markdown

- Generic Markdown preserves the agent name, description, and instructions body without harness-specific fields.
- Use `.agents/<name>.md` for manual import or future adapters; it does not promise automatic discovery by any harness.

## Verification checklist

After sync:

1. **Claude**: run `/agents`; confirm agents appear and are invokable.
2. **Codex**: run a subagent workflow using one emitted `.codex/agents/*.toml` definition.
3. **Copilot**: open agent configuration/diagnostics and confirm `.github/agents/*.agent.md` files are loaded.
4. **Cursor**: verify whether `.cursor/agents/*.md` are picked up in your version; if not, use rules/skills/SDK path.

## Design principle

- Canonical source of truth: `geeky-orchestration/agents/*.md`
- All other harness files are generated artifacts
- Re-run sync whenever canonical agent files change
