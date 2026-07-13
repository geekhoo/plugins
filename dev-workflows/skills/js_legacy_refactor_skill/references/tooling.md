# Tooling bundled with this skill

The tools live in this skill's `tools/` directory (resolve the path from the skill's own directory, e.g. `<plugin-root>/skills/js_legacy_refactor_skill/tools/` — the examples below assume you substitute that absolute path for `tools/`). Run them from the root of the app being refactored.

## Static audit and comparison

```bash
python tools/js_legacy_refactor_audit.py audit /path/to/app --out /path/to/app/.refactor_audit/baseline
python tools/js_legacy_refactor_audit.py audit /path/to/app-refactored --out /path/to/app/.refactor_audit/after
python tools/js_legacy_refactor_audit.py compare /path/to/app/.refactor_audit/baseline/audit.json /path/to/app/.refactor_audit/after/audit.json --out /path/to/app/.refactor_audit/static-compare.md
```

The audit tool is dependency-free Python. It intentionally reports conservative warnings and may over-report. Treat warnings as investigation targets, not automatic proof.

## Optional browser regression probe

```bash
cd /path/to/app
npm install --save-dev playwright
npx playwright install chromium
node tools/browser_regression_probe.mjs snapshot --root . --url http://127.0.0.1:8080 --pages index.html,settings.html --out .refactor_audit/browser-baseline.json
node tools/browser_regression_probe.mjs snapshot --root ../app-refactored --url http://127.0.0.1:8081 --pages index.html,settings.html --out .refactor_audit/browser-after.json
node tools/browser_regression_probe.mjs compare .refactor_audit/browser-baseline.json .refactor_audit/browser-after.json --out .refactor_audit/browser-compare.md
```

Run the same local server behavior for baseline and refactored trees. Do not compare `file://` behavior to HTTP behavior because module loading, CORS, relative URLs, and origin behavior differ.
