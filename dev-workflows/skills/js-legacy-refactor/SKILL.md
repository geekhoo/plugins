---
name: js-legacy-refactor
description: Safely refactor JavaScript-heavy HTML/CSS/JS web apps with no bundler or build step. Use for legacy browser scripts, inline scripts, global-scope code, duplicate declarations, load-order hazards, and behavior-preserving consolidation. Enforces a strict no-regression rule and a mandatory three-pass audit, refactor, and verification workflow.
---

# Legacy Browser JavaScript Refactor — No Regression Skill

## Purpose

Use this skill when refactoring JavaScript-heavy HTML/CSS/JS web apps that run directly in the browser without a bundler, builder, transpiler, or module packaging step. The app may contain many `.js` files, large monolithic files, inline `<script>` blocks inside HTML, top-level browser globals, duplicate declarations, implicit globals, and hidden dependencies that only work because HTML script tags currently load in the right order.

The skill optimizes for safe consolidation, readability, and maintainability while preserving exact browser behavior.

## Non-negotiable rule

**No regression is allowed.** The refactored app must behave exactly the same before and after the refactor.

If any syntax error, runtime error, browser-console error, changed public global, changed script timing, changed DOM state, changed network behavior, changed test result, or other behavior delta is detected:

1. Stop applying the risky change.
2. Revert or bypass the affected refactor.
3. Continue auditing the remaining files where safe.
4. Record the issue with file, line or script-block index, suspected cause, and suggested remediation.
5. Raise all accumulated issues after the refactor pass is complete.

A skipped refactor with a clear issue report is preferred to a compact codebase with a possible regression.

## Important browser constraints

Treat classic browser scripts as order-sensitive and side-effectful unless proven otherwise.

Do not assume that moving, wrapping, merging, or converting scripts is safe. Classic scripts can create globals, overwrite earlier declarations, depend on parser-blocking execution, mutate DOM while HTML is still being parsed, rely on `document.currentScript`, rely on `this === window`, rely on `var` hoisting, or intentionally override functions loaded by earlier files.

Never convert classic scripts to `type="module"` as a routine cleanup. Module scripts are deferred by default, use strict mode, have module scope, and execute only once per module URL. Those differences can change legacy app behavior.

Never add `async` to scripts that have any dependency on another script. `async` removes ordering guarantees.

Never add `defer`, move a script to the end of the page, externalize an inline script, or replace many tags with one consolidated file unless the baseline and after-refactor probes prove equivalence for the affected pages.

## Required three-pass workflow

Always perform exactly three passes through the JavaScript and the HTML that loads it. Each pass is still governed by the no-regression rule. **Load `references/three-pass-workflow.md` for the full, binding task lists and allowed/forbidden operation lists of each pass before starting it.** In summary:

- **Pass 1 — Inventory, baseline, and risk map.** Map every entry page, script tag (order + attributes), inline block, event-handler attribute, dynamic script insertion, and declaration; classify duplicate declarations (exact / compatible-looking / divergent / intentional override); produce a baseline report and browser runtime snapshot. No source refactoring in this pass.
- **Pass 2 — Safe consolidation and local cleanup.** Apply only equivalence-proven consolidations; a defined set of operations needs explicit proof first (inline-script moves, reordering, IIFE wrapping, var→let/const, attribute changes, module conversion...), and behavior migrations are forbidden without explicit user authorization. Output changed/skipped lists with equivalence evidence.
- **Pass 3 — Verification, regression guard, and final issue report.** Re-run the static inventory, compare against the Pass 1 baseline, run the project's tests and browser probes, inspect every delta, and produce the final PASS / BYPASS-PARTIAL / FAIL-REVERT decision.

## Consolidation strategy and duplicate handling

Consolidation must be page-aware (per-page dependency sequences, original file-boundary comments) and duplicate declarations must be handled per classification — full rules and the hidden-dependency detection checklist (window globals, HTML attribute handlers, timer strings, dynamic dispatch, document.write, eval, monkey patches...) are in `references/consolidation-and-duplicates.md`. Load it before consolidating or merging any duplicate.
## Issue report format

Use the structured report template (status, accepted/bypassed tables, behavior
comparison, remaining risks) and the severity values in
[references/report-format.md](references/report-format.md) for the final report.

## Tooling bundled with this skill

A dependency-free Python static audit/compare tool and an optional Playwright browser regression probe ship in this skill's `tools/` dir. Commands, path-resolution notes (resolve `tools/` from the skill directory, not the app cwd), and the file://-vs-HTTP caveat are in `references/tooling.md`.

## Agent operating rules

- Work on a branch or copy, never directly on the only source tree.
- Preserve original files until Pass 3 passes.
- Prefer small, reversible commits or patches.
- Do not rely on static analysis alone for behavior equivalence.
- Use the app's existing test suite first, then add probes for uncovered HTML pages.
- When an issue is found, report it after the pass; do not silently “fix” it in a way that changes behavior.
- The best refactor may be partial. Compactness is secondary to proven equivalence.
