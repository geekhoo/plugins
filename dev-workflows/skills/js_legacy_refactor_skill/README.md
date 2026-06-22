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

The tools do not refactor automatically. They are guardrails for coding agents that perform the refactor.
