---
name: dx-ux-review
description: Use when reviewing DevExtreme jQuery pages for fit, correctness, scope, states, and validation — including the render gate that verifies generated UI in a real browser before it is claimed working.
---

# DevExtreme UX Review

Use this checklist when reviewing generated or modified DevExtreme jQuery pages:

- Correct widget selected for each UX need.
- No framework code, JSX, TSX, or wrapper package usage.
- No ThemeBuilder output.
- Correct script and CSS load order.
- Widget containers exist in `index.html`.
- Widget options are used instead of unnecessary CSS overrides.
- Styling is wrapper-scoped.
- Loading, empty, error, disabled, and validation states exist where relevant.
- Keyboard navigation and focus behavior are considered.
- Labels and input attributes are present.
- Responsive layout is stable.
- Text does not overflow its container.
- Data formatting is appropriate for dates, numbers, currency, status, and summaries.
- Static validation scripts pass.
- Browser smoke test is recommended for generated UI.

Report concrete file and line findings first when reviewing code. Do not claim browser validation unless it was actually run.

## Render gate — verify in a real browser before "done"

Static checks cannot prove a DevExtreme page renders. Before generated or modified UI is reported working:

1. Serve the page over local HTTP (Playwright MCP blocks `file://` — e.g. `py -3 -m http.server` from the app directory).
2. Run the `browser-verify` skill (works with Chrome DevTools MCP or Playwright MCP, Browser-pane fallback), or `browser-qa` from dev-workflows when a user flow needs exercising end-to-end.
3. Minimum evidence: the page loads with zero console errors, every widget container actually instantiated a widget (no empty divs), and a screenshot of the key states.
4. Name in the report exactly what was run and observed — this section is how the "do not claim browser validation" rule above gets satisfied, not bypassed.
