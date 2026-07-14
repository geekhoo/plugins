---
name: work-cleaner
description: Use when asked to clean, tighten, de-slop, reduce bloat, simplify, strip AI-generated clutter, review unnecessary code/docs, or prepare a recent implementation, planning packet, plugin, skill, frontend, or agent-generated work for review or validation — while preserving behavior, user-owned changes, durable artifacts, and proof. For cleanup scoped purely to source code files, use simplify-code instead.
---

# Work Cleaner

## Overview

Remove generated clutter from code, docs, skills, plugins, planning packets, hooks, and reports without changing intended behavior or losing evidence. Treat cleanup as validation-bound engineering work, not aesthetic shortening.

## Harness environment

This skill runs under both Claude Code and Codex. Load the reference for the active harness before editing — it carries the repo roots, validators, tool preferences, and runtime-layer rules that differ between them:

- **Claude Code** → `references/claude-env.md`
- **Codex** → `references/codex-env.md`

## Prime Rules

- Preserve behavior, tests, public APIs, task state, user-owned edits, and durable evidence.
- Inspect `git status --short --branch --untracked-files=all` before editing inside a repo.
- When allowed edit paths or protected paths are unclear, establish them first (see your harness reference for the boundary/scope-guard tooling it routes to).
- Never use broad destructive revert commands such as `git checkout -- .`, `git reset --hard`, recursive delete, or whole-folder cleanup to recover from a failed pass.
- Revert only the pass you just made, with a targeted patch, and leave unrelated dirty work untouched.
- Do not clean tests unless the user explicitly asks for test cleanup. Tests may be verbose because they encode behavior.
- Do not delete `outputs/`, planning-packet notes, `handoff.md`, `kanban.md`, memory/history files, evaluation artifacts, screenshots, or validation logs unless the user explicitly scopes that cleanup.
- Never edit installed plugin cache copies — the durable source is the plugin's own repo (see your harness reference for the exact paths).

## Workflow

1. Define the cleanup target:
   - Identify the requested files, packet, feature, branch, or generated output.
   - Record protected surfaces and unrelated dirty changes.
   - Exclude vendor folders, caches, plugin cache copies, build outputs (`bin/`, `obj/`, `node_modules/`), and archives unless the request names them.

2. Establish the baseline:
   - Read existing validation instructions: repo `CLAUDE.md`/`AGENTS.md`, solution files, package scripts, planning-packet closeout docs, or plugin validators.
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

Use this pass order by default (full rules, keep/remove examples, and the per-harness Pass 5 in `references/pass-guide.md`):

1. Mechanical clutter: dead imports, unused locals from recent work, debug statements, commented-out code, scaffold placeholders.
2. Comment and documentation noise: obvious comments, redundant doc blocks, decorative banners, over-explained UI or skill text.
3. Generated surface tightening: duplicated packet/report prose, stale command variants, unused frontend state, placeholder links.
4. Abstraction reduction: one-use helpers, single-implementation factories, over-generic types, duplication that can be simplified clearly.
5. Environment fit: PowerShell-safe quoted commands, `git -C`, dedicated tools over broad scans, runtime-layer vs durable-source separation — the harness-specific rules are in your env reference.

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
| User-owned dirty work | The user may have intentionally changed it outside this task. |
| Feature flags and fallback paths | They may be toggled or environment-dependent. |
| Generated vendor or cache code | Fix the generator or exclude the path unless explicitly scoped. |

## Validation Examples

Choose gates proportional to the cleanup (harness-specific validators and repo roots are in your env reference):

- Skill or plugin edits: re-read the frontmatter for spec compliance; for geeky planning artifacts run the deterministic validators before and after.
- .NET work: run the narrow `dotnet build` / `dotnet test --filter` command named by the packet or solution docs; record DB prerequisite gaps explicitly.
- Frontend work: run lint/build where present and a browser check when UI output changes. For ProgramsV2 grid files, verify the CSS/JS interdependency chain stays atomic — never clean one side of a column/band pair.
- Documentation-only cleanup: run link/drift scripts when present, otherwise inspect rendered-sensitive Markdown and final diffs.
- Hook or script cleanup: static parse plus a representative payload when safe.

## Final Report Shape

Report cleanup in this order:

1. Outcome: what was cleaned and where.
2. Evidence: validation commands and pass/fail/gap.
3. Scope: files touched and protected dirty work left untouched.
4. Skips: passes intentionally skipped and why.
5. Risk: remaining uncertainty or host prerequisites.

Avoid reporting "lines removed" as the main success metric. The goal is clarity per line with preserved proof.

## Resources

- `references/pass-guide.md`: detailed pass rules, keep/remove examples, per-harness Pass 5, and final reporting guidance for larger cleanup tasks.
- `references/claude-env.md`: Claude Code repo roots, validators, tool preferences, runtime-layer rules.
- `references/codex-env.md`: Codex repo roots, validators, tool preferences, runtime-layer rules.
