---
name: browser-qa
description: Use when the user asks to "validate a web app", "check the rendered UI", "test responsive or viewport", "verify UX completion", or "check console errors" — QA a running web app in a real browser and report pass/fail with evidence.
---

# Browser QA

## Overview

Validate frontend work through actual rendered browser behavior, not source edits or build checks alone. Treat the browser run as evidence: route, flow, viewport, console, network, DOM, screenshot, and residual risk.

## Prerequisites and Clarification

- Identify the target server, URL, route set, expected flows, and protected browser state before testing.
- Discover or start the local server when the repo makes that safe and obvious.
- Ask for target routes only when they are not inferable from the request, app routing, or changed files.
- Ask before using external logged-in sessions, production systems, non-local browser state, or credentialed flows.
- Prefer the in-app Browser plugin for local targets when callable; use Playwright or another current browser path when that is the available reliable option.

## Workflow

1. Establish scope: target route/server, changed UI surface, expected workflows, desktop/mobile viewport set, and before/after comparison need.
2. Inspect repo evidence for app start commands and routes. Do not invent package managers, ports, paths, services, or validation results.
3. Open target routes in a real browser path.
4. Capture console errors, failed network requests, route/DOM facts, and screenshots when useful for evidence or later comparison.
5. Exercise expected user flows, including primary interactions, loading/error states that are in scope, and responsive layout behavior.
6. Compare before/after only when a baseline exists or the user requested parity; otherwise report current rendered behavior.
7. Report pass/fail per route or flow with evidence, skipped checks, and remaining UI risk.

Use `browser-probe` for repeatable scripted browser checks when available. Use `ui-parity-validator` for source-target visual matching when available.

## Verification Gates

| Gate | Requirement |
|---|---|
| G0 Scope | Target route/server, allowed browser state, and protected paths are known. |
| G1 Evidence | Expected user flows and route evidence are identified from the request or repo. |
| G2 Plan | Routes, flows, viewports, and comparison targets are explicit before execution. |
| G3 Execution | Browser checks run in the allowed scope. |
| G4 Validation | Screenshots, DOM assertions, console/network status, or interaction results are captured. |
| G5 Reporting | Final report states rendered pass/fail and residual UI risk. |

## Acceptance Criteria

- UI is rendered through a real browser path.
- Important routes and workflows are checked at relevant desktop and mobile/responsive viewports.
- Console, network, layout, interaction, and screenshot evidence is reported when relevant.
- Failures and skipped checks are visible; completion is not claimed from build or source checks alone.

## Expected Outcome

Produce a browser-visible QA report with checked routes, flows, viewports, evidence captured, pass/fail status, screenshots where useful, skipped checks, and remaining UI risk.

## Common Mistakes

- Treating a successful build, test, or source review as rendered UI validation.
- Testing only one viewport when responsive behavior is in scope.
- Ignoring console errors, failed requests, broken focus/interaction, or layout overflow because the page "looks okay."
- Inventing routes, ports, credentials, browser tools, or screenshot evidence.
- Using production or logged-in browser state without permission.
- Omitting skipped routes or residual UI risk from the final report.
