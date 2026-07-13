---
name: simplify-code
description: Use when asked to simplify, clean up, deslop, tidy, or reduce slop in source code — a branch before PR/review, named code files, or AI-generated code just written — without changing behavior. Preferred over the generic built-in simplify skill for repo work in this environment. Not for bug, security, architecture, or performance review; for docs, skill, plugin, or planning-packet artifacts use claude-work-cleaner.
---

# Simplify Code

Make code smaller, clearer, and more idiomatic without changing behavior. Prefer targeted edits that reduce maintenance cost and can be verified in the current repo. For bug-hunting use `/code-review` instead; this skill covers the environment-aware manual pass (the built-in `/simplify` and the `code-simplifier` agent are generic alternatives).

## Workflow

1. Resolve scope.
   - Use `branch` when a git diff exists. Find the repo root, current branch, base branch, and changed files.
   - Use `paths` when the user names files or directories. Do not widen scope unless the named code imports local siblings that must be checked to simplify safely.
   - Use `conversation` when the current turn produced code but no repo diff is available. Review only files touched in the turn.
   - Use `codebase` only when the user explicitly asks for broad cleanup. Rank hotspots first by churn, size, and recent edits; state sampled-in and sampled-out paths before editing.

2. Ground the pass.
   - Read local instructions: the repo's `CLAUDE.md`, `README.md`, `.editorconfig`, formatter config, test docs, and nearby code.
   - Check memory for repo-relevant constraints (e.g. the ProgramsV2 grid CSS/JS coupling — its pieces must change atomically, so "redundant-looking" CSS or JS state may be load-bearing).
   - Keep user constraints verbatim, especially "do not change behavior", "do not touch X", "follow existing convention", and validation requirements.

3. Select cleanup lanes.
   - Read `references/cleanup-rubric.md` when the task is non-trivial, broad, or ambiguous.
   - Use only lanes that match the scoped files. A docs-only or config-only change may need no code cleanup.
   - Batch independent file reads as parallel tool calls. Delegate to the `code-simplifier` agent only when lanes are large enough to justify isolated review; you remain responsible for integration and final proof.

4. Apply only safe fixes.
   - Auto-apply behavior-preserving edits: remove stale or narrational comments, inline trivial wrappers, replace one-off helpers with direct code, remove duplicate branches, tighten names, use existing local helpers (`Markefin.*` utilities before new ones), simplify needless defensive code when behavior is provably unchanged, and delete dead code only when all call sites are proven absent (Grep across the repo, including `.cshtml` string references to JS/CSS names).
   - Flag instead of applying: public API/signature changes, cross-module refactors, production helper deletion with uncertain callers, test strategy changes, broad architecture changes, performance-sensitive rewrites, concurrency changes, or anything needing product judgment.
   - Preserve unrelated user edits. If scoped files are already dirty, read the diff carefully and work with it rather than resetting or reverting.

5. Verify.
   - Run the smallest meaningful formatter, lint, typecheck, build, or test command from repo conventions: targeted `dotnet build` / `dotnet test --filter` for `mf-dotnet`/`v2`; a browser check (preview tools or playwright-cli) for `v2` Razor/DevExtreme and `mf-dx-cc` static frontend, which has no build step to catch mistakes.
   - Classify Windows host/tooling failures separately from code defects. After two unrelated command failures, stop retrying blindly and report the likely host blocker with the exact failing command.
   - If no validator is available, perform source-level proof: cite call sites, invariants, deleted paths, and why behavior is unchanged.

6. Report.
   - Lead with what changed and how it was verified.
   - Separate applied simplifications from flagged follow-ups.
   - For broad or sampled passes, explicitly name exclusions and remaining risk.

## Cleanup Rules

Load `references/cleanup-rubric.md` for the detailed lane checklist. Keep the live pass focused on evidence from the current codebase; do not rewrite code merely because a pattern looks unfashionable.

## Stop Conditions

Stop and ask before continuing when simplification would require changing behavior, resolving conflicting product intent, touching secrets or production configuration, widening from a targeted request to repo-wide cleanup, or deleting code whose callers cannot be confidently identified.
