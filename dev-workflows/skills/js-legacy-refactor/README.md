# Legacy Browser JavaScript Refactor Skill Package

This package contains a reusable coding-agent skill for safely refactoring JavaScript-heavy browser apps that run directly from HTML/CSS/JS without a bundler or builder.

Files:

- `SKILL.md` — the agent skill instructions, including the mandatory no-regression and three-pass workflow.
- `tools/js_legacy_refactor_audit.py` — dependency-free Python static audit tool.
- `tools/browser_regression_probe.mjs` — optional Playwright browser regression probe.
- `examples/custom_probe_body.js` — example custom browser probe body.
- `package.json` — optional dev dependency metadata for the browser probe only.

Suggested first commands from an app root:

```bash
python /path/to/skill/tools/js_legacy_refactor_audit.py audit . --out .refactor_audit/baseline
npm install --save-dev playwright
npx playwright install chromium
node /path/to/skill/tools/browser_regression_probe.mjs snapshot --root . --port 8123 --audit .refactor_audit/baseline/audit.json --out .refactor_audit/browser-baseline.json
```

## Audit scan modes

By default the audit walks every `.js` file under the root and also inventories the scripts each HTML page references. `--referenced-only` narrows the analysed set to inline scripts plus the local files actually reached from a `<script src>`:

```bash
python tools/js_legacy_refactor_audit.py audit . --out .refactor_audit/baseline --referenced-only
```

`src` resolution honours `<base href>`, drops query strings and fragments, deduplicates files shared across pages, and refuses any path that escapes the audit root. Unit ids match those the default mode produces for the same file, so the two modes' reports stay comparable.

One difference worth knowing: orphan detection needs the full JS set to diff against, so it is unavailable in this mode. The report says so explicitly — `orphan_js_files` is `null` with `orphan_detection: "unavailable_referenced_only"`, rather than a misleading `0`. Use the default mode when you want to find unreferenced files.

## Tests

```bash
python -m pytest tests/ -q
```

The tools do not refactor automatically. They are guardrails for coding agents that perform the refactor.
