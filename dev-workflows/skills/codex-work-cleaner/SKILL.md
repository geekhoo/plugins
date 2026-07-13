---
name: codex-work-cleaner
description: Use when the user asks to clean, tighten, de-slop, reduce bloat, simplify, remove AI-generated clutter, review unnecessary code/docs, or prepare recent implementation, packet, plugin, skill, frontend, or agent-generated work for validation while preserving behavior, user-owned changes, durable artifacts, and proof.
---

# Codex Work Cleaner

## Overview

Remove generated clutter from code, docs, skills, packets, hooks, and reports without changing intended behavior or losing evidence. Treat cleanup as validation-bound engineering work, not aesthetic shortening.

This skill is adapted for the shared Windows Codex environment where work often spans `mf-dotnet`, `mf-stack`, `C:\Users\gerald.khoo\geekhoo-plugins`, `.codex` runtime layers, packet folders, browser/frontend output, and durable artifacts such as `handoff.md`, `kanban.md`, reports, prompts, and validation logs.

## Prime Rules

- Preserve behavior, tests, public APIs, task state, user-owned edits, and durable evidence.
- Inspect `git status --short --branch --untracked-files=all` before editing inside a repo.
- Use `scope-guard` first when allowed edit paths or protected paths are unclear.
- Use `repo-validation-runner` when validation spans multiple commands or repo gates.
- Use `git-hygiene` for staging, committing, branch sync, or broad dirty-worktree management.
- Never use broad destructive revert commands such as `git checkout -- .`, `git reset --hard`, recursive delete, or whole-folder cleanup to recover from a failed pass.
- Revert only the pass you just made, preferably with `apply_patch`, and leave unrelated dirty work untouched.
- Do not clean tests unless the user explicitly asks for test cleanup. Tests may be verbose because they encode behavior.
- Do not delete `outputs/`, packet notes, handoffs, kanban state, evaluation artifacts, screenshots, or validation logs unless the user explicitly scopes that cleanup.

## Workflow

1. Define the cleanup target:
   - Identify the requested files, packet, feature, branch, or generated output.
   - Record protected surfaces and unrelated dirty changes.
   - Exclude generated vendor folders, caches, plugin cache runtime copies, build outputs, and archives unless the request names them.

2. Establish the baseline:
   - Read existing validation instructions: package scripts, solution files, `VALIDATION-GATES.md`, packet closeout docs, or local skill/plugin validators.
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
5. Windows and Codex environment fit: PowerShell-safe commands, `git -C`, `rg`, bundled runtimes, durable plugin source versus `.codex` runtime layers.

Read `references/pass-guide.md` when the cleanup target is broad, risky, cross-repo, documentation-heavy, or involves plugin/skill/runtime compatibility.

## Never Clean By Default

| Surface | Reason |
| --- | --- |
| Tests | They protect behavior and may encode edge cases verbosely. |
| Public API signatures | Callers may live outside the current search surface. |
| Packet state files | `kanban.md`, `handoff.md`, task notes, and closeout reports are durable coordination state. |
| Validation evidence | Logs, screenshots, reports, and output artifacts may be the only proof trail. |
| Runtime compatibility files | `.claude-plugin`, `.codex-plugin`, hook shims, and agent configs can serve different consumers. |
| User-owned dirty work | The user may have intentionally changed it outside this task. |
| Feature flags and fallback paths | They may be toggled or environment-dependent. |
| Generated vendor or cache code | Fix the generator or exclude the path unless explicitly scoped. |

## Validation Examples

Choose gates proportional to the cleanup:

- Skill edits: run `quick_validate.py <skill-folder>` and inspect `agents/openai.yaml`.
- Plugin work: run local tests or plugin validators that already exist in the plugin; use fresh `outputs/` folders for evaluator runs.
- .NET work: run the narrow test/build command named by the packet or solution docs; record DB prerequisite gaps explicitly.
- Frontend work: run lint/build and browser/screenshot checks when UI output changes.
- Documentation-only cleanup: run link/drift/check scripts when present, otherwise inspect rendered-sensitive Markdown and final diffs.
- Shell or hook cleanup: run static parse plus a representative payload when safe.

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
