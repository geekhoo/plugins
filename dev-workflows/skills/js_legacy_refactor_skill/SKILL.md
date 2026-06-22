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

Always perform exactly three passes through the JavaScript and the HTML that loads it. Each pass is still governed by the no-regression rule.

### Pass 1 — Inventory, baseline, and risk map

Goal: learn the app's real execution model before changing code.

Tasks:

- Find all HTML entry pages and every `<script>` tag in document order.
- Record each external script `src`, resolved local file path, and loading attributes: `type`, `async`, `defer`, `nomodule`, `integrity`, `crossorigin`, `nonce`, and `referrerpolicy`.
- Record every inline script block with page name, block index, source hash, approximate line number, and surrounding context.
- Record event-handler attributes such as `onclick`, `onchange`, and `onload`; these are JavaScript entry points and must not be missed.
- Record dynamic script insertion patterns such as `document.createElement('script')`, `appendChild(script)`, `import()`, `eval`, `new Function`, and `document.write`.
- Inventory declarations from all referenced scripts and inline scripts: `function`, `class`, `var`, `let`, `const`, `window.name =`, `globalThis.name =`, prototype mutation, and suspected implicit globals.
- Identify duplicate declarations by symbol name. Classify duplicates as:
  - **exact duplicate**: same name and normalized body hash;
  - **compatible-looking duplicate**: same name and similar signature but not byte-equivalent;
  - **divergent duplicate**: same name with different body, initializer, arity, side effects, or file order;
  - **intentional override candidate**: later declaration appears to replace earlier behavior.
- Generate a baseline report and, when possible, a browser runtime snapshot for all main pages.

Pass 1 output must include:

- script-load manifest;
- global/declaration inventory;
- duplicate/override map;
- order-dependency hazards;
- inline-script hazards;
- unresolved or missing script files;
- test commands or browser probe commands used;
- pass/fail status.

No source-code refactor is allowed in Pass 1 except adding non-invasive comments to an agent-owned working copy. Prefer not to modify source at all.

### Pass 2 — Safe consolidation and local cleanup

Goal: improve structure only where equivalence can be demonstrated.

Allowed operations by default:

- Move repeated pure helper logic into a single helper only when all duplicate bodies are equivalent and the move preserves call timing and global exposure.
- Consolidate exact duplicate function bodies only when the resulting function keeps the same global name, arity, `typeof`, call behavior, and availability timing on every page that used it.
- Split a very large file into clearer sections inside the same file without changing statement order.
- Combine adjacent files into a page-specific consolidated file only when it preserves exact execution order, top-level side effects, parser timing, and all public globals. Keep boundary comments marking original file names and inline-script positions.
- Replace repeated literal configuration objects with one shared object only when there is no mutation or when mutation behavior is preserved exactly.
- Remove dead code only when it is proven unreachable from HTML event attributes, external callbacks, timers, dynamic property lookup, string-based calls, and browser/global references.
- Improve naming only for private local variables inside a closed lexical scope. Do not rename public globals, HTML-called functions, callback names, object keys, or function names that might appear in stack traces or string lookup.

Operations requiring explicit proof before application:

- Moving inline scripts into external files.
- Reordering any top-level statement.
- Wrapping legacy top-level code in an IIFE.
- Replacing `var` with `let` or `const`.
- Replacing function declarations with function expressions or arrow functions.
- Changing script attributes or locations in HTML.
- Creating a single all-page consolidated script.
- Converting direct globals into a namespace object.
- Converting classic scripts to ES modules.
- Minifying or compacting in a way that changes function names, stack traces, `Function.prototype.toString()`, line-dependent diagnostics, or timing.

Forbidden unless the user explicitly authorizes a behavior migration project instead of a no-regression refactor:

- Changing UI behavior, validation rules, API payloads, DOM structure, event order, timer timing, or network request sequence.
- Introducing a bundler, build step, transpiler, framework, or module loader.
- Adding `async` to dependent scripts.
- Removing apparently unused globals that could be called from HTML attributes, bookmarklets, server-rendered markup, external integrations, browser console workflows, or string-based dynamic dispatch.
- Treating divergent duplicate functions as redundant. Divergent duplicates must be flagged as possible overrides.

Pass 2 output must include:

- changed files list;
- skipped changes list;
- equivalence evidence for each accepted consolidation;
- unresolved risks;
- issues detected and bypassed.

### Pass 3 — Verification, regression guard, and final issue report

Goal: prove the refactor did not change behavior.

Tasks:

- Re-run the static inventory on the refactored tree.
- Compare script order, script attributes, public global names, function arity, declaration availability, event-handler entry points, and missing files against the Pass 1 baseline.
- Run existing tests exactly as the project normally runs them.
- Run browser probes for every primary HTML page, including representative interactions when feasible.
- Compare console errors, `pageerror` events, failed network requests, DOM snapshots, known global descriptors, and page-specific custom probes.
- Manually inspect every flagged delta. If a delta is not proven benign, revert or bypass the causative change.
- Produce a final report listing accepted refactors, bypassed refactors, all issues found, and any recommended follow-up work.

Pass 3 final decision:

- **PASS** only if every required static/runtime/test comparison is unchanged or each delta is explicitly proven benign and documented.
- **BYPASS/PARTIAL** if risky changes were skipped but safe changes passed all checks.
- **FAIL/REVERT REQUIRED** if behavior changed and cannot be proven harmless.

## Page-aware consolidation strategy

For a no-bundler browser app, the safest consolidation is usually page-aware rather than global:

1. Preserve each HTML page's script execution order as the source of truth.
2. Build a per-page dependency sequence from external and inline scripts.
3. Consolidate only within a page or within a set of pages that share the exact same dependency sequence.
4. Keep global API compatibility for cross-page or externally callable symbols.
5. Use original file-boundary comments in consolidated files:

```js
/* === BEGIN original: js/utils.js, loaded by index.html script[2] === */
// original code
/* === END original: js/utils.js === */
```

If inline code is moved, preserve a boundary marker:

```js
/* === BEGIN original inline script: index.html script[4], sha256:... === */
// original inline code
/* === END original inline script: index.html script[4] === */
```

Before moving inline code, check for `document.currentScript`, parser-timing DOM assumptions, CSP nonce dependence, template/script data blocks, `this` at top level, and adjacent markup dependence. If any exists, leave the inline script in place and report the risk.

## Duplicate declaration handling

When the same name appears more than once:

- Same name, identical normalized body, same arity, same scope, same pages, same availability timing: eligible for consolidation after tests.
- Same name, different body: do not merge. Treat as override or conflict. Preserve load order and report.
- Same name, `var` plus `function`: preserve semantics because `var` initializers can override hoisted functions.
- Same name, `let`/`const`/`class` collisions: treat as high-risk; these can be syntax/runtime errors depending on scope and load path.
- Same name loaded on different pages with different dependencies: do not globally consolidate until all affected pages pass probes.
- Same function used by HTML attributes: preserve global name and `window[name]` availability.

## Hidden dependency detection checklist

Search for:

- `window.someName`, `globalThis.someName`, `self.someName`;
- unqualified calls such as `init()`, `validateForm()`, `saveData()`;
- HTML attributes: `onclick="saveData()"`, `onload="init()"`;
- timer strings: `setTimeout("init()", 0)`, `setInterval("tick()", 1000)`;
- dynamic dispatch: `window[actionName]()`, `obj[methodName]()`;
- library globals: `$`, `jQuery`, `_`, `moment`, `axios`, `Vue`, `React`, etc.;
- server-rendered callbacks referenced by string;
- DOMContentLoaded/load handlers;
- `document.write` and parser-timing mutations;
- `eval`, `new Function`, inline event attributes, and JSONP callbacks;
- prototype extensions and monkey patches;
- mutation of shared config objects;
- reliance on source order for default settings overridden later.

## Issue report format

Use this exact structure for final reports:

```md
# JavaScript Refactor Report

## Status
PASS | BYPASS/PARTIAL | FAIL/REVERT REQUIRED

## Summary
- Files changed:
- Files intentionally not changed:
- Pages verified:
- Tests/probes run:

## Accepted refactors
| ID | Files | Change | Safety evidence |
|---|---|---|---|

## Bypassed refactors / issues
| ID | Severity | Location | Reason | Recommended fix |
|---|---|---|---|---|

## Behavior comparison
| Check | Baseline | Refactor | Result |
|---|---:|---:|---|

## Remaining risks
| Risk | Affected pages/files | Mitigation |
|---|---|---|
```

Severity values:

- `BLOCKER_REFRACTOR_BYPASSED`: a change would likely alter behavior or triggered an error.
- `HIGH_ORDER_DEPENDENCY`: hidden load-order or override dependency.
- `HIGH_GLOBAL_COLLISION`: duplicate/divergent global declaration.
- `MEDIUM_INLINE_SCRIPT`: inline script cannot safely move yet.
- `MEDIUM_DYNAMIC_CODE`: dynamic calls prevent confident static analysis.
- `LOW_CLEANUP`: safe follow-up cleanup opportunity.

## Tooling bundled with this skill

Use the tools in `tools/` from the root of the app being refactored.

### Static audit and comparison

```bash
python tools/js_legacy_refactor_audit.py audit /path/to/app --out /path/to/app/.refactor_audit/baseline
python tools/js_legacy_refactor_audit.py audit /path/to/app-refactored --out /path/to/app/.refactor_audit/after
python tools/js_legacy_refactor_audit.py compare /path/to/app/.refactor_audit/baseline/audit.json /path/to/app/.refactor_audit/after/audit.json --out /path/to/app/.refactor_audit/static-compare.md
```

The audit tool is dependency-free Python. It intentionally reports conservative warnings and may over-report. Treat warnings as investigation targets, not automatic proof.

### Optional browser regression probe

```bash
cd /path/to/app
npm install --save-dev playwright
npx playwright install chromium
node tools/browser_regression_probe.mjs snapshot --root . --url http://127.0.0.1:8080 --pages index.html,settings.html --out .refactor_audit/browser-baseline.json
node tools/browser_regression_probe.mjs snapshot --root ../app-refactored --url http://127.0.0.1:8081 --pages index.html,settings.html --out .refactor_audit/browser-after.json
node tools/browser_regression_probe.mjs compare .refactor_audit/browser-baseline.json .refactor_audit/browser-after.json --out .refactor_audit/browser-compare.md
```

Run the same local server behavior for baseline and refactored trees. Do not compare `file://` behavior to HTTP behavior because module loading, CORS, relative URLs, and origin behavior differ.

## Agent operating rules

- Work on a branch or copy, never directly on the only source tree.
- Preserve original files until Pass 3 passes.
- Prefer small, reversible commits or patches.
- Do not rely on static analysis alone for behavior equivalence.
- Use the app's existing test suite first, then add probes for uncovered HTML pages.
- When an issue is found, report it after the pass; do not silently “fix” it in a way that changes behavior.
- The best refactor may be partial. Compactness is secondary to proven equivalence.
