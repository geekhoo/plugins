# Three-pass workflow — full task lists

Supporting reference for `js-legacy-refactor`. Each pass is governed by the no-regression rule in SKILL.md.

## Pass 1 — Inventory, baseline, and risk map

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

## Pass 2 — Safe consolidation and local cleanup

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

## Pass 3 — Verification, regression guard, and final issue report

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
