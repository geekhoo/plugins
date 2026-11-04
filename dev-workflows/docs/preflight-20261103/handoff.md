# Operational preflight maintenance record

Repository: `C:\Users\gerald.khoo\geekhoo-plugins`.
Verified base HEAD: `ea94635d2f76918f4a01699aea3e356f90954033`.
Worktree patch is uncommitted. Verify HEAD and the current diff before continuing.

Read in order:

1. `dev-workflows/skills/codex-operational-stabilizer/scripts/operational_preflight_shim.py`
2. `dev-workflows/skills/codex-operational-stabilizer/scripts/operational_preflight_hooks.py`
3. `dev-workflows/skills/codex-operational-stabilizer/tests/test_codex_operational_preflight.py`
4. This record and `kanban.md` beside it.

Source checker now recognizes the installed `[Console]::OpenStandardInput().CopyToAsync($process.StandardInput.BaseStream)` signature and direct Node script commands. Script paths preserve Windows separators and spaces. Unsupported wrappers, expansion, inline code, complex options, and compound Node commands are not claimed as validated; an empty extracted-path list does not establish a valid command.

Validation from repository root:

```powershell
python -B -m unittest discover -s dev-workflows/skills/codex-operational-stabilizer/tests -p test_codex_operational_preflight.py -v
```

Result: eight tests passed. Read-only source preflight reports stdin recognition, `UseShellExecute = $false`, and no shim issues. The installed SessionStart and Stop Node script paths appear in referenced paths and exist. `git diff --check` passed, with Git line-ending notices only.

These checks prove static recognition/path existence, not hook execution. Installed standalone and plugin-cache copies were not updated. No runtime shim, hook registration, credentials, evaluation artifacts, commits, or pushes belong to this patch.

Documentation disposition: root README lacked the supported-form and validation distinction and now links here. No existing scoped kanban/handoff was present for this repair, so these records were added. The skill's existing routing reference remains applicable and was left unchanged. Installation instructions remain applicable; do not claim installed-active repair until a separately scoped synchronization is verified.

Future installed-copy work must inspect the then-current runtime paths and compare changes before using the normal plugin installation/update mechanism. Do not overwrite caches or unrelated dirty files. Done criteria for this source patch are the focused tests and static recognition above; installed-copy synchronization remains explicitly outstanding.
