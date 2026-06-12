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

# explicit project root
python scripts/sync-agents.py --project-root "C:/path/to/repo"
node   scripts/sync-agents.js --project-root "C:/path/to/repo"

# machine-readable output
python scripts/sync-agents.py --json
node   scripts/sync-agents.js --json
```

## Generated outputs

Default output paths (relative to `--project-root`):

- Claude: `.claude/agents/<name>.md`
- Copilot/VS Code: `.github/agents/<name>.agent.md`
- Codex CLI: `.codex/agents/<name>.toml`
- Cursor (best effort): `.cursor/agents/<name>.md`

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

### Copilot (VS Code custom agents)

- Workspace custom agents are discovered from `.github/agents/` and use `.agent.md` files.
- This script emits compatibility-safe files preserving `name`, `description`, and instructions body.

### Cursor

- Cursor capabilities around file-based custom agent registration have changed across versions.
- This script emits best-effort `.cursor/agents/*.md` projections.
- Validate behavior in your installed Cursor build and fall back to `.cursor/rules`, `.cursor/skills`, and SDK-based definitions when needed.

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
