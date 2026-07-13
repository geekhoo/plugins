---
name: claude-work-cleaner
description: Use when asked to clean, tighten, de-slop, or strip AI-generated bloat from docs, skills, plugins, planning packets, handoff/kanban notes, reports, or a whole recent implementation (code plus its artifacts) before review or validation — in Claude Code sessions. In Codex sessions use codex-work-cleaner; for cleanup scoped purely to source code files, use simplify-code instead.
---

# Claude Work Cleaner

## Overview

Remove generated clutter from code, docs, skills, plugins, planning packets, and reports without changing intended behavior or losing evidence. Treat cleanup as validation-bound engineering work, not aesthetic shortening.

This skill is adapted for Gerald's Claude Code environment on Windows 11, where work spans the Markefin repos under `C:\Users\gerald.khoo\Codes\` (`v2`, `mf-dotnet`, `mf-dx-cc`, `mf-skills`), the durable plugin source at `C:\Users\gerald.khoo\geekhoo-plugins`, the `~\.claude` runtime layer, and durable artifacts such as `handoff.md`, `kanban.md`, `docs/` planning folders, memory files, `.remember/` history, reports, and validation logs.

## Prime Rules

- Preserve behavior, tests, public APIs, task state, user-owned edits, and durable evidence.
- Inspect `git status --short --branch --untracked-files=all` before editing inside a repo.
- Use the dedicated Grep/Glob/Read/Edit tools for discovery and patching; use PowerShell only for git and validation commands, with all paths quoted.
- Never use broad destructive revert commands such as `git checkout -- .`, `git reset --hard`, recursive delete, or whole-folder cleanup to recover from a failed pass.
- Revert only the pass you just made, with targeted Edit calls, and leave unrelated dirty work untouched.
- Do not clean tests unless the user explicitly asks for test cleanup. Tests may be verbose because they encode behavior.
- Do not delete `outputs/`, planning-packet notes, `handoff.md`, `kanban.md`, memory files, `.remember/` history, evaluation artifacts, screenshots, or validation logs unless the user explicitly scopes that cleanup.
- Never edit `~\.claude\plugins\cache\` — that is installed runtime; the durable source is `geekhoo-plugins` or the plugin's own repo.

## Workflow

1. Define the cleanup target:
   - Identify the requested files, packet, feature, branch, or generated output.
   - Record protected surfaces and unrelated dirty changes.
   - Exclude vendor folders, caches, plugin cache copies, build outputs (`bin/`, `obj/`, `node_modules/`), and archives unless the request names them.

2. Establish the baseline:
   - Read existing validation instructions: repo `CLAUDE.md`, solution files, package scripts, planning-packet closeout docs, or plugin validators.
   - Run the smallest meaningful baseline gate when feasible.
   - If the baseline is already red, record the failure and continue only with cleanup that can be checked by narrower gates.

3. Clean one pass at a time:
   - Pick one pass category from the list below.
   - Apply a small patch.
   - Run the narrowest gate that could catch regression for that pass.
   - Keep the pass if validation holds or the risk is obviously documentation-only.
   - Revert that pass if validation fails and the failure is plausibly caused by the cleanup.

4. Close with proof:
   - Run a final relevant gate when feasible.
   - Report files touched, what was removed or simplified, validation results, skipped gates, and remaining risk.
   - Mention any protected dirty work left untouched.

## Cleanup Passes

Use this pass order by default:

1. Mechanical clutter: dead imports, unused locals from recent work, debug statements, commented-out code, scaffold placeholders.
2. Comment and documentation noise: obvious comments, redundant doc blocks, decorative banners, over-explained UI or skill text.
3. Generated surface tightening: duplicated packet/report prose, stale command variants, unused frontend state, placeholder links.
4. Abstraction reduction: one-use helpers, single-implementation factories, over-generic types, duplication that can be simplified clearly.
5. Windows and Claude environment fit: PowerShell-safe quoted commands, `git -C`, dedicated tools over shell scans, runtime-layer versus durable plugin source separation.

Read `references/pass-guide.md` when the cleanup target is broad, risky, cross-repo, documentation-heavy, or involves plugin/skill/runtime compatibility.

## Never Clean By Default

| Surface | Reason |
| --- | --- |
| Tests | They protect behavior and may encode edge cases verbosely. |
| Public API signatures | Callers may live outside the current search surface. |
| Packet state files | `kanban.md`, `handoff.md`, task notes, and closeout reports are durable coordination state, and the geeky validators enforce their schema. |
| Validation evidence | Logs, screenshots, reports, and output artifacts may be the only proof trail. |
| Runtime compatibility files | `.claude-plugin`, `.codex-plugin`, `agents/*.yaml`, hook shims, and agent configs serve different consumers — the same skill folder may be read by both Claude Code and Codex. |
| Memory and history | `MEMORY.md`, memory files, `.remember/` — cross-session state, not clutter. |
| User-owned dirty work | Gerald may have intentionally changed it outside this task. |
| Feature flags and fallback paths | They may be toggled or environment-dependent. |
| Generated vendor or cache code | Fix the generator or exclude the path unless explicitly scoped. |

## Validation Examples

Choose gates proportional to the cleanup:

- Skill or plugin edits: re-read the frontmatter for spec compliance; for geeky planning artifacts run the deterministic validators (`geeky_validate_kanban`, `geeky_validate_task_schema`, `geeky_check_dod`) before and after.
- .NET work (`mf-dotnet`, `v2`): run the narrow `dotnet build` / `dotnet test --filter` command named by the packet or solution docs; record DB prerequisite gaps explicitly.
- Frontend work (`v2` Razor/DevExtreme, `mf-dx-cc` static): run lint/build where present and a browser check (preview tools or playwright-cli) when UI output changes. For ProgramsV2 grid files, verify the CSS/JS interdependency chain stays atomic — never clean one side of a column/band pair.
- Documentation-only cleanup: run link/drift scripts when present, otherwise inspect rendered-sensitive Markdown and final diffs.
- Hook or script cleanup: static parse (`pwsh -NoProfile -Command` syntax check or `bash -n`) plus a representative payload when safe.

## Final Report Shape

Report cleanup in this order:

1. Outcome: what was cleaned and where.
2. Evidence: validation commands and pass/fail/gap.
3. Scope: files touched and protected dirty work left untouched.
4. Skips: passes intentionally skipped and why.
5. Risk: remaining uncertainty or host prerequisites.

Avoid reporting "lines removed" as the main success metric. The goal is clarity per line with preserved proof.

## Resources

- `references/pass-guide.md`: detailed pass rules, keep/remove examples, and final reporting guidance for larger cleanup tasks.
