---
name: browser-probe
description: Use when the user asks for "browser automation", "scripted screenshots", "console capture", "DOM assertions", or "Playwright checks" (including legacy mcp__playwright names) — run repeatable scripted browser probes and capture evidence.
---

# Browser Probe

## Overview

Run a small, evidence-producing browser probe before claiming browser-visible behavior works. Prefer the current Browser plugin for known local targets; use the bundled script when a repeatable fallback is useful or direct browser tools are unavailable. Use `browser-qa` for broad rendered UI validation, full-route coverage, or user-flow QA; `browser-probe` owns repeatable scripted evidence.

## Workflow

1. Establish the target:
   - Confirm the URL, required login/session state, and viewport list.
   - Ask before installing browser or package dependencies unless the user explicitly requested setup.
   - Treat old tool names like `mcp__playwright` as intent, then map them to the current Browser plugin, Playwright MCP, or `scripts/browser_probe.mjs`.

2. Check browser capability:
   - For local targets, prefer the Browser plugin when available.
   - For scripted fallback, verify Node, `playwright-core` or `playwright`, and an installed Chrome executable or `CHROME_PATH`.
   - If a dependency is missing, report the missing piece instead of silently switching to an unverified path.

3. Probe each viewport:
   - Capture a screenshot.
   - Collect console messages, page errors, request failures, HTTP 4xx/5xx responses, title, URL, body text length, and basic DOM facts.
   - Add task-specific DOM checks when the user names selectors, text, or layout expectations.

4. Return evidence:
   - Summarize pass/fail in compact Markdown.
   - Attach or name generated screenshot and JSON artifacts.
   - Call out limitations such as unauthenticated state, blocked navigation, missing assets, or skipped viewports.

## Script

Use `scripts/browser_probe.mjs` for deterministic fallback checks:

```powershell
node .\scripts\browser_probe.mjs --url http://localhost:3000 --viewport 1440x900 --viewport 390x844 --out .\artifacts\browser-probe --wait-until domcontentloaded --settle-ms 500 --expect-text "Dashboard" --selector-exists "#app"
```

Run from this skill folder or pass the full script path from another working directory. The script defaults to `--wait-until domcontentloaded`; use `--wait-until load` or a short `--settle-ms` delay for SPAs that render after initial navigation, and reserve `networkidle` for pages where quiet network behavior is expected. Set `CHROME_PATH` when Chrome is installed in a nonstandard location.

## Verification Gates

| Gate | Requirement |
| --- | --- |
| G0 | URL and viewport set are known. |
| G1 | Browser tool, Playwright package, and Chrome availability are checked. |
| G3 | Probe executes against the requested target. |
| G4 | Screenshot, console, DOM, and response-failure evidence is created or the blocker is diagnosed. |

## Acceptance Criteria

- Probe output is deterministic enough to rerun and compare.
- Missing browser dependencies are explicit in the result.
- Old browser tool names are mapped to current operations.
- The final answer includes artifact paths and the browser-visible evidence that supports the conclusion.

## Expected Outcome

A reusable browser probe result: compact Markdown findings plus optional screenshots and JSON evidence for each viewport.

## Common Mistakes

- Claiming a UI works after only checking `/api/health` or server logs.
- Treating a screenshot as sufficient while ignoring console errors or failed responses.
- Hiding missing Browser plugin, Playwright, Chrome, or authentication requirements.
- Reusing stale direct tool names instead of mapping them to available tools.
- Stopping after one desktop viewport when the task requested responsive behavior.
