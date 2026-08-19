# Page-aware consolidation, duplicate handling, and hidden-dependency detection

Supporting reference for `js-legacy-refactor`.

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
