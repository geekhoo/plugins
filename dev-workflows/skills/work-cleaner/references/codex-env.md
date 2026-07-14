# Work Cleaner — Codex environment

Load this when running `work-cleaner` in a Codex session. Resolve the placeholder roots to the real paths on the current machine.

## Repos & durable source

- Work often spans `mf-dotnet`, `mf-stack`, packet folders, and browser/frontend output.
- Durable plugin source is the `geekhoo-plugins` repo (`<geekhoo-plugins-root>`); the `.codex` layer is runtime. Keep `.codex` runtime-layer changes separate from durable plugin source changes.

## Tools

- Prefer `apply_patch` for edits; revert only the pass you just made with `apply_patch`.
- Prefer `git -C <repo>` for multi-repo work and `rg` with targeted roots over broad recursive scans.
- Use bundled or discovered runtimes when PATH is unreliable.
- For boundary/protected-path questions, use `scope-guard` first when allowed/protected edit paths are unclear.
- Use `repo-validation-runner` when validation spans multiple commands or repo gates, and `git-hygiene` for staging/commit/branch-sync/dirty-worktree management.

## Validators & gates

- Skill edits: run `quick_validate.py <skill-folder>` and inspect `agents/openai.yaml`.
- Plugin work: run local tests or plugin validators that already exist in the plugin; use fresh `outputs/` folders for evaluator runs.
- `.NET` work: the narrow test/build command named by the packet or solution docs; record DB prerequisite gaps explicitly.
- Frontend work: lint/build and browser/screenshot checks when UI output changes.
- Shell/hook cleanup: static parse plus a representative payload when safe.

## Windows notes

- PowerShell-safe commands with quoted `-LiteralPath` for Windows paths.
- Preserve `.claude-plugin` compatibility when adding Codex plugin metadata.
