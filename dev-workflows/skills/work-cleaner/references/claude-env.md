# Work Cleaner — Claude Code environment

Load this when running `work-cleaner` in a Claude Code session. Resolve the placeholder roots to the real paths on the current machine (do not assume a hardcoded user profile).

## Repos & durable source

- Markefin repos live under `<markefin-code-root>` (e.g. `v2`, `mf-dotnet`, `mf-dx-cc`, `mf-skills`).
- Durable plugin source is the `geekhoo-plugins` repo (`<geekhoo-plugins-root>`); the `~\.claude` layer is runtime.
- **Never edit `~\.claude\plugins\cache\`** — that is installed runtime; edit the durable source (`geekhoo-plugins` or the plugin's own repo).

## Tools

- Use the dedicated Grep/Glob/Read/Edit tools for discovery and patching; use PowerShell only for git and validation commands, with all paths quoted.
- Revert a bad pass with targeted Edit calls (not broad git reverts).
- For boundary/protected-path questions, route to `pragmatic-scope-guard` (the standing scope discipline in this environment).

## Validators & gates

- Skill/plugin edits: re-read frontmatter for spec compliance; for geeky planning artifacts run the deterministic validators (`geeky_validate_kanban`, `geeky_validate_task_schema`, `geeky_check_dod`) before and after.
- `.NET` work (`mf-dotnet`, `v2`): the narrow `dotnet build` / `dotnet test --filter` named by the packet or solution docs; record DB prerequisite gaps explicitly.
- Frontend (`v2` Razor/DevExtreme, `mf-dx-cc` static): lint/build where present and a browser check (preview tools or `playwright-cli`) when UI output changes. For ProgramsV2 grid files, keep the CSS/JS interdependency chain atomic — never clean one side of a column/band pair.
- Scripts: prefer `py -3` style PATH-stable launchers, not bare `python`.

## Protected surfaces (in addition to the SKILL.md table)

- `MEMORY.md`, memory files, and `.remember/` history are cross-session state.
- `.claude-plugin`, `.codex-plugin`, `agents/*.yaml`, and hook shims serve multiple runtimes — the same skill folder may be read by both Claude Code and Codex.
