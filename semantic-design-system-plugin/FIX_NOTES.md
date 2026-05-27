# Fix notes

Version 0.1.1 fixes the Claude Code plugin manifest validation error:

- Removed the redundant `skills` manifest field because the default `skills/` directory is auto-discovered.
- Changed `agents` from the invalid directory value `"./agents/"` to explicit agent Markdown files:
  - `./agents/design-token-architect.md`
  - `./agents/codebase-token-auditor.md`
  - `./agents/design-system-migrator.md`

The current Claude Code plugin schema expects the `agents` manifest field to reference custom agent files, not a directory.
